import sqlite3
import json
from datetime import date, datetime
import config


def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            account      TEXT NOT NULL,
            description  TEXT NOT NULL,
            category     TEXT,
            tags         TEXT,
            amount       REAL NOT NULL,
            import_batch TEXT NOT NULL,
            source       TEXT DEFAULT 'csv',
            raw_json     TEXT,
            UNIQUE(date, account, description, amount)
        );

        CREATE TABLE IF NOT EXISTS account_balances (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            account       TEXT NOT NULL,
            balance       REAL NOT NULL,
            account_type  TEXT,
            import_batch  TEXT NOT NULL,
            UNIQUE(snapshot_date, account)
        );

        CREATE TABLE IF NOT EXISTS net_worth_snapshots (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date     TEXT NOT NULL UNIQUE,
            total_assets      REAL NOT NULL,
            total_liabilities REAL NOT NULL,
            net_worth         REAL NOT NULL,
            computed_at       TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_type TEXT NOT NULL,
            label      TEXT NOT NULL,
            amount     REAL,
            recurrence TEXT DEFAULT 'none',
            notes      TEXT,
            source     TEXT DEFAULT 'knowledge',
            UNIQUE(event_date, label)
        );

        CREATE TABLE IF NOT EXISTS screenshot_parses (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            filename       TEXT NOT NULL,
            parsed_at      TEXT DEFAULT CURRENT_TIMESTAMP,
            extracted_json TEXT,
            tokens_used    INTEGER,
            status         TEXT DEFAULT 'ok'
        );

        CREATE TABLE IF NOT EXISTS budget_categories (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            category       TEXT NOT NULL UNIQUE,
            monthly_target REAL,
            active         INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS budget_plan (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            year           INTEGER NOT NULL,
            month          INTEGER NOT NULL,
            category       TEXT NOT NULL,
            planned_amount REAL NOT NULL,
            notes          TEXT,
            UNIQUE(year, month, category)
        );

        CREATE TABLE IF NOT EXISTS budget_month_status (
            year      INTEGER NOT NULL,
            month     INTEGER NOT NULL,
            locked    INTEGER DEFAULT 0,
            locked_at TEXT,
            PRIMARY KEY (year, month)
        );

        CREATE TABLE IF NOT EXISTS budget_actuals_notes (
            year     INTEGER NOT NULL,
            month    INTEGER NOT NULL,
            category TEXT NOT NULL,
            note     TEXT,
            PRIMARY KEY (year, month, category)
        );

        CREATE INDEX IF NOT EXISTS idx_txn_date      ON transactions(date);
        CREATE INDEX IF NOT EXISTS idx_txn_category  ON transactions(category);
        CREATE INDEX IF NOT EXISTS idx_balances_date ON account_balances(snapshot_date);
        CREATE INDEX IF NOT EXISTS idx_events_date   ON events(event_date);
        CREATE INDEX IF NOT EXISTS idx_budget_ym     ON budget_plan(year, month);
    """)
    conn.commit()
    conn.close()
    print("DB initialized.")


# --- Transactions ---

def save_transactions(rows, import_batch):
    """
    rows: list of dicts with keys: date, account, description, category, tags, amount
    Returns (new_count, skipped_count)
    """
    conn = get_conn()
    new_count = 0
    skipped = 0
    for row in rows:
        cur = conn.execute(
            """INSERT OR IGNORE INTO transactions
               (date, account, description, category, tags, amount, import_batch, source, raw_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                row["date"], row["account"], row["description"],
                row.get("category"), row.get("tags"), row["amount"],
                import_batch, row.get("source", "csv"),
                json.dumps(row)
            )
        )
        if cur.rowcount:
            new_count += 1
        else:
            skipped += 1
    conn.commit()
    conn.close()
    return new_count, skipped


def get_transactions(start_date=None, end_date=None, category=None):
    conn = get_conn()
    q = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if start_date:
        q += " AND date >= ?"
        params.append(start_date)
    if end_date:
        q += " AND date <= ?"
        params.append(end_date)
    if category:
        q += " AND category = ?"
        params.append(category)
    q += " ORDER BY date DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_spending_by_category(start_date=None, end_date=None):
    """Returns list of {category, total} for expenses (amount < 0) sorted by total desc."""
    conn = get_conn()
    q = """
        SELECT category, ROUND(SUM(ABS(amount)), 2) as total
        FROM transactions
        WHERE amount < 0
    """
    params = []
    if start_date:
        q += " AND date >= ?"
        params.append(start_date)
    if end_date:
        q += " AND date <= ?"
        params.append(end_date)
    q += " GROUP BY category ORDER BY total DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_categories():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT category FROM transactions WHERE category IS NOT NULL ORDER BY category"
    ).fetchall()
    conn.close()
    return [r["category"] for r in rows]


# --- Account Balances ---

def save_balances(rows, import_batch):
    """
    rows: list of dicts with keys: snapshot_date, account, balance, account_type
    Returns (new_count, skipped_count)
    """
    conn = get_conn()
    new_count = 0
    skipped = 0
    for row in rows:
        cur = conn.execute(
            """INSERT OR REPLACE INTO account_balances
               (snapshot_date, account, balance, account_type, import_batch)
               VALUES (?,?,?,?,?)""",
            (row["snapshot_date"], row["account"], row["balance"],
             row.get("account_type"), import_batch)
        )
        if cur.rowcount:
            new_count += 1
        else:
            skipped += 1
    conn.commit()
    conn.close()
    return new_count, skipped


def get_latest_balances():
    """Returns the most recent balance for each account."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*
        FROM account_balances a
        INNER JOIN (
            SELECT account, MAX(snapshot_date) as max_date
            FROM account_balances
            GROUP BY account
        ) b ON a.account = b.account AND a.snapshot_date = b.max_date
        ORDER BY a.account_type, a.account
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Net Worth ---

def recompute_net_worth():
    """
    For each unique snapshot_date in account_balances, compute and upsert net worth.
    Returns list of dates updated.
    """
    conn = get_conn()
    dates = conn.execute(
        "SELECT DISTINCT snapshot_date FROM account_balances ORDER BY snapshot_date"
    ).fetchall()

    updated = []
    for row in dates:
        snap_date = row["snapshot_date"]
        balances = conn.execute(
            "SELECT balance, account_type FROM account_balances WHERE snapshot_date = ?",
            (snap_date,)
        ).fetchall()

        total_assets = 0.0
        total_liabilities = 0.0
        for b in balances:
            bal = b["balance"]
            atype = (b["account_type"] or "").lower()
            if atype in ("credit", "loan", "mortgage") or bal < 0:
                total_liabilities += abs(bal)
            else:
                total_assets += bal

        net_worth = total_assets - total_liabilities
        conn.execute(
            """INSERT OR REPLACE INTO net_worth_snapshots
               (snapshot_date, total_assets, total_liabilities, net_worth, computed_at)
               VALUES (?,?,?,?,?)""",
            (snap_date, round(total_assets, 2), round(total_liabilities, 2),
             round(net_worth, 2), datetime.now().isoformat())
        )
        updated.append(snap_date)

    conn.commit()
    conn.close()
    return updated


def get_net_worth_history():
    conn = get_conn()
    rows = conn.execute(
        "SELECT snapshot_date, total_assets, total_liabilities, net_worth FROM net_worth_snapshots ORDER BY snapshot_date"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_net_worth():
    conn = get_conn()
    row = conn.execute(
        "SELECT net_worth, snapshot_date FROM net_worth_snapshots ORDER BY snapshot_date DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return {"net_worth": row["net_worth"], "date": row["snapshot_date"]}
    return None


# --- Events ---

def upsert_event(event):
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO events
           (event_date, event_type, label, amount, recurrence, notes, source)
           VALUES (?,?,?,?,?,?,?)""",
        (
            event["event_date"], event["event_type"], event["label"],
            event.get("amount"), event.get("recurrence", "none"),
            event.get("notes"), event.get("source", "knowledge")
        )
    )
    conn.commit()
    conn.close()


def get_events(future_only=False):
    conn = get_conn()
    q = "SELECT * FROM events"
    params = []
    if future_only:
        q += " WHERE event_date >= ?"
        params.append(date.today().isoformat())
    q += " ORDER BY event_date"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_event(event_id):
    conn = get_conn()
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


# --- Screenshot Parses ---

def log_screenshot_parse(filename, extracted_json, tokens_used, status="ok"):
    conn = get_conn()
    conn.execute(
        """INSERT INTO screenshot_parses (filename, extracted_json, tokens_used, status)
           VALUES (?,?,?,?)""",
        (filename, json.dumps(extracted_json) if extracted_json else None, tokens_used, status)
    )
    conn.commit()
    conn.close()


# --- Budget Categories ---

def get_budget_categories():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM budget_categories WHERE active = 1 ORDER BY category"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_budget_target(category, monthly_target):
    conn = get_conn()
    conn.execute(
        """INSERT INTO budget_categories (category, monthly_target)
           VALUES (?,?)
           ON CONFLICT(category) DO UPDATE SET monthly_target = excluded.monthly_target""",
        (category, monthly_target)
    )
    conn.commit()
    conn.close()


def ensure_budget_categories(categories):
    """Create budget_categories rows (no target) for any new categories found in transactions."""
    conn = get_conn()
    for cat in categories:
        conn.execute(
            "INSERT OR IGNORE INTO budget_categories (category, monthly_target) VALUES (?,NULL)",
            (cat,)
        )
    conn.commit()
    conn.close()


# --- Analytics helpers ---

def get_avg_monthly_income(lookback_days=90):
    conn = get_conn()
    from datetime import timedelta
    since = (date.today() - timedelta(days=lookback_days)).isoformat()
    row = conn.execute(
        "SELECT SUM(amount) as total FROM transactions WHERE amount > 0 AND date >= ?",
        (since,)
    ).fetchone()
    conn.close()
    total = row["total"] or 0.0
    months = lookback_days / 30.0
    return round(total / months, 2)


def get_avg_monthly_spend(lookback_days=90):
    conn = get_conn()
    from datetime import timedelta
    since = (date.today() - timedelta(days=lookback_days)).isoformat()
    row = conn.execute(
        "SELECT SUM(ABS(amount)) as total FROM transactions WHERE amount < 0 AND date >= ?",
        (since,)
    ).fetchone()
    conn.close()
    total = row["total"] or 0.0
    months = lookback_days / 30.0
    return round(total / months, 2)


# --- Budget Plan (from PDF) ---

BUDGET_CATEGORIES = [
    "nastya_income", "pratik_income", "monthly_expenses",
    "one_time_income", "one_time_expense", "hysa", "roth", "net_income"
]


def save_budget_plan(rows):
    """
    rows: list of dicts: year, month, category, planned_amount, notes
    INSERT OR REPLACE so re-importing a new PDF updates values.
    """
    conn = get_conn()
    count = 0
    for row in rows:
        conn.execute(
            """INSERT OR REPLACE INTO budget_plan (year, month, category, planned_amount, notes)
               VALUES (?,?,?,?,?)""",
            (row["year"], row["month"], row["category"],
             row["planned_amount"], row.get("notes"))
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def get_budget_plan(year, month):
    """Returns dict of {category: {amount, notes}} for a given month."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, planned_amount, notes FROM budget_plan WHERE year=? AND month=?",
        (year, month)
    ).fetchall()
    conn.close()
    return {r["category"]: {"amount": r["planned_amount"], "notes": r["notes"]} for r in rows}


def get_budget_plan_range():
    """Returns (min_ym, max_ym) as (year, month) tuples. None if no data."""
    conn = get_conn()
    row = conn.execute(
        "SELECT MIN(year*100+month) as mn, MAX(year*100+month) as mx FROM budget_plan"
    ).fetchone()
    conn.close()
    if not row or not row["mn"]:
        return None, None
    mn, mx = row["mn"], row["mx"]
    return (mn // 100, mn % 100), (mx // 100, mx % 100)


def get_projected_checking(year, month, checking_account="BFSFCU Checking"):
    """
    Projects checking account balance at the end of a given month.
    Starts from the latest actual checking snapshot balance, then adds
    planned net cash for each month AFTER the snapshot through the target month.
    If the target month is at or before the snapshot month, returns the actual balance.
    Net cash per month = SUM(planned_amount) since income is positive, expenses negative.
    """
    conn = get_conn()

    # Get the actual checking balance and its snapshot date
    row = conn.execute(
        "SELECT balance, snapshot_date FROM account_balances WHERE account=? ORDER BY snapshot_date DESC LIMIT 1",
        (checking_account,)
    ).fetchone()
    if not row:
        conn.close()
        return None

    start_balance = row["balance"]
    snap_date = row["snapshot_date"]
    snap_year = int(snap_date[:4])
    snap_month = int(snap_date[5:7])

    # If the target is at or before the snapshot month, the actual balance is the answer
    if (year, month) <= (snap_year, snap_month):
        conn.close()
        return round(start_balance, 2)

    # Build list of months from the month AFTER the snapshot through target
    months = []
    y, m = snap_year, snap_month + 1
    if m > 12:
        m = 1
        y += 1
    while (y, m) <= (year, month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1

    # Exclude summary/computed rows that duplicate individual line items
    EXCLUDE_CATS = ("monthly_expenses", "net_income")
    placeholders = ",".join("?" for _ in EXCLUDE_CATS)

    cumulative = start_balance
    for y, m in months:
        row = conn.execute(
            f"SELECT COALESCE(SUM(planned_amount), 0) as net FROM budget_plan WHERE year=? AND month=? AND category NOT IN ({placeholders})",
            (y, m, *EXCLUDE_CATS)
        ).fetchone()
        cumulative += row["net"]

    conn.close()
    return round(cumulative, 2)


def get_latest_transaction_date():
    conn = get_conn()
    row = conn.execute("SELECT MAX(date) as d FROM transactions").fetchone()
    conn.close()
    return row["d"] if row and row["d"] else None


def lock_month(year, month):
    conn = get_conn()
    conn.execute(
        """INSERT INTO budget_month_status (year, month, locked, locked_at)
           VALUES (?,?,1,?)
           ON CONFLICT(year, month) DO UPDATE SET locked=1, locked_at=excluded.locked_at""",
        (year, month, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_month_status(year, month):
    conn = get_conn()
    row = conn.execute(
        "SELECT locked, locked_at FROM budget_month_status WHERE year=? AND month=?",
        (year, month)
    ).fetchone()
    conn.close()
    if row:
        return {"locked": bool(row["locked"]), "locked_at": row["locked_at"]}
    return {"locked": False, "locked_at": None}


def get_actuals_by_budget_category(year, month):
    """
    Scan transactions for the month, apply BUDGET_CATEGORY_RULES.
    Returns {budget_cat: total_spent} where total_spent is a positive number.
    Unmatched expenses go to expenses_buffer_misc.
    Income transactions (amount > 0) skipped.
    CC payment rows and investment/retirement account transactions are excluded.
    """
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{last_day:02d}"

    conn = get_conn()
    rows = conn.execute(
        "SELECT description, category, amount, account FROM transactions WHERE date>=? AND date<=? AND amount<0",
        (start, end)
    ).fetchall()
    conn.close()

    # Skip CC payment rows from checking account (double-counts the actual charge on the CC)
    SKIP_CATS = {"credit card payments", "securities trades", "investment income"}
    # Skip transactions from investment/retirement accounts (not real spending)
    INVEST_ACCT_KEYS = (
        "roth ira", "brokerage", "401(k)", "401k",
        "designated beneficiary", "equity awards", "google llc 401",
    )

    rules = config.BUDGET_CATEGORY_RULES
    totals = {}

    for row in rows:
        desc = (row["description"] or "").lower()
        cat  = (row["category"]    or "").lower()
        acct = (row["account"]     or "").lower()
        spent = abs(row["amount"])

        if cat in SKIP_CATS:
            continue
        if any(kw in acct for kw in INVEST_ACCT_KEYS):
            continue

        matched = None
        for keyword, budget_cat in rules.items():
            if keyword in desc:
                matched = budget_cat
                break
        if matched is None:
            for keyword, budget_cat in rules.items():
                if keyword in cat:
                    matched = budget_cat
                    break
        # Skip generic transfers that didn't match a savings/spending keyword
        if matched is None and cat == "transfers":
            continue
        if matched is None:
            matched = "expenses_buffer_misc"

        totals[matched] = round(totals.get(matched, 0.0) + spent, 2)

    return totals


def get_transactions_by_budget_category(year, month, budget_cat):
    """
    Return individual transactions that map to budget_cat for a given month.
    Applies the same filtering as get_actuals_by_budget_category.
    """
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year}-{month:02d}-01"
    end   = f"{year}-{month:02d}-{last_day:02d}"

    conn = get_conn()
    rows = conn.execute(
        "SELECT date, description, category, amount, account FROM transactions "
        "WHERE date>=? AND date<=? AND amount<0 ORDER BY date",
        (start, end)
    ).fetchall()
    conn.close()

    SKIP_CATS = {"credit card payments", "securities trades", "investment income"}
    INVEST_ACCT_KEYS = (
        "roth ira", "brokerage", "401(k)", "401k",
        "designated beneficiary", "equity awards", "google llc 401",
    )
    rules = config.BUDGET_CATEGORY_RULES
    result = []

    for row in rows:
        desc = (row["description"] or "").lower()
        cat  = (row["category"]    or "").lower()
        acct = (row["account"]     or "").lower()

        if cat in SKIP_CATS:
            continue
        if any(kw in acct for kw in INVEST_ACCT_KEYS):
            continue

        matched = None
        for keyword, bc in rules.items():
            if keyword in desc:
                matched = bc
                break
        if matched is None:
            for keyword, bc in rules.items():
                if keyword in cat:
                    matched = bc
                    break
        if matched is None and cat == "transfers":
            continue
        if matched is None:
            matched = "expenses_buffer_misc"

        if matched == budget_cat:
            result.append({
                "date":        row["date"],
                "description": row["description"],
                "amount":      row["amount"],
                "account":     row["account"],
            })

    return result


def get_actual_income_total(year, month):
    """
    Sum of real income deposits for the month.
    Excludes: CC payment credits, investment/retirement account transactions,
    and plain transfers (Roth contributions, HYSA sweeps, etc.).
    """
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{last_day:02d}"

    SKIP_CATS = {"credit card payments", "securities trades", "investment income"}
    INVEST_ACCT_KEYS = (
        "roth ira", "brokerage", "401(k)", "401k",
        "designated beneficiary", "equity awards", "google llc 401",
    )

    conn = get_conn()
    rows = conn.execute(
        "SELECT amount, category, account FROM transactions WHERE amount>0 AND date>=? AND date<=?",
        (start, end)
    ).fetchall()
    conn.close()

    total = 0.0
    for row in rows:
        cat  = (row["category"] or "").lower()
        acct = (row["account"]  or "").lower()
        if cat in SKIP_CATS:
            continue
        if any(kw in acct for kw in INVEST_ACCT_KEYS):
            continue
        if cat == "transfers":
            continue
        total += row["amount"]

    return round(total, 2)


def get_budget_vs_actual(year, month):
    """Combines budget plan for the month with actual transaction totals."""
    import calendar
    plan = get_budget_plan(year, month)
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{last_day:02d}"
    conn = get_conn()
    inc = conn.execute(
        "SELECT COALESCE(SUM(amount),0) as t FROM transactions WHERE amount>0 AND date>=? AND date<=?",
        (start, end)
    ).fetchone()
    exp = conn.execute(
        "SELECT COALESCE(SUM(ABS(amount)),0) as t FROM transactions WHERE amount<0 AND date>=? AND date<=?",
        (start, end)
    ).fetchone()
    conn.close()
    return {
        "year": year, "month": month,
        "plan": plan,
        "actual_income": round(inc["t"], 2),
        "actual_expenses": round(exp["t"], 2),
    }

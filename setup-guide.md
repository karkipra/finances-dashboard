# Personal Finance Dashboard - Setup Guide

A local Flask dashboard for tracking net worth, monthly budgets (planned vs. actual), and long-term projections. Copy this guide into Claude Code and follow the steps to build your own.

---

## What This Builds

- **Monthly Budget page** - planned vs. actual spending by sub-category, inline notes, month locking
- **Net Worth page** - account balance history chart, grouped by account type, equity vesting cards
- **Forecast page** - 24-month net worth projection with confidence bands
- **Spending page** - transaction breakdown by category and date range
- **Events page** - future financial milestones (salary changes, large purchases, etc.)

Stack: Python, Flask, SQLite, Chart.js, vanilla JS. No React, no build step, runs entirely on localhost.

---

## Project Structure

```
finances-dashboard/
  app.py               - Flask routes and API endpoints
  config.py            - Constants, API keys, account aliases, category rules
  storage.py           - SQLite CRUD layer
  ingest.py            - Weekly data import orchestrator
  parse_csv.py         - Empower + CC statement CSV parsing
  parse_screenshot.py  - Claude Vision: screenshot -> account balance
  parse_pdf.py         - PDF budget parsing (optional)
  seed_budget.py       - One-time seed of 12-24 month budget plan
  knowledge_base.py    - Syncs knowledge.yaml events to DB
  knowledge.yaml       - Life events: salary changes, big purchases, subscriptions
  forecast.py          - Net worth projection logic
  equity.py            - Equity vesting calculator (optional)
  templates/
    base.html          - Navbar, theme toggle, Chart.js, shared JS utils
    budget.html        - Monthly Budget page
    net_worth.html     - Net Worth page
    spending.html      - Spending breakdown
    forecast.html      - Projection chart
    events.html        - Financial events editor
  static/
    style.css          - Dark/light theme, all component styles
  data/
    finances.db        - SQLite database (gitignore this)
  imports/             - Drop CSVs/screenshots here for weekly ingest
    processed/         - Auto-archived after ingest
```

---

## Step 1 - Environment Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install flask python-dotenv anthropic requests pyyaml
```

Create `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Create `.gitignore`:
```
.env
data/
venv/
imports/processed/
__pycache__/
*.pyc
```

---

## Step 2 - config.py

This is the single source of truth. Customize every section for your situation.

```python
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

# Paths
DB_PATH = PROJECT_DIR / "data" / "finances.db"
IMPORTS_DIR = PROJECT_DIR / "imports"
KNOWLEDGE_FILE = PROJECT_DIR / "knowledge.yaml"

# Flask
FLASK_PORT = 5000
FLASK_DEBUG = True

# Anthropic (for screenshot parsing and KB suggestions)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Income ---
# Fill in your household's post-tax monthly take-home for each income source.
# These are used as fallback values when transaction history is too thin to average.
PERSON_A_MONTHLY_NET = 0.00   # e.g. your W-2 monthly net
PERSON_B_MONTHLY_NET = 0.00   # e.g. partner's monthly net (0 if single)
COMBINED_MONTHLY_NET = PERSON_A_MONTHLY_NET + PERSON_B_MONTHLY_NET

# --- Savings accounts not in Empower ---
# Update these manually each month if not auto-imported
HYSA_BALANCE = 0.00
HYSA_APY = 0.045
HYSA_MONTHLY_CONTRIBUTION = 500.00

# --- Account name aliases ---
# Maps raw institution names (from Empower CSV) to friendly display names.
# Empower sometimes exports generic names like "Manual Bank".
ACCOUNT_ALIASES = {
    # "Manual Bank": "Ally HYSA",
    # "Cash": "Chase Checking",
}

# --- Account type classification ---
# Keywords that identify liabilities (subtracted from net worth)
LIABILITY_KEYWORDS = {"credit card", "credit", "loan", "mortgage", "debt"}
# Keywords that identify income in transaction descriptions
INCOME_KEYWORDS = {"payroll", "direct deposit", "ach credit", "zelle", "venmo credit", "refund"}

# --- Budget category rules ---
# Maps merchant keywords (lowercase) to budget sub-category keys.
# Two-stage: checks transaction description first, then category field.
# Order matters - more specific rules go first. Fallback: expenses_buffer_misc.
BUDGET_CATEGORY_RULES = {
    # Groceries
    "whole foods": "expenses_groceries",
    "trader joe": "expenses_groceries",
    "safeway": "expenses_groceries",
    "kroger": "expenses_groceries",
    # Dining
    "doordash": "expenses_dining",
    "uber eats": "expenses_dining",
    "grubhub": "expenses_dining",
    # Transportation
    "shell": "expenses_gas",
    "chevron": "expenses_gas",
    "exxon": "expenses_gas",
    "uber": "expenses_transport",
    "lyft": "expenses_transport",
    # Utilities
    "at&t": "expenses_phone",
    "verizon": "expenses_phone",
    "comcast": "expenses_internet",
    "xfinity": "expenses_internet",
    # Subscriptions
    "netflix": "expenses_subscriptions",
    "spotify": "expenses_subscriptions",
    "hulu": "expenses_subscriptions",
    "amazon prime": "expenses_subscriptions",
    # Healthcare
    "cvs": "expenses_healthcare",
    "walgreens": "expenses_healthcare",
    # Fitness
    "gym": "expenses_fitness",
    "planet fitness": "expenses_fitness",
    # Rent/mortgage - usually a large ACH, match by description keyword
    "rent": "expenses_rent",
    "mortgage": "expenses_rent",
    # Transfers to skip (not real spending)
    "american express payment": "SKIP",
    "chase autopay": "SKIP",
    "transfer to savings": "SKIP",
    "brokerage": "SKIP",
    "investment": "SKIP",
    "401k": "SKIP",
    "ira contribution": "SKIP",
}

# --- Data sources status (for the UI checklist on Net Worth page) ---
# Tracks which accounts are connected to Empower vs. manual vs. todo.
DATA_SOURCES = [
    {"label": "Checking", "status": "connected", "notes": "Via Empower CSV"},
    {"label": "HYSA", "status": "manual", "notes": "Update balance monthly"},
    {"label": "Roth IRA", "status": "connected", "notes": "Via Empower"},
    {"label": "401k", "status": "connected", "notes": "Via Empower"},
    {"label": "Credit Card", "status": "connected", "notes": "Via Empower"},
    # Add more as needed
]

# --- Forecast parameters ---
FORECAST_MONTHS = 24
FORECAST_LOOKBACK_DAYS = 90
FORECAST_VOLATILITY_PCT = 0.15  # +/- 15% confidence band

# --- Equity grants (optional) ---
# If you have company equity, define vesting schedules here.
# Set to None to disable equity cards on the Net Worth page.
#
# MY_EQUITY = {
#     "company": "Acme Corp",
#     "total_shares": 100_000,
#     "cost_basis": 10.00,           # total $ paid for the grant
#     "current_price_per_share": 0.0, # update when valuation changes
#     "vesting_start": "2024-01-01",
#     "cliff_date": "2025-01-01",
#     "cliff_shares": 25_000,        # 1-year cliff
#     "monthly_shares": 2_083,       # after cliff
#     "fully_vested_date": "2028-01-01",
# }
MY_EQUITY = None
```

---

## Step 3 - SQLite Schema (storage.py)

Create `storage.py` with `init_db()` that runs on startup:

```python
import sqlite3
import config

def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    config.DB_PATH.parent.mkdir(exist_ok=True)
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            account TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            amount REAL NOT NULL,
            import_batch TEXT NOT NULL,
            source TEXT DEFAULT 'csv',
            raw_json TEXT,
            UNIQUE(date, account, description, amount)
        );
        CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(date);
        CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category);

        CREATE TABLE IF NOT EXISTS account_balances (
            id INTEGER PRIMARY KEY,
            snapshot_date TEXT NOT NULL,
            account TEXT NOT NULL,
            balance REAL NOT NULL,
            account_type TEXT,
            import_batch TEXT NOT NULL,
            UNIQUE(snapshot_date, account)
        );
        CREATE INDEX IF NOT EXISTS idx_balances_date ON account_balances(snapshot_date);

        CREATE TABLE IF NOT EXISTS net_worth_snapshots (
            id INTEGER PRIMARY KEY,
            snapshot_date TEXT UNIQUE NOT NULL,
            total_assets REAL NOT NULL,
            total_liabilities REAL NOT NULL,
            net_worth REAL NOT NULL,
            computed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            event_date TEXT NOT NULL,
            event_type TEXT NOT NULL,
            label TEXT NOT NULL,
            amount REAL,
            recurrence TEXT DEFAULT 'none',
            notes TEXT,
            source TEXT DEFAULT 'knowledge',
            UNIQUE(event_date, label)
        );
        CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);

        CREATE TABLE IF NOT EXISTS budget_plan (
            id INTEGER PRIMARY KEY,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            category TEXT NOT NULL,
            planned_amount REAL NOT NULL,
            notes TEXT,
            UNIQUE(year, month, category)
        );
        CREATE INDEX IF NOT EXISTS idx_budget_ym ON budget_plan(year, month);

        CREATE TABLE IF NOT EXISTS budget_month_status (
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            locked INTEGER DEFAULT 0,
            locked_at TEXT,
            PRIMARY KEY (year, month)
        );

        CREATE TABLE IF NOT EXISTS budget_actuals_notes (
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            PRIMARY KEY (year, month, category)
        );

        CREATE TABLE IF NOT EXISTS screenshot_parses (
            id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            parsed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            extracted_json TEXT,
            tokens_used INTEGER,
            status TEXT DEFAULT 'ok'
        );
    """)
    conn.commit()
    conn.close()
```

Key patterns in `storage.py`:

```python
# Save transactions (deduplication is automatic via UNIQUE constraint)
def save_transactions(rows: list[dict]) -> int:
    """Returns count of newly inserted rows (duplicates silently skipped)."""
    conn = get_conn()
    inserted = 0
    for row in rows:
        try:
            conn.execute("""
                INSERT INTO transactions (date, account, description, category, amount, import_batch, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row['date'], row['account'], row['description'],
                  row.get('category'), row['amount'], row['import_batch'],
                  row.get('raw_json')))
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # duplicate - skip silently
    conn.commit()
    conn.close()
    return inserted

# Recompute net worth from account_balances (call after every ingest)
def recompute_net_worth():
    conn = get_conn()
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT snapshot_date FROM account_balances ORDER BY snapshot_date"
    ).fetchall()]
    for d in dates:
        rows = conn.execute(
            "SELECT account, balance, account_type FROM account_balances WHERE snapshot_date=?", (d,)
        ).fetchall()
        assets, liabilities = 0.0, 0.0
        for r in rows:
            acct_type = (r['account_type'] or '').lower()
            name = r['account'].lower()
            is_liability = any(k in acct_type or k in name
                               for k in config.LIABILITY_KEYWORDS)
            if is_liability:
                liabilities += abs(r['balance'])
            else:
                assets += r['balance']
        conn.execute("""
            INSERT OR REPLACE INTO net_worth_snapshots
            (snapshot_date, total_assets, total_liabilities, net_worth)
            VALUES (?, ?, ?, ?)
        """, (d, assets, liabilities, assets - liabilities))
    conn.commit()
    conn.close()

# Get actuals by budget category (computed live from transactions)
def get_actuals_by_budget_category(year: int, month: int) -> dict:
    """Returns {category_key: total_spent} for the given month."""
    from_date = f"{year:04d}-{month:02d}-01"
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    to_date = f"{year:04d}-{month:02d}-{last_day:02d}"
    conn = get_conn()
    rows = conn.execute("""
        SELECT description, category, amount FROM transactions
        WHERE date >= ? AND date <= ? AND amount < 0
    """, (from_date, to_date)).fetchall()
    conn.close()

    totals = {}
    for row in rows:
        cat = _classify_transaction(row['description'], row['category'])
        if cat == "SKIP":
            continue
        totals[cat] = totals.get(cat, 0.0) + abs(row['amount'])
    return totals

def _classify_transaction(description: str, category: str) -> str:
    desc = (description or '').lower()
    cat = (category or '').lower()
    for keyword, budget_cat in config.BUDGET_CATEGORY_RULES.items():
        if keyword in desc or keyword in cat:
            return budget_cat
    return 'expenses_buffer_misc'
```

---

## Step 4 - CSV Parsing (parse_csv.py)

Empower exports two types of CSVs. Auto-detect by headers:

```python
import csv, json
from datetime import datetime

def parse_csv_file(filepath: str, import_batch: str) -> dict:
    """
    Auto-detects CSV type and returns:
    {
        'transactions': [...],  # list of transaction dicts
        'balances': [...],      # list of balance dicts
        'csv_type': 'empower_transactions' | 'empower_balances' | 'cc_statement' | 'unknown'
    }
    """
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in (reader.fieldnames or [])]
        rows = list(reader)

    if 'account name' in headers and 'amount' in headers and 'description' in headers:
        return _parse_empower_transactions(rows, import_batch)
    elif 'account name' in headers and 'balance' in headers:
        return _parse_empower_balances(rows, import_batch)
    elif 'transaction date' in headers and 'amount' in headers:
        return _parse_cc_statement(rows, import_batch)
    else:
        print(f"  Unknown CSV format. Headers: {headers}")
        return {'transactions': [], 'balances': [], 'csv_type': 'unknown'}

def _parse_empower_transactions(rows, import_batch):
    """Empower All Transactions CSV."""
    txns = []
    for row in rows:
        amount_raw = row.get('Amount', '0').replace('$', '').replace(',', '').strip()
        try:
            amount = float(amount_raw)
        except ValueError:
            continue
        # Expenses are negative, income is positive (Empower convention matches)
        txns.append({
            'date': _normalize_date(row.get('Date', '')),
            'account': row.get('Account Name', 'Unknown'),
            'description': row.get('Description', '').strip(),
            'category': row.get('Category', '').strip(),
            'amount': amount,
            'import_batch': import_batch,
            'raw_json': json.dumps(dict(row)),
        })
    return {'transactions': txns, 'balances': [], 'csv_type': 'empower_transactions'}

def _parse_empower_balances(rows, import_batch):
    """Empower Net Worth / Balance export CSV."""
    from config import ACCOUNT_ALIASES
    balances = []
    for row in rows:
        balance_raw = row.get('Balance', '0').replace('$', '').replace(',', '').strip()
        try:
            balance = float(balance_raw)
        except ValueError:
            continue
        account_raw = row.get('Account Name', 'Unknown').strip()
        account = ACCOUNT_ALIASES.get(account_raw, account_raw)
        balances.append({
            'snapshot_date': _normalize_date(row.get('Date', '')),
            'account': account,
            'balance': balance,
            'account_type': row.get('Account Type', '').strip().lower(),
            'import_batch': import_batch,
        })
    return {'transactions': [], 'balances': balances, 'csv_type': 'empower_balances'}

def _parse_cc_statement(rows, import_batch):
    """Direct CC statement (Amex, Chase, etc). WARNING: avoid if using Empower - double counting risk."""
    txns = []
    for row in rows:
        amount_raw = row.get('Amount', '0').replace('$', '').replace(',', '').strip()
        try:
            amount = float(amount_raw)
        except ValueError:
            continue
        # CC statements: positive = charge (expense). Flip sign to negative.
        txns.append({
            'date': _normalize_date(row.get('Transaction Date', '')),
            'account': 'Credit Card',
            'description': row.get('Description', '').strip(),
            'category': row.get('Category', '').strip(),
            'amount': -abs(amount),  # expenses negative
            'import_batch': import_batch,
            'raw_json': json.dumps(dict(row)),
        })
    return {'transactions': txns, 'balances': [], 'csv_type': 'cc_statement'}

def _normalize_date(raw: str) -> str:
    for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return raw.strip()
```

---

## Step 5 - Ingest Pipeline (ingest.py)

```python
import os
import shutil
from datetime import datetime
from pathlib import Path
import config
import storage
import parse_csv
import parse_screenshot
import knowledge_base

def run_ingest():
    storage.init_db()
    imports_dir = config.IMPORTS_DIR
    imports_dir.mkdir(exist_ok=True)

    batch = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    archive_dir = imports_dir / "processed" / datetime.now().strftime('%Y-%m-%d')
    archive_dir.mkdir(parents=True, exist_ok=True)

    txn_count, balance_count = 0, 0

    for f in sorted(imports_dir.iterdir()):
        if f.is_dir():
            continue
        print(f"Processing: {f.name}")
        ext = f.suffix.lower()

        if ext == '.csv':
            result = parse_csv.parse_csv_file(str(f), batch)
            if result['transactions']:
                n = storage.save_transactions(result['transactions'])
                txn_count += n
                print(f"  Transactions: {n} new")
            if result['balances']:
                storage.save_balances(result['balances'])
                balance_count += len(result['balances'])
                print(f"  Balances: {len(result['balances'])} rows")

        elif ext in ('.png', '.jpg', '.jpeg', '.webp'):
            if not config.ANTHROPIC_API_KEY:
                print("  Skipping screenshot (no ANTHROPIC_API_KEY)")
            else:
                accounts = parse_screenshot.parse_screenshot(str(f), batch)
                if accounts:
                    storage.save_balances(accounts)
                    print(f"  Screenshot: extracted {len(accounts)} balances")

        shutil.move(str(f), archive_dir / f.name)

    if balance_count > 0:
        storage.recompute_net_worth()
        print("Net worth recomputed.")

    knowledge_base.sync_events()
    print(f"\nIngest complete. {txn_count} new transactions, {balance_count} balance rows.")

if __name__ == '__main__':
    run_ingest()
```

---

## Step 6 - Budget Plan Seeder (seed_budget.py)

Define your expected monthly budget and seed it into the DB. Run once (or re-run to update).

```python
"""
One-time seed of the budget plan table.
Customize the categories and amounts for your household.
Re-run any time to update planned amounts.
"""
import storage
import config

storage.init_db()

# Define the category keys that match your BUDGET_CATEGORY_RULES in config.py
# and the budget page rendering logic in budget.html.
#
# Convention used throughout the app:
#   person_a_income, person_b_income  - income lines
#   expenses_*                        - spending sub-categories
#   savings_hysa, savings_roth_*      - savings lines (treated as wealth-building, not spending)
#   onetime_*                         - one-off expenses for specific months

MONTHLY_BUDGET = {
    # Income (positive)
    'person_a_income': 3000.00,    # replace with your post-tax monthly take-home
    'person_b_income': 2500.00,    # replace with partner's, or remove if single

    # Fixed expenses
    'expenses_rent': 1500.00,
    'expenses_internet': 60.00,
    'expenses_phone': 80.00,
    'expenses_car_insurance': 120.00,

    # Variable expenses
    'expenses_groceries': 600.00,
    'expenses_dining': 200.00,
    'expenses_transport': 100.00,
    'expenses_subscriptions': 50.00,
    'expenses_healthcare': 100.00,
    'expenses_fitness': 50.00,
    'expenses_personal': 100.00,
    'expenses_pets': 0.00,         # set to 0 if no pets
    'expenses_buffer_misc': 200.00, # catch-all for unclassified spending

    # Savings (not counted as spending in the net calculation)
    'savings_hysa': 500.00,
    'savings_roth_person_a': 583.00,   # ~$7000/yr / 12
    'savings_roth_person_b': 583.00,
}

# Seed for a date range. Adjust years/months as needed.
START_YEAR, START_MONTH = 2025, 1
END_YEAR, END_MONTH = 2026, 12

conn = storage.get_conn()
year, month = START_YEAR, START_MONTH
while (year, month) <= (END_YEAR, END_MONTH):
    budget = dict(MONTHLY_BUDGET)

    # Override specific months as needed. Examples:
    # if (year, month) == (2026, 3):
    #     budget['onetime_car_payoff'] = 1200.00  # final loan payment

    for cat, amount in budget.items():
        conn.execute("""
            INSERT OR REPLACE INTO budget_plan (year, month, category, planned_amount)
            VALUES (?, ?, ?, ?)
        """, (year, month, cat, amount))

    month += 1
    if month > 12:
        month = 1
        year += 1

conn.commit()
conn.close()
print(f"Seeded budget plan {START_YEAR}-{START_MONTH:02d} through {END_YEAR}-{END_MONTH:02d}.")
```

---

## Step 7 - Flask App (app.py)

```python
from flask import Flask, render_template, request, jsonify
import storage
import config
import forecast

app = Flask(__name__)
storage.init_db()

# --- Page routes ---
@app.route('/')
def index():
    return render_template('budget.html')

@app.route('/budget')
def budget():
    return render_template('budget.html')

@app.route('/net-worth')
def net_worth():
    return render_template('net_worth.html')

@app.route('/spending')
def spending():
    return render_template('spending.html')

@app.route('/forecast')
def forecast_page():
    return render_template('forecast.html')

@app.route('/events')
def events():
    return render_template('events.html')

# --- API: Budget ---
@app.route('/api/budget-plan')
def api_budget_plan():
    year = int(request.args.get('year', 2026))
    month = int(request.args.get('month', 1))
    plan = storage.get_budget_plan(year, month)
    status = storage.get_month_status(year, month)
    actuals = {}
    if status.get('locked'):
        actuals = storage.get_actuals_by_budget_category(year, month)
    notes = storage.get_budget_notes(year, month)
    return jsonify({'plan': plan, 'actuals': actuals, 'status': status, 'notes': notes})

@app.route('/api/budget-plan/update', methods=['POST'])
def api_update_budget():
    data = request.json
    storage.save_budget_plan(data['year'], data['month'], data['category'], data['amount'])
    return jsonify({'ok': True})

@app.route('/api/lock-month', methods=['POST'])
def api_lock_month():
    data = request.json
    storage.lock_month(data['year'], data['month'])
    return jsonify({'ok': True})

@app.route('/api/budget-notes', methods=['POST'])
def api_save_note():
    data = request.json
    storage.save_budget_note(data['year'], data['month'], data['category'], data['note'])
    return jsonify({'ok': True})

# --- API: Net Worth ---
@app.route('/api/net-worth')
def api_net_worth():
    window = request.args.get('window', 'all')  # 3m, 6m, 1y, all
    history = storage.get_net_worth_history(window)
    accounts = storage.get_latest_account_balances()
    sources = config.DATA_SOURCES
    return jsonify({'history': history, 'accounts': accounts, 'data_sources': sources})

# --- API: Transactions ---
@app.route('/api/transactions')
def api_transactions():
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    category = request.args.get('category')
    rows = storage.get_transactions(limit=limit, offset=offset, category=category)
    return jsonify({'transactions': rows})

# --- API: Forecast ---
@app.route('/api/forecast')
def api_forecast():
    data = forecast.generate_forecast()
    return jsonify(data)

# --- API: Events ---
@app.route('/api/events')
def api_events():
    events = storage.get_events()
    return jsonify({'events': events})

@app.route('/api/events', methods=['POST'])
def api_add_event():
    data = request.json
    storage.save_event(data)
    return jsonify({'ok': True})

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def api_delete_event(event_id):
    storage.delete_event(event_id)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
```

---

## Step 8 - knowledge.yaml

Track life events that affect forecasts. Synced to the `events` table on each ingest.

```yaml
income_changes:
  - date: "2025-01-01"
    label: "Person A job start"
    amount: 3000.00         # monthly net
    event_type: "income"
    notes: "Starting salary at Acme Corp"

annual_expenses:
  - month: 4               # April
    label: "Tax payment"
    amount: -500.00
    event_type: "tax"

subscriptions:
  - label: "Gym membership"
    amount: -50.00
    recurrence: "monthly"
    start_date: "2025-01-01"

one_off_events:
  - date: "2026-04-01"
    label: "Car loan paid off"
    amount: 1200.00         # freed up monthly cash
    event_type: "debt"
  - date: "2026-06-01"
    label: "Vacation"
    amount: -3000.00
    event_type: "expense"
```

---

## Step 9 - Forecast Logic (forecast.py)

```python
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import storage
import config

def generate_forecast() -> dict:
    today = date.today()
    lookback = today - timedelta(days=config.FORECAST_LOOKBACK_DAYS)

    # Get recent transaction averages
    avg_income = storage.get_avg_monthly_income(lookback.isoformat(), today.isoformat())
    avg_spend = storage.get_avg_monthly_spend(lookback.isoformat(), today.isoformat())

    # Fallback to config values if transaction history is too thin
    if avg_income < 500:
        avg_income = config.COMBINED_MONTHLY_NET
    if avg_spend < 500:
        avg_spend = storage.get_avg_planned_spend() or 2000.0

    net_delta = avg_income - avg_spend

    # Get starting point
    latest_nw = storage.get_latest_net_worth() or 0.0

    # Generate month-by-month projection
    base, high, low = [], [], []
    future_events = storage.get_future_events(today.isoformat())

    current = latest_nw
    for i in range(config.FORECAST_MONTHS):
        d = today + relativedelta(months=i + 1)
        month_str = d.strftime('%Y-%m')

        # Apply any one-off events in this month
        event_delta = sum(
            e['amount'] for e in future_events
            if e['event_date'].startswith(month_str)
        )

        base_nw = current + net_delta + event_delta
        high_nw = current + net_delta * (1 + config.FORECAST_VOLATILITY_PCT) + event_delta
        low_nw = current + net_delta * (1 - config.FORECAST_VOLATILITY_PCT) + event_delta

        base.append({'date': month_str, 'net_worth': round(base_nw, 2)})
        high.append({'date': month_str, 'net_worth': round(high_nw, 2)})
        low.append({'date': month_str, 'net_worth': round(low_nw, 2)})
        current = base_nw

    return {
        'base': base,
        'high': high,
        'low': low,
        'assumptions': {
            'avg_monthly_income': round(avg_income, 2),
            'avg_monthly_spend': round(avg_spend, 2),
            'net_monthly_delta': round(net_delta, 2),
            'starting_net_worth': round(latest_nw, 2),
            'future_event_count': len(future_events),
            'confidence_band_pct': config.FORECAST_VOLATILITY_PCT,
        }
    }
```

---

## Step 10 - Screenshot Parsing (parse_screenshot.py)

Uses Claude Vision to extract account balances from Empower screenshots.

```python
import base64
import json
import anthropic
import config

HAIKU_MODEL = "claude-haiku-4-5-20251001"

def parse_screenshot(filepath: str, import_batch: str) -> list[dict]:
    """
    Pass an Empower Net Worth screenshot to Claude Vision.
    Returns list of {snapshot_date, account, balance, account_type, import_batch}.
    """
    if not config.ANTHROPIC_API_KEY:
        return []

    with open(filepath, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    ext = filepath.rsplit('.', 1)[-1].lower()
    media_type = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/png')

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": (
                    "This is a screenshot of a financial account dashboard. "
                    "Extract all account names and balances. "
                    "Respond ONLY with valid JSON in this format:\n"
                    '{"date": "YYYY-MM-DD", "accounts": [{"name": "...", "balance": 12345.67, "type": "checking|savings|investment|retirement|credit|loan"}]}\n'
                    "Use today's date if no date is visible. Negative balances for credit cards and loans."
                )}
            ]
        }]
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith('```'):
        raw = raw.split('```')[1]
        if raw.startswith('json'):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  Failed to parse screenshot JSON: {raw[:200]}")
        return []

    from config import ACCOUNT_ALIASES
    result = []
    for acct in data.get('accounts', []):
        name = ACCOUNT_ALIASES.get(acct['name'], acct['name'])
        result.append({
            'snapshot_date': data.get('date'),
            'account': name,
            'balance': acct['balance'],
            'account_type': acct.get('type', ''),
            'import_batch': import_batch,
        })
    return result
```

---

## Step 11 - Running It

```bash
# First time only
python seed_budget.py

# Start the server
python app.py
# Visit http://localhost:5000

# Weekly: drop CSV exports from Empower into imports/ then:
python ingest.py
```

---

## Weekly Workflow

1. Log into Empower (empower.com)
2. **All Transactions** - Export CSV for your desired date range
3. **Net Worth** - Export CSV (shows all account balances)
4. For any account not in Empower (e.g. a HYSA): take a screenshot of the balance page
5. Drop all files into `imports/`
6. Run `python ingest.py`
7. Visit `http://localhost:5000`

**Key rule:** Use Empower as the single source for all transactions. Never mix Empower exports with direct credit card statement CSVs for the same card - the dedup key is `(date, account, description, amount)` and the account name will differ, causing double-counting.

---

## Monthly Workflow

**Start of month:**
1. Open the Budget page, navigate to the new month
2. Review planned amounts - adjust any that changed
3. Click "Lock [Month] Budget" - this activates the Planned | Actual | Diff columns

**During month:**
- Upload weekly as above. Actuals update automatically.

**End of month:**
- Review actuals vs. plan. Adjust next month's plan if needed.
- If you uploaded correctly, all transactions are already in the DB.

---

## Customizing Budget Categories

The category system is fully keyword-driven. No ML, no retraining.

1. Edit `BUDGET_CATEGORY_RULES` in `config.py` - add `"merchant keyword": "expenses_category_key"` entries
2. Refresh the budget page - actuals recompute live from the DB (no re-ingest needed)
3. To skip a transaction type (CC payments, investment transfers): map to `"SKIP"`

Add a new sub-category:
1. Add `"expenses_new_cat": amount` to your budget plan in `seed_budget.py` and re-run
2. Add rules to `BUDGET_CATEGORY_RULES` in `config.py`
3. Add a row for it in the budget table in `budget.html`

---

## Adding Equity Tracking (Optional)

If you have company equity (stock options, RSUs, etc.):

1. Fill in `MY_EQUITY` in `config.py` with your grant details
2. Create `equity.py` with a vesting calculator that generates month-by-month vested/unvested share counts
3. Add `/api/equity?as_of=YYYY-MM-DD` endpoint in `app.py`
4. Add an equity card section in `net_worth.html`

The `as_of` parameter lets you inspect vesting state at any past or future date without modifying the DB - useful for scenario planning.

---

## Troubleshooting

**Actuals columns not showing:**
- Month must be locked first (click "Lock" on the Budget page)
- Transactions must exist in the DB for that month (run ingest)
- Check that `BUDGET_CATEGORY_RULES` covers your merchants

**Net worth not updating after ingest:**
- `recompute_net_worth()` only runs if balance rows were saved
- If you inserted directly into `account_balances`, call `storage.recompute_net_worth()` manually

**Double-counted transactions:**
- Check you're not mixing Empower CSV + direct CC CSV for the same card
- Inspect with: `SELECT date, account, description, amount, COUNT(*) FROM transactions GROUP BY date, account, description, amount HAVING COUNT(*) > 1`

**Screenshot parsing fails:**
- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- Empower screenshots work best when the full account list is visible and unobscured

**Stale net worth snapshots after deleting balance rows:**
- Deleting from `account_balances` does NOT auto-delete `net_worth_snapshots`
- Manually: `DELETE FROM net_worth_snapshots WHERE snapshot_date='YYYY-MM-DD'`
- Then run `storage.recompute_net_worth()`

---

## Design Decisions Worth Knowing

- **No ML categorization** - keyword rules in `config.py` are fast, transparent, and easy to debug. Tune by adding merchant keywords.
- **Actuals computed live** - no separate actuals table. Fix a miscategorized merchant, refresh the page, it's fixed instantly.
- **Month locking is a display gate** - it only controls whether Planned | Actual | Diff columns appear. It does not freeze data. Unlock anytime: `DELETE FROM budget_month_status WHERE year=X AND month=Y`.
- **Empower as single source** - one CSV, all accounts, no dedup risk between sources.
- **Recompute on every ingest** - net worth is rebuilt from scratch each time. Safe because balance snapshots are sparse (weekly, not high-frequency).
- **Vanilla JS** - no framework, no build step. Fast enough for a personal dashboard. Add Chart.js via CDN.

import csv
import json
from pathlib import Path
from datetime import date
import config

# Header sets for file type detection (lowercase, stripped)
TRANSACTION_REQUIRED = {"date", "account", "description", "amount"}
BALANCE_REQUIRED = {"account name", "balance"}

# Liability keyword match on account name (lowercase)
LIABILITY_KEYWORDS = config.LIABILITY_KEYWORDS

# Income keywords on description (lowercase)
INCOME_KEYWORDS = config.INCOME_KEYWORDS


def _normalize_amount(raw, description=""):
    """
    Convert a raw amount string to a float with correct sign.
    Empower typically exports expenses as negative, income as positive.
    We keep that convention but normalize any string weirdness.
    """
    if raw is None:
        return 0.0
    clean = str(raw).replace("$", "").replace(",", "").strip()
    if not clean or clean == "-":
        return 0.0
    try:
        amount = float(clean)
    except ValueError:
        return 0.0

    # If income keyword detected and amount is negative, flip it
    desc_lower = description.lower()
    if any(kw in desc_lower for kw in INCOME_KEYWORDS) and amount < 0:
        amount = abs(amount)

    return round(amount, 2)


def _classify_account_type(account_name, empower_type=None):
    """Determine account type from name or Empower-provided type field."""
    if empower_type:
        et = empower_type.lower()
        if "credit" in et or "card" in et:
            return "credit"
        if "loan" in et or "mortgage" in et:
            return "loan"
        if "401k" in et or "ira" in et or "retirement" in et or "invest" in et or "brokerage" in et:
            return "investment"
        if "saving" in et:
            return "savings"
        if "check" in et:
            return "checking"

    name_lower = account_name.lower()
    if any(kw in name_lower for kw in ("credit card", "credit", "visa", "mastercard", "amex", "discover")):
        return "credit"
    if any(kw in name_lower for kw in ("loan", "mortgage", "debt")):
        return "loan"
    if any(kw in name_lower for kw in ("401k", "ira", "roth", "vanguard",
                                        "retirement", "empower retire")):
        return "retirement"
    if any(kw in name_lower for kw in ("schwab", "fidelity", "invest", "brokerage")):
        return "investment"
    if "saving" in name_lower:
        return "savings"
    return "checking"


def _detect_file_type(headers):
    """Return 'transactions', 'balances', 'cc_transactions', or 'unknown'."""
    lower = {h.lower().strip() for h in headers}
    if TRANSACTION_REQUIRED.issubset(lower):
        return "transactions"
    if BALANCE_REQUIRED.issubset(lower):
        return "balances"
    if _is_cc_csv(lower):
        return "cc_transactions"
    return "unknown"


def _is_cc_csv(lower_headers):
    """Detect Chase/Amex CC statement format (no 'account' column, has date + description + amount)."""
    has_date = "transaction date" in lower_headers or "date" in lower_headers
    has_desc = "description" in lower_headers
    has_amount = "amount" in lower_headers
    no_account = "account" not in lower_headers
    return has_date and has_desc and has_amount and no_account


def _normalize_date(raw):
    """Convert MM/DD/YYYY or YYYY-MM-DD to YYYY-MM-DD."""
    raw = raw.strip()
    if not raw:
        return None
    if "/" in raw:
        parts = raw.split("/")
        if len(parts) == 3:
            m, d, y = parts
            return f"{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}"
    return raw  # already ISO


def parse_file(filepath):
    """
    Auto-detect file type and parse.
    Returns (file_type, list_of_dicts)
    file_type is 'transactions', 'balances', or 'unknown'
    """
    path = Path(filepath)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return "unknown", []
        headers = reader.fieldnames
        file_type = _detect_file_type(headers)
        rows = list(reader)

    if file_type == "transactions":
        return "transactions", _parse_transactions(rows, headers)
    elif file_type == "balances":
        # Use filename date or today as snapshot date
        snap_date = _extract_date_from_filename(path) or date.today().isoformat()
        return "balances", _parse_balances(rows, headers, snap_date)
    elif file_type == "cc_transactions":
        # Infer account name from filename (e.g. amex_march.csv -> "Amex")
        account_name = _infer_cc_account_name(path)
        return "transactions", _parse_cc_transactions(rows, headers, account_name)
    else:
        print(f"  [WARN] Could not detect CSV type for {path.name}. Headers: {headers}")
        return "unknown", []


def _header_map(headers):
    """Build a lowercase -> original mapping for flexible header matching."""
    return {h.lower().strip(): h for h in headers}


def _parse_transactions(rows, headers):
    hmap = _header_map(headers)

    def get(row, key_options):
        for k in key_options:
            orig = hmap.get(k)
            if orig and orig in row and row[orig].strip():
                return row[orig].strip()
        return ""

    results = []
    for row in rows:
        raw_date = get(row, ["date"])
        desc = get(row, ["description", "merchant"])
        account = get(row, ["account", "account name"])
        category = get(row, ["category"]) or "Uncategorized"
        tags = get(row, ["tags", "tag"])
        raw_amount = get(row, ["amount"])

        if not raw_date or not desc or not account:
            continue  # skip blank rows

        iso_date = _normalize_date(raw_date)
        if not iso_date:
            continue

        amount = _normalize_amount(raw_amount, description=desc)

        results.append({
            "date": iso_date,
            "account": account,
            "description": desc,
            "category": category,
            "tags": tags,
            "amount": amount,
            "source": "csv",
        })

    return results


def _parse_balances(rows, headers, snap_date):
    hmap = _header_map(headers)

    def get(row, key_options):
        for k in key_options:
            orig = hmap.get(k)
            if orig and orig in row and row[orig].strip():
                return row[orig].strip()
        return ""

    results = []
    for row in rows:
        account = get(row, ["account name", "account", "name"])
        raw_balance = get(row, ["balance", "current balance", "value"])
        acct_type_raw = get(row, ["account type", "type"])

        if not account or not raw_balance:
            continue

        balance_str = raw_balance.replace("$", "").replace(",", "").strip()
        # Handle parenthetical negatives like (1,234.56)
        if balance_str.startswith("(") and balance_str.endswith(")"):
            balance_str = "-" + balance_str[1:-1]
        try:
            balance = round(float(balance_str), 2)
        except ValueError:
            continue

        account_type = _classify_account_type(account, acct_type_raw)

        results.append({
            "snapshot_date": snap_date,
            "account": account,
            "balance": balance,
            "account_type": account_type,
        })

    return results


def _infer_cc_account_name(path):
    """Guess the card name from the filename. e.g. amex_march.csv -> 'Amex'."""
    name = path.stem.lower()
    if "amex" in name or "american express" in name:
        return "Amex"
    if "chase" in name:
        return "Chase"
    if "fsfcu" in name or "fidelity" in name:
        return "FSFCU Credit"
    # Fall back to title-cased stem
    return path.stem.replace("_", " ").title()


def _parse_cc_transactions(rows, headers, account_name):
    """
    Parse Chase/Amex CC statement CSVs.
    CC sign convention: positive = you spent, negative = credit/refund.
    We flip: positive -> negative (expense), negative -> positive (refund).
    """
    hmap = _header_map(headers)

    def get(row, key_options):
        for k in key_options:
            orig = hmap.get(k)
            if orig and orig in row and row[orig].strip():
                return row[orig].strip()
        return ""

    results = []
    for row in rows:
        raw_date = get(row, ["transaction date", "date"])
        desc = get(row, ["description", "merchant"])
        category = get(row, ["category"]) or "Uncategorized"
        raw_amount = get(row, ["amount"])

        if not raw_date or not desc:
            continue

        iso_date = _normalize_date(raw_date)
        if not iso_date:
            continue

        # Parse amount as-is (no income-keyword flipping for CC)
        clean = raw_amount.replace("$", "").replace(",", "").strip()
        if not clean or clean == "-":
            continue
        try:
            cc_amount = float(clean)
        except ValueError:
            continue

        # CC convention: positive = purchase (expense), negative = credit (refund)
        # Flip to our convention: expense = negative, income/refund = positive
        amount = round(-cc_amount, 2)

        results.append({
            "date": iso_date,
            "account": account_name,
            "description": desc,
            "category": category,
            "tags": "",
            "amount": amount,
            "source": "cc_csv",
        })

    return results


def _extract_date_from_filename(path):
    """Try to pull YYYY-MM-DD or MMDDYY from filename."""
    import re
    name = path.stem
    # Try YYYY-MM-DD
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    if m:
        return m.group(1)
    # Try MMDDYY
    m = re.search(r"(\d{2})(\d{2})(\d{2})$", name)
    if m:
        mo, dy, yr = m.groups()
        full_yr = "20" + yr
        return f"{full_yr}-{mo}-{dy}"
    return None

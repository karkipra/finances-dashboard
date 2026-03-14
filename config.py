import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).parent
load_dotenv(PROJECT_DIR / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SONNET_MODEL = "claude-sonnet-4-20250514"

DB_PATH = PROJECT_DIR / "data" / "finances.db"
IMPORTS_DIR = PROJECT_DIR / "imports"
KNOWLEDGE_FILE = PROJECT_DIR / "knowledge.yaml"

FLASK_PORT = 5000
FLASK_DEBUG = True

# Account classification: names containing these keywords are liabilities
LIABILITY_KEYWORDS = {"credit card", "credit", "loan", "mortgage", "debt"}

# Transaction description keywords that signal income
INCOME_KEYWORDS = {"payroll", "direct deposit", "ach credit", "zelle", "venmo credit", "refund"}

# Forecast assumptions
FORECAST_MONTHS = 24
FORECAST_LOOKBACK_DAYS = 90
FORECAST_VOLATILITY_PCT = 0.15   # +/- 15% of avg monthly spend for confidence band

# Known income (net/month) - used to anchor forecast when transaction history is thin
PRATIK_MONTHLY_NET = 2552.00    # W-2 through Anthromind
NASTYA_MONTHLY_NET = 3600.00    # Nastya paycheck
COMBINED_MONTHLY_NET = PRATIK_MONTHLY_NET + NASTYA_MONTHLY_NET  # 6152.00

# Lending Club HYSA
HYSA_BALANCE = 9273.51
HYSA_APY = 0.042
HYSA_MONTHLY_CONTRIBUTION = 500.00

# Friendly name overrides for Empower's internal account labels
ACCOUNT_ALIASES = {
    "Manual Bank":                   "Lending Club HYSA",
    "Cash":                          "BFSFCU Checking",
    "Fund Staff Federal Credit Union": "BFSFCU Car Note",
    "Pratik Roth IRA (Vanguard)":    "Vanguard (Pratik Roth IRA)",
    "Vanguard (Google 401k)":        "Vanguard (Google 401k)",
    "Vanguard":                      "Vanguard (Google 401k)",
}

# Budget category rules: map merchant/category keywords to budget sub-category keys.
# Checked against transaction description first, then category. First match wins.
# Unmatched expenses fall through to expenses_buffer_misc.
BUDGET_CATEGORY_RULES = {
    # Rent (includes renters insurance)
    "uc santa barbara":   "expenses_rent",
    "state farm":         "expenses_rent",
    "rent":               "expenses_rent",
    "apartment":          "expenses_rent",
    # Groceries
    "whole foods":        "expenses_groceries",
    "trader joe":         "expenses_groceries",
    "safeway":            "expenses_groceries",
    "albertsons":         "expenses_groceries",
    "vons":               "expenses_groceries",
    "olive hill":         "expenses_groceries",
    "indo china":         "expenses_groceries",
    "costco":             "expenses_groceries",
    "grocery":            "expenses_groceries",
    "supermarket":        "expenses_groceries",
    # Dining
    "doordash":           "expenses_dining",
    "uber eats":          "expenses_dining",
    "tst*":               "expenses_dining",
    "ls drift":           "expenses_dining",
    "hilton":             "expenses_dining",
    "restaurant":         "expenses_dining",
    "dining":             "expenses_dining",
    # Car insurance — must come before plain "tesla" rule
    "tesla insurance":    "expenses_car_insurance",
    # EV charging
    "tesla supercharger": "expenses_ev_charging",
    "chargepoint":        "expenses_ev_charging",
    "charging":           "expenses_ev_charging",
    "tesla":              "expenses_ev_charging",
    # Internet (no generic "internet" keyword - banks use it for wire transfers)
    "at&t":               "expenses_internet",
    "xfinity":            "expenses_internet",
    "comcast":            "expenses_internet",
    # Entertainment (movies, plays, theaters)
    "metropolitan theatres": "expenses_entertainment",
    "garvin theatre":     "expenses_entertainment",
    "ucsb assoc":         "expenses_entertainment",
    "sbiff":              "expenses_entertainment",
    "theatre":            "expenses_entertainment",
    "theater":            "expenses_entertainment",
    "cinema":             "expenses_entertainment",
    # Subscriptions
    "youtube":            "expenses_subscriptions",
    "spotify":            "expenses_subscriptions",
    "netflix":            "expenses_subscriptions",
    "playstation":        "expenses_subscriptions",
    "overleaf":           "expenses_subscriptions",
    "hbomax":             "expenses_subscriptions",
    "hbo max":            "expenses_subscriptions",
    # Healthcare
    "zion healthshare":   "expenses_healthcare",
    "dental insurance":   "expenses_healthcare",
    "musely":             "expenses_healthcare",
    "kaiser":             "expenses_healthcare",
    "pharmacy":           "expenses_healthcare",
    "medical":            "expenses_healthcare",
    # Pets
    "catandbirds":        "expenses_pets",
    "cat and bird":       "expenses_pets",
    "chewy":              "expenses_pets",
    "embrace pet":        "expenses_pets",
    "petco":              "expenses_pets",
    "petsmart":           "expenses_pets",
    "banfield":           "expenses_pets",
    "vet":                "expenses_pets",
    # Fitness
    "katelyn carano":     "expenses_fitness",
    "aerial":             "expenses_fitness",
    "gym":                "expenses_fitness",
    # Car loan
    "to principal":       "expenses_car_loan",
    # Nastya gifts / personal shopping
    "nastya gift":        "expenses_nastya_gifts",
    "alpha thrift":       "expenses_nastya_gifts",
    "spanx":              "expenses_nastya_gifts",
    "lingerie":           "expenses_nastya_gifts",
    "marshalls":          "expenses_nastya_gifts",
    "sephora":            "expenses_nastya_gifts",
    # Personal / misc
    "amazon":             "expenses_personal_misc",
    "target":             "expenses_personal_misc",
    "haircut":            "expenses_personal_misc",
    "salon":              "expenses_personal_misc",
    # Savings (for HYSA/Roth contributions appearing in bank transactions)
    "hysa":               "hysa",
    "high yield":         "hysa",
    "lendingclub":        "hysa",
    "lending club":       "hysa",
    "roth":               "roth",
    "vanguard":           "roth",
    "schwab":             "roth",
}

# Anthromind equity grant (CS-2, 40% of total)
ANTHROMIND_EQUITY = {
    "company":                 "Anthromind",
    "total_shares":            3_769_250,
    "cost_basis":              37.69,       # total paid as co-founder
    "purchase_price_per_share": 0.00001,
    "current_price_per_share":  0.0,        # update when priced round happens
    "vesting_start":           "2024-07-29",
    "cliff_date":              "2025-07-29",
    "cliff_shares":            942_312,
    "monthly_shares":          78_526,      # 78,527 on periods 13 and 37 (Jul anniversaries)
    "fully_vested_date":       "2028-07-29",
    "qsbs_eligible_date":      "2029-07-29",  # 5-year holding period from purchase
}

# Where, Inc. equity (co-founder, 33% of 10M share pool)
# Uncomment to activate when ready
# WHERE_EQUITY = {
#     "company":                 "Where, Inc.",
#     "total_shares":            3_333_333,    # 33% of 10M
#     "cost_basis":              33.00,
#     "purchase_price_per_share": 0.00001,
#     "current_price_per_share":  0.0,
#     "immediately_vested":       True,
#     "purchase_date":           "2026-03-11",
#     "qsbs_eligible_date":      "2031-03-11",  # 5-year holding from today
#     "fully_vested_date":       "2026-03-11",
# }

# Data sources checklist - shown on dashboard as setup TODO card
DATA_SOURCES = [
    {"label": "BFSFCU Checking (4346)", "status": "connected", "notes": "$3,251 as of Mar 2026. Transactions via Empower CSV."},
    {"label": "Lending Club HYSA", "status": "manual", "notes": "$9,723 at 4.2% APY. Not connected to Empower - update balance manually each month. +$500/month contribution."},
    {"label": "Charles Schwab (Pratik Roth IRA)", "status": "connected", "notes": "$42,574 as of Mar 2026.", "category": "investment"},
    {"label": "Vanguard (Pratik Roth IRA)", "status": "connected", "notes": "$13,699 as of Mar 2026.", "category": "retirement"},
    {"label": "Vanguard (Google 401k)", "status": "connected", "notes": "$80,575 as of Mar 2026.", "category": "retirement"},
    {"label": "American Express (1006)", "status": "partial", "notes": "$972 balance as of Mar 2026. Balance tracked. Need CC transaction CSV for spending breakdown."},
    {"label": "FSFCU Credit Card (3048)", "status": "connected", "notes": "$130 balance as of Mar 2026."},
    {"label": "BFSFCU Car Note", "status": "connected", "notes": "$2,423 remaining as of Mar 2026. $1,010/month - paid off Apr 2026."},
    {"label": "Principal (IMF 401k)", "status": "manual", "notes": "~$21K as of Mar 2026. Approximate — real number via Empower later.", "category": "retirement"},
    {"label": "Fidelity (Nastya Roth IRA)", "status": "manual", "notes": "~$17K as of Mar 2026. Approximate — real number via Empower later.", "category": "retirement"},
    {"label": "Personal spending CSV", "status": "todo", "notes": "Current CSV is from Empower retirement portal only. Export full transaction history from Empower Personal Capital for groceries, dining, etc."},
]

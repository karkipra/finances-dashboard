"""
One-time seed of budget_plan table from the 2025-2026 budget PDF.
Data extracted from: '2025-2026 budget - Sheet1-1.pdf'
Run once: python seed_budget.py
"""

import storage

# All amounts: positive = income/inflow, negative = expense/outflow
# Source: 24 Month Budget PDF read on 2026-03-11

BUDGET_2025 = [
    # Jan 2025
    {"year": 2025, "month": 1,  "category": "nastya_income",       "planned_amount": 3600.00},
    {"year": 2025, "month": 1,  "category": "pratik_income",        "planned_amount": 0.0},
    {"year": 2025, "month": 1,  "category": "monthly_expenses",     "planned_amount": -3500.00},
    {"year": 2025, "month": 1,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 1,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 1,  "category": "hysa",                 "planned_amount": 0.0},
    {"year": 2025, "month": 1,  "category": "roth",                 "planned_amount": -1166.66},
    {"year": 2025, "month": 1,  "category": "net_income",           "planned_amount": 100.00},
    # Feb 2025
    {"year": 2025, "month": 2,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 2,  "category": "pratik_income",        "planned_amount": 0.0},
    {"year": 2025, "month": 2,  "category": "monthly_expenses",     "planned_amount": -3500.00},
    {"year": 2025, "month": 2,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 2,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 2,  "category": "hysa",                 "planned_amount": 0.0},
    {"year": 2025, "month": 2,  "category": "roth",                 "planned_amount": -1166.66},
    {"year": 2025, "month": 2,  "category": "net_income",           "planned_amount": 100.00},
    # Mar 2025
    {"year": 2025, "month": 3,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 3,  "category": "pratik_income",        "planned_amount": 0.0},
    {"year": 2025, "month": 3,  "category": "monthly_expenses",     "planned_amount": -3500.00},
    {"year": 2025, "month": 3,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 3,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 3,  "category": "hysa",                 "planned_amount": 0.0},
    {"year": 2025, "month": 3,  "category": "roth",                 "planned_amount": -1166.66},
    {"year": 2025, "month": 3,  "category": "net_income",           "planned_amount": 100.00},
    # Apr 2025
    {"year": 2025, "month": 4,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 4,  "category": "pratik_income",        "planned_amount": 0.0},
    {"year": 2025, "month": 4,  "category": "monthly_expenses",     "planned_amount": -3500.00},
    {"year": 2025, "month": 4,  "category": "one_time_income",      "planned_amount": 3000.00},
    {"year": 2025, "month": 4,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 4,  "category": "hysa",                 "planned_amount": 0.0},
    {"year": 2025, "month": 4,  "category": "roth",                 "planned_amount": 0.0},
    {"year": 2025, "month": 4,  "category": "net_income",           "planned_amount": 3100.00},
    # May 2025
    {"year": 2025, "month": 5,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 5,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 5,  "category": "monthly_expenses",     "planned_amount": -3500.00},
    {"year": 2025, "month": 5,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 5,  "category": "one_time_expense",     "planned_amount": -2000.00},
    {"year": 2025, "month": 5,  "category": "hysa",                 "planned_amount": 0.0},
    {"year": 2025, "month": 5,  "category": "roth",                 "planned_amount": 0.0},
    {"year": 2025, "month": 5,  "category": "net_income",           "planned_amount": -764.66},
    # Jun 2025
    {"year": 2025, "month": 6,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 6,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 6,  "category": "monthly_expenses",     "planned_amount": -3652.00},
    {"year": 2025, "month": 6,  "category": "one_time_income",      "planned_amount": 1849.00},
    {"year": 2025, "month": 6,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 6,  "category": "hysa",                 "planned_amount": -250.00},
    {"year": 2025, "month": 6,  "category": "roth",                 "planned_amount": 0.0},
    {"year": 2025, "month": 6,  "category": "net_income",           "planned_amount": 2932.34},
    # Jul 2025
    {"year": 2025, "month": 7,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 7,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 7,  "category": "monthly_expenses",     "planned_amount": -3763.00},
    {"year": 2025, "month": 7,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 7,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 7,  "category": "hysa",                 "planned_amount": -250.00},
    {"year": 2025, "month": 7,  "category": "roth",                 "planned_amount": -1166.66},
    {"year": 2025, "month": 7,  "category": "net_income",           "planned_amount": 972.34},
    # Aug 2025
    {"year": 2025, "month": 8,  "category": "nastya_income",        "planned_amount": 0.0},
    {"year": 2025, "month": 8,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 8,  "category": "monthly_expenses",     "planned_amount": -3763.00},
    {"year": 2025, "month": 8,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 8,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 8,  "category": "hysa",                 "planned_amount": -250.00},
    {"year": 2025, "month": 8,  "category": "roth",                 "planned_amount": -1500.00},
    {"year": 2025, "month": 8,  "category": "net_income",           "planned_amount": -1461.00},
    # Sep 2025
    {"year": 2025, "month": 9,  "category": "nastya_income",        "planned_amount": 6183.90},
    {"year": 2025, "month": 9,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 9,  "category": "monthly_expenses",     "planned_amount": -3763.00},
    {"year": 2025, "month": 9,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 9,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 9,  "category": "hysa",                 "planned_amount": -250.00},
    {"year": 2025, "month": 9,  "category": "roth",                 "planned_amount": -1500.00},
    {"year": 2025, "month": 9,  "category": "net_income",           "planned_amount": 4722.90},
    # Oct 2025
    {"year": 2025, "month": 10, "category": "nastya_income",        "planned_amount": 0.0},
    {"year": 2025, "month": 10, "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 10, "category": "monthly_expenses",     "planned_amount": -3763.00},
    {"year": 2025, "month": 10, "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 10, "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 10, "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2025, "month": 10, "category": "roth",                 "planned_amount": 0.0},
    {"year": 2025, "month": 10, "category": "net_income",           "planned_amount": -1461.00},
    # Nov 2025
    {"year": 2025, "month": 11, "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 11, "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 11, "category": "monthly_expenses",     "planned_amount": -3652.00},
    {"year": 2025, "month": 11, "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 11, "category": "one_time_expense",     "planned_amount": -600.00},
    {"year": 2025, "month": 11, "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2025, "month": 11, "category": "roth",                 "planned_amount": -1500.00},
    {"year": 2025, "month": 11, "category": "net_income",           "planned_amount": -100.00},
    # Dec 2025
    {"year": 2025, "month": 12, "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2025, "month": 12, "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2025, "month": 12, "category": "monthly_expenses",     "planned_amount": -3652.00},
    {"year": 2025, "month": 12, "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2025, "month": 12, "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2025, "month": 12, "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2025, "month": 12, "category": "roth",                 "planned_amount": -1500.00},
    {"year": 2025, "month": 12, "category": "net_income",           "planned_amount": 500.00},
]

BUDGET_2026 = [
    # Jan 2026
    {"year": 2026, "month": 1,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2026, "month": 1,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2026, "month": 1,  "category": "monthly_expenses",     "planned_amount": -3652.00},
    {"year": 2026, "month": 1,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2026, "month": 1,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2026, "month": 1,  "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2026, "month": 1,  "category": "roth",                 "planned_amount": -1500.00},
    {"year": 2026, "month": 1,  "category": "net_income",           "planned_amount": 500.00},
    # Feb 2026
    {"year": 2026, "month": 2,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2026, "month": 2,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2026, "month": 2,  "category": "monthly_expenses",     "planned_amount": -3652.00},
    {"year": 2026, "month": 2,  "category": "one_time_income",      "planned_amount": 800.00},
    {"year": 2026, "month": 2,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2026, "month": 2,  "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2026, "month": 2,  "category": "roth",                 "planned_amount": -1500.00},
    {"year": 2026, "month": 2,  "category": "net_income",           "planned_amount": 1300.00},
    # Mar 2026 — buffer trimmed $250 so net = $0
    {"year": 2026, "month": 3,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2026, "month": 3,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2026, "month": 3,  "category": "monthly_expenses",     "planned_amount": -3402.00},
    {"year": 2026, "month": 3,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2026, "month": 3,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2026, "month": 3,  "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2026, "month": 3,  "category": "roth",                 "planned_amount": -2250.00},
    {"year": 2026, "month": 3,  "category": "net_income",           "planned_amount": 0.00},
    # Apr 2026
    {"year": 2026, "month": 4,  "category": "nastya_income",        "planned_amount": 3600.00},
    {"year": 2026, "month": 4,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2026, "month": 4,  "category": "monthly_expenses",     "planned_amount": -3652.00},
    {"year": 2026, "month": 4,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2026, "month": 4,  "category": "one_time_expense",     "planned_amount": -1200.00},
    {"year": 2026, "month": 4,  "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2026, "month": 4,  "category": "roth",                 "planned_amount": -2250.00},
    {"year": 2026, "month": 4,  "category": "net_income",           "planned_amount": -1450.00},
    # May-Dec 2026: Nastya income = $0 (PhD summer gap, fellowship TBD)
    # Expenses drop to $2,642, roth $1,364/month
    {"year": 2026, "month": 5,  "category": "nastya_income",        "planned_amount": 0.0},
    {"year": 2026, "month": 5,  "category": "pratik_income",        "planned_amount": 2552.00},
    {"year": 2026, "month": 5,  "category": "monthly_expenses",     "planned_amount": -2642.00},
    {"year": 2026, "month": 5,  "category": "one_time_income",      "planned_amount": 0.0},
    {"year": 2026, "month": 5,  "category": "one_time_expense",     "planned_amount": 0.0},
    {"year": 2026, "month": 5,  "category": "hysa",                 "planned_amount": -500.00},
    {"year": 2026, "month": 5,  "category": "roth",                 "planned_amount": -1364.00},
    {"year": 2026, "month": 5,  "category": "net_income",           "planned_amount": -1954.00},
]

# May-Dec 2026: Nastya income $0 (summer PhD gap)
for m in range(6, 13):
    phone_plan = -400.00 if m == 10 else 0.0  # Oct 2026: $400/yr phone plan renewal (2 people)
    net = -1954.00 + phone_plan
    BUDGET_2026 += [
        {"year": 2026, "month": m, "category": "nastya_income",    "planned_amount": 0.0},
        {"year": 2026, "month": m, "category": "pratik_income",    "planned_amount": 2552.00},
        {"year": 2026, "month": m, "category": "monthly_expenses", "planned_amount": -2642.00},
        {"year": 2026, "month": m, "category": "one_time_income",  "planned_amount": 0.0},
        {"year": 2026, "month": m, "category": "one_time_expense", "planned_amount": phone_plan},
        {"year": 2026, "month": m, "category": "hysa",             "planned_amount": -500.00},
        {"year": 2026, "month": m, "category": "roth",             "planned_amount": -1364.00},
        {"year": 2026, "month": m, "category": "net_income",       "planned_amount": net},
    ]


FITNESS_MONTHS = {1, 4, 7, 10}  # Jan, Apr, Jul, Oct (quarterly: Nastya aerial)

# Fixed monthly expense items (Jan-Apr 2026 / 2025 full months)
EXPENSE_FIXED = {
    "expenses_rent":          1335.00,
    "expenses_groceries":      750.00,
    "expenses_dining":         150.00,
    "expenses_car_insurance":  150.00,
    "expenses_ev_charging":     45.00,
    "expenses_internet":        60.00,  # Xfinity/ISP - all-inclusive rent, internet billed separately
    "expenses_subscriptions":   35.00,
    "expenses_healthcare":     111.00,
    "expenses_pets":           200.00,  # food + insurance + medication
    "expenses_personal_misc":   75.00,
}
EXPENSE_FIXED_TOTAL = sum(EXPENSE_FIXED.values())  # 2911.00

# Lean budget items (May-Dec 2026, reduced groceries/dining/personal, tighter pets)
EXPENSE_FIXED_LEAN = {
    "expenses_rent":          1335.00,
    "expenses_groceries":      600.00,
    "expenses_dining":         100.00,
    "expenses_car_insurance":  150.00,
    "expenses_ev_charging":     45.00,
    "expenses_internet":        60.00,
    "expenses_subscriptions":   35.00,
    "expenses_healthcare":     111.00,
    "expenses_pets":           150.00,  # trimmed during lean months (food + insurance only)
    "expenses_personal_misc":   50.00,
}
EXPENSE_FIXED_LEAN_TOTAL = sum(EXPENSE_FIXED_LEAN.values())  # 2636.00


def expense_sub_rows(year, month, total_abs, lean=False):
    """
    Build display-only expense sub-category rows for a given month.
    lean=True: uses reduced groceries/dining/personal (May-Dec 2026).
    total_abs: absolute value of monthly_expenses for the month.
    Buffer/misc absorbs the remainder (to be audited end of March 2026).
    """
    if lean:
        fixed = EXPENSE_FIXED_LEAN
        fixed_total = EXPENSE_FIXED_LEAN_TOTAL
        fitness = 0.0
    else:
        fixed = EXPENSE_FIXED
        fixed_total = EXPENSE_FIXED_TOTAL
        fitness = 250.00 if month in FITNESS_MONTHS else 0.0

    buffer_misc = round(total_abs - fixed_total - fitness, 2)

    rows = []
    for cat, amt in fixed.items():
        rows.append({"year": year, "month": month, "category": cat, "planned_amount": -amt})
    rows.append({"year": year, "month": month, "category": "expenses_fitness",
                 "planned_amount": -fitness})
    rows.append({"year": year, "month": month, "category": "expenses_buffer_misc",
                 "planned_amount": -buffer_misc})
    return rows


def build_all_expense_sub_rows():
    rows = []
    # 2025 - expenses per month (absolute values matching monthly_expenses in BUDGET_2025)
    expenses_2025 = {
        1: 3500, 2: 3500, 3: 3500, 4: 3500, 5: 3500,
        6: 3652, 7: 3763, 8: 3763, 9: 3763, 10: 3763,
        11: 3652, 12: 3652,
    }
    for m, total in expenses_2025.items():
        rows += expense_sub_rows(2025, m, total)
    # 2026 Jan-Apr: $3,652/mo except Mar ($3,402, buffer trimmed to reach net $0)
    for m in range(1, 5):
        total = 3402 if m == 3 else 3652
        rows += expense_sub_rows(2026, m, total)
    # 2026 May-Dec: $2,642/mo, lean budget
    for m in range(5, 13):
        rows += expense_sub_rows(2026, m, 2642, lean=True)
    return rows


def run():
    storage.init_db()
    # Remove renamed/retired categories before re-seeding
    conn = storage.get_conn()
    retired = conn.execute(
        "DELETE FROM budget_plan WHERE category IN ('expenses_utilities_other')"
    ).rowcount
    conn.commit()
    conn.close()
    if retired:
        print(f"Removed {retired} retired category rows.")
    all_rows = BUDGET_2025 + BUDGET_2026
    count = storage.save_budget_plan(all_rows)
    print(f"Seeded {count} budget_plan rows (2025-2026).")
    sub_rows = build_all_expense_sub_rows()
    count2 = storage.save_budget_plan(sub_rows)
    print(f"Seeded {count2} expense sub-category rows.")


if __name__ == "__main__":
    run()

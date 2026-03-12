"""
2-year net worth projection.
Uses last 90 days of transactions to compute avg monthly income and spend.
Applies future events from knowledge.yaml as one-time adjustments.
"""

from datetime import date
from dateutil.relativedelta import relativedelta
import storage
import config


def generate_forecast(months=None):
    """
    Returns list of dicts: {date, base_nw, low_nw, high_nw}
    Also returns the assumptions dict used.
    """
    if months is None:
        months = config.FORECAST_MONTHS

    lookback = config.FORECAST_LOOKBACK_DAYS
    volatility_pct = config.FORECAST_VOLATILITY_PCT

    avg_income_txn = storage.get_avg_monthly_income(lookback_days=lookback)
    avg_spend = storage.get_avg_monthly_spend(lookback_days=lookback)

    # If transaction-derived income is less than 50% of known combined salary,
    # the CSV is investment-only (not personal spending). Fall back to config values.
    income_source = "transactions"
    if avg_income_txn < config.COMBINED_MONTHLY_NET * 0.5:
        avg_income = config.COMBINED_MONTHLY_NET
        income_source = "config (known salary - import personal CSV for actuals)"
    else:
        avg_income = avg_income_txn

    # If spend looks like investment trades only (no real expenses), use budget plan avg
    spend_source = "transactions"
    if avg_spend < 500:
        # Pull average monthly expense from 2026 budget plan
        plan_expenses = []
        for m in range(1, 13):
            plan = storage.get_budget_plan(2026, m)
            if plan.get("monthly_expenses"):
                plan_expenses.append(abs(plan["monthly_expenses"]["amount"]))
        if plan_expenses:
            avg_spend = sum(plan_expenses) / len(plan_expenses)
            spend_source = "2026 budget plan"

    base_monthly_delta = avg_income - avg_spend
    spend_volatility = avg_spend * volatility_pct

    latest = storage.get_latest_net_worth()
    starting_nw = latest["net_worth"] if latest else 0.0
    start_date_str = latest["date"] if latest else date.today().isoformat()

    future_events = storage.get_events(future_only=True)

    assumptions = {
        "income_source": income_source,
        "spend_source": spend_source,
        "avg_monthly_income": avg_income,
        "avg_monthly_spend": avg_spend,
        "base_monthly_delta": round(base_monthly_delta, 2),
        "volatility_band": round(spend_volatility, 2),
        "starting_net_worth": starting_nw,
        "starting_date": start_date_str,
        "lookback_days": lookback,
        "future_event_count": len(future_events),
    }

    results = []
    base_nw = starting_nw
    low_nw = starting_nw
    high_nw = starting_nw
    today = date.today()

    for offset in range(1, months + 1):
        proj_date = today + relativedelta(months=offset)

        base_nw += base_monthly_delta
        low_nw += (base_monthly_delta - spend_volatility)
        high_nw += (base_monthly_delta + spend_volatility)

        # Apply future events that fall in this month
        for event in future_events:
            edate_str = event.get("event_date", "")
            if not edate_str:
                continue
            amount = event.get("amount") or 0.0

            try:
                edate = date.fromisoformat(edate_str)
            except ValueError:
                continue

            # One-off: matches year + month
            if event.get("recurrence") == "none":
                if edate.year == proj_date.year and edate.month == proj_date.month:
                    base_nw += amount
                    low_nw += amount
                    high_nw += amount

            # Annual recurrence: same month/day in any projected year
            elif event.get("recurrence") == "annual":
                if edate.month == proj_date.month:
                    # Only apply if the original event has passed (we're projecting forward)
                    if proj_date > edate or proj_date.year > edate.year:
                        try:
                            recur = date(proj_date.year, edate.month, edate.day)
                            if recur.year == proj_date.year and recur.month == proj_date.month:
                                base_nw += amount
                                low_nw += amount
                                high_nw += amount
                        except ValueError:
                            pass  # Feb 29 in non-leap year

            # Monthly recurrence: apply every month after event date
            elif event.get("recurrence") == "monthly":
                if proj_date >= date(edate.year, edate.month, 1):
                    base_nw += amount
                    low_nw += amount
                    high_nw += amount

        results.append({
            "date": proj_date.isoformat(),
            "base_nw": round(base_nw, 2),
            "low_nw": round(low_nw, 2),
            "high_nw": round(high_nw, 2),
        })

    return results, assumptions

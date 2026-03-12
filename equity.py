from datetime import date
from dateutil.relativedelta import relativedelta
import config


def get_vesting_schedule(eq):
    """
    Build vesting schedule for a standard cliff + monthly grant.
    Returns list of (vest_date, shares).
    For immediately_vested grants, returns a single entry on purchase_date.
    """
    if eq.get("immediately_vested"):
        purchase = date.fromisoformat(eq["purchase_date"])
        return [(purchase, eq["total_shares"])]

    cliff = date.fromisoformat(eq["cliff_date"])
    schedule = [(cliff, eq["cliff_shares"])]
    for i in range(1, 37):
        vest_date = cliff + relativedelta(months=i)
        # Anthromind: periods 13 and 37 (Jul anniversaries) get +1 share
        shares = eq["monthly_shares"] + (1 if i in (12, 36) else 0)
        schedule.append((vest_date, shares))
    return schedule


def get_equity_summary(eq, as_of=None):
    """Generic equity summary for any position config."""
    if as_of is None:
        as_of = date.today()

    schedule = get_vesting_schedule(eq)
    vested_periods   = [(d, s) for d, s in schedule if d <= as_of]
    unvested_periods = [(d, s) for d, s in schedule if d > as_of]

    vested_shares   = sum(s for _, s in vested_periods)
    unvested_shares = sum(s for _, s in unvested_periods)
    total_shares    = vested_shares + unvested_shares

    price      = eq["current_price_per_share"]
    next_vest  = unvested_periods[0] if unvested_periods else None

    return {
        "company":            eq.get("company", "Unknown"),
        "vested_shares":      vested_shares,
        "unvested_shares":    unvested_shares,
        "total_shares":       total_shares,
        "pct_vested":         round(vested_shares / total_shares * 100, 1) if total_shares else 0,
        "current_price":      price,
        "current_value":      round(vested_shares * price, 2),
        "cost_basis":         eq["cost_basis"],
        "purchase_price_per_share": eq.get("purchase_price_per_share", 0),
        "next_vest_date":     next_vest[0].isoformat() if next_vest else None,
        "next_vest_shares":   next_vest[1] if next_vest else 0,
        "fully_vested_date":  eq["fully_vested_date"],
        "qsbs_eligible_date": eq["qsbs_eligible_date"],
        "no_value_yet":       price == 0.0,
        "immediately_vested": eq.get("immediately_vested", False),
    }


def get_all_equity(as_of=None):
    positions = [config.ANTHROMIND_EQUITY]
    # Add more positions here as they become active:
    # positions.append(config.WHERE_EQUITY)
    return [get_equity_summary(eq, as_of) for eq in positions]

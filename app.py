"""
Local Flask dashboard. Run:  python app.py
Then open:  http://localhost:5000
"""

from datetime import date, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
import storage
import forecast as forecast_module
import config
import equity as equity_module

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


# --- Page routes ---

@app.route("/")
def index():
    return redirect(url_for("budget"))


@app.route("/net-worth")
def net_worth():
    from datetime import datetime
    latest = storage.get_latest_net_worth()
    if latest:
        try:
            latest["date_pretty"] = datetime.strptime(latest["date"], "%Y-%m-%d").strftime("%b %d, %Y")
        except Exception:
            latest["date_pretty"] = latest["date"]
    balances = storage.get_latest_balances()
    return render_template("net_worth.html", latest=latest, balances=balances)


@app.route("/spending")
def spending():
    return render_template("spending.html")


@app.route("/budget")
def budget():
    return render_template("budget.html")


@app.route("/events")
def events():
    all_events = storage.get_events()
    return render_template("events.html", events=all_events)


@app.route("/forecast")
def forecast_page():
    return render_template("forecast.html")


# --- API routes ---

@app.route("/api/net-worth")
def api_net_worth():
    history = storage.get_net_worth_history()
    return jsonify(history)


@app.route("/api/spending")
def api_spending():
    period = request.args.get("period", "month")
    today = date.today()

    if period == "week":
        start = (today - timedelta(days=7)).isoformat()
        end = today.isoformat()
    elif period == "month":
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
    elif period == "3months":
        start = (today - timedelta(days=90)).isoformat()
        end = today.isoformat()
    elif period == "custom":
        start = request.args.get("start", today.replace(day=1).isoformat())
        end = request.args.get("end", today.isoformat())
    else:
        start = today.replace(day=1).isoformat()
        end = today.isoformat()

    categories = storage.get_spending_by_category(start_date=start, end_date=end)
    transactions = storage.get_transactions(start_date=start, end_date=end)

    total = sum(c["total"] for c in categories)

    return jsonify({
        "categories": categories,
        "transactions": transactions,
        "total": round(total, 2),
        "period": {"start": start, "end": end},
    })


@app.route("/api/budget")
def api_budget():
    period = request.args.get("period", "month")
    today = date.today()

    if period == "month":
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
    else:
        start = (today - timedelta(days=30)).isoformat()
        end = today.isoformat()

    actuals = storage.get_spending_by_category(start_date=start, end_date=end)
    budget_cats = storage.get_budget_categories()
    target_map = {b["category"]: b["monthly_target"] for b in budget_cats}

    result = []
    for item in actuals:
        cat = item["category"]
        actual = item["total"]
        target = target_map.get(cat)
        diff = round(actual - target, 2) if target else None
        result.append({
            "category": cat,
            "actual": actual,
            "target": target,
            "diff": diff,
            "status": _budget_status(actual, target),
        })

    return jsonify({"rows": result, "period": {"start": start, "end": end}})


def _budget_status(actual, target):
    if target is None:
        return "tracking"
    if actual > target:
        return "over"
    if actual > target * 0.9:
        return "near"
    return "under"


@app.route("/api/forecast")
def api_forecast():
    results, assumptions = forecast_module.generate_forecast()
    return jsonify({"points": results, "assumptions": assumptions})


@app.route("/api/events")
def api_events():
    future_only = request.args.get("future_only") == "true"
    events = storage.get_events(future_only=future_only)
    return jsonify(events)


@app.route("/api/events", methods=["POST"])
def api_add_event():
    data = request.get_json()
    required = {"event_date", "event_type", "label"}
    if not required.issubset(data.keys()):
        return jsonify({"error": "Missing required fields: event_date, event_type, label"}), 400

    storage.upsert_event({
        "event_date": data["event_date"],
        "event_type": data["event_type"],
        "label": data["label"],
        "amount": data.get("amount"),
        "recurrence": data.get("recurrence", "none"),
        "notes": data.get("notes"),
        "source": "manual",
    })
    return jsonify({"status": "ok"})


@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    storage.delete_event(event_id)
    return jsonify({"status": "ok"})


@app.route("/api/budget-plan")
def api_budget_plan():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    data = storage.get_budget_vs_actual(year, month)
    min_ym, max_ym = storage.get_budget_plan_range()
    data["range"] = {
        "min": {"year": min_ym[0], "month": min_ym[1]} if min_ym else None,
        "max": {"year": max_ym[0], "month": max_ym[1]} if max_ym else None,
    }
    status = storage.get_month_status(year, month)
    data["locked"] = status["locked"]
    actuals = storage.get_actuals_by_budget_category(year, month)
    data["actuals_by_category"] = actuals
    data["has_actuals"] = any(v > 0 for v in actuals.values())
    data["actual_income_total"] = storage.get_actual_income_total(year, month)
    data["is_current_month"] = (year == today.year and month == today.month)
    data["latest_transaction_date"] = storage.get_latest_transaction_date()
    data["projected_checking"] = storage.get_projected_checking(year, month)
    return jsonify(data)


@app.route("/api/budget-category-transactions")
def api_budget_category_transactions():
    today = date.today()
    year       = request.args.get("year",       today.year,  type=int)
    month      = request.args.get("month",      today.month, type=int)
    budget_cat = request.args.get("budget_cat", "")
    if not budget_cat:
        return jsonify([])
    return jsonify(storage.get_transactions_by_budget_category(year, month, budget_cat))


@app.route("/api/lock-month", methods=["POST"])
def api_lock_month():
    body = request.get_json()
    storage.lock_month(body["year"], body["month"])
    return jsonify({"status": "locked"})


@app.route("/api/budget-plan/update", methods=["POST"])
def api_budget_plan_update():
    body = request.get_json()
    # Block edits on locked months
    status = storage.get_month_status(body["year"], body["month"])
    if status["locked"]:
        return jsonify({"error": "Month is locked"}), 403
    storage.save_budget_plan([{
        "year":           body["year"],
        "month":          body["month"],
        "category":       body["category"],
        "planned_amount": body["amount"],
        "notes":          body.get("notes"),
    }])
    return jsonify({"status": "ok"})


@app.route("/api/equity")
def api_equity():
    from datetime import date
    as_of_str = request.args.get("as_of")
    as_of = date.fromisoformat(as_of_str) if as_of_str else None
    return jsonify(equity_module.get_all_equity(as_of))


@app.route("/api/setup-status")
def api_setup_status():
    return jsonify(config.DATA_SOURCES)


@app.route("/api/budget-target", methods=["POST"])
def api_budget_target():
    data = request.get_json()
    category = data.get("category")
    target = data.get("monthly_target")
    if not category:
        return jsonify({"error": "category required"}), 400
    storage.set_budget_target(category, target)
    return jsonify({"status": "ok"})


@app.route("/api/transactions")
def api_transactions():
    start = request.args.get("start")
    end = request.args.get("end")
    category = request.args.get("category")
    transactions = storage.get_transactions(start_date=start, end_date=end, category=category)
    return jsonify(transactions)


if __name__ == "__main__":
    storage.init_db()
    app.run(host="0.0.0.0", debug=config.FLASK_DEBUG, port=config.FLASK_PORT)

import yaml
import storage
import config


def sync_events():
    """
    Load knowledge.yaml and upsert all events into the DB.
    Idempotent - safe to call on every ingest run.
    Returns count of events synced.
    """
    if not config.KNOWLEDGE_FILE.exists():
        print("  [INFO] knowledge.yaml not found, skipping event sync.")
        return 0

    with open(config.KNOWLEDGE_FILE, "r") as f:
        data = yaml.safe_load(f) or {}

    count = 0

    # income_changes
    for item in data.get("income_changes", []):
        storage.upsert_event({
            "event_date": str(item["date"]),
            "event_type": "income_change",
            "label": item["label"],
            "amount": item.get("amount"),
            "recurrence": item.get("recurrence", "none"),
            "notes": item.get("notes"),
            "source": "knowledge",
        })
        count += 1

    # annual_expenses
    for item in data.get("annual_expenses", []):
        storage.upsert_event({
            "event_date": str(item["date"]),
            "event_type": "annual_expense",
            "label": item["label"],
            "amount": item.get("amount"),
            "recurrence": item.get("recurrence", "none"),
            "notes": item.get("notes"),
            "source": "knowledge",
        })
        count += 1

    # subscription_changes
    for item in data.get("subscription_changes", []):
        storage.upsert_event({
            "event_date": str(item["date"]),
            "event_type": "subscription",
            "label": item["label"],
            "amount": item.get("amount"),
            "recurrence": item.get("recurrence", "monthly"),
            "notes": item.get("notes"),
            "source": "knowledge",
        })
        count += 1

    # one_off_events
    for item in data.get("one_off_events", []):
        storage.upsert_event({
            "event_date": str(item["date"]),
            "event_type": "one_off",
            "label": item["label"],
            "amount": item.get("amount"),
            "recurrence": "none",
            "notes": item.get("notes"),
            "source": "knowledge",
        })
        count += 1

    return count

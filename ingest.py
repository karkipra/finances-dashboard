"""
Weekly ingest: drop CSVs + screenshots in imports/, then run:
  python ingest.py

Processes all files, writes to SQLite, archives processed files.
"""

import shutil
from pathlib import Path
from datetime import date, timedelta
import json

import config
import storage
import parse_csv
import parse_screenshot
import parse_pdf
import knowledge_base


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def suggest_kb_additions():
    """
    Scans recent transactions and current knowledge.yaml, then uses Claude Haiku
    to suggest additions. Prints YAML snippets to console - user reviews and pastes.
    """
    if not config.ANTHROPIC_API_KEY:
        return

    import anthropic

    lookback_start = (date.today() - timedelta(days=90)).isoformat()
    txns = storage.get_transactions(start_date=lookback_start)
    if not txns:
        return

    kb_path = config.KNOWLEDGE_FILE
    kb_text = kb_path.read_text() if kb_path.exists() else ""

    txn_lines = []
    for t in txns:
        txn_lines.append(f"{t['date']}  {t['amount']:+.2f}  {t['description']}  [{t['category'] or 'uncategorized'}]")
    txn_block = "\n".join(txn_lines)

    prompt = f"""You are a personal finance assistant. Review these recent transactions and the existing knowledge base.
Identify patterns NOT already covered in knowledge.yaml:
- New recurring charges (same merchant, similar amount, monthly) -> suggest subscription_changes entry
- Large credits (>$500) not matching known income -> suggest one_off_events entry
- Large one-time debits (>$500) not matching known expenses -> suggest one_off_events or annual_expenses entry

Be conservative. Only suggest if you are confident. Skip investment transactions (dividends, securities, transfers between accounts).

Current knowledge.yaml:
---
{kb_text}
---

Recent transactions (last 90 days):
{txn_block}

Respond with ONLY a YAML snippet of new entries to add, using the same format as knowledge.yaml.
If nothing new to suggest, respond with exactly: # No new suggestions
Do not repeat entries already in knowledge.yaml."""

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        suggestion = msg.content[0].text.strip()
        if suggestion and suggestion != "# No new suggestions":
            print("\n" + "=" * 60)
            print("KB SUGGESTIONS - review and paste into knowledge.yaml if correct:")
            print("=" * 60)
            print(suggestion)
            print("=" * 60)
        else:
            print("\n  KB suggestions: nothing new to add.")
    except Exception as e:
        print(f"\n  KB suggestions skipped: {e}")


def run():
    today = date.today().isoformat()
    print(f"\n=== Pratik Finances Ingest - {today} ===\n")

    # Step 1: Init DB
    storage.init_db()

    imports_dir = config.IMPORTS_DIR
    if not imports_dir.exists():
        imports_dir.mkdir(parents=True)

    all_files = [f for f in imports_dir.iterdir() if f.is_file()]
    csv_files   = [f for f in all_files if f.suffix.lower() == ".csv"]
    image_files = [f for f in all_files if f.suffix.lower() in IMAGE_EXTENSIONS]
    pdf_files   = [f for f in all_files if f.suffix.lower() == ".pdf"]

    if not csv_files and not image_files and not pdf_files:
        print("No files found in imports/. Drop CSVs, PDFs, or screenshots there and re-run.")
    else:
        print(f"Found {len(csv_files)} CSV(s), {len(pdf_files)} PDF(s), {len(image_files)} image(s).\n")

    # Step 2: Process CSVs
    total_txn_new = 0
    total_txn_skip = 0
    total_bal_new = 0

    for f in csv_files:
        print(f"  Parsing CSV: {f.name}")
        file_type, rows = parse_csv.parse_file(f)

        if file_type == "transactions":
            new, skipped = storage.save_transactions(rows, import_batch=today)
            total_txn_new += new
            total_txn_skip += skipped
            print(f"    -> Transactions: {new} new, {skipped} skipped (dedup)")
        elif file_type == "balances":
            new, _ = storage.save_balances(rows, import_batch=today)
            total_bal_new += new
            print(f"    -> Balances: {new} accounts saved")
        else:
            print(f"    -> Unrecognized format, skipping.")

    # Step 3: Recompute net worth from balances
    nw_dates = storage.recompute_net_worth()
    if nw_dates:
        latest = storage.get_latest_net_worth()
        if latest:
            print(f"\n  Net worth updated for {len(nw_dates)} date(s).")
            print(f"  Latest net worth: ${latest['net_worth']:,.2f} ({latest['date']})")

    # Step 4: Process screenshots
    for f in image_files:
        print(f"\n  Parsing screenshot: {f.name}")
        extracted, tokens = parse_screenshot.extract_data(f)

        if extracted:
            status = "ok"
            storage.log_screenshot_parse(f.name, extracted, tokens, status)

            # Use today as the snapshot date (import date, not screenshot UI date)
            snap_date = today
            accounts = extracted.get("accounts") or []
            bal_rows = []
            for acct in accounts:
                if acct.get("balance") is not None:
                    raw_name = acct.get("name", "Unknown")
                    friendly = config.ACCOUNT_ALIASES.get(raw_name, raw_name)
                    bal_rows.append({
                        "snapshot_date": snap_date,
                        "account": friendly,
                        "balance": acct["balance"],
                        "account_type": acct.get("account_type", ""),
                    })

            # Also check totals
            totals = extracted.get("totals") or {}
            if totals.get("net_worth") is not None and not bal_rows:
                # No individual accounts but we have a net worth total - save as synthetic row
                print(f"    -> Net worth from screenshot: ${totals['net_worth']:,.2f}")

            if bal_rows:
                new, _ = storage.save_balances(bal_rows, import_batch=today)
                print(f"    -> Saved {new} account balance(s) from screenshot (date: {snap_date})")
                # Recompute net worth again with the new screenshot data
                storage.recompute_net_worth()
                latest = storage.get_latest_net_worth()
                if latest:
                    print(f"    -> Net worth updated: ${latest['net_worth']:,.2f}")

            print(f"    -> Screenshot parsed ({tokens} tokens, confidence: {extracted.get('confidence', 'n/a')})")
        else:
            storage.log_screenshot_parse(f.name, None, tokens, "error")
            print(f"    -> Parse failed or API key missing.")

    # Step 4b: Process PDFs (budget documents)
    for f in pdf_files:
        print(f"\n  Parsing PDF: {f.name}")
        rows, tokens = parse_pdf.extract_budget(f)
        if rows:
            count = storage.save_budget_plan(rows)
            print(f"    -> Saved {count} budget plan row(s) ({tokens} tokens)")
        else:
            print(f"    -> No budget data extracted (API key missing or parse error).")

    # Step 5: Sync knowledge.yaml
    print(f"\n  Syncing knowledge.yaml...")
    event_count = knowledge_base.sync_events()
    print(f"  -> {event_count} event(s) synced.")

    # Step 6: Ensure all transaction categories exist in budget_categories
    categories = storage.get_all_categories()
    storage.ensure_budget_categories(categories)

    # Step 7: Archive processed files
    if all_files:
        archive_dir = imports_dir / "processed" / today
        archive_dir.mkdir(parents=True, exist_ok=True)
        moved = 0
        for f in all_files:
            dest = archive_dir / f.name
            # Handle name collisions
            if dest.exists():
                dest = archive_dir / (f.stem + "_2" + f.suffix)
            shutil.move(str(f), str(dest))
            moved += 1
        print(f"\n  Archived {moved} file(s) to imports/processed/{today}/")

    # Step 7b: KB suggestions (semi-auto knowledge base)
    suggest_kb_additions()

    # Summary
    print(f"\n=== Summary ===")
    if total_txn_new or total_txn_skip:
        print(f"  Transactions: {total_txn_new} new, {total_txn_skip} skipped")
    if total_bal_new:
        print(f"  Balance rows: {total_bal_new} saved")
    latest = storage.get_latest_net_worth()
    if latest:
        print(f"  Net worth: ${latest['net_worth']:,.2f} as of {latest['date']}")
    print(f"\nOpen http://localhost:{config.FLASK_PORT} to view dashboard.")
    print("Run 'python app.py' if Flask isn't already running.\n")


if __name__ == "__main__":
    run()

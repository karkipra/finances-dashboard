"""
Ingest Empower transactions CSV.

Usage:
  python ingest.py              # import new transactions, archive file
  python ingest.py --dry-run    # preview what would be added, no DB writes

Drop the Empower CSV in imports/ before running.

Everything else (account balances, PDF reading, Amex direct exports, BFSFCU manual
transactions) is handled manually by Claude reading files directly. See README for
the full session workflow.
"""

import sys
import shutil
from pathlib import Path
from datetime import date

import config
import storage
import parse_csv
import knowledge_base


def run(dry_run=False):
    today = date.today().isoformat()
    mode = "DRY RUN - no changes will be written" if dry_run else today
    print(f"\n=== Pratik Finances Ingest - {mode} ===\n")

    storage.init_db()

    imports_dir = config.IMPORTS_DIR
    if not imports_dir.exists():
        imports_dir.mkdir(parents=True)

    csv_files = [f for f in imports_dir.iterdir() if f.is_file() and f.suffix.lower() == ".csv"]

    if not csv_files:
        print("No CSV files found in imports/. Drop the Empower transactions CSV there and re-run.")
        print("(For balances, Amex exports, BFSFCU transactions - ask Claude to read and ingest manually.)\n")
        return

    print(f"Found {len(csv_files)} CSV(s).\n")

    total_new = 0
    total_skip = 0

    for f in csv_files:
        print(f"  Parsing: {f.name}")
        file_type, rows = parse_csv.parse_file(f)

        if file_type != "transactions":
            print(f"    -> Not a transactions CSV, skipping.")
            continue

        if dry_run:
            # Preview only - check each row against DB without writing
            import sqlite3
            conn = sqlite3.connect(str(config.DB_PATH))
            new_rows = []
            skip_rows = []
            for row in rows:
                exists = conn.execute(
                    "SELECT 1 FROM transactions WHERE date=? AND account=? AND description=? AND amount=?",
                    (row["date"], row["account"], row["description"], row["amount"])
                ).fetchone()
                if exists:
                    skip_rows.append(row)
                else:
                    new_rows.append(row)
            conn.close()

            print(f"    -> Would add {len(new_rows)} new, skip {len(skip_rows)} duplicates")
            if new_rows:
                print(f"\n    NEW transactions:")
                for r in new_rows:
                    print(f"      {r['date']}  {r['description'][:40]:40}  ${abs(r['amount']):.2f}")
        else:
            new, skipped = storage.save_transactions(rows, import_batch=today)
            total_new += new
            total_skip += skipped
            print(f"    -> {new} new, {skipped} skipped (dedup)")

    if not dry_run:
        # Recompute net worth from all balance snapshots
        nw_dates = storage.recompute_net_worth()
        if nw_dates:
            latest = storage.get_latest_net_worth()
            if latest:
                print(f"\n  Net worth recomputed for {len(nw_dates)} date(s).")
                print(f"  Latest: ${latest['net_worth']:,.2f} as of {latest['date']}")

        # Sync knowledge.yaml events
        event_count = knowledge_base.sync_events()
        print(f"\n  Knowledge base: {event_count} event(s) synced.")

        # Archive processed files
        all_files = [f for f in imports_dir.iterdir() if f.is_file()]
        if all_files:
            archive_dir = imports_dir / "processed" / today
            archive_dir.mkdir(parents=True, exist_ok=True)
            for f in all_files:
                dest = archive_dir / f.name
                if dest.exists():
                    dest = archive_dir / (f.stem + "_2" + f.suffix)
                shutil.move(str(f), str(dest))
            print(f"  Archived {len(all_files)} file(s) to imports/processed/{today}/")

        print(f"\n=== Summary ===")
        print(f"  Transactions: {total_new} new, {total_skip} skipped")
        latest = storage.get_latest_net_worth()
        if latest:
            print(f"  Net worth: ${latest['net_worth']:,.2f} as of {latest['date']}")

        # Broken account checklist - always shown so nothing gets missed
        print(f"\n*** Manual update required - ask Claude or update directly ***")
        import sqlite3
        conn = sqlite3.connect(str(config.DB_PATH))
        conn.row_factory = sqlite3.Row
        broken = [
            ("BFSFCU Checking (4346)",        "Empower shows $0 - get real balance from BFSFCU app"),
            ("LendingClub HYSA",              "Never use Empower value - last DB balance + $500/month"),
            ("HealthEquity HSA",              "Delayed in Empower - carry forward or update manually"),
            ("FSFCU Visa Signature (Nastya)", "Intermittent - confirm current balance"),
        ]
        for account, note in broken:
            row = conn.execute(
                "SELECT balance, snapshot_date FROM account_balances WHERE account = ? ORDER BY snapshot_date DESC LIMIT 1",
                (account,)
            ).fetchone()
            if row:
                print(f"  - {account}: ${row['balance']:,.2f} as of {row['snapshot_date']}. {note}")
            else:
                print(f"  - {account}: no record. {note}")
        conn.close()

    print(f"\nOpen http://localhost:{config.FLASK_PORT} to view dashboard.\n")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)

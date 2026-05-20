"""
One-time ingest: May 2026 session (2026-05-20)
Sources: Empower CSV + BFSFCU export
"""
import sqlite3, csv
from datetime import datetime

BATCH = "2026-05-20"
BFSFCU_BATCH = "manual-2026-05-20"

conn = sqlite3.connect("data/finances.db")
c = conn.cursor()

inserted = []
skipped_dupe = []

def insert_tx(date, account, desc, amount, batch):
    c.execute(
        "SELECT id FROM transactions WHERE date=? AND account=? AND description=? AND ABS(amount - ?) < 0.01",
        (date, account, desc, float(amount))
    )
    if c.fetchone():
        skipped_dupe.append((date, desc, amount))
        return False
    c.execute(
        "INSERT INTO transactions (date, account, description, amount, import_batch) VALUES (?,?,?,?,?)",
        (date, account, desc, float(amount), batch)
    )
    inserted.append((date, account[:30], desc[:45], float(amount)))
    return True

# ---- EMPOWER CSV: MAY ONLY ----
SKIP_ACCTS = [
    "Roth Ira - Ending in 3868",
    "Pratik Karki Roth Ira Brokerage",
    "Traditional Ira",
    "Uc Defined Contribution",
    "University Of California 457",
    "University Of California Fmtc",
    "401(k) Account",
    "Google Llc 401(k)",
    "Designated Beneficiary In - Ending in 258",
    "Anastasiia Morozova",
    "Vehicle: Vehicle Fixed",
    "Account: Visa Signature",
]

CC_PMT = [
    "autopay payment - thank you",
    "autopay 2xxxxxxxxxx5391",
    "amex epayment",
    "citi autopay",
    "applecard gsbank",
    "visa/mc payment",
    "citibank",
    "american express",
    "apple card",
    "cardmember serv",
]

with open(r"C:\Users\karki\Downloads\2026-02-20 thru 2026-05-20 transactions.csv", newline="", encoding="utf-8") as f:
    empower_rows = list(csv.DictReader(f))

txns_1022 = {}
for row in empower_rows:
    if "1022" in row["Account"]:
        txns_1022[(row["Date"], row["Description"].strip(), row["Amount"])] = True

for row in empower_rows:
    date = row["Date"]
    if not date.startswith("2026-05"):
        continue

    acct = row["Account"]
    desc = row["Description"].strip()
    amt  = float(row["Amount"])
    dl   = desc.lower()

    if any(s.lower() in acct.lower() for s in SKIP_ACCTS):
        continue
    if "uc pathway" in dl:
        continue
    if any(s in dl for s in CC_PMT):
        continue
    if "citi" in acct.lower() and "autopay" in dl:
        continue

    # Plain transfer filter for BFSFCU
    if "joint checking" in acct.lower():
        is_xfer = "external deposit" in dl or "external withdrawal" in dl or "withdrawal transfer" in dl
        exceptions = ["anthromind","uc santa barbara","lendingclub","zion","vanguard group",
                      "franchise tax","venmo","zelle","embrace","payroll"]
        if is_xfer and not any(e in dl for e in exceptions):
            continue
        # Skip Vanguard Group (already manually added as Roth contrib)
        if "vanguard group" in dl:
            continue

    # 1006/1022 dedup
    if "1006" in acct:
        if (date, desc, row["Amount"]) in txns_1022:
            continue

    # Skip vet visit (reimbursed)
    if "veterinary" in dl:
        continue

    insert_tx(date, acct, desc, amt, BATCH)

# ---- BFSFCU EXPORT: MAY ONLY ----
BFSFCU_CC = ["cardmember serv","amex epayment","citi autopay","applecard gsbank","visa/mc payment"]
BFSFCU_SKIP = ["ext-xfer","credit interest"]
# Skip plain "- transfer" entries unless meaningful
BFSFCU_KEEP = ["anthromind","payroll","lendingclub","lending","zion","vanguard",
               "nastya","state farm","embrace","venmo","individual buy"]

with open(r"C:\Users\karki\Downloads\export_20260520.csv", newline="", encoding="utf-8") as f:
    bfsfcu_rows = list(csv.DictReader(f))

for row in bfsfcu_rows:
    dt = datetime.strptime(row["Date"].strip(), "%m/%d/%Y")
    date = dt.strftime("%Y-%m-%d")
    if not date.startswith("2026-05"):
        continue

    desc = row["Description"].strip()
    amt_str = row["Amount"].replace("$","").replace(",","")
    amt = float(amt_str)
    dl  = desc.lower()

    if any(s in dl for s in BFSFCU_CC):
        continue

    is_plain = "- transfer" in dl or any(s in dl for s in BFSFCU_SKIP)
    is_keep  = any(s in dl for s in BFSFCU_KEEP)
    if is_plain and not is_keep:
        continue

    # Skip already-in-DB entries (car payment, rent - covered by earlier manual batch)
    # insert_tx handles dupe detection via SQL constraint

    # Skip Vanguard (will add as separate Roth entry below)
    if "vanguard buy individual buy" in dl:
        continue

    insert_tx(date, "BFSFCU Checking", desc, amt, BFSFCU_BATCH)

# ---- MANUAL ADDITIONS ----

# May 18 Chargepoint from Citi (from user's pasted data, not in Empower CSV)
insert_tx("2026-05-18", "Costco Anywhere Visa Card By Citi - Ending in 7865",
          "Chargepoint", -5.22, BFSFCU_BATCH)

# May 16 Venmo Cameron Hannah (from BFSFCU export - missed in automated pass)
insert_tx("2026-05-16", "BFSFCU Checking",
          "Point Of Sale Withdrawal VENMO *Cameron Hannah- Visa Direct NY", -12.00, BFSFCU_BATCH)

# Pratik Roth IRA contribution via Vanguard May 8 ($750)
insert_tx("2026-05-08", "BFSFCU Checking",
          "Roth IRA Contribution - Pratik (Vanguard)", -750.00, BFSFCU_BATCH)

# US Bank checking account bonus (one-time income)
insert_tx("2026-05-20", "BFSFCU Checking",
          "US Bank Checking Account Bonus", 450.00, BFSFCU_BATCH)

conn.commit()

print("=" * 60)
print(f"INSERTED: {len(inserted)}")
for r in inserted:
    print(f"  {r[0]}  {r[3]:>9.2f}  {r[2]}")

print()
print(f"SKIPPED (dupes): {len(skipped_dupe)}")
for r in skipped_dupe:
    print(f"  {r[0]}  {r[2]:>9.2f}  {r[1]}")

conn.close()
print("\nDone. Run storage.recompute_net_worth() next.")

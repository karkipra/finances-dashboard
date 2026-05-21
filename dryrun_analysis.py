import sqlite3, csv
from datetime import datetime

conn = sqlite3.connect("data/finances.db")
c = conn.cursor()

def in_db(date, account, desc, amt):
    c.execute("SELECT id FROM transactions WHERE date=? AND account=? AND description=? AND ABS(amount - ?) < 0.01",
              (date, account, desc, float(amt)))
    return c.fetchone() is not None

def in_db_any(date, amt, desc_frag):
    c.execute("SELECT id, account, description FROM transactions WHERE date=? AND ABS(amount - ?) < 0.01 AND LOWER(description) LIKE ?",
              (date, float(amt), "%" + desc_frag.lower() + "%"))
    return c.fetchone()

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

will_insert = []
issues = []

for row in empower_rows:
    date = row["Date"]
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

    is_xfer = ("external deposit" in dl or "external withdrawal" in dl or "withdrawal transfer" in dl)
    exceptions = [
        "anthromind","uc santa barbara","lendingclub","lending club",
        "zion","vanguard group","franchise tax","poshmark","venmo","zelle",
        "embrace","university of california","payroll",
    ]
    if is_xfer and not any(e in dl for e in exceptions):
        continue

    if "joint checking" in acct.lower() and "vanguard group" in dl:
        issues.append("FLAG  {}  BFSFCU->Vanguard {}  Pratik Roth; DB has -1125, CSV shows -1126 (off by $1)".format(date, amt))
        continue

    if "1006" in acct:
        if (date, desc, row["Amount"]) in txns_1022:
            continue

    if "veterinary" in dl:
        issues.append("FLAG  {}  VET {} on 1022 - DO NOT INSERT (reimbursed by Embrace)".format(date, amt))
        continue

    if in_db(date, acct, desc, amt):
        continue

    if "joint checking" in acct.lower() or "4346" in acct:
        if in_db_any(date, amt, desc[:12]):
            continue

    will_insert.append((date, acct, desc, amt))

by_month = {}
for r in will_insert:
    m = r[0][:7]
    by_month.setdefault(m, []).append(r)

print("=" * 65)
print("EMPOWER CSV - DRY RUN (would insert)")
print("=" * 65)
for month in sorted(by_month.keys()):
    rows_m = by_month[month]
    print("\n--- {} ({} rows) ---".format(month, len(rows_m)))
    for r in rows_m:
        note = ""
        if "embrace" in r[2].lower() and r[3] > 0:
            note = "  <- INSURANCE REIMBURSEMENT (income)"
        if "franchise tax" in r[2].lower():
            note = "  <- TAX PAYMENT"
        if "venmo" in r[2].lower():
            note = "  <- VENMO TRANSFER"
        if "zion" in r[2].lower():
            note = "  <- ZION HEALTHSHARE"
        print("  {}  {:>9.2f}  {:<26}  {:<40}{}".format(
            r[0], r[3], r[1][:26], r[2][:40], note))

print("\nTotal empower: {}".format(len(will_insert)))

print()
print("=" * 65)
print("FLAGS / QUESTIONS")
print("=" * 65)
for i in issues:
    print(" ", i)

c.execute("SELECT id, date, amount, import_batch FROM transactions WHERE LOWER(description) LIKE '%tesla insurance%' ORDER BY date")
rows = c.fetchall()
print("\n  Tesla Insurance in DB:")
for r in rows:
    print("    id={}  date={}  amt={}  batch={}".format(r[0], r[1], r[2], r[3]))
print("  (Empower CSV: 2026-02-27 -149.44, 2026-03-27 -149.41, 2026-04-24 -156.58)")

# BFSFCU export - May only
print()
print("=" * 65)
print("BFSFCU EXPORT - May entries only (not in Empower)")
print("=" * 65)

BFSFCU_CC    = ["cardmember serv","amex epayment","citi autopay","applecard gsbank","visa/mc payment"]
BFSFCU_PLAIN = ["ext-xfer","- transfer","credit interest"]
BFSFCU_KEEP  = [
    "anthromind","payroll","lendingclub","lending","uc santa","university of california",
    "zion","vanguard","individual buy","nastya","state farm","embrace","venmo",
]

with open(r"C:\Users\karki\Downloads\export_20260520.csv", newline="", encoding="utf-8") as f:
    bfsfcu_rows = list(csv.DictReader(f))

bfsfcu_insert = []
for row in bfsfcu_rows:
    dt = datetime.strptime(row["Date"].strip(), "%m/%d/%Y")
    date = dt.strftime("%Y-%m-%d")
    if date < "2026-05-01":
        continue

    desc = row["Description"].strip()
    amt_str = row["Amount"].replace("$","").replace(",","")
    amt = float(amt_str)
    dl = desc.lower()

    if any(s in dl for s in BFSFCU_CC):
        continue
    is_plain = any(s in dl for s in BFSFCU_PLAIN)
    is_keep  = any(s in dl for s in BFSFCU_KEEP)
    if is_plain and not is_keep:
        continue

    if any(e[0] == date and abs(e[3] - amt) < 0.01 for e in will_insert):
        continue

    if in_db_any(date, amt, desc[:10]):
        continue

    bfsfcu_insert.append((date, desc, amt))

for r in bfsfcu_insert:
    note = ""
    dl = r[1].lower()
    if "vanguard" in dl or "individual buy" in dl:
        note = "  <- PRATIK ROTH CONTRIBUTION"
    if "lendingclub" in dl or ("lend" in dl and "club" in dl):
        note = "  <- HYSA $500"
    if "nastya" in dl or "x8699" in dl:
        note = "  <- NASTYA ROTH TRANSFER"
    if "zion" in dl:
        note = "  <- ZION HEALTHSHARE"
    if "payroll" in dl or "anthromind" in dl:
        note = "  <- ANTHROMIND PAYROLL"
    if "state farm" in dl:
        note = "  <- STATE FARM INSURANCE"
    if "venmo" in dl:
        note = "  <- VENMO"
    print("  {}  {:>9.2f}  {:<55}{}".format(r[0], r[2], r[1][:55], note))

print("\nTotal BFSFCU-only May: {}".format(len(bfsfcu_insert)))
conn.close()

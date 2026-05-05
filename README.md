# Nastik Finances Dashboard

> **Core requirement:** Both Pratik and Nastya must be able to open this dashboard from any device on home WiFi at any time. Always verify LAN access works after setup or changes.

> We are improving this over time. Every week we get new data, which means the financial projections will be tighter. The goal is a living system that gets smarter each month - eventually powering accurate 2-5 year plans.

Local Flask dashboard for Pratik + Nastya (Nastik). Tracks net worth, monthly budget planned vs actual, and long-term projections. Runs at `http://localhost:5000`.

---

## Weekly Session Checklist

**Follow every step in order. Do not skip any step.**

This is the mandatory protocol for every weekly budget update session.

---

### Step 0 - Pre-session setup

- [ ] Launch app: `python app.py` then open http://localhost:5000
- [ ] Note what date range to cover (usually last Friday to today)
- [ ] Collect from Pratik:
  - Empower transactions CSV: empower.com -> All Transactions -> Export (set date range explicitly)
  - FireShot PDF: full-page screenshot of Empower net worth page
  - BFSFCU real balance from BFSFCU app (Empower does not sync - never use Empower value)
  - Any manual transactions not in Empower (Apple Card, etc.)

---

### Step 1 - Read the PDF (account balances)

Read each account from the Empower screenshot. Apply these rules before inserting anything:

**LendingClub HYSA (CRITICAL):**
- [ ] NEVER use the Empower value - Empower does not connect to LendingClub, value is permanently stale
- [ ] Find last real balance in DB: `SELECT * FROM account_balances WHERE account='Lending Club HYSA' ORDER BY snapshot_date DESC LIMIT 3`
- [ ] Add $500 for each month that has passed since that snapshot
- [ ] Use that computed value, not anything from the PDF

**BFSFCU Checking:**
- [ ] NEVER use the Empower value (Empower shows $0 or stale)
- [ ] Use the real balance Pratik got from the BFSFCU app this session

**HealthEquity HSA:**
- [ ] Empower shows "Delayed" and excludes it from the net worth total
- [ ] Carry forward the last known DB value unless Pratik provides an update
- [ ] Check last value: `SELECT * FROM account_balances WHERE account='HealthEquity HSA' ORDER BY snapshot_date DESC LIMIT 1`

**American Express balance:**
- [ ] Use only the 1006 balance as the total for the whole account
- [ ] NEVER insert a 1022 (Nastya subcard) balance row into account_balances
- [ ] 1006 balance = combined total for both cards

**BFSFCU Car Note:**
- [ ] Do NOT zero out until the actual payoff date: May 1, 2026
- [ ] After May 1: set balance to $0 and note the payoff milestone

**Credit cards:**
- [ ] Credit card balances are NOT counted as liabilities in net worth
- [ ] Only `account_type = "loan"` or `"mortgage"` counts toward liabilities
- [ ] This is enforced in `recompute_net_worth()` in storage.py - credit type is skipped

**All other accounts:** use Empower values from the PDF directly.

---

### Step 2 - Process the CSV (transactions)

**Delete immediately after ingest (every session, no exceptions):**
- [ ] UC Pathway entries: "Uc Pathway Xx60 - Fees" and "Uc Pathway Xx60 - Realizedgainloss" (UC Defined Contribution account 0988). DELETE from transactions - they are internal Fidelity fees already reflected in the account balance.
- [ ] "Account: Visa Signature" Roth/Fidelity entries on known Roth contribution dates. These are duplicates of the real BFSFCU -> Nastya 8699 -> Fidelity 3868 flow. DELETE any "Account: Visa Signature" rows for "Roth" or "Fidelity Investments" on dates matching a known Roth contribution.

**Skip without inserting:**
- [ ] CC payment lump sums from checking: "AMEX EPAYMENT", "CITI AUTOPAY", "APPLECARD GSBANK", "External Withdrawal Visa/mc Payment" - these are already counted via individual CC charges
- [ ] Plain transfers with no keyword match (e.g. "External Deposit ... Transfer")
- [ ] All 401(k) fund entries (internal Vanguard/Fidelity trades, reinvestments, sweeps)
- [ ] Investment account purchases, trades, and reinvestments from brokerage accounts

**Amex 1006/1022 dedup (CRITICAL - apply to every 1006 entry):**
- [ ] Pratik (1006) and Nastya (1022) share ONE Amex account. Nastya has a supplementary card.
- [ ] Empower regularly shows the same charge on BOTH cards in the CSV - this is a quirk, not two charges.
- [ ] For every 1006 transaction: check if the same date + amount + merchant exists on 1022. If yes, skip the 1006 entry entirely. Keep only the 1022 version.
- [ ] Only insert a 1006 transaction if it has NO 1022 counterpart on that date.
- [ ] Exception: if both cards were used for genuinely different purchases at the same merchant on the same day (rare), keep both.
- [ ] Check SQL: `SELECT * FROM transactions WHERE date='DATE' AND ABS(amount)=AMOUNT AND LOWER(description) LIKE '%MERCHANT%'`

**Reimbursements:**
- [ ] Ask Pratik before including any charge he flagged as "reimbursed"
- [ ] If fully reimbursed (e.g. vet visit where insurance paid out the full amount): DELETE the gross expense entry. The net effect comes through via the insurance deposit in the checking account.
- [ ] If pending reimbursement (e.g. conference fee to be reimbursed by employer): insert as one_time_expense with a note. Update budget_plan row (see Step 4).
- [ ] Insurance reimbursement deposits from checking: treat as income (positive transactions from BFSFCU)

**Duplicate detection before every insert:**
- [ ] Query: `SELECT id FROM transactions WHERE date='X' AND account='Y' AND description='Z' AND amount=A`
- [ ] If a row exists, skip. Never insert twice.

---

### Step 3 - Manual adds (BFSFCU is disconnected)

BFSFCU does not sync with Empower. All BFSFCU transactions must be added manually with `import_batch='manual-YYYY-MM-DD'`.

- [ ] Pratik paycheck (biweekly, ~$1,281.82 net from Anthromind) - check if 1 or 2 paychecks fell in this period
- [ ] Nastya UCSB paycheck (monthly, ~$3,767.22 net) - check if it landed this period. Note: income goes to $0 after PhD gap starts (May 2026).
- [ ] Rent to UCSB ($1,335 - maps to expenses_rent via "uc santa barbara" keyword)
- [ ] State Farm rental insurance (~$14/mo from BFSFCU - maps to expenses_rent via "state farm" keyword)
- [ ] HYSA contribution ($500/mo - maps to "hysa" category via "lendingclub" or "lending club" keyword)
- [ ] Roth IRA contributions if they went through BFSFCU (maps to "roth" category)
- [ ] Any Apple Card charges Pratik flagged this week (Apple Card not in Empower)
- [ ] Any other direct debits or deposits Pratik flags

**When adding a Roth contribution:**
- [ ] Only count it ONCE. The checking transfer out (BFSFCU -> Nastya account -> Fidelity) counts as the contribution.
- [ ] Do NOT also insert from the Fidelity/Roth side - that side is already in the CSV and will be caught by the delete rules above.

---

### Step 4 - Category and budget plan check

- [ ] Open /budget page for the current month. Check if actuals are rendering.
- [ ] Scan the Buffer/Misc row. If it is large (>$200), identify unmatched transactions.
  - Add keywords to `BUDGET_CATEGORY_RULES` in config.py (description-first, first match wins)
  - Refresh the page - no re-ingest needed, actuals recompute live
- [ ] Check for one-time expenses (conferences, taxes, travel, medical):
  - These need a `budget_plan` row update, not just a transaction insert
  - `UPDATE budget_plan SET one_time_expense=AMOUNT, notes='description' WHERE year=Y AND month=M`
  - The budget template reads one_time_expense from budget_plan, NOT from actuals
  - Inserting the transaction alone will NOT make it appear in the one_time_expense row
- [ ] Verify the Total Outflow diff row shows green (under budget) or red (over budget)
- [ ] Spot-check: expenses_car_loan and expenses_rent should not be doubled. If they are, search for manual + Empower duplicate entries and delete the older one.

---

### Step 5 - Save account snapshot and recompute

- [ ] Save ALL accounts for today's date as a single snapshot - not just changed accounts
  - Use `storage.save_balances(snapshot_date, {account: balance, ...})`
  - Include every account from the accounts table, even ones that didn't change
- [ ] After saving, run: `storage.recompute_net_worth()`
- [ ] Verify no stale `net_worth_snapshots` rows exist for dates you may have touched
  - If you manually edited account_balances for a past date, clean up: `DELETE FROM net_worth_snapshots WHERE snapshot_date='DATE'` then recompute

---

### Step 6 - Final verification

- [ ] Net worth delta vs last week makes sense (typical week: +$200 to +$800 depending on paychecks)
- [ ] Liabilities total only includes loan/mortgage accounts - NOT credit cards
- [ ] LendingClub balance: was +$500 added for this month? Confirm the new real balance.
- [ ] Check each broken account was explicitly handled this session:
  - BFSFCU Checking: used real balance from BFSFCU app
  - LendingClub HYSA: computed from last real balance + $500 increments
  - HealthEquity HSA: carried forward or updated
- [ ] If any broken account was NOT updated, say so explicitly before closing
- [ ] Budget page: actuals show for current month, categories look correct
- [ ] No double-counted entries in expenses_car_loan, expenses_rent, or roth

---

### Step 7 - Post-session

- [ ] Add any new rules, exceptions, or surprises to Lessons Learned in this README
- [ ] Update CLAUDE.md if any global patterns changed
- [ ] Note next session's expected one-time items (e.g. quarterly aerial payment, tax installment)

---

## Budget Planner: Rules and Assumptions

Four numbers drive the monthly budget view: Inflow, Outflow, Invested, Net Cash.

### Inflow
- All positive transactions from non-investment accounts count as inflow
- Paychecks, refunds, reimbursements, and one-time income (e.g. Poshmark sales) are all included
- Excluded: CC payment credits, retirement/brokerage account transactions, and plain transfers with no keyword match
- BFSFCU checking is disconnected from Empower - any deposits not in the CSV must be added manually

### Outflow
- All negative transactions from non-investment accounts count as outflow
- CC payment lump sums from checking are excluded (individual charges on the CC are counted instead, avoiding double-counting)
- Investment/retirement account purchases and trades are excluded (not real spending)
- Transfers with no keyword match are silently dropped
- Anything that doesn't match a category rule lands in Buffer/Misc

### Invested (HYSA + Roth)
- HYSA and Roth contributions are tracked as their own outflow categories and shown in the Invested KPI separately
- LendingClub balance: ALWAYS wrong in Empower. Never use the Empower PDF value. See Step 1 above.
- Keywords "lending club", "lendingclub" map to HYSA; "vanguard", "schwab", "roth" map to Roth

### Net Cash
- Net cash = total inflow - total outflow (spending + savings combined)
- When actuals exist (month is locked and has transactions): uses real transaction totals
- When no actuals: uses planned amounts from the budget seed

### Category Matching Rules
- Keywords match transaction description first, then Empower category - first match wins
- Order in `BUDGET_CATEGORY_RULES` in `config.py` matters: more specific rules must come before generic ones
- Key ordering dependencies:
  - "tesla insurance" before "tesla" (else all Tesla charges go to EV charging)
  - "orchid eros" before generic dining rules
  - "uber eats" before "uber"
- Unmatched expenses fall to Buffer/Misc - if Buffer is large, tune keywords in config.py
- Actuals recompute live on every API call - no re-ingest needed after changing a rule

### American Express: Two Cards, One Account

Pratik and Nastya each have a physical Amex card but they are on the same account with one shared balance.

- `Blue Cash Everyday ( ) - Ending in 1006` - Pratik's card
- `Blue Cash Everyday ( ) - Ending in 1022` - Nastya's supplementary card

**Balance rule:** The 1006 balance from Empower is the true total for the whole account. Never add 1006 + 1022 together. Never insert a 1022 balance row into account_balances.

**Transaction rule:** Empower shows the same charge on both 1006 and 1022 when Nastya uses her card. This is a quirk. Same merchant + amount + date on both = ONE transaction. Keep only the 1022 version. Only insert a 1006 entry when it has no 1022 counterpart.

**Dedup rule (every session):** Before inserting any 1006 transaction, check if the same date + amount + merchant exists on 1022. If yes, skip the 1006 entry entirely.

**Citi Costco card (7865):** This is Pratik's card. Not subject to the 1006/1022 dedup rule. Insert normally.

### BFSFCU: Empower Connection Broken

BFSFCU (checking 4346) is not syncing with Empower. Until reconnected, all BFSFCU transactions must be added manually each session. Use `import_batch='manual-YYYY-MM-DD'`.

Known BFSFCU transactions to add each session:
- Pratik paycheck (biweekly)
- Nastya paycheck (monthly, until May 2026 PhD gap)
- Rent to UCSB
- State Farm rental insurance
- HYSA contribution
- Any direct debits

### Broken / Delayed Accounts

| Account | Status | What to do each session |
|---------|--------|------------------------|
| BFSFCU Checking (4346) | Not syncing (Empower shows $0) | Get real balance from BFSFCU app |
| LendingClub HYSA | Not connected (Empower value permanently stale) | Last real DB balance + $500 per month elapsed |
| HealthEquity HSA | "Delayed" in Empower (excluded from Empower total) | Carry forward last DB balance unless Pratik updates |
| FSFCU Visa Signature (Nastya) | Intermittent | Confirm balance each session |

**Rule:** If any of these was not explicitly handled this session, say so. Never let a stale Empower value silently overwrite a manually set correct balance.

### Transactions to Delete After Every Ingest

- **UC Pathway fee/gain-loss entries:** "Uc Pathway Xx60 - Fees" and "Uc Pathway Xx60 - Realizedgainloss" (account 0988). Internal Fidelity admin fees - already reflected in the account balance. Delete every time.
- **"Account: Visa Signature" Roth entries:** Duplicate of the real Roth contribution flow. Delete any "Account: Visa Signature" rows for "Roth" or "Fidelity Investments" on known Roth contribution dates.

---

## Quick Start

```bash
cd pratik-finances-dashboard
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python seed_budget.py   # one-time: seeds 2025-2026 budget plan
python app.py           # visit http://localhost:5000 or http://192.168.1.186:5000
```

**Daily use:**
```bash
python app.py
```
Binds to `0.0.0.0` - accessible at `http://192.168.1.133:5000` from any device on home WiFi.

Requires a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Sharing on Home Network (Nastya's Phone / Other Devices)

**Nastya's URL:** `http://192.168.1.186:5000`

No setup needed - just open that URL in any browser while connected to home WiFi.

Requirements:
- Pratik's laptop must be on and the server running (`python app.py`)
- Both devices must be on the same WiFi network
- Does not work on cellular or outside the home network

**Windows Firewall (one-time setup, required for LAN access):**
Run once in an elevated terminal:
```
netsh advfirewall firewall add rule name="Flask 5000 - Finances Dashboard" dir=in action=allow protocol=TCP localport=5000
```

**IP address note:** `192.168.1.186` is DHCP-assigned and could change after a restart. To lock it permanently: log into the router admin page (usually `192.168.1.1`), find "DHCP Reservations", and pin the laptop's MAC address to `192.168.1.186`.

---

## Pages

### Monthly Budget (`/budget`) - default page

Shows the planned budget for any month from Jan 2025 to Dec 2026 side by side with actuals.

Layout:
- Left column: Income (post-tax) + Net (big number)
- Right column: Expenses in three zones:
  - Spending: 11 sub-categories (rent, groceries, dining, car ins, EV, internet, subs, healthcare, pets, personal, fitness + buffer)
  - Savings: HYSA + Roth IRA (green tinted)
  - One-time: taxes, conference fees, travel, etc. (when applicable - requires budget_plan row update)

Planned vs Actual: When transactions exist for a month, the expense table shows Planned | Actual | Diff columns. Green = under budget, red = over.

Transaction drill-down: Every category row has a `+` button. Click to expand and see each transaction counted toward that category.

**Key months:**
| Month | Notes |
|-------|-------|
| Jan-Apr 2026 | Both incomes, full spending, Roth maxing |
| Apr 2026 | $1,414 car loan final payment. $300 taxes (1 of 4). 2025 Roth maxed. |
| May 2026 | Car note paid off (May 1). Nastya income drops to $0. Pratik 3-paycheck month. |
| May-Dec 2026 | Lean $2,642 budget (Nastya no income). $285/mo taxes (2-4 of 4). |
| Oct 2026 | Pratik 3-paycheck month (+$1,281 extra). |

### Net Worth (`/net-worth`)

Tracks total assets, liabilities, and net worth over time from account balance snapshots.

Current net worth: ~$199,212 (as of Apr 24, 2026). Credit card balances excluded from liabilities.

Note: Net worth history before Mar 2026 is mock data approximating the real trajectory. Real tracked data starts Mar 2026.

---

## Accounts

| Account | Status | Notes |
|---------|--------|-------|
| BFSFCU Checking (4346) | Not syncing | Get real balance from BFSFCU app each session |
| Lending Club HYSA | Manual | 4.2% APY, +$500/mo. Empower value always stale. |
| Charles Schwab (Pratik Roth IRA) | Connected | Investment brokerage |
| Vanguard (Pratik Roth IRA) | Connected | Retirement |
| Vanguard (Google 401k) | Connected | Retirement |
| American Express (1006) | Connected | One account for both 1006 (Pratik) and 1022 (Nastya subcard). Use 1006 balance only. |
| Citi Costco Visa (7865) | Connected | Pratik's card |
| FSFCU Credit Card (3048) | Connected | |
| BFSFCU Car Note | Connected | Final payoff May 1, 2026. Balance ~$1,422 until then. |
| HealthEquity HSA | Delayed | Carry forward $3,314 until Pratik provides update. |
| Principal (IMF 401k) | Manual | ~$20,623 as of Mar 2026. Nastya's retirement. |
| Fidelity (Nastya Roth IRA) | Manual | ~$15,130 as of Mar 2026. |
| Anastasiia's BFSFCU (8699) | Tracked | Nastya's checking - used for Roth contribution routing |

---

## Budget Plan Data

Seeded from `seed_budget.py` for all months (Jan 2025 - Apr 2027). To update and re-seed:

```bash
python seed_budget.py
```

### Monthly Expense Breakdown (Jan-Apr 2026, ~$3,402/mo spending)

| Category | Amount | Notes |
|----------|--------|-------|
| Rent | $1,335 | Fixed, all-inclusive. State Farm insurance included in this line. |
| Groceries | $540 | Whole Foods, Trader Joe's, Costco, Target, Albertsons |
| Dining / takeout | $150 | DoorDash, Uber Eats, restaurants |
| Car insurance | $150 | Tesla, fixed |
| EV charging | $45 | Tesla Supercharger + ChargePoint |
| Internet | $60 | AT&T / Xfinity |
| Subscriptions | $35 | YT Premium + rotation |
| Healthcare | $111 | Zion Healthshare (Pratik only) |
| Pets | $200 | Food + Embrace insurance + medication |
| Personal / misc | $45 | Amazon, household, haircuts, nail, clothing |
| Fitness | $250 | Nastya aerial - quarterly (Jan/Apr/Jul/Oct only) |
| Buffer / misc | $241-$491 | Catch-all. Shrinks as rules get more specific. |

Savings (on top of spending):
- HYSA: $500/mo
- Roth IRA: $1,364-$2,250/mo (both Pratik and Nastya, target $7,000-$7,500/yr each)

### Lean Budget (May-Dec 2026, ~$2,642/mo spending)

Nastya has no income during PhD summer gap. Groceries cut to $600, dining $100, personal $50, pets $150, buffer reduced.

---

## Data Upload Cadence

| Phase | Schedule | Period |
|-------|----------|--------|
| Phase 1 | Every Friday | Mar 2026 - ~Jun 2026 |
| Phase 2 | 1st and 15th of month | ~Jul 2026 onward |

**What to collect each session:**
- Empower transactions CSV (All Transactions export - includes CC transactions from connected accounts)
- FireShot PDF of Empower net worth page (full-page screenshot)
- BFSFCU real balance (BFSFCU app)
- Any manual transactions (Apple Card, etc.)

**Source of truth for CC transactions:** Empower only. Never mix Empower exports with direct CC statement CSVs for the same card. The dedup key is `(date, account, description, amount)` - same transaction from two sources has a different account name and inserts twice.

---

## Actuals Pipeline

**How it works:**
1. Export CC statement as CSV (Amex, Citi, etc.) - or use Empower which consolidates all
2. Drop into `imports/` and run `python ingest.py`
3. Transactions stored in the `transactions` table
4. `BUDGET_CATEGORY_RULES` in `config.py` maps merchant names / CC categories to budget sub-categories
5. `/api/budget-plan` returns `actuals_by_category` derived live from transactions
6. Budget page shows Planned | Actual | Diff when month is locked and data exists

**Tuning:** Add a keyword to `BUDGET_CATEGORY_RULES` in config.py, refresh page - no re-ingest needed.

**Deduplication:** Transactions have a `UNIQUE(date, account, description, amount)` constraint. Re-uploading the same CSV skips duplicates silently.

---

## Equity Tracking

The Anthromind equity card is the template for any future equity position.

**Where, Inc.** is configured in `config.py` but commented out. To activate:
1. Uncomment `WHERE_EQUITY` in `config.py`
2. Uncomment `positions.append(config.WHERE_EQUITY)` in `equity.py`

To add a new equity position:
1. Add a new config block in `config.py` (same shape as `ANTHROMIND_EQUITY`)
2. Add a vesting schedule generator in `equity.py`
3. Add a card in `renderEquity()` in `net_worth.html`

Key fields: `total_shares`, `cost_basis`, `current_price_per_share`, `vesting_start`, `cliff_date`, `cliff_shares`, `monthly_shares`, `fully_vested_date`.

Use `/api/equity?as_of=YYYY-MM-DD` to inspect vesting state at any past or future date.

---

## TODOs

### Data Completeness
- [ ] Add Nastya's retirement accounts to Empower and export CSVs (currently using manual balances)
- [ ] Export Empower full transaction history (Personal Capital) for all spending categories
- [ ] Update LendingClub HYSA balance manually each month

### Budget
- [ ] Lock April 2026 budget
- [ ] After April closes: review actuals vs plan, adjust May sub-category amounts if needed
- [ ] Seed 2027+ months once income/expense picture for next year becomes clearer
- [ ] Update lean budget (May-Dec 2026) numbers once Nastya's PhD stipend or part-time income is known

### Net Worth
- [ ] Remove mock historical snapshots once 6+ months of real Empower data exists
- [ ] Add Nastya's accounts to Empower - net worth chart will jump when added, that's expected

### Future Features
- [ ] Spending page: add chart (currently just a table)
- [ ] Budget page: show "as of [date]" per category so you know how stale each sub-cat is
- [ ] Forecast: replace hardcoded income constants with actual average from transactions once 3+ months of data exists
- [ ] Add a "notes" tooltip on budget rows for one-time items (e.g. "taxes owed - 2 of 4")
- [ ] Retirement projector: project year-by-year to ages 55, 60, 65 with 7% return assumption
- [ ] Goals tracker: user-defined savings goals with progress bars

---

## Home Equity Tracking (Future)

When a house is purchased, activate the home equity card in `net_worth.html`:
1. Uncomment `// + renderHomeEquityCard(latestDate)` in `renderEquity()`
2. Update constants: `PURCHASE_PRICE`, `APPRAISED_VALUE`, `DOWN_PAYMENT`, `CLOSING_COSTS`, `LOAN_AMOUNT`, `ANNUAL_RATE`, `MONTHLY_PAYMENT`, `START_DATE`, `TERM_MONTHS`
3. Wire the equity value into the net worth total

Equity formula: `appraised value - remaining loan balance - closing costs`. Amortization runs entirely in JS from the start date - no DB needed.

---

## Forecasting Model (Planned)

Goal: a model that blends the budget plan with actuals over time.

```
weight = min(months_of_data / 6, 1.0)
forecast_spend[cat] = plan[cat] * (1 - weight) + actual_avg[cat] * weight
```

Activate once 3+ months of real Empower data exists (target: ~Jun 2026).

---

## File Structure

```
pratik-finances-dashboard/
  app.py               - Flask routes and API endpoints
  config.py            - Constants, API keys, account aliases, category rules
  storage.py           - SQLite CRUD (transactions, balances, net worth, budget plan)
  ingest.py            - Weekly import orchestrator
  parse_csv.py         - Empower + CC statement CSV parsing
  parse_screenshot.py  - Claude Haiku screenshot account balance extraction
  parse_pdf.py         - Budget PDF parsing
  seed_budget.py       - One-time seed of 2025-2027 budget plan
  knowledge_base.py    - YAML event sync (life events, one-offs)
  knowledge.yaml       - Life events: job dates, bonuses, big purchases, etc.
  forecast.py          - Net worth projection logic
  templates/
    base.html          - Navbar, theme toggle, shared JS utilities
    budget.html        - Monthly Budget page
    net_worth.html     - Net Worth page
  static/
    style.css          - Dark/light theme, all component styles
  data/
    finances.db        - SQLite database (gitignored)
  imports/             - Drop files here for weekly ingest
    processed/         - Auto-archived after ingest
```

---

## Lessons Learned (2026-04-24 Session)

### Amex 1006/1022 Dedup - The Core Rule
1006 (Pratik) and 1022 (Nastya) are the SAME Amex account, one balance, one statement. Empower regularly shows the same charge on BOTH cards in the CSV. Never count a 1006 transaction if the same date + amount + merchant exists on 1022. Only insert 1006 entries that have no 1022 counterpart (Pratik made a separate purchase that day).

### new BUDGET_CATEGORY_RULES Added (Apr 2026)
- `"uber"` - `expenses_dining` (Uber rides counted as dining; Uber Eats was already there)
- `"jack in the box"` - `expenses_dining`
- `"petros"` - `expenses_dining`
- `"european deli"` - `expenses_dining`
- `"disney"` - `expenses_entertainment`
- `"nail"` - `expenses_personal_misc`
- `"economist"` - `one_time_expense`
- `"target"` - `expenses_groceries`
- All nastya-specific rules (apres, aries, alpha, spanx, lingerie, marshalls, sephora) moved to `expenses_personal_misc`

### UC Pathway Fees Must Be Deleted After Every Ingest
"Uc Pathway Xx60 - Fees" and "Uc Pathway Xx60 - Realizedgainloss" (UC Defined Contribution, account 0988) appear in every Empower CSV. Delete them from `transactions` after every ingest.

### Account: Visa Signature Roth Entries Are Duplicates
Empower sometimes includes duplicate Roth contribution entries under "Account: Visa Signature". Delete any "Account: Visa Signature" entries for "Roth" or "Fidelity Investments" on the same date as a known Roth contribution.

### Credit Cards Excluded from Net Worth Liabilities
Credit card balances are NOT counted as liabilities. They are paid monthly and represent a timing artifact, not real debt. Only `account_type = "loan"` or `"mortgage"` counts toward liabilities. `recompute_net_worth()` in storage.py explicitly skips `atype == "credit"` accounts.

### One-Time Expenses Need Budget Plan Row Update
Inserting a transaction alone does NOT make it show in the one_time_expense budget row. The template reads `one_time_expense` from the `budget_plan` table. If a one-time expense occurs (conference, tax, travel), also run:
`UPDATE budget_plan SET one_time_expense=AMOUNT, notes='description' WHERE year=Y AND month=M`

### Total Outflow Diff Column Requires Two Data Points
The diff column for divider rows (like Total Outflow) requires both `actual` and `planned` to be passed to the `dividerRow()` function in budget.html. The `totalExpenseActual` calculation must include `one_time_expense` actuals:
`const totalExpenseActual = spendingActual + savingsActual + nastayGiftsActual + oneTimeActual`

### Reimbursed Expenses - Delete Gross, Let Reimbursement Stand
Pet insurance reimbursed $772.39 against a $732.46 vet visit (net +$39.93 gain). Solution: delete the vet transaction entirely. The insurance payout shows as income in the checking account. This is cleaner than complex offsetting logic.

### Car Note Payoff Timing
Do NOT zero out the BFSFCU Car Note balance based on "April 2026 payoff" language in notes. The actual final payment clears May 1, 2026. Always confirm the exact payoff date with Pratik before zeroing any loan.

### Net Worth Apr 24, 2026: $199,212
Assets: $200,634 | Liabilities: $2,578 (car note only)
- Empower shows $193,040 (stale: LendingClub $9,723 vs real $10,223; excludes HealthEquity $3,313; still shows car note -$1,422)
- Our DB is correct. Difference explained by: +$500 LendingClub, +$3,314 HealthEquity, +$1,422 car note not yet paid.

---

## Lessons Learned (2026-04-04 Session)

### BFSFCU Disconnected - All Transactions Manual
BFSFCU (Joint Checking 4346) is not syncing with Empower. All deposits must be added manually each session with `import_batch='manual-YYYY-MM-DD'`.

### Manual Entries Create Duplicates When Real Data Arrives
A transaction manually added earlier can conflict with the same transaction in a later Empower CSV (different description, same data) - bypassing the dedup key. Always check for manual batch entries before ingesting a CSV that covers the same date range. Symptoms: doubled car note, doubled rent.

### Actual Income Inflated - Filter Rules
`get_actual_income_total()` must exclude: plain transfers ("External Deposit ... Transfer"), CC refund credits from CC accounts. Correct income = paychecks + one-time events + misc reimbursements only.

### Budget Plan Extended to April 2027
Jan-Apr 2027 seeded with lean budget estimates. Roth updated to $1,364/month for all months May 2026 - Apr 2027 (new $7,500 target).

### Milestone Celebration Banners
Events with `amount=0` in knowledge.yaml show as green banners on the budget page for their month. Add a new entry each March marking Roth IRA maxed for the current tax year - contributions run May through March (12 months, $1,250/mo), fully funded by end of March. April 15 is the deadline but the plan hits the limit in March. Update dollar amounts if IRS limits change.

### Flask JSON Emoji Fix
Flask's default `JSON_AS_ASCII=True` escapes emoji as unicode surrogates. Fix: `app.config['JSON_AS_ASCII'] = False`. Milestone emoji hardcoded as `&#127881;` in the HTML template rather than stored in YAML/DB.

---

## Lessons Learned (2026-03-30 Session)

### projected_checking Was Double-Applying the Current Month
`get_projected_checking()` now reads the snapshot date from `account_balances` and only applies planned cash flow for months AFTER the snapshot date. For the current month, it returns the actual balance directly.

### expenses_nastya_gifts Missing from Net Cash (Planned Side)
`nastayGiftsPlanned` was extracted in budget.html but never added to `totalExpensePlanned`. Fixed: `+ nastayGiftsPlanned` now included in `totalExpensePlanned`.

### HealthEquity Is in Empower but Delayed
HealthEquity shows in Empower as "Delayed". Empower excludes it from the reported net worth total. We keep the manual balance in our DB - this is intentional.

### Empower PDF Net Worth May Differ from DB for Known Reasons
When the PDF total and our DB total differ, check: BFSFCU accounts (stale in Empower), HealthEquity excluded (Delayed status), car note balance not reflecting a recent payment.

---

## Lessons Learned (2026-03-22 Session)

### Citi Card Direct Import vs Empower: Persistent Duplicate Risk
The `Year to date.CSV` (direct Citi export) and the Empower transactions CSV both cover the Costco Citi card but with different account names and different description formats. Every transaction appears twice. Never import the direct Citi CSV for any date range already covered by an Empower export.

### Manual Placeholder Transactions Leak into Actuals
Manual DB inserts for placeholder/demo purposes should use a description that won't match any category rule, or be tagged with `import_batch='manual_demo'` so they're easy to find and clean up.

### Empower Net Worth PDF Requires Manual Balance Save
`parse_pdf.extract_budget()` is for the budget spreadsheet PDF only - it does not parse the Empower net worth screenshot. To update balances: read account values from the PDF manually and call `storage.save_balances()` directly.

### New Accounts Must Be Added to DB Manually on First Appearance
Any account visible in the Empower net worth PDF but missing from `account_balances` should be added with `storage.save_balances()`. Net worth will be understated until this is done.

---

## Lessons Learned (2026-03-11 Session, Part 2)

### Mock Scenarios: Clean Revert Pattern
For any "what if" simulation involving DB changes:
1. Use a unique `import_batch` tag (e.g. `temp_series_a`) on all inserted rows
2. Revert with: `DELETE FROM account_balances WHERE import_batch='temp_series_a'`
3. Delete any stale future `net_worth_snapshots` manually
4. Call `storage.recompute_net_worth()` to restore correct figures

### Direct DB Patches Always Need recompute_net_worth()
Any UPDATE or INSERT to `account_balances` must be followed by `storage.recompute_net_worth()`. Deleting from `account_balances` does NOT auto-delete stale `net_worth_snapshots` rows - those must be cleaned up manually.

### Account Type Classification Order Matters
"retirement" keywords (vanguard, ira, roth, 401k) must be checked before "investment" keywords (schwab, fidelity) in `_classify_account_type()` in parse_csv.py. Otherwise Vanguard accounts land in the wrong bucket.

---

## Lessons Learned (2026-03-11 Session, Part 1)

### Actuals Are Computed Live, Not Stored
`get_actuals_by_budget_category()` scans transactions on every API call. No separate actuals table. Fix a merchant rule in `BUDGET_CATEGORY_RULES`, refresh - actuals update instantly.

### Lock Is a Display Gate, Not a Data Lock
`budget_month_status.locked` only controls whether the Planned | Actual | Diff columns appear. It does not freeze plan numbers. If you accidentally lock a month early, delete the row: `DELETE FROM budget_month_status WHERE year=X AND month=Y`.

### Always Use Empower as the Single Source for Transactions
Never mix Empower exports with direct CC statement CSVs for the same card. Dedup key is `(date, account, description, amount)` - same transaction from two sources has a different account value and inserts twice.

### Stale net_worth_snapshots Rows Survive Deletion from account_balances
`recompute_net_worth()` only processes dates that still exist in `account_balances`. If you delete a balance row for a date, the corresponding `net_worth_snapshots` row is NOT auto-deleted. Must manually: `DELETE FROM net_worth_snapshots WHERE snapshot_date='YYYY-MM-DD'`.

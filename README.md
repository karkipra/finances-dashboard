# Nastik Finances Dashboard

> **Core requirement:** Both Pratik and Nastya must be able to open this dashboard from any device on home WiFi at any time. Always verify LAN access works after setup or changes. See [Sharing on Home Network](#sharing-on-home-network-nastyas-phone--other-devices) below.

> We are improving this over time. Every week we get new data, which means the financial projections will be tighter. The goal is a living system that gets smarter each month - eventually powering accurate 2-5 year plans.

Local Flask dashboard for Pratik + Nastya (Nastik). Tracks net worth, monthly budget planned vs actual, and long-term projections. Runs at `http://localhost:5000`.

---

## Budget Planner: Assumptions and Golden Rules

Four numbers drive the monthly budget view: **Inflow, Outflow, Invested, Net Cash.**

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
- LendingClub balance is manual - the $500/month auto-transfer is not auto-detected; add it manually each session when updating balances
- Keywords "lending club", "lendingclub" map to HYSA; "vanguard", "schwab", "roth" map to Roth

### Net Cash
- Net cash = total inflow - total outflow (spending + savings combined)
- When actuals exist (month is locked and has transactions): uses real transaction totals
- When no actuals: uses planned amounts from the budget seed
- Invested is shown separately so you can see where the cash went

### Category Matching Rules
- Keywords match transaction description first, then Empower category - first match wins
- Order in `BUDGET_CATEGORY_RULES` in `config.py` matters: more specific rules must come before generic ones
- Key ordering dependencies: "tesla insurance" before "tesla" (else all Tesla charges go to EV); "orchid eros" before generic dining rules
- Unmatched expenses fall to Buffer/Misc - if Buffer is large, tune keywords in `config.py`
- Costco and Indo China Market map to Groceries
- Hairitage salon maps to Nastya's gifts
- Rental insurance from BFSFCU checking is not in Empower - add manually when it hits

### BFSFCU - Empower Connection Broken
BFSFCU (checking account 4346) is not syncing with Empower. Until reconnected, **all BFSFCU transactions must be added manually** each session:
- Pratik's Anthromind paycheck (biweekly)
- Nastya's UCSB paycheck (monthly)
- Rent payment to UCSB
- Any direct debits or deposits through BFSFCU checking

Add manually with `import_batch='manual-YYYY-MM-DD'`. The Empower CSV will not contain these.

### What Gets Manually Added Each Session
- BFSFCU checking balance (get real balance from BFSFCU app - Empower value is stale)
- All BFSFCU transactions (see above - connection broken)
- LendingClub HYSA balance (+$500/month auto-transfer)
- HealthEquity HSA balance (in Empower but "Delayed" - connection broken)
- Any pending CC charges you know about before they settle
- Apple Card transactions not in Empower - Pratik will flag these ad hoc (e.g. parking, one-off charges). Add with `import_batch='manual-YYYY-MM-DD'`.

### Transactions to Remove After Ingest
- **UC Pathway fees/gain-loss** (e.g. "Uc Pathway Xx60 - Fees", "Uc Pathway Xx60 - Realizedgainloss"): internal Fidelity admin fees inside the UC Defined Contribution account (0988). Not charged to a card, already reflected in the account balance. Delete from `transactions` table after ingest - they only affect net worth via the balance snapshot, not budget actuals.

---

## Quick Start

```bash
cd pratik-finances-dashboard
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python seed_budget.py   # one-time: seeds 2025-2026 budget plan
python app.py           # visit http://localhost:5000 or http://192.168.1.133:5000
```

**To start the server (daily use):**
```bash
python app.py
```
Binds to `0.0.0.0` — accessible at `http://192.168.1.133:5000` from any device on home WiFi.

Requires a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Sharing on Home Network (Nastya's Phone / Other Devices)

The dashboard runs on `0.0.0.0` so any device on home WiFi can reach it.

**Nastya's URL:** `http://192.168.1.133:5000`

No setup needed on her end - just open that URL in any browser while connected to home WiFi.

**Requirements:**
- Pratik's laptop must be on and the server running (`python app.py`)
- Both devices must be on the same WiFi network
- Does not work on cellular or outside the home network

**Port:** Always 5000. Defined in `config.py` as `FLASK_PORT`.

**Windows Firewall (one-time setup, required for LAN access):**
Run this once in an elevated/admin terminal:
```
netsh advfirewall firewall add rule name="Flask 5000 - Finances Dashboard" dir=in action=allow protocol=TCP localport=5000
```
Without this, Windows blocks incoming connections even though Flask is listening.

**IP address caveat:** `192.168.1.133` is assigned by the router via DHCP and could change after a restart.
To lock it permanently: log into the router admin page (usually `192.168.1.1`), find
"DHCP Reservations" or "Static IP Assignment", and pin the laptop's MAC address to `192.168.1.133`.
One-time setup, then the URL never changes.

---

## Weekly Workflow

Each week, drop new exports into `data/` and ask Claude Code to ingest them:

**What to export from Empower each week:**
1. Transactions CSV: empower.com -> All Transactions -> Export (pick date range covering last week+)
2. Net worth PDF: take a FireShot (full-page screenshot saved as PDF) of the Empower Personal Dashboard net worth page

**Drop both files into `data/` then run ingest:**

```bash
# Claude Code handles the ingest, or run manually:
python ingest.py   # processes files from imports/ - Claude moves them there first
```

**What Claude does during ingest:**
- Copies the new CSV and PDF from `data/` to `imports/`
- Runs `python ingest.py` (imports transactions, deduplicates)
- Reads the Empower PDF screenshot visually and saves account balances to the DB
- Recomputes net worth

**Note:** BFSFCU accounts (Checking, Car Note, credit cards) show "Reconnect/Loading" in Empower and are stale. Always get the real BFSFCU Checking balance from the BFSFCU app and update manually. HealthEquity shows "Delayed" - manual balance is kept in DB as-is.

Ingest automatically:
- Imports transactions and deduplicates
- Updates account balances and recomputes net worth
- Archives processed files to `imports/processed/YYYY-MM-DD/`
- Suggests knowledge base additions (new subscriptions, one-off events)

---

## Pages

### Monthly Budget (`/budget`) — default page

Shows the planned budget for any month from Jan 2025 to Dec 2026 side by side with actuals once CC transactions are imported.

**Layout:**
- Left column: Income (post-tax) + Net (big number)
- Right column: Expenses broken into three zones:
  - **Spending** — 11 sub-categories (rent, groceries, dining, car ins, EV, internet, subs, healthcare, pets, personal, fitness + buffer)
  - **Savings** — HYSA + Roth IRA (green tinted, wealth-building)
  - **One-time** — taxes, phone plan renewal, travel, etc. (when applicable)

**Planned vs Actual:** When CC statement transactions exist for a month, the expense table automatically gains Planned | Actual | Diff columns. Green = under budget, red = over.

**Transaction drill-down:** Every category row has a `+` button on the left. Click it to expand and see every transaction that was counted toward that category (date, description, source account, amount). Click again to collapse. Cache clears automatically when navigating months.

**Key months:**
| Month | Notes |
|-------|-------|
| Jan-Apr 2026 | Both incomes, full spending, Roth maxing |
| Mar 2026 | First live month. $1,010 car loan payment. |
| Apr 2026 | $1,414 car loan final payoff. $300 taxes (1 of 4). |
| May-Jul 2026 | $285/mo taxes (2-4 of 4). Nastya income $0 (PhD gap starts). |
| May 2026 | Pratik 3-paycheck month (+$1,281 extra). |
| May-Dec 2026 | Lean $2,642 budget (Nastya no income). |
| Oct 2026 | Pratik 3-paycheck month (+$1,281 extra). |

### Net Worth (`/net-worth`)

Tracks total assets, liabilities, and net worth over time from Empower balance snapshots. Chart shows history with event annotations (job start, car payoff, etc.).

Current net worth: ~$184,298 (as of Mar 2026). Includes approximate Nastya retirement balances ($21K Principal 401k + $17K Fidelity Roth IRA).

**Note:** Net worth history before Mar 2026 is illustrative mock data approximating the real trajectory
(debt payoff grind 2021-2023, NVIDIA stock inflection Oct 2023, steady growth 2024-2025).
Real tracked data starts Mar 2026 — history will be replaced as actual Empower snapshots accumulate.

**Note:** Even Mar 2026 is incomplete — Nastya's retirement accounts are not yet in Empower.
Net worth is understated until her accounts are added.

---

## Budget Plan Data

Seeded from `seed_budget.py` for all 24 months (Jan 2025 - Dec 2026). To update and re-seed:

```bash
python seed_budget.py
```

### Monthly Expense Breakdown (Jan-Apr 2026, $3,402/mo spending)

| Category | Amount | Notes |
|---|---|---|
| Rent | $1,335 | Fixed, all-inclusive (no separate utilities) |
| Groceries | $750 | Estimate |
| Dining / takeout | $150 | Estimate |
| Car insurance | $150 | Tesla, fixed |
| EV charging | $45 | Tesla Supercharger, estimate |
| Internet | $60 | Separate from rent |
| Subscriptions | $35 | YT Premium + rotation |
| Healthcare | $111 | Pratik only (Nastya covered by UCSB) |
| Pets | $200 | Food + insurance + medication |
| Personal / misc | $75 | Amazon, household, haircuts |
| Fitness | $250 | Nastya aerial — quarterly (Jan/Apr/Jul/Oct only) |
| Buffer / misc | $241-$491 | Catch-all remainder. To be calibrated after March actuals. |

Savings (on top of spending):
- HYSA: $500/mo
- Roth IRA: $1,500-$2,250/mo (ramping to max $7,000/yr each)

### Lean Budget (May-Dec 2026, $2,642/mo spending)

Nastya has no income during PhD summer gap. Groceries cut to $600, dining $100, personal $50, pets $150, buffer ~$6.

---

## Data Upload Cadence

The system gets smarter every time you upload. More data = tighter projections.

| Phase | Schedule | Period |
|---|---|---|
| Phase 1 | Every Friday | Mar 2026 - ~Jun 2026 |
| Phase 2 | 1st and 15th of month | ~Jul 2026 onward |

**What to drop into `data/` each upload:**
- Empower transactions CSV (All Transactions export - includes CC transactions)
- FireShot PDF of Empower net worth page (full-page screenshot saved as PDF)

Then ask Claude Code to ingest, or run `python ingest.py` manually (after moving files to `imports/`).

**Source of truth for CC transactions:** Export from Empower (not directly from Amex/Chase).
Empower consolidates all accounts in one CSV, so no need for separate per-card exports.
This also avoids the risk of double-counting the same transaction from two sources.

---

## Monthly Budget Workflow

Each month follows a two-step rhythm:

**Step 1 — Lock the budget (1st of month)**
Open the Monthly Budget page, navigate to the new month. Review the seeded plan numbers.
Click "Lock [Month] Budget" to commit. This marks the plan as final and activates actuals tracking.

**Step 2 — Upload and track (weekly/biweekly)**
Drop Empower CSV into `imports/`, run `python ingest.py`. The budget page automatically shows:
- **Planned** — the locked plan amount
- **Actual so far** — sum of real transactions mapped to each sub-category
- **Diff** — green if under, red if over

Month ends → full actuals are locked in history. Start again on the 1st.

**Backdating works automatically.** If you upload on Apr 1 with remaining March transactions,
they land in the DB with their real March dates and appear in March actuals immediately.
Just make sure the Empower export covers the full date range you need (e.g. Mar 1 - Mar 31),
not just "last 30 days from today."

---

## Actuals Pipeline (Phase 5 — in progress)

**How it works:**
1. Export CC statement as CSV (Amex, Chase, etc.)
2. Drop into `imports/` and run `python ingest.py`
3. Transactions stored in the `transactions` table
4. `BUDGET_CATEGORY_RULES` in `config.py` maps merchant names/CC categories to budget sub-categories
5. `/api/budget-plan` returns `actuals_by_category` derived live from transactions
6. Budget page shows Planned | Actual so far | Diff when month is locked and data exists

**Tuning the category map:** If a merchant lands in the wrong bucket, add a keyword to
`BUDGET_CATEGORY_RULES` in `config.py` above the generic catch-all. Refresh the page —
no re-ingest needed (actuals are computed live from transactions).

**Deduplication:** Transactions have a `UNIQUE(date, account, description, amount)` constraint.
Re-uploading the same CSV skips duplicates silently — nothing double-counts. Safe to re-run
`ingest.py` any number of times with overlapping exports.

**Dedup edge cases to watch:**
- Same transaction with slightly different description text (e.g. Amex truncates merchant names
  between statement periods) — would insert as two rows. Rare but possible.
- CC transactions from Empower vs. a separate CC statement CSV for the same card — would
  duplicate because the account name differs. **Avoid this by always using Empower as the
  single source.** Never mix Empower exports with direct CC statement CSVs for the same card.

**Status: implemented (Phase 5 complete).**
- `BUDGET_CATEGORY_RULES` in `config.py` - add/tweak keywords to remap merchants
- `budget_month_status` table + `lock_month()` / `get_month_status()` in `storage.py`
- `get_actuals_by_budget_category(year, month)` in `storage.py`
- `get_transactions_by_budget_category(year, month, budget_cat)` in `storage.py` - powers the drill-down
- CC statement CSV detection + sign-flip in `parse_csv.py`
- `POST /api/lock-month` + extended `/api/budget-plan` in `app.py`
- `GET /api/budget-category-transactions` in `app.py` - returns individual transactions for a category/month
- Budget page: lock button, Planned | Actual so far | Diff columns, per-category `+` drill-down

---

## Accounts

| Account | Status | Notes |
|---|---|---|
| BFSFCU Checking (4346) | Connected | Transactions via Empower CSV |
| Lending Club HYSA | Manual | 4.2% APY, +$500/mo. Update balance monthly. |
| Charles Schwab (Pratik Roth IRA) | Connected | Retirement |
| Vanguard (Pratik Roth IRA) | Connected | Retirement |
| Vanguard (Google 401k) | Connected | Retirement |
| American Express (1006) | Partial | Balance tracked. Need CC CSV for spending actuals. |
| FSFCU Credit Card (3048) | Connected | |
| BFSFCU Car Note | Connected | $1,010/mo, paid off Apr 2026 |
| Principal (IMF 401k) | Manual | ~$21K as of Mar 2026. Approximate until Empower connected. |
| Fidelity (Nastya Roth IRA) | Manual | ~$17K as of Mar 2026. Approximate until Empower connected. |

---

## Home Equity Tracking (Future)

When we buy a house, add a home equity card to the equity section on the Net Worth page.
The logic is already built in `net_worth.html` - just activate it:

1. Uncomment `// + renderHomeEquityCard(latestDate)` in `renderEquity()`
2. Update the constants at the top of `renderHomeEquityCard()`:
   - `PURCHASE_PRICE`, `APPRAISED_VALUE`, `DOWN_PAYMENT`, `CLOSING_COSTS`
   - `LOAN_AMOUNT`, `ANNUAL_RATE`, `MONTHLY_PAYMENT`, `START_DATE`, `TERM_MONTHS`
3. When ready to include in net worth, wire the equity value into the net worth total

Equity formula: `appraised value - remaining loan balance - closing costs`
Amortization runs entirely in JS from the start date - no DB needed.

---

## Equity Tracking Pattern

The Anthromind equity card is the template for tracking any future equity position:
- Angel investments (add company, shares, entry price, current price)
- Future role equity packages (add grant, cliff, monthly schedule, strike price)

**Where, Inc.** is configured in `config.py` but commented out. To activate:
1. Uncomment `WHERE_EQUITY` in `config.py`
2. Uncomment `positions.append(config.WHERE_EQUITY)` in `equity.py`

To add a new equity position:
1. Add a new entry to `ANTHROMIND_EQUITY`-style config block in `config.py`
2. Add a vesting schedule generator in `equity.py` (same pattern)
3. Add a card in `renderEquity()` in `net_worth.html`

Key fields for any equity position:
- `total_shares` - grant size
- `cost_basis` - total paid (or $0 for RSUs/options)
- `current_price_per_share` - update manually when valuations change
- `vesting_start`, `cliff_date`, `cliff_shares`, `monthly_shares`, `fully_vested_date`

For angel investments with no vesting: set `cliff_date = purchase_date`, `cliff_shares = total_shares`, no monthly schedule.

---

## TODOs

### Data Completeness
- [ ] Add Nastya's retirement accounts to Empower and export CSVs — currently using approximate manual balances ($21K + $17K)
- [ ] Export Empower full transaction history (Personal Capital) for groceries, dining, etc. — current CSV is retirement portal only
- [ ] Update Lending Club HYSA balance manually each month (not connected to Empower)

### Actuals Calibration (after first real upload)
- [ ] **Re-enable actuals columns** — currently disabled in `budget.html` (`hasActuals = false`). Two issues to fix first:
  - Credit card payment transactions (e.g. "American Express Credit Card Payments") are double-counting real spend — need to filter out by description or category
  - Investment/brokerage transactions (securities trades, reinvestments, sweeps) from retirement accounts are leaking into spending categories — filter by account type or category keywords before re-enabling
- [ ] Review `BUDGET_CATEGORY_RULES` against real transactions — add merchant keywords as needed
- [ ] Tune `expenses_buffer_misc` — should shrink as rules get more specific
- [ ] Validate dedup: confirm no double-counting after first Empower CSV upload

### Actual Income Filtering (`get_actual_income_total` in `storage.py`)
- [ ] **Fix inflated income total** — currently overcounts by ~$1,400+/month. Actual income = paychecks + one-time income events + misc reimbursements only. Must exclude:
  - Plain transfers (description contains "transfer" — e.g. "External Deposit ... Transfer" from checking)
  - CC refund/return credits (positive transactions on CC accounts like Amex, Citi, Apple Card)
  - Do NOT add transfers or CC credits manually — they are not income

### Budget
- [ ] Lock March 2026 budget (first live month)
- [ ] After March closes: review actuals vs plan, adjust April sub-category amounts if needed
- [ ] Update Apr 2026 monthly_expenses summary row if any remaining one-time or car loan amounts change
- [ ] Seed 2027+ months once income/expense picture for next year becomes clearer
- [ ] Update lean budget (May-Dec 2026) numbers once Nastya's PhD stipend or part-time income is known

### Net Worth
- [ ] Remove mock historical snapshots once 6+ months of real Empower data exists
- [ ] Add Nastya's accounts — net worth chart will jump when added, that's expected

### Future Features (not urgent)
- [ ] Spending page: add chart (currently just a table)
- [ ] Budget page: show "as of [date]" per category so you know how stale each sub-cat is
- [ ] Forecast: replace hardcoded income constants with actual average from transactions once 3+ months of data exists
- [ ] Projected checking balance: currently uses planned amounts only — switch to blend actual + remaining planned once actuals are re-enabled
- [ ] Add fitness ($250) back to Apr/Jul/Oct 2026 quarter payments once confirmed Nastya is still doing aerial
- [ ] Consider adding a "notes" tooltip on budget rows so one-time items can show context inline (e.g. "taxes owed - 2 of 4")

---

## Planned Features

### 1. Retirement Projector
New card at the bottom of the Net Worth page.
- Takes current retirement balances + monthly Roth contributions + 7% annual return assumption
- Projects year-by-year to ages 55, 60, 65 with a line chart and milestone markers ($500K, $1M, $2M)
- Useful immediately - no transaction history needed
- Files: `config.py` (birth years), `forecast.py` (`project_retirement()`), `app.py` (`/api/retirement-projection`), `net_worth.html`

### 2. Goals Tracker
New `/goals` page, added to navbar.
- Fully flexible: user-defined goals (emergency fund, travel, kids fund, etc.)
- Each goal: emoji, name, target amount, optional target date, progress bar, months-to-completion
- Manual balance updates (you set current amount - not auto-synced to transactions)
- Pre-seeded with: Emergency Fund ($30K target)
- New DB table: `goals` (id, name, emoji, target_amount, current_amount, target_date, monthly_contribution, notes)
- Files: `storage.py`, `app.py` (CRUD routes), `templates/goals.html`, `templates/base.html` (navbar)

### 3. Spending Trends
Enhance the existing `/spending` page.
- Category-by-category: budget plan vs. last month vs. 3-month rolling average + trend arrows
- Bar chart: monthly total spend colored by over/under budget
- Auto-gated: shows "--" until 2+ months of real transaction data exists
- Files: `storage.py` (`get_spending_trends()`), `app.py`, `templates/spending.html`

**Build order:** Retirement projector → Goals tracker → Spending trends (needs data)

---

## Forecasting Model (Planned)

The goal is a model that automatically gets smarter as real transaction data accumulates.
No manual tuning needed - it blends the budget plan with actuals over time.

### Auto-Blending: Plan vs. Actuals

```
weight = min(months_of_data / 6, 1.0)
forecast_spend[cat] = plan[cat] * (1 - weight) + actual_avg[cat] * weight
```

- 0-2 months: plan-driven
- 3-5 months: blending
- 6+ months: fully actuals-driven

### What the Forecast Page Will Show

1. **Named scenario toggle** - pill buttons to switch between:
   - Base, Lean (Nastya PhD gap), Pratik Raise, Nastya Stipend, House
   - Each scenario overrides specific income/expense lines from a start month
2. **Net worth projection** - 24-month line chart with confidence bands, updates per scenario
3. **FIRE tracker** - target ($), current invested assets, months away, projected date
   - FIRE number = avg monthly spend x 12 x 25 (4% rule)
4. **Monthly cash flow** - bar chart, income vs. spend per month
5. **Account balance projections** - Checking / HYSA (4.2% APY + $500/mo) / Roth (7% return)
6. **Category spend trends** - table: plan | 3mo actual avg | trend arrow | forecast
7. **Data confidence banner** - tells you how much the model is plan- vs. actuals-weighted

### Files to Build/Modify

- `forecast.py` - add `get_category_trends()`, `blend_plan_actuals()`, `project_account_balances()`, `get_fire_number()`, `generate_forecast_v2(scenario=None)`
- `config.py` - add `FORECAST_SCENARIOS` list of override dicts
- `app.py` - add `/api/forecast/v2?scenario=` and `/api/forecast/scenarios` endpoints
- `templates/forecast.html` - overhaul with all 7 sections above

### Build Order

1. Core forecast engine + scenarios in `forecast.py` + `config.py`
2. API endpoints in `app.py`
3. Scenario pills + net worth chart + confidence banner
4. Account projections
5. FIRE tracker
6. Category trends table
7. Cash flow bar chart

Activate once 3+ months of real Empower data exists (target: ~Jun 2026).

---

## Long-Term Vision (2-5 Year Plans)

As actuals accumulate, the system will:
1. **Tighten projections** — replace estimates with real spending averages per category
2. **Model Nastya's income recovery** — PhD gap May-Dec 2026, then stipend or job
3. **Track Roth progress** — $7,000/yr each = $14,000/yr combined, compound growth
4. **Model car payoff** — $1,010/mo freed up after Apr 2026 (redirect to savings/Roth)
5. **FIRE number tracking** — at current savings rate, project time to financial independence

Each month of real data makes every future projection more accurate. The goal is that by end of 2026, the system has enough calibration data to model 2028-2030 with confidence.

---

## Lessons Learned (2026-04-04 Session)

### Weekly Ingest Workflow Updated
Files are dropped into `data/` (not `imports/`). Claude Code handles the ingest: copies the two new files (transactions CSV + Empower FireShot PDF) to `imports/`, runs `python ingest.py`, then reads the PDF visually to extract and save account balances manually. The ingest script only handles CSVs and budget PDFs - net worth screenshots require manual balance entry via `storage.save_balances()`.

### BFSFCU Disconnected - All Transactions Manual
BFSFCU (Joint Checking 4346) is not syncing with Empower. All deposits must be added manually each session:
- Pratik's Anthromind paycheck (biweekly, ~$1,281.82)
- Nastya's UCSB paycheck (monthly, ~$3,767.22)
- Rent, direct debits, any other BFSFCU activity
Use `import_batch='manual-YYYY-MM-DD'` for all manual inserts.

### UC Pathway Fees Must Be Deleted After Ingest
"Uc Pathway Xx60 - Fees" and "Uc Pathway Xx60 - Realizedgainloss" appear in the Empower CSV from the UC Defined Contribution account (0988). These are internal Fidelity admin fees - not real spending. Delete them from `transactions` after every ingest.

### Apple Card Not in Empower - Ad Hoc Manual Entry
Nastya's Apple Card is not linked in Empower. Pratik will flag individual Apple Card charges ad hoc (e.g. parking). Add with `import_batch='manual-YYYY-MM-DD'`. Do not import Apple Card CSV alongside Empower CSV for overlapping date ranges - causes duplicates since account names differ.

### Manual Entries Create Duplicates When Real Data Arrives
Pattern seen multiple times: a transaction is manually added (`manual-*` batch), then the real Empower CSV import contains the same transaction with a slightly different description, bypassing the dedup key `(date, account, description, amount)`. Always check for manual batch entries before ingesting a CSV that covers the same date range. Known duplicates fixed this session:
- Car note: manual `BFSFCU Vehicle Note To Principal` (id=695) vs Empower `Regular Payment Transfer...To Principal` (id=742) - deleted 695
- Rental insurance: manual `Rental Insurance` (id=696) vs Empower `State Farm` (id=786) - deleted 696
- Rent (UCSB): id=98 already in DB, no duplicate found

### Actual Income Inflated - `get_actual_income_total` Fix
`get_actual_income_total()` in `storage.py` was including plain transfers and CC refund credits as income. Fixed by adding two exclusion filters:
- `CC_ACCT_KEYS`: excludes positive transactions from CC accounts (Amex, Citi, Apple Card, Visa Signature) - these are refunds, not income
- `"transfer" in desc`: excludes plain transfers (e.g. "External Deposit ... Transfer")
Correct March income after fix: $6,467.86 (was $7,882.48). Real income = paychecks + one-time events + misc reimbursements only.

### Two Mystery Transfers in March (Unresolved)
id=785 ($1,000, Mar 24, "External Deposit Seef8a38cdcdaef - Transfer") and id=765 ($306, Mar 25) are in the DB but their source is unknown. Correctly excluded from income by the transfer filter. Origin not yet confirmed.

### Car Note Double-Counted in March Budget
The manually added car note entry (`BFSFCU Vehicle Note To Principal`, batch=`2026-03-30-manual`) and the real Empower entry (`Regular Payment Transfer...To Principal`, batch=`2026-04-04`) both matched the `"to principal"` budget category rule, doubling March `expenses_car_loan` to $2,020. Fixed by deleting the manual entry (id=695).

### Budget Plan Updates (April 2026)
- `expenses_groceries`: $600 -> $540
- `expenses_personal_misc`: $75 -> $45
- HYSA transaction added manually ($500, Apr 1) since BFSFCU disconnected
- Roth contribution added manually ($2,250, Apr 1) - 2025 Roth maxed for both Pratik and Nastya

### Budget Plan Extended to April 2027
- May 2026 - Apr 2027: seeded with lean budget estimates (same as Jun 2026 template)
- Roth contributions updated to $1,364/month for all months May 2026 - Apr 2027 (new $7,500 target)
- Jan-Apr 2027 were not previously seeded; added from Jun 2026 lean template

### Milestone Celebration Banners
Added per-month milestone banners to the budget page. Events with `amount=0` in knowledge.yaml show as green banners at the top of the budget page for their respective month. Emoji stored as HTML entity `&#127881;` in the template (not in YAML/DB) to avoid UTF-8/JSON encoding issues on Windows. Current milestones:
- Apr 2026: "2025 Roth IRA maxed - both Pratik & Nastya ($7,000 each, $14,000 total)"
- May 2026: "Car note paid off - $1,010/month freed up"

### Flask JSON Emoji Fix
Flask's default `JSON_AS_ASCII=True` escapes emoji as unicode surrogates, rendering as garbled text in the browser. Fix: `app.config['JSON_AS_ASCII'] = False`. Additionally, milestone emoji is now hardcoded as `&#127881;` in the HTML template rather than stored in YAML/DB, removing the encoding dependency entirely.

### Planned Cashflow Sliver
Added a thin bar between the KPI cards and the Income section showing planned inflow minus total outflow. Uses rounded `fmt()` (not `fmtExact`) to keep numbers short. `white-space:nowrap` keeps it on one line. Grid position: `budget-cashflow { grid-column:1; grid-row:2 }`.

### Budget Grid Equal-Height Columns
`align-self: stretch` on `.budget-income` and `.budget-expenses` ensures the two columns always match height. KPIs, cashflow sliver, and lock card use `align-self: start` to keep their natural height.

---

## Lessons Learned (2026-03-30 Session)

### projected_checking Was Double-Applying the Current Month
`get_projected_checking()` used a hardcoded base of March 2026 and summed planned cash flow from that month forward, including March itself. But once actual data is loaded, the actual checking balance already reflects March's activity - applying March's plan on top double-counted it.
Fix: function now reads the snapshot date from `account_balances`, and only applies planned cash flow for months AFTER the snapshot. For the current month, it returns the actual balance directly.

### expenses_nastya_gifts Missing from Net Cash (Planned Side)
`nastayGiftsPlanned` was extracted in `budget.html` but never added to `totalExpensePlanned`. Actuals correctly included it, planned did not. Net cash was overstated by $520.
Fix: added `+ nastayGiftsPlanned` to `totalExpensePlanned`.

### BFSFCU Is Disconnected from Empower
BFSFCU (checking, car note, credit cards) is not syncing with Empower. Balances in any Empower PDF screenshot will be stale (last synced 3/22/2026). Do not trust BFSFCU values from the PDF - get real balances directly from the BFSFCU app or statements before updating `account_balances`.

### HealthEquity Is in Empower but Delayed
HealthEquity shows in Empower with a broken connection ("Delayed"). Empower excludes it from the reported net worth total. We keep the manual balance ($3,313.60) in our DB - this is intentional and does not need to be a live connection.

### Empower PDF Net Worth May Differ from DB for Known Reasons
When the PDF total and our DB total differ, the usual suspects are:
- BFSFCU accounts showing stale Empower balances (disconnected)
- HealthEquity excluded from Empower total (Delayed status)
- Car note balance in Empower not yet reflecting a recent payment
Reconcile by adjusting DB values to match known real balances, not blindly matching the PDF total.

### LendingClub HYSA Needs +$500 Added Manually Each Month
LendingClub is a "Manual Bank" in Empower and does not auto-sync. The $500/month automated transfer is not reflected automatically. Each time balances are updated, check if the LendingClub balance needs +$500 added for the month's transfer.

### Pending CC Charges Can Be Manually Inserted
Charges that are pending (not yet settled/posted in Empower) will be missing from the CSV export. They can be inserted manually with `import_batch='manual-YYYY-MM-DD'` so they're easy to find. They will appear in actuals immediately since actuals are computed live from the transactions table.

---

## Lessons Learned (2026-03-22 Session)

### Citi Card Direct Import vs Empower: Persistent Duplicate Risk
The `Year to date.CSV` (direct Citi export) and the Empower transactions CSV both cover the Costco Citi card, but with different account names and different merchant description formats:
- Direct Citi: account = `"Costco Citi"`, description = `"CHARGEPOINT 8887584389 408-8414500 CA"`
- Empower: account = `"Costco Anywhere Visa Card By Citi - Ending in 7865"`, description = `"Chargepoint"`

Because the dedup key is `(date, account, description, amount)` and both the account and description differ, every transaction appears twice. Affects EV charging, entertainment (SBCC), groceries, and any other Citi card spend.

**Rule: Never import the direct Citi `Year to date.CSV` for any date range already covered by an Empower export. The `Year to date.CSV` is only useful for Jan-Feb 2026 data not yet in Empower.**

Fix applied 2026-03-22:
- `DELETE FROM transactions WHERE description='COSTCO WHSE #0474 GOLETA CA' AND account='Costco Citi'` (9 rows - Costco store purchases)
- `DELETE FROM transactions WHERE account='Costco Citi' AND date >= '2026-03-01'` (6 rows - all March Citi dupes)
- Jan-Feb `Costco Citi` rows kept - those dates are not covered by any Empower export yet.

Going forward: once Empower exports consistently include the Citi card (as seen in the 2026-03-22 export), use Empower only. Verify with: `SELECT account, MIN(date), MAX(date), COUNT(*) FROM transactions WHERE LOWER(account) LIKE '%citi%' GROUP BY account`.

### Manual Placeholder Transactions Leak into Actuals
"Nastya Gift (manual)" was a manually-inserted row from a prior session. It matched the `"nastya gift"` rule in `BUDGET_CATEGORY_RULES` and appeared in actuals as $520. It had no backing real transaction.
Fix: `DELETE FROM transactions WHERE description='Nastya Gift (manual)'`.
Lesson: manual DB inserts for placeholder/demo purposes should use a description that won't match any category rule, or be tagged with `import_batch='manual_demo'` so they're easy to find and clean up.

### Empower Net Worth PDF Requires Manual Balance Save
The ingest pipeline's `parse_pdf.extract_budget()` is for the budget spreadsheet PDF only - it does not parse the Empower net worth screenshot PDF.
To update balances from an Empower net worth screenshot: read the account values from the PDF manually and call `storage.save_balances()` directly with the correct account names and `snapshot_date`.
The account names must match what's already in `account_balances` table exactly (e.g. "BFSFCU Checking", "Vanguard (Google 401k)") or a new account row is created.

### New Accounts Must Be Added to DB Manually on First Appearance
The Citibank Costco Visa (7865) had transaction history in Empower but no balance row in `account_balances`. Net worth was understated by ~$1,010 until a balance row was added.
Any account visible in the Empower net worth PDF but missing from `account_balances` should be added with `storage.save_balances()`.

### Apple Card Is Not in Empower - Safe to Import Separately
Nastya's Apple Card transactions are not linked in Empower, so importing the Apple Card CSV alongside the Empower transactions CSV does not cause double-counting. The dedup key protects against re-importing the same Apple Card CSV twice.

---

## Lessons Learned (2026-03-11 Session, Part 2)

### Equity Card Date Must Match Chart Date
The equity card uses `date.today()` by default, so during a mock future scenario the vested share
count stays stuck at today. Fix: pass `?as_of=YYYY-MM-DD` to `/api/equity`. The frontend reads
the latest snapshot date from `/api/net-worth` and passes it through, so equity always reflects
the same point in time as the chart.

### Mock Scenarios: Clean Revert Pattern
For any "what if" simulation involving DB changes:
1. Use a unique `import_batch` tag (e.g. `temp_series_a`) on all inserted rows
2. Revert with: `DELETE FROM account_balances WHERE import_batch='temp_series_a'`
3. Delete any stale future `net_worth_snapshots` manually: `DELETE FROM net_worth_snapshots WHERE snapshot_date >= 'YYYY-MM-DD'`
4. Call `storage.recompute_net_worth()` to restore correct figures
5. Revert config changes (price per share, etc.) in `config.py`

### Series A Scenario Numbers (Jun 2027, $5.40/share)
For reference if this comes up again:
- Vested by Jun 1 2027: 2,669,885 shares (70.8% of 3,769,250)
- Value at $5.40: $14,417,379
- Net worth with equity: ~$14,637,676

### Equity Dashboard: `as_of` API Pattern
`/api/equity?as_of=2027-06-01` lets you inspect the vesting state at any past or future date
without touching the DB. Useful for scenario planning, investor conversations, tax planning.

### Account Type Classification Order Matters
`_classify_account_type()` in `parse_csv.py` checks keyword lists in order. "retirement" keywords
(vanguard, ira, roth, 401k) must be checked before "investment" keywords (schwab, fidelity)
or Vanguard accounts land in the wrong bucket. Schwab is investment (brokerage), not retirement.

### Direct DB Patches Always Need recompute_net_worth()
Any UPDATE or INSERT to `account_balances` must be followed by `storage.recompute_net_worth()`.
Also: deleting from `account_balances` does NOT auto-delete stale `net_worth_snapshots` rows —
those must be cleaned up manually.

---

## Lessons Learned (2026-03-11 Session, Part 1)

### Actuals Are Computed Live, Not Stored
`get_actuals_by_budget_category()` scans transactions on every API call. No separate actuals table.
Benefit: fix a misrouted merchant in `BUDGET_CATEGORY_RULES`, refresh — actuals update instantly with no re-ingest.

### Lock Is a Display Gate, Not a Data Lock
`budget_month_status.locked` only controls whether the Planned | Actual | Diff columns appear.
It does not freeze plan numbers or block re-seeding. If you accidentally lock a month early,
delete the row: `DELETE FROM budget_month_status WHERE year=X AND month=Y`.

### Always Use Empower as the Single Source for Transactions
Never mix Empower exports with direct CC statement CSVs for the same card. The dedup key is
`(date, account, description, amount)` — same transaction from two sources has a different
`account` value and inserts twice. Empower consolidates all accounts, use that only.

### DB Patches Need `recompute_net_worth()` After
Any direct UPDATE or INSERT into `account_balances` must be followed by `storage.recompute_net_worth()`
or the `net_worth_snapshots` table stays stale. The net worth page reads from `net_worth_snapshots`, not
`account_balances` directly.

### Stale `net_worth_snapshots` Rows Survive Deletion from `account_balances`
`recompute_net_worth()` only processes dates that still exist in `account_balances`. If you delete
a balance row for a date, the corresponding `net_worth_snapshots` row is NOT auto-deleted.
Must manually: `DELETE FROM net_worth_snapshots WHERE snapshot_date='YYYY-MM-DD'`.

### Chart.js Y-Axis Floating
Set `min`/`max` explicitly on the y-axis using the data range + 15% padding, rounded to nearest $5K.
Do not rely on `beginAtZero` default (it anchors to 0, making small ranges look flat).

### Event Annotations Clutter Charts
Filtering annotations by `event_type` is not enough — recurring small events (fitness quarterly,
subscriptions) are noise on a net worth chart. Filter by `abs(amount) >= 1000` OR specific major
types only (`milestone`, `windfall`, `debt`). When in doubt, show fewer annotations.

### Mock Historical Data Strategy
Insert directly into `net_worth_snapshots` (not `account_balances`) for historical mock data.
`recompute_net_worth()` will not overwrite these since it only processes dates present in
`account_balances`. Safe to coexist with real data. Tag with a known `import_batch` value
(e.g. `temp_demo`) so they can be bulk-deleted later.

---

## File Structure

```
pratik-finances-dashboard/
  app.py               - Flask routes and API endpoints
  config.py            - Constants, API keys, account aliases, category rules
  storage.py           - SQLite CRUD (transactions, balances, net worth, budget plan)
  ingest.py            - Weekly import orchestrator
  parse_csv.py         - Empower + CC statement CSV parsing
  parse_screenshot.py  - Claude Haiku screenshot → account balance extraction
  parse_pdf.py         - Budget PDF parsing
  seed_budget.py       - One-time seed of 2025-2026 budget plan
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

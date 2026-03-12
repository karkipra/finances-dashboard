# Nastik Finances Dashboard

> We are improving this over time. Every week we get new data, which means the financial projections will be tighter. The goal is a living system that gets smarter each month — eventually powering accurate 2-5 year plans.

Local Flask dashboard for Pratik + Nastya (Nastik). Tracks net worth, monthly budget planned vs actual, and long-term projections. Runs at `http://localhost:5000`.

---

## Quick Start

```bash
cd pratik-finances-dashboard
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python seed_budget.py   # one-time: seeds 2025-2026 budget plan
python app.py           # visit http://localhost:5000
```

Requires a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Sharing on Home Network (Nastya's Phone / Other Devices)

The dashboard runs on `0.0.0.0` so any device on your home WiFi can access it.

**Nastya's URL:** `http://192.168.1.133:5000`

No setup needed on her end - just open that URL in any browser while connected to home WiFi.

**Requirements:**
- Your laptop must be on and the server running (`python app.py`)
- Both devices must be on the same WiFi network
- Does not work on cellular or outside the home network

**Port:** Always 5000. Defined in `config.py` as `FLASK_PORT`.

**IP address caveat:** `192.168.1.133` is assigned by your router via DHCP and could change
(e.g. after a router restart or if you connect from a different network first).
To lock it permanently: log into your router admin page (usually `192.168.1.1`), find
"DHCP Reservations" or "Static IP Assignment", and pin your laptop's MAC address to `192.168.1.133`.
One-time setup, then the URL never changes.

---

## Weekly Workflow

Each week, drop new exports into `imports/` and run ingest:

```bash
# 1. Drop files into imports/:
#    - Empower transactions CSV (from empower.com → All Transactions → Export)
#    - Empower balances CSV (from empower.com → Net Worth → Export)
#    - Amex / Chase CC statement CSVs (for spending actuals)
#    - Screenshots of accounts not in Empower (e.g. Lending Club HYSA)

# 2. Run ingest
python ingest.py

# 3. Open dashboard
python app.py
```

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

**What to drop into `imports/` each upload:**
- Empower transactions CSV (All Transactions export — includes CC transactions)
- Empower balances CSV (Net Worth export)
- Screenshots of accounts not in Empower (e.g. Lending Club HYSA balance)

Then: `python ingest.py`

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
- CC statement CSV detection + sign-flip in `parse_csv.py`
- `POST /api/lock-month` + extended `/api/budget-plan` in `app.py`
- Budget page: lock button, Planned | Actual so far | Diff columns (appears when locked + data exists)

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

## Long-Term Vision (2-5 Year Plans)

As actuals accumulate, the system will:
1. **Tighten projections** — replace estimates with real spending averages per category
2. **Model Nastya's income recovery** — PhD gap May-Dec 2026, then stipend or job
3. **Track Roth progress** — $7,000/yr each = $14,000/yr combined, compound growth
4. **Model car payoff** — $1,010/mo freed up after Apr 2026 (redirect to savings/Roth)
5. **FIRE number tracking** — at current savings rate, project time to financial independence

Each month of real data makes every future projection more accurate. The goal is that by end of 2026, the system has enough calibration data to model 2028-2030 with confidence.

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

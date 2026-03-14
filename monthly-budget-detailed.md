# Pratik + Nastya Monthly Budget - Detailed Reference

Last updated: 2026-03-14 (session 3). Use this file to orient any new session quickly.
GitHub: `karkipra/nastik-finances-dashboard` (karkipra account, not pratik-anthromind).

---

## Income

| Source | Monthly Net | Notes |
|--------|------------|-------|
| Pratik - Anthromind (W-2) | $2,552 | Standard months. $2,562 after a small raise baked into Mar 2026 forward. 3-paycheck months (extra Friday): $3,843 - happens in May and Oct 2026. |
| Nastya - University of California | $3,767.22 | Updated Mar 2026. Paycheck always arrives on the **1st of the month**. Aug/Sep 2026 are $0 - summer gap (academic year contract). |
| Combined standard | ~$6,152 | Pratik $2,552 + Nastya $3,600 |
| Combined Mar 2026+ | ~$6,329 | Pratik $2,562 + Nastya $3,767 |

**Feb 2026 actual income: $6,244.68** (slightly over plan - timing of deposits).
**Mar 2026 actual income: ~$5,049** ($3,767.22 Nastya + $1,281.82 Pratik). Nastya's Mar check was missing from Empower CSV - inserted manually.

**Empower CSV gap:** Nastya's paycheck may not appear in Empower exports if it hits on the 1st and the export window doesn't capture it cleanly. Always verify March 1 deposit is present after each import; insert manually if missing.

Income filter note: the dashboard only counts real deposits. Filtered out: CC autopay credits, investment/retirement account transactions, and raw transfers (HYSA/Roth sweeps).

---

## Monthly Recurring Expenses

### Rent: $1,346.54/month
- UCSB-affiliated housing (UC Santa Barbara)
- Also includes State Farm renters insurance (~$11.54/month, rolls into same budget line)
- Feb 2026 rent was entered manually as $1,335 (old rate, pre-update) - the actual charge was $1,335 that month
- Keywords that route to rent: `uc santa barbara`, `state farm`, `rent`, `apartment`

### Groceries: $600/month
- Stores: Whole Foods, Trader Joe's, Costco, Safeway, Albertsons, Vons, Olive Hill, Indo China
- Budget lowered from $750 to $600 based on real Feb data ($509 actual)
- Costco routes here (not to car/dining) because the Costco Citi card is mainly grocery runs

### Dining: $150/month
- Feb actual: $278.93 (over budget)
- Includes: DoorDash, Uber Eats, LS Drift, Oat Bakery, Kin Bake, Renauds Patisserie, TST* merchants, Home Plate Grill, Caje Paseo
- Hilton Garden Inn ($80 in Feb) - categorized as dining because it was a restaurant visit, not a room charge
- `TST*` prefix = Toast point-of-sale system used by local Santa Barbara restaurants
- Dining budget stays $150 for Jan-Apr, drops to $100 May+ (behavior change assumption)

### Healthcare: $164/month (flat, all of 2026)
- Feb actual: $231.85 (slightly over plan but close)
- Components:
  - Zion Healthshare: ~$65 every 3 months (Pratik's health sharing plan). Smoothed to ~$22/month
  - Musely (Nastya): ~$94 every 3 months. Smoothed to ~$31/month
  - Embrace Pet Insurance: monthly, routes to pets not healthcare
  - Cottage Health one-time bill: was in Feb, do not expect to recur
  - $164/month flat all year (Jan-Dec 2026). Breakdown: Zion Healthshare $114/month (Pratik's insurance, monthly recurring) + Musely $94 every 3 months (~$31/month amortized) + ~$19 buffer for pharmacy. Feb Cottage Health was a one-time anomaly.
- Keywords: `zion healthshare`, `dental insurance`, `musely`, `kaiser`, `pharmacy`, `medical`

### Fitness: $150/month (flat, all months)
- Katelyn Carano = aerial silks instructor (Nastya). $110/session currently.
- Gym membership: ~$5/month billed annually upfront. Amortized into the $150.
- Do not expect exact $150 every month - aerial is session-based. Average out quarterly.
- Feb actual: $110 (one aerial session). Mar actual so far: $110.
- Keywords: `katelyn carano`, `aerial`, `gym`

### Pets: $200/month (Jan-Apr), $150/month (May+)
- Feb actual: $304.11 (over - likely vet visit or large supply run)
- Includes: cat food from Catandbirds.com, Chewy auto-orders, Embrace Pet Insurance, vet visits
- `Www.catandbirds.com` - this is an online pet store, NOT a restaurant. The Empower category labels it "Restaurants" which is wrong. The keyword `catandbirds` in the description catches it correctly as pets before the category check fires.
- Keywords: `catandbirds`, `cat and bird`, `chewy`, `embrace pet`, `petco`, `petsmart`, `banfield`, `vet`

### Car Insurance (Tesla): $150/month
- Tesla Insurance only (not the car loan). Separate from EV charging.
- Keyword `tesla insurance` must appear BEFORE plain `tesla` in BUDGET_CATEGORY_RULES - order matters.
- Feb actual: $149.44 (on target)

### EV Charging: $45/month
- Tesla Supercharger + ChargePoint
- Feb actual: $162.10 (way over - possibly a road trip or heavy charging month)
- Plain `tesla` keyword routes here (catches anything Tesla-branded that isn't insurance)
- Keywords: `tesla supercharger`, `chargepoint`, `charging`, `tesla`

### Internet: $60/month
- AT&T home internet
- Keyword warning: `internet` was intentionally REMOVED from BUDGET_CATEGORY_RULES. The generic word "internet" appears in bank wire transfer descriptions ("Withdrawal Internet Xfr") and caused a $1,125 false match in March. Only specific ISP names are keyed: `at&t`, `xfinity`, `comcast`.
- Feb actual: $60.65 (on target)

### Subscriptions: $35/month
- YouTube Premium, Spotify, Netflix, PlayStation, Overleaf, HBO Max
- Feb actual: $62.95 (over - check for annual renewals)
- Keywords: `youtube`, `spotify`, `netflix`, `playstation`, `overleaf`, `hbomax`, `hbo max`

### Entertainment: $100/month
- Movie theaters, plays, live performances
- Venues: Metropolitan Theatres, Garvin Theatre, UCSB Associated Students events, SBIFF
- `UCSB Assoc` routes here (UCSB student events/tickets, not groceries or campus admin)
- Feb actual: $52.50 (under budget - good)
- Keywords: `metropolitan theatres`, `garvin theatre`, `ucsb assoc`, `sbiff`, `theatre`, `theater`, `cinema`

### Personal/Misc: $75/month (Jan-Apr), $50/month (May+)
- Amazon, Target, haircuts, salons
- Feb actual: $60.76. Note: Le Petit Lingerie ($110.75) was in this bucket initially but was reclassified as nastya_gifts
- Keywords: `amazon`, `target`, `haircut`, `salon`

### Buffer/Misc: $100/month
- Catch-all for unmatched expenses
- Feb actual: $61.64. Mar actual so far: $126.86 (UHaul, parking, FedEx, Poshmark, etc.)
- Unclassified items that do NOT match any keyword and are NOT in the Transfers category route here automatically

---

## Savings (Routed as Outflows in Budget)

### HYSA (Lending Club): $500/month
- $500 monthly contribution out of checking
- Balance as of Mar 2026: $9,723.51 (was $9,273.51 before recent contribution)
- APY: 4.2%
- Not connected to Empower - balance updated manually each month
- Keywords that route to hysa: `hysa`, `high yield`, `lendingclub`, `lending club`

### Roth IRA Contributions
- Jan-Feb: $1,500/month (Pratik only, via Schwab)
- Mar-Apr: $2,250/month (maxing out - Pratik + Nastya catch-up)
- May+: $1,364/month (back to regular cadence after annual max hit)
- Keywords: `roth`, `vanguard`, `schwab`

---

## Car Loan (Tesla)

- BFSFCU (Fund Staff Federal Credit Union) car loan
- $1,010/month payment (principal + interest combined)
- Started in budget: Feb 2026
- Payoff: April 2026 (final full payment). May 2026 has a ~$404 payoff balance.
- After May 2026: no more car loan line.
- Routing nuance: the loan payment hits TWO transactions in the CSV:
  1. BFSFCU Vehicle account: "Service Charges/Fees" at -$1,010.16 - matches keyword `to principal` -> `expenses_car_loan`
  2. BFSFCU Checking account: "Transfers" category at -$1,010.16 - falls into Transfers category skip (no keyword match on "transfers" = skipped). This prevents double-counting.

---

## One-Time Items by Month

| Month | Item | Amount | Notes |
|-------|------|--------|-------|
| Feb 2026 | Nastya's gift | $453.22 | Lingerie, personal shopping. Manually reclassified. |
| Feb 2026 | Cottage Health | ~$40 | One-time medical bill. Do not expect to recur. |
| Mar 2026 | Nastya's gift | $520.00 | Manually inserted transaction (description: "Nastya Gift (manual)"). |
| May 2026 | Taxes owed | $1,140.00 | Tax payment planned. |
| May 2026 | Tesla loan payoff | $404.00 | Final balance. |
| Oct 2026 | Mint Mobile | $400.00 | Annual phone plan payment. |
| Nov 2026 | Car registration | $500.00 | Annual DMV renewal. |

---

## Accounts and Balances (as of Mar 11, 2026)

### Liquid / Checking
| Account | Balance | Notes |
|---------|---------|-------|
| BFSFCU Checking | $3,251.56 | Primary checking. Empower alias: "Cash". |
| Lending Club HYSA | $9,723.51 | High-yield savings. 4.2% APY. Manual balance update monthly. Empower alias: "Manual Bank". |

### Credit Cards (Liabilities)
| Account | Balance | Notes |
|---------|---------|-------|
| American Express (1006) | -$972.64 | Balance tracked. Transaction CSV not yet imported (Empower is source of truth going forward). |
| FSFCU Credit Card (3048) | -$130.00 | Low utilization. |

### Car Loan (Liability)
| Account | Balance | Notes |
|---------|---------|-------|
| BFSFCU Car Note | -$2,423.93 | ~2.5 payments left. Paid off Apr 2026. Empower alias: "Fund Staff Federal Credit Union". |

### Investments
| Account | Balance | Notes |
|---------|---------|-------|
| Charles Schwab (Pratik Roth IRA) | $42,574.11 | Main Roth account. This is where new contributions go. |
| Pratik Roth IRA (Vanguard) | $13,699.62 | Old Vanguard Roth - not actively contributing, just growing. |
| Vanguard (Google 401k) | $80,575.63 | Google 401k (prior employer). Not actively contributing. |

### Retirement (Nastya)
| Account | Balance | Notes |
|---------|---------|-------|
| Fidelity (Nastya Roth IRA) | $15,653.37 | Real number as of Mar 2026 from Empower screenshot. Was $17K estimated. |
| Fidelity UC Defined Contribution (Nastya) | $534.75 | Nastya's UC employer retirement plan. Small balance, just started. |
| Principal (IMF 401k) | $21,218.04 | Real number as of Mar 2026 from Empower screenshot. Was $21K estimated. |
| Pratik HealthEquity (HSA) | $3,313.60 | Pratik's HSA. Grows tax-free. |

**Net worth as of Mar 11, 2026: ~$184,298** (approximate - computed from above balances).

---

## Data Sources and Import Status

| Source | Status | Notes |
|--------|--------|-------|
| Empower transactions CSV | Connected | Primary source for all bank + CC transactions. Covers Dec 15 2025 - Mar 14 2026. |
| Costco Citi card CSV | Imported | Year-to-date 2026. Citi format: Debit/Credit columns. Detected as `citi_transactions`. |
| Apple Card CSV | Imported | Jan-Mar 2026. Detected as `apple_transactions`. Payment rows skipped. |
| Empower balance snapshot | Manual | Balance PDF exported Mar 11, 2026. Loaded into `account_balances` table. |
| Lending Club HYSA balance | Manual | Updated in DB each month. Not connected to Empower. |
| Nastya Fidelity Roth IRA | Manual | Real balance from Empower screenshot Mar 2026. |
| Principal IMF 401k | Manual | Real balance from Empower screenshot Mar 2026. |
| Full Empower Personal Capital transactions | TODO | Current CSV is from retirement portal only. Need full export for complete spending breakdown. |

**Critical rule:** Empower is the only source for BFSFCU Checking and American Express transactions. Do NOT import Chase/Amex direct CC statement CSVs for cards already covered by Empower - the account name differs and dedup breaks, causing duplicates. Dedup key is `(date, account, description, amount)`.

---

## Transaction Routing Nuances

### CC Payment Double-Count Prevention
When Pratik pays his Amex bill from BFSFCU Checking, two transactions appear:
1. Amex account: original purchase (negative, already counted as spending)
2. BFSFCU Checking: "Credit Card Payments" category (positive payment - filtered out of income)

The `SKIP_CATS` set in `get_actuals_by_budget_category` blocks category = "credit card payments" from being counted in expenses.

### Investment Account Filtering
Roth IRA and 401k accounts generate transactions in Empower (dividend reinvestments, sweeps, etc.). These are NOT spending. `INVEST_ACCT_KEYS` filters any transaction where the account name contains: `roth ira`, `brokerage`, `401(k)`, `401k`, `designated beneficiary`, `equity awards`, `google llc 401`.

### Transfers Category Rule
Generic "transfers" (e.g., internal bank sweeps) are skipped UNLESS a keyword match fired first. This means:
- HYSA transfer: description contains "lending club" -> matches `hysa` keyword -> counted as HYSA savings outflow
- Roth transfer: description contains "schwab" or "vanguard" -> counted as Roth savings outflow
- Random sweep with no keyword match + category = Transfers -> skipped entirely (not double-counted)

### Keyword Order Matters
`BUDGET_CATEGORY_RULES` is checked in insertion order. Key orderings:
- `tesla insurance` must come before `tesla` (otherwise car insurance hits EV charging)
- Description is checked first across all keywords, THEN category is checked across all keywords
- This means catandbirds.com (description) -> pets, even though Empower labels it category "Restaurants"

### Merchants That Were Manually Excluded
- Noodle City: reimbursed by friend, deleted from DB entirely
- Poshmark: selling platform (income, not expense), ignore
- UHaul: one-time buffer, falls to buffer_misc
- FedEx: one-time, falls to buffer_misc
- UCSB Parking: personal misc / buffer

---

## Monthly Budget Plan - Summary View 2026

| Category | Jan | Feb | Mar | Apr | May | Jun-Dec |
|----------|-----|-----|-----|-----|-----|---------|
| Pratik income | 2,552 | 2,552 | 2,562 | 2,562 | 3,843 | 2,562 (Oct: 3,843) |
| Nastya income | 3,600 | 3,600 | 3,767 | 3,767 | 3,767 | 3,767 (Aug/Sep: 0) |
| Rent | -1,347 | -1,347 | -1,347 | -1,347 | -1,347 | -1,347 |
| Groceries | -600 | -600 | -600 | -600 | -600 | -600 |
| Dining | -150 | -150 | -150 | -150 | -100 | -100 |
| Healthcare | -164 | -164 | -164 | -164 | -164 | -164 |
| Pets | -200 | -200 | -200 | -200 | -150 | -150 |
| Fitness | -150 | -150 | -150 | -150 | -150 | -150 |
| Car insurance | -150 | -150 | -150 | -150 | -150 | -150 |
| EV charging | -45 | -45 | -45 | -45 | -45 | -45 |
| Internet | -60 | -60 | -60 | -60 | -60 | -60 |
| Subscriptions | -35 | -35 | -35 | -35 | -35 | -35 |
| Entertainment | -100 | -100 | -100 | -100 | -100 | -100 |
| Personal misc | -75 | -75 | -75 | -75 | -50 | -50 |
| Buffer/misc | -100 | -100 | -100 | -100 | -100 | -100 |
| Car loan | 0 | -1,010 | -1,010 | -1,010 | -404 | 0 |
| HYSA | -500 | -500 | -500 | -500 | -500 | -500 |
| Roth | -1,500 | -1,500 | -2,250 | -2,250 | -1,364 | -1,364 |
| One-time expense | 0 | 0 | 0 | 0 | -1,140 (taxes) | Oct: -400, Nov: -500 |

---

## Equity (Not in Budget Cash Flow)

### Anthromind (Pratik, CS-2 grant, 40% stake)
- Total shares: 3,769,250
- Vesting start: Jul 29, 2024. Cliff: Jul 29, 2025 (942,312 shares vested).
- Monthly vesting: 78,526 shares/month after cliff.
- Fully vested: Jul 29, 2028.
- Current price per share: $0.00 (unpriced round). Update when Series A closes.
- QSBS eligible: Jul 29, 2029 (5-year holding from purchase).
- Cost basis: $37.69 total.

### Where, Inc. (Pratik, co-founder, 33% of 10M share pool)
- Configured in config.py but commented out - activate when ready.
- Immediately vested as of Mar 11, 2026.

---

## Annual Reminders

### Every April - Max Roth IRA for Prior Year
- IRS deadline to contribute to prior year's Roth IRA is Tax Day (~April 15)
- Max out both Pratik (Schwab) and Nastya (Fidelity) Roth IRAs for the prior year before the deadline
- 2026 limit: $7,000/person ($14,000 combined)
- Budget note "🎉 max Roth for prior year!" is pre-loaded in April of every year in the dashboard
- March-April budget shows higher Roth contributions ($2,250/month) to reflect this catch-up

### Every October - Mint Mobile Annual Renewal
- $400 one-time expense for phone plan. Pre-loaded in budget plan.

### Every November - Car Registration
- ~$500 DMV renewal. Pre-loaded in budget plan.

---

## Session 3 Learnings (2026-03-14)

### Net Worth Updates from Empower PDF
Full Empower dashboard PDF had several accounts missing from DB or with stale balances:
- Charles Schwab: corrected to $41,649.34
- Vanguard Google 401k: corrected to $78,627.76
- Vanguard Pratik Roth: corrected to $13,522.82
- American Express: corrected to -$1,014.72
- Added: Fidelity UC Defined Contribution (Nastya) $534.75 - her UC employer plan
- Added: Pratik HealthEquity (HSA) $3,313.60
- Removed: Fidelity Traditional IRA ($7.58 rounding artifact)
- Excluded: Citibank Costco Visa and FSFCU Visa Signature (CC liabilities not tracked individually)
- Net worth as of Mar 14, 2026: **$183,926.10**

### Always Cross-Check Empower PDF Against DB After Each Import
The PDF is the source of truth. After importing a new CSV, open the Empower dashboard PDF and verify:
1. All investment/retirement account balances match
2. No accounts are missing
3. Credit card balances match (Amex, FSFCU)

### Empower PDF Reading
Use the Read tool directly on the PDF - it can render it visually without needing pdfplumber or PyPDF2.

### Notes Feature
- Click `+` icon on any row to add a note (plan or actuals months)
- Notes show in italic below the row, and 🎉 icon replaces `+` when note exists
- Notes on `roth` or `hysa` category also surface in the "Invested" KPI card at the top
- Stored in `budget_actuals_notes` table: (year, month, category, note)
- Deleting note text and saving removes it from DB

### Progress Bar
- Now shows for all months with a plan (not just months with actuals)
- Future months: shows full planned amount, "No actuals yet" label
- Current month: shows "so far" with % of budget used
- Past months: shows "actual" with over/under flags

### Healthcare is $164 Flat All Year
- Zion Healthshare is $114/month recurring (Pratik's insurance). Not quarterly - every month.
- Cottage Health in Feb was a one-time bill, not recurring

---

## Transaction Classification Notes

### Tesla $65-107 monthly charge (Amex 1006, category: Automotive)
- Appears as description `Tesla`, category `Automotive` - this is Tesla Insurance autopay
- Routes to `expenses_ev_charging` via the plain `tesla` keyword (correct enough for now)
- Feb charge was $106.67 (possibly included a catch-up), Mar was $65.00 regular rate
- Mar $65 Tesla on Amex was confirmed as a wheel rotation service, not insurance
- Do not add an `automotive` category rule - it would over-catch unrelated charges

### EV Charging actual vs budget
- Budget: $45/month. Real charging (ChargePoint + Supercharger) runs ~$40-55/month
- Tesla Insurance ($65-107) inflates this line. Mental note: true EV charging spend is lower.

### Subscriptions double PlayStation charge (Feb)
- Two PS Network charges in Feb ($15.98 + $11.99) = $27.97. One is PS Plus, one likely a game.
- Normal ongoing subscriptions: YouTube $13.99 + HBO Max $10.99 + Overleaf $10 + PS Plus ~$8 = ~$43/month

### Notes feature (added this session)
- Each row in the actuals column has a `+` icon (pencil when note exists)
- Click to add/edit an inline note per category per month
- Stored in `budget_actuals_notes` table: (year, month, category, note)

---

## Historical Mock Data Note

Net worth snapshots before Mar 2026 are mock/interpolated data inserted directly into `net_worth_snapshots`. They were not derived from real `account_balances` rows. Safe to keep - `recompute_net_worth()` only processes dates present in `account_balances` and will not overwrite them. Delete when 6+ months of real data exists:
```sql
DELETE FROM net_worth_snapshots WHERE snapshot_date < '2026-03-11';
```
Mock trajectory: Aug 2021 (-$22.5K debt) -> slow payoff -> Oct 2023 NVIDIA inflection (big jump) -> steady growth -> Mar 2026 ($184K real).

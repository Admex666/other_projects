---
id: ADR-007-revolut-stripe-cashflow-integration
type: decision
name: ADR-007 Revolut Pro and Stripe Live Cashflow & Financial Ledger Integration
status: active
description: Unifying live Stripe balance/transaction ledger with historical Revolut Pro bank statement for automated enterprise liquidity and cashflow tracking.
date: 2026-08-31
deciders:
  - Adam
  - Antigravity AI
related:
  - "[[revolut]]"
  - "[[stripe]]"
  - "[[admin-panel|Admin Panel]]"
  - "[[unit-economics|Unit Economics]]"
  - "[[fixed-costs|Fixed Costs]]"
---

# ADR-007: Revolut Pro and Stripe Live Cashflow & Financial Ledger Integration

## Context
Previously, financial performance was inferred from order revenues and estimated cost models without real-time reconciliation against actual bank balances, processing fees, supplier payouts, and tax obligations.
To establish a verifiable single source of truth for liquid capital, runway, and cash burn, the system required:
1. Direct live visibility into available and pending Stripe balances and individual transaction processing fees.
2. Ingestion of the primary **Revolut Pro** bank account statements from inception (`2026-05-07`) to date.
3. Categorized cashflow analysis distinguishing Capex (medal batches), Opex (Meta Ads, Foxpost, accounting, software), and Tax obligations.

## Decisions

1. **Dual Financial Sourcing in `/api/admin-data`:**
   * **Stripe Live API:** Calls `stripe.balance.retrieve()`, `stripe.balanceTransactions.list()`, and `stripe.payouts.list()` on demand.
   * **Revolut Pro Statement Parser:** Reads `revolut_statement.csv` and auto-categorizes entries into Capex, Marketing, Logistics, Packaging, Accounting, Tax, Stripe Payouts, and Owner Equity.

2. **Dedicated `💳 Pénzügy & Cashflow` Dashboard in `admin.html`:**
   * **Top Liquidity Overview:** Displays combined liquid capital ($\text{Stripe Available} + \text{Revolut Pro Balances}$), pending Stripe settlements, and period inflow/outflow totals.
   * **Category Breakdown Grid:** Summarizes net expense by cost center.
   * **Combined Transactions Ledger:** Sortable and searchable ledger table merging both banking streams.

3. **Cumulative Daily Cashflow Timeline (Inception to Date):**
   * **Sales Timing Realignment:** Stripe card sales are credited to cashflow on the exact day the purchase occurred (`tx.net`).
   * **Internal Transfer Deduplication:** Payouts from Stripe to Revolut Pro (`stripe_payout` / `STRIPE TECHNOLOGY EUROPE`) are excluded from cashflow addition to prevent double-counting revenues.
   * **Evolution Curve:** Interactive SVG chart and day-by-day ledger displaying daily net cashflow ($\Delta \text{Cash}_d$) and cumulative cash balance from Day 1 (`2026-05-07`) to date.

4. **Inventory Balance Sheet & Total Asset Overlay (Mérleg & Vagyon):**
   * **Dynamic Medal Batch Valuation:** Automatically detects Alibaba/Capex disbursements in Revolut statements to determine exact per-unit cost:
     - Batch 1 (Prédikálószék): 151 244,53 Ft / 100 = **1 512,45 Ft / érem**.
     - Batch 2 (Nagy-Kevély / Pilis): 162 865,23 Ft / 100 = **1 628,65 Ft / érem**.
   * **Asset Capitalization:** Cash disbursements for medal manufacturing do not decrease enterprise equity—they convert liquid cash into physical inventory assets.
   * **COGS Outflow on Sale:** Upon customer purchase, the medal cost is deducted from inventory while net sale price is credited, accurately reflecting gross profit and true balance sheet value ($\text{Vagyon} = \text{Likvid Pénz} + \text{Raktárkészlet}$).
   * **Dual-Curve Visualization:** Overlays the Gold Total Asset curve against the Cyan Pure Cashflow curve.
   * **Unified Inventory Source of Truth:** Stock counts for Prédikálószék (`predikaloRemaining`) and Nagy-Kevély (`pilisRemaining`) are computed identically to `admin-proofs.js` (`updateStats`), using `allRuns.filter(!isTestRun)` subtracted from campaign limits (`100`), ensuring 100% data consistency across all views.

## Consequences
* Enterprise liquidity, daily cash burn, and cash runway are immediately readable with zero guesswork.
* True balance sheet equity ($\text{Cash} + \text{Inventory}$) distinguishes between operational cash burn and physical asset holding.
* Accurate chronological financial history reflecting actual purchasing events alongside real bank disbursements.
* Real processing fees and FX conversion differences are accurately tracked.
* Seamless audit trail connecting Stripe order charges to bank account payouts and supplier disbursements without revenue duplication.
* Single source of truth for physical inventory in both the runner/logistics management tabs and financial balance sheet.

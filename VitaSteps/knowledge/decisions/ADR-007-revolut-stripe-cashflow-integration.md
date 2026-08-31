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
   * **1-Click Statement Refresh:** Direct frontend CSV upload endpoint (`type: 'upload_revolut'`).

## Consequences
* Enterprise liquidity and cash runway are immediately readable with zero guesswork.
* Real processing fees and FX conversion differences are accurately tracked.
* Seamless audit trail connecting Stripe order charges to bank account payouts and supplier disbursements.

---
id: revolut
type: system
name: Revolut Pro Banking & Cashflow
status: active
description: Revolut Pro commercial bank account management, multi-category expense tracking, and CSV statement ingestion.
account_type: Revolut Pro
currency: HUF / EUR / USD
code:
  - landing_predikalo1/api/admin-data.js
  - landing_predikalo1/admin.html
  - landing_predikalo1/revolut_statement.csv
related:
  - "[[stripe]]"
  - "[[fixed-costs|Fixed Costs]]"
  - "[[variable-costs|Variable Costs]]"
  - "[[admin-panel|Admin Panel]]"
  - "[[ADR-007-revolut-stripe-cashflow-integration|ADR-007 Revolut & Stripe Cashflow]]"
---

# System: Revolut Pro Banking & Cashflow

VitaSteps uses a **Revolut Pro** account as its primary operating and settlement bank account.

## Account Characteristics
* **Type:** Revolut Pro Account (Sole Proprietorship / Freelance tier)
* **Currencies:** Primary HUF, FX USD (for Alibaba medal manufacturing wire transfers)
* **Cashback:** 0.4%–1.0% Pro cashback on eligible business purchases

## Key Cashflow Categories & Expense Mapping
1. 🏅 **Éremgyártás (Capex):** Alibaba supplier card payments & USD conversions (163 000 Ft / 100-medal batch).
2. 📢 **Marketing (Meta Ads):** Automated Facebook card debit charges.
3. 🦊 **Logisztika (Foxpost & Csomagolás):** Monthly FoxPost Kft. wire transfers & Simplep Shop packaging materials.
4. 💼 **Könyvelés & Admin (Opex):** Monthly transfers to Péter László ev. (15 000 Ft/mo) & KBOSS.hu (Számlázz.hu).
5. 🏛️ **Adók:** NAV Általános Forgalmi Adó (ÁFA) tax authority payments.
6. 💰 **Bevétel Jóváírások:** Automatic payouts from Stripe Technology Europe.
7. 🏦 **Kezdőtőke / Betétek:** Owner initial equity injections via Google Pay.

## Integration Architecture
* **Cloud Persistence:** Uploaded statements are stored in **Supabase Storage** (`medals/finance/revolut_statement.csv`), ensuring durable state persistence across Vercel Serverless Function instances (preventing `EROFS` read-only filesystem issues).
* **Local Fallback:** Local development reads from `landing_predikalo1/revolut_statement.csv` or directly syncs with Supabase Storage.
* **Ingestion & Classification:** Processed and categorized dynamically by `/api/admin-data` (when `type: 'finance'` or `type: 'upload_revolut'`).
* **Admin Dashboard:** `admin.html` provides a 1-click upload interface to update statements and view live vs historical cashflow trends and unified bank ledger.

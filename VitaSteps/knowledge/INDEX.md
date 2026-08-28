---
id: index
type: navigation
name: Knowledge Index
status: active
description: Master navigation map for the VitaSteps Project Knowledge Graph.
---

# 🗺️ VitaSteps Knowledge Index

Welcome to the **VitaSteps Project Knowledge Graph**. This index provides direct, progressive navigation into all domain concepts, systems, processes, metrics, decisions, and operations.

---

## 🏛️ Domain Entities (`knowledge/entities/`)
Concrete physical and business objects of the VitaSteps platform.

* [[customer|Customer]]: Participant & runner model (Supabase: `runners`).
* [[run|Run]]: Individual challenge entry, serial rank, verification & delivery state (Supabase: `runs`).
* [[order|Order]]: Stripe payment transaction and checkout metadata.
* [[medal|Medal]]: Physical collectible medals, specs, and Chinese supplier relations.
* [[campaign-predikaloszek|Campaign Predikaloszek]]: Prédikálószék Vertical 100-medal challenge.
* [[campaign-nagykevely|Campaign Nagy-Kevely]]: Nagy-Kevély csillagai 100-medal astronomical night challenge.

---

## 💡 Concepts (`knowledge/concepts/`)
Foundational business and architectural principles.

* [[verified-challenge|Verified Challenge]]: GPS & photo-based validation mechanics for collectible awards.
* [[unified-campaign-config|Unified Campaign Config]]: Dynamic, config-driven multi-campaign frontend architecture.
* [[dynamic-pricing|Dynamic Pricing]]: Entry pricing, quantity tiers, home delivery surcharges.
* [[referral-program|Referral Program]]: 1 000 Ft coupon discount and referrer reward system.

---

## 🔄 Processes (`knowledge/processes/`)
Core end-to-end operational workflows.

* [[checkout-pipeline|Checkout Pipeline]]: Stripe Checkout $\rightarrow$ `process-payment.js` $\rightarrow$ DB sync + E-Invoice + Welcome Email.
* [[proof-verification|Proof Verification]]: User GPX/photo upload on `portal.html` $\rightarrow$ Admin approval $\rightarrow$ Diploma + Congratulation Email.
* [[order-fulfillment|Order Fulfillment]]: Multi-medal & cross-campaign grouping $\rightarrow$ Packing guide $\rightarrow$ Foxpost locker dispatch.
* [[meta-sync-pipeline|Meta Sync Pipeline]]: Daily GitHub Action automated sync for Meta Ads performance metrics.

---

## ⚙️ Systems & Architecture (`knowledge/systems/`)
Integrated technical components and infrastructure.

* [[admin-panel|Admin Panel]]: Web dashboard (`admin.html`) for proofs, shipments, and live analytics.
* [[supabase|Supabase]]: PostgreSQL schema, Row-Level Security (RLS) policies, database triggers.
* [[stripe|Stripe]]: Payment processing, session metadata, webhook-free fulfillment.
* [[foxpost|Foxpost]]: Parcel locker automated API, shipment status lifecycle & tracking.
* [[szamlazz-hu|Számlázz.hu]]: Automated NAV-compliant electronic invoice generation.
* [[meta-ads|Meta Ads]]: Marketing API, Ad Sets, UTM tracking, creative performance analytics.
* [[vercel|Vercel]]: Serverless Node.js backend endpoints and global edge deployment.
* [[microsoft-clarity|Microsoft Clarity]]: User heatmaps, session recordings, and conversion UX analysis.

---

## 📊 Metrics & Economics (`knowledge/metrics/`)
Key performance indicators with single-source-of-truth formulas.

* [[fixed-costs|Fixed Costs]]: Fix költségek (163k éremgyártás + 15k/hó könyvelés + Capex).
* [[variable-costs|Variable Costs]]: Termékenkénti változó költségek (Foxpost, Stripe, Számlázz.hu, CAC).
* [[unit-economics|Unit Economics]]: Contribution margin (egységfedezet = ár - változó költségek).
* [[break-even|Break-Even]]: Nullszaldós pont számítása a fix költségek fedezeti törlesztéséből.
* [[cac|CAC]]: Customer Acquisition Cost per challenge entry.
* [[roas|ROAS]]: Return on Advertising Spend.

---

## ⚖️ Decisions (ADRs) (`knowledge/decisions/`)
Durable architectural and strategic decisions.

* [[ADR-001-supabase-migration|ADR-001 Supabase Migration]]: Moving from Google Sheets to normalized PostgreSQL.
* [[ADR-002-webhook-free-payment|ADR-002 Webhook-Free Payment]]: Siker.html client-triggered post-payment processing.
* [[ADR-003-unified-campaign-config|ADR-003 Unified Campaign Config]]: Centralizing campaign settings in `config/campaigns.json`.
* [[ADR-004-consolidated-shipping|ADR-004 Consolidated Shipping]]: Multi-medal & cross-campaign package merging.
* [[ADR-005-strict-rls-security|ADR-005 Strict RLS Security]]: Supabase database hardening and admin endpoints.

---

## 🧠 Learnings (`knowledge/learnings/`)
Validated empirical insights and troubleshooting findings.

* [[meta-ad-creatives|Meta Ad Creatives]]: Converting visual & copy angles (V4/V5 hiker vs medal focus).
* [[leaflet-print-rendering|Leaflet Print Rendering]]: Geographic padding & container height sync in PDF/print view.
* [[returning-customer-rate|Returning Customer Rate]]: 80%+ repeat purchase rate between sequential challenges.

---

## 🛠️ Operations (`knowledge/operations/`)
Practical human & agent operating runbooks.

* [[how-to-pack-and-ship|How to Pack and Ship]]: Using `admin.html` packing guide and generating Foxpost labels.
* [[how-to-launch-campaign|How to Launch Campaign]]: Adding a new challenge into `campaigns.json` and deploying landing pages.
* [[how-to-run-daily-sync|How to Run Daily Sync]]: Triggering and inspecting daily Meta & Foxpost sync jobs.
* [[how-to-manual-approve|How to Manual Approve]]: Approving proof received outside the runner portal.

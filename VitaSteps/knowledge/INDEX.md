---
id: index
type: navigation
name: Knowledge Index
status: active
description: Master navigation map for the VitaSteps Project Knowledge Graph.
---

# 🗺️ VitaSteps Knowledge Index

Welcome to the **VitaSteps Project Knowledge Graph**. This index provides direct, progressive navigation into all strategic concepts, domain entities, systems, processes, metrics, decisions, and operations.

---

## 🏛️ Domain Entities (`knowledge/entities/`)
Concrete physical, digital, and business objects of the VitaSteps platform.

* [[customer|Customer]]: Participant & runner model (Supabase: `runners`).
* [[run|Run]]: Individual challenge entry, serial rank, verification & delivery state (Supabase: `runs`).
* [[order|Order]]: Stripe payment transaction and checkout metadata.
* [[medal|Medal]]: Physical collectible medals, specs, and Chinese supplier relations.
* [[campaign-predikaloszek|Campaign Predikaloszek]]: Prédikálószék Vertical 100-medal challenge.
* [[campaign-nagykevely|Campaign Nagy-Kevely]]: Nagy-Kevély csillagai 100-medal astronomical night challenge.
* [[virtual-challenge|Virtual Challenge]]: Helyszínfüggetlen távolsági és kilométer-kihívások (MVP modell).
* [[hosszu-lepesek|Hosszú Lépések]]: Önvezetett tematikus városi audioséták és történetmesélés.

---

## 💡 Concepts & Strategy (`knowledge/concepts/`)
Foundational strategic positioning, marketing loops, and architectural principles.

* [[strategic-positioning|Strategic Positioning]]: A VitaSteps mozgás-, felfedezés- és teljesítésközpontú élményrendszere (*„MOZOGJ. FEDEZZ FEL. TELJESÍTS.”*).
* [[growth-loop|Growth Loop]]: Integrált növekedési hurok (Organic + Community + Lead + Email + Meta + UGC + Referral).
* [[organic-content-pillars|Organic Content Pillars]]: A 4 organikus tartalom pillér (Hasznos, Felfedezés, Teljesítés, VitaSteps).
* [[verified-challenge|Verified Challenge]]: GPS és fotó alapú fizikai túrakihívás hitelesítési mechanizmus.
* [[unified-campaign-config|Unified Campaign Config]]: Dinamikus, konfiguráció-vezérelt többkampányos frontend architektúra.
* [[dynamic-pricing|Dynamic Pricing]]: Nevezési árazás, sávos kedvezmények, szállítási díjak.
* [[referral-program|Referral Program]]: 10%-os baráti kupon és progresszív szintlépő ajánlói rendszer.

---

## 🔄 Processes (`knowledge/processes/`)
Core end-to-end operational and lifecycle workflows.

* [[customer-funnel|Customer Funnel]]: End-to-end vásárlói életciklus (Akvizíció $\rightarrow$ Landing $\rightarrow$ Lead Kapu $\rightarrow$ Checkout $\rightarrow$ Igazolás $\rightarrow$ Kiszállítás $\rightarrow$ Retenció).
* [[organic-content-workflow|Organic Content Workflow]]: Kétheti ~60 perces batch tartalomgyártási folyamat (Nyersanyag $\rightarrow$ AI $\rightarrow$ Szerkesztés $\rightarrow$ Ütemezés).
* [[community-engagement-protocol|Community Engagement Protocol]]: Facebook közösségi részvételi szabályzat (*„Help first, brand second”*).
* [[lead-nurturing-sequence|Lead Nurturing Sequence]]: 0–10 napos automatizált e-mail szekvencia és downstream konverziókövetés.
* [[ugc-referral-engine|UGC & Referral Engine]]: Teljesítés utáni visszacsatolás, élményszelfik, történetek és ajánlói megosztások.
* [[checkout-pipeline|Checkout Pipeline]]: Stripe Checkout $\rightarrow$ `process-payment.js` $\rightarrow$ DB sync + E-Számla + Welcome Email.
* [[proof-verification|Proof Verification]]: Felhasználói GPX/fotó feltöltés $\rightarrow$ Admin jóváhagyás $\rightarrow$ Diploma + Gratuláló Email.
* [[order-fulfillment|Order Fulfillment]]: Többérmes és kampányközi csomagösszevonás $\rightarrow$ Csomagolási segédlet $\rightarrow$ Foxpost feladás.
* [[meta-sync-pipeline|Meta Sync Pipeline]]: Automatikus napi GitHub Action szinkronizáció a Meta Ads Marketing API-ból.

---

## ⚙️ Systems & Architecture (`knowledge/systems/`)
Integrated technical components and infrastructure.

* [[admin-panel|Admin Panel]]: Webes adminisztrációs felület (`admin.html`) igazolásokhoz, logisztikához és marketing analitikához.
* [[email-templates|Email Templates]]: Szabványosított HTML sablonok (`email_templates/`) tranzakciós, biztonsági és nurturing levelekhez.
* [[supabase|Supabase]]: PostgreSQL adatbázis séma, RLS biztonsági házirendek és triggerek.
* [[stripe|Stripe]]: Fizetésfeldolgozás, munkamenet metaadatok, webhook-mentes architektúra.
* [[revolut|Revolut Pro]]: Üzleti bankszámla, kiadás-kategorizálás és cashflow nyilvántartás.
* [[foxpost|Foxpost]]: Csomagautomata API, feladás, állapot-életciklus és automatikus nyomkövetés.
* [[szamlazz-hu|Számlázz.hu]]: Automatikus NAV-kompatibilis elektronikus számlázás.
* [[meta-ads|Meta Ads]]: Marketing API, hirdetéscsoportok, UTM struktúra és kreatív-szintű analitika.
* [[vercel|Vercel]]: Serverless Node.js backend végpontok és globális edge hosting.
* [[microsoft-clarity|Microsoft Clarity]]: Felhasználói hőtérképek, session videók és konverziós viselkedéselemzés.

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
Durable architectural, product, and strategic decisions.

* [[ADR-001-supabase-migration|ADR-001 Supabase Migration]]: Átállás Google Sheets-ről normalizált PostgreSQL-re.
* [[ADR-002-webhook-free-payment|ADR-002 Webhook-Free Payment]]: Kliens által indított, golyóálló fizetés-feldolgozás.
* [[ADR-003-unified-campaign-config|ADR-003 Unified Campaign Config]]: Kampánybeállítások központosítása a `campaigns.json`-ban.
* [[ADR-004-consolidated-shipping|ADR-004 Consolidated Shipping]]: Többérmes és kereszt-kampányos rendelések egybecsomagolása.
* [[ADR-005-strict-rls-security|ADR-005 Strict RLS Security]]: Supabase adatbázis védelem és adminisztrátori végpontok.
* [[ADR-006-multicampaign-unit-economics|ADR-006 Multi-Campaign Unit Economics]]: Kampány capex izoláció és kreatív-szintű megtérülés.
* [[ADR-007-revolut-stripe-cashflow-integration|ADR-007 Revolut & Stripe Cashflow]]: Stripe egyenleg és Revolut Pro cashflow egységesítése.
* [[ADR-008-foxpost-batch-resilience|ADR-008 Foxpost Batch Resilience]]: Előzetes validáció és csoportos hibatűrés a Foxpost API hívásoknál.
* [[ADR-009-strategic-ecosystem-pivot|ADR-009 Strategic Ecosystem Pivot]]: Átállás az egytermékes modellről a mozgás- és felfedezésközpontú 5-pilléres ökoszisztémára.

---

## 🧠 Learnings (`knowledge/learnings/`)
Validated empirical insights and troubleshooting findings.

* [[lead-magnet-intent|Lead Magnet Intent]]: Az ingyenes anyagok a magas vásárlási szándékú érdeklődőket szűrik ki, downstream követés szükséges.
* [[meta-ad-creatives|Meta Ad Creatives]]: Konvertáló vizuális és szöveges horgok (hiker vs érem fókusz).
* [[leaflet-print-rendering|Leaflet Print Rendering]]: Földrajzi kitöltés és konténer-magasság szinkron a nyomtatási nézetben.
* [[returning-customer-rate|Returning Customer Rate]]: 80%+ visszatérési arány az egymást követő kihívások között.

---

## 🛠️ Operations (`knowledge/operations/`)
Practical human & agent operating runbooks.

* [[how-to-pack-and-ship|How to Pack and Ship]]: Csomagolási segédlet és Foxpost címkenyomtatás.
* [[how-to-launch-campaign|How to Launch Campaign]]: Új kihívás felvétele a `campaigns.json`-ba és élesítés.
* [[how-to-run-daily-sync|How to Run Daily Sync]]: Napi Meta és Foxpost szinkronizációs folyamatok futtatása.
* [[how-to-manual-approve|How to Manual Approve]]: Portálon kívül érkezett igazolások jóváhagyása.

---
id: admin-panel
type: system
name: Admin Panel
status: active
description: Central administrative Single Page Application for proof verification, packing guides, Foxpost automated dispatch, and marketing break-even tracking.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/admin-data.js
  - landing_predikalo1/api/admin-approve.js
  - landing_predikalo1/api/create-foxpost-parcels.js
related:
  - "[[proof-verification|Proof Verification]]"
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[break-even|Break-Even]]"
  - "[[unit-economics|Unit Economics]]"
  - "[[how-to-manual-approve|How to Manual Approve]]"
  - "[[how-to-pack-and-ship|How to Pack and Ship]]"
---

# System: Admin Panel (`admin.html`)

The VitaSteps Admin Dashboard is a password-protected Single Page Application (`admin.html`) connecting directly to serverless Vercel endpoints and Supabase.

## Core Operational Views

### 1. ⏳ Várakozó (Egységes Várakozó és Jóváhagyó Lista)
* **Központi lista:** Minden várakozó résztvevő egy helyen kezelhető (mind a Prédikálószék, mind a Nagy-Kevély futók).
* **Al-szűrők:**
  - `⏳ Összes várakozó`: Minden még nem teljesített regisztráció.
  - `📥 Beküldött igazolások`: Portálon képet vagy GPX-et feltöltött, elbírálásra váró futók.
  - `🏃 Még nem igazolt`: Nevezett, de még nem igazolt résztvevők.
* **Kihívás szerinti gyorsszűrő:** `Összes`, `🏔️ Prédikálószék`, `🌌 Nagy-Kevély`.
* **Közvetlen `✅ Manuális Jóváhagyás`:** Egykattintásos jóváhagyás külső (e-mail, közösségi média) igazolásokhoz.

### 2. ✅ Jóváhagyott (Approved)
* Sikeresen hitelesített és oklevéllel ellátott teljesítők archívuma.

### 3. 🦊 Logisztika (Foxpost)
* **Csomagolási és Kiszállítási Segédlet:** Kártyás nézet, amely kampányonként részletezi a borítékba teendő érmek sorszámait és darabszámát (több kampányos összevonás támogatása azonos címzettnél).
* **1-Kattintásos Foxpost API Feladás:** Csomagok automatikus létrehozása, vonalkódok generálása és követési kód szinkronizáció.

### 4. 📊 Marketing & Break-Even Dashboard
* **Megtérülés (Break-Even):** 193 000 Ft fix költség (163k érem + 30k könyvelés) törlesztésének követése a termékenkénti nettó fedezetből.
* **Tételes Változó Költségek (CM):** Bruttó bevétel − Meta(+ÁFA) − Foxpost (1 250 Ft) − Stripe (1,5%+50Ft) − Számlázz.hu (35 Ft) − Csomagolás (120 Ft).
* **Lojalitási Kohorsz Analízis:** Új vs. visszatérő vásárlók aránya kihívásonként.

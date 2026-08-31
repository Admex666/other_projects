---
id: numbeo-cost-model
type: concept
name: Numbeo Cost of Living Model
status: active

description: A célvárosok hivatalos Numbeo adatbázisán és valós árfolyamán alapuló standard fogyasztói kosár modell, amely szigorú Single Source of Truth elven és 3 transzparens étkezési profilon (Takarékos, Átlagos, Kényelmes) keresztül határozza meg a költségeket.

source:
  type: decision
  ref: "[[ADR-002-deterministic-numbeo-food-pricing]]"

code:
  - app/services/numbeo_service.py
  - app/routers/planner.py
  - static/js/trip_cart.js

related:
  - "[[daily-food-cost]]"
  - "[[daily-transit-cost]]"
  - "[[numbeo-database]]"
  - "[[proposal-generation]]"
  - "[[ADR-002-deterministic-numbeo-food-pricing]]"

used_by:
  - "[[trip-cart-engine]]"
  - "[[destination-matching]]"
  - "[[master-planner-wizard]]"
---

# 🧮 Concept: Numbeo Cost of Living Model

Az Optivoya elutasítja a becsült vagy hasraütésszerű költségeket. Az étkezési és helyi közlekedési költségkeret szigorú, reprodukálható Numbeo fogyasztási kosáron és az `[[ENGINEERING_PRINCIPLES]]` (Single Source of Truth) elvén alapul.

---

## 🍽️ A 3 Transzparens Étkezési Profil

Mivel a Numbeo adatbázisban a valós `meal_inexpensive`, `meal_midrange` (2 fős 3-fogásos vacsora), `coffee` és `transport_ticket` tételek szerepelnek, a rendszer 3 egyszerű, könnyen védhető és ellenőrizhető profilt biztosít:

| Profil | Reggeli | Ebéd | Vacsora | Kávé / Ital | Képlet (€/fő/nap) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **🥪 Takarékos** | Market / Pékség ($0.5\times$) | Olcsó étterem ($1.0\times$) | Olcsó étterem ($1.0\times$) | 1 kávé ($1.0\times$) | $2.5 \times \text{inexpensive} + 1.0 \times \text{coffee}$ |
| **🍝 Átlagos (Default)** | Egyszerű reggeli ($1.0\times$) | Olcsó étterem ($1.0\times$) | 3-fogásos vacsora ($0.5\times \text{midrange}$) | 1 kávé ($1.0\times$) | $2.0 \times \text{inexpensive} + 0.5 \times \text{midrange} + 1.0 \times \text{coffee}$ |
| **🍷 Kényelmes** | Kávézó ($1.0\times$) | Beülős ebéd ($0.5\times \text{midrange}$) | Beülős vacsora ($0.5\times \text{midrange}$) | 2 kávé/ital ($2.0\times$) | $1.0 \times \text{inexpensive} + 1.0 \times \text{midrange} + 2.0 \times \text{coffee}$ |

---

## 🚇 Napi Helyi Közlekedés (€/fő/nap):
$$\text{Transit}_{\text{daily}} = 2.0 \times \text{transport\_ticket}$$
* **2×** egyirányú helyi vonaljegy / metrójegy / villamosjegy naponta.

---

## 🏛️ Kanonikus Végpont & Árfolyamkezelés

* **Kanonikus forrás:** `app/services/numbeo_service.py` ➔ `/api/numbeo/breakdown`
* **Dinamikus devizakonverzió:** A forintosítás a napi élő árfolyam (`eur_rate`) alapján történik, kliensoldali heurisztika vagy beégetett árfolyamok nélkül.

---
id: current-constraints
aliases:
  - CONSTRAINTS
type: strategic_concept
name: Constraints & Scope Limits
status: active

description: A projekt stratégiai, termékbeli és erőforrásbeli korlátai — Szigorú Beta Scope Szabály, Non-Goalok és Még NEM szükséges funkciók.

related:
  - "[[CURRENT_STATE]]"
  - "[[PRIORITIES]]"
  - "[[NORTH_STAR]]"
  - "[[optivoya-strategy]]"
  - "[[honest-scraping-policy]]"
---

# 🛑 Constraints, Scope Limits & Non-Goals

## 🔒 A Beta Scope Szabály (Anti-Feature-Bloat)

> **Vezérelv:** Új feature csak akkor kerülhet a beta scope-ba, ha valódi user bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.

---

## 🚫 Üzleti NEM Célok

1. **Nincs VC / fundraising:** Nem cél kockázati tőke bevonása vagy felhígulás.
2. **Nincs nagy csapat:** Kis méretű, automatizált működés.
3. **Nincs agresszív növekedés:** Nem cél a tőkeégetés a profit rovására.
4. **Nincs felesleges feature-fejlesztés:** Csak a validációhoz közvetlenül szükséges funkciókat fejlesztjük.
5. **Nincs founder-intenzív agency business:** Nem vállalunk manuális, ügynökségi szervezési feladatokat.
6. **Erőforráskorlát:** $\le 10$ founder óra / hét a megcélzott operációs limit.

---

## ⏸️ Bétában Még NEM Szükséges Funkciók

A béta célja annak bizonyítása, hogy az advisor gyorsabban tud-e jobb ügyfélajánlatot készíteni a jelenlegi motorokkal. A következők kifejezetten kívül esnek a jelenlegi scope-on:
* Teljes itinerary engine
* Komplex TSP / VRPTW útvonaloptimalizáció
* Teljes programtervezés
* Mobilapp
* Chatbot
* Enterprise funkciók
* Komplex CRM
* Egyéb „nice-to-have” kényelmi funkciók

---

## ⚙️ Technikai & Adatinvariánsok

* **Honest Scraping Invariant:** Nem jelenítünk meg hallucinált vagy kitalált árakat/járatokat. Ha külső forrás nem elérhető, transzparensen jelezzük.
* **Human-in-the-loop elv:** A rendszer döntéstámogató jelölteket és rangsort ad, a végleges jóváhagyás és szerkesztés az emberi tanácsadó kezében marad.

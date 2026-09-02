---
id: current-constraints
aliases:
  - CONSTRAINTS
type: strategic_concept
name: Constraints & Scope Limits
status: active

description: A projekt aktuális stratégiai, technikai és erőforrásbeli korlátai (Scope Rule, Founder Hours ≤10h, Nem Célok).

related:
  - "[[CURRENT_STATE]]"
  - "[[PRIORITIES]]"
  - "[[NORTH_STAR]]"
  - "[[optivoya-strategy]]"
  - "[[honest-scraping-policy]]"
---

# 🛑 Constraints, Scope Limits & Non-Goals

## 🔒 Scope Szabály (Anti-Feature-Bloat)
> **Aranyszabály:** Új feature csak akkor kerülhet a béta scope-ba, ha valódi felhasználó bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.

---

## 🚫 Stratégiai NEM Célok (Non-Goals)
1. **Nincs VC / Tőkebevonás:** Nem cél nagy kockázati tőkés csapat felépítése.
2. **Nincs Founder-intenzív Agency:** Nem vállalunk manuális utazási ügynökségi szolgáltatást.
3. **Erőforráskorlát:** $\le 10$ founder óra / hét a cél, a rendszernek automatizáltnak és skálázhatónak kell maradnia.
4. **Bétában NEM szükséges:**
   * Teljes itinerary / programtervező engine
   * Komplex TSP / VRPTW útvonaloptimalizáció
   * Mobilapp, chatbot, CRM és enterprise funkciók

---

## ⚙️ Technikai & Adatinvariánsok
* **Honest Scraping Invariant:** Nem jelenítünk meg hallucinált vagy kitalált árakat/járatokat.
* **Kétirányú gyorsítótárazás és sebesség:** A válaszidőknek meg kell felelniük a `[[PERFORMANCE_STANDARDS]]` előírásainak.

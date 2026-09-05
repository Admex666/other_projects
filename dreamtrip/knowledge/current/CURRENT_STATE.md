---
id: current-state
aliases:
  - CURRENT_STATE
type: strategic_concept
name: Current State
status: active

description: Az Optivoya projekt jelenlegi állapota — M1 B2B Beta Validation fázis, működő unified motorok, human-in-the-loop workflow és az első fizető ügyfél fókusz.

related:
  - "[[master-planner-wizard]]"
  - "[[unified-trip-model]]"
  - "[[supabase-database]]"
  - "[[OBJECTIVES]]"
  - "[[PRIORITIES]]"
  - "[[optivoya-strategy]]"
---

# 📍 Current State: M1 — B2B Beta Validation

Az Optivoya jelenleg az **M1 — B2B Beta Validation** mérföldkőnél tart.

> **Jelenlegi fókusz:** B2B validation $\to$ első fizető ügyfél.

---

## 🚀 Kész és Működő Rendszerek (Beta MUST HAVE)

1. **Destination Matcher:** Desztinációk személyre szabott rangsorolása Open-Meteo klíma, Kiwi repülőjegy árak és Numbeo költség/biztonság adatok alapján.
2. **Flight Intelligence:** Valós Kiwi.com járatadatok, ár, menetidő, átszállás, időzítés és PROMETHEE II rangsorolás.
3. **Accommodation Intelligence:** Cozycozy élő szállásadatok, ár, értékelés, lokáció és személyre szabott rangsor.
4. **Unified Workflow (Master Planner `/planner`):** A három motor egyetlen, integrált folyamatba kötve:  
   $$\text{Optivoya jelöltek} \longrightarrow \text{AHP/PROMETHEE rangsor} \longrightarrow \text{Trade-offs} \longrightarrow \text{Advisor ellenőrzés/szerkesztés} \longrightarrow \text{Ügyfélajánlat}$$
5. **Kanonikus Lebegő Kosár & Ajánlatkészítő (`TripCart`):** Automatikus összegzés és professzionális PDF/nyomtatható ajánlat.
6. **Supabase Cloud PostgreSQL & Telemetria (`[[supabase-database]]`):** Éles felhős adatbázis a béta felhasználók, hitelesítés, session-alapú látogatási utak (User Journeys) és esemény-telemetria perzisztens tárolásához.
7. **B2B Usage Analytics Dashboard (`/admin/dashboard`):** Valós idejű KPI-k, tanácsadói session utak, dwell time mérés és Microsoft Clarity képernyőfelvétel mélyintegráció.

---

## 🎯 Jelenlegi Fókuszfeladat

Bizonyítani a travel advisorokkal, hogy a teljes research $\to$ shortlist $\to$ proposal munkafolyamat során az Optivoya mérhető időmegtakarítást ($\text{Total Time Saved / Client}$) biztosít az output magas minőségének megőrzése mellett.

---
id: strategy-principles
aliases:
  - PRINCIPLES
type: strategic_concept
name: Strategic Principles
status: active

description: Alapvető stratégiai és termékdöntési elvek az Optivoya fejlesztésében — Decisions over Data Dumps, Human-in-the-Loop, Total Time Saved és Evidence over Volume.

related:
  - "[[PURPOSE]]"
  - "[[THESIS]]"
  - "[[VALUE_PROPOSITION]]"
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[honest-scraping-policy]]"
---

# 🧭 Strategic Principles

1. **Decisions over Data Dumps:** A felhasználót nem árasztjuk el ömlesztett adatokkal (nem egyszerű flight+hotel kereső vagyunk), hanem strukturált, rangsorolt opciókat nyújtunk világos döntési indoklással és kompromisszumokkal (trade-offs).
2. **Human-in-the-Loop Enablement:** Nem az advisor lecserélése a cél, hanem annak elérése, hogy ugyanazt a minőségi munkát lényegesen gyorsabban és jobb döntéstámogatással végezze el. Az advisor ellenőrzése és szerkesztése a folyamat szerves része.
3. **Total Workflow Time over Raw Latency:** Nem az API milliszekundumos válaszideje a fő érték, hanem az, hogy mennyi idő alatt jut el az advisor egy ügyfélnek kiküldhető, megbízható ajánlatig ($T_{\text{manual}} - T_{\text{Optivoya}}$).
4. **Honesty over Hallucination:** Kizárólag valós, ellenőrizhető külső forrásból származó adatokat mutatunk. Nincs fiktív adat; ha egy API nem elérhető, transzparensen jelezzük.
5. **End-to-End Coherence:** A célállomás, a járat és a szállás nem különálló silók, hanem egymásra épülő közös utazási állapot (`UnifiedTrip`).
6. **Evidence over Development Volume:** Nem a megírt feature-ök száma számít, hanem a szigorú validációs bizonyítás:  
   $$\text{Problem} \longrightarrow \text{Value} \longrightarrow \text{Quality} \longrightarrow \text{Repeat Usage} \longrightarrow \text{Payment} \longrightarrow \text{Repeatable Acquisition}$$
7. **Strict Scope Control (Anti-Feature-Bloat):** Új funkció csak akkor kerülhet a scope-ba, ha valódi felhasználó bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.

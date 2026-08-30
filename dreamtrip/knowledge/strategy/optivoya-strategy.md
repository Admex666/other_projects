---
id: optivoya-strategy
aliases:
  - optivoya-strategy
  - OPTIVOYA_STRATEGY
type: strategy
name: Optivoya Canonical Strategic Context & Product Direction
status: active

description: Az Optivoya kanonikus stratégiai forrása és termékvíziója — küldetés, B2B és B2C fókusz, döntéstámogatási tézis, termékelvek és a B2B Beta validációs fázis explicit hatóköre.

related:
  - "[[unified-trip-model]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[master-planner-wizard]]"
  - "[[guided-progressive-decision-flow]]"
  - "[[proposal-generation]]"

used_by:
  - "[[ADR-001-unified-trip-architecture]]"
  - "[[ADR-006-master-planner-wizard]]"
---

# Optivoya — Strategic Context & Canonical Product Direction

Ez a dokumentum a projekt stratégiai irányának **kanonikus forrása** (Single Source of Truth). A stratégiai tényeket és irányelveket más tudáscsomópontokban nem duplikáljuk, hanem ide hivatkozunk vissza.

---

## 🎯 Mission (Küldetés)

Az Optivoya segít az utazóknak és utazási szakembereknek jobb utazási döntéseket hozni kevesebb manuális kutatással, a fragmentált utazási adatok egyetlen intelligens, döntéstámogató munkafolyamatba szervezésével.

---

## 🌟 Vision (Jövőkép)

Az Optivoya célja, hogy egy **teljes körű (end-to-end) utazástervező rendszerré** váljon.

A rendszernek a teljes folyamatot támogatnia kell:

**"Hová utazzunk?" → célállomás → repülőjáratok → szállás → programok/tevékenységek → teljes útiterv → költségvetés → azonnal használható utazási ajánlat.**

Az Optivoya nem csupán járatokat és szállásokat keres: **programokat és látnivalókat is ajánl a célállomáson, valamint segít felépíteni a teljes útitervet**, így a felhasználó az egész utazást egyetlen rendszerben tudja megtervezni.

### Hosszú távú működési modellek:
1. **B2B:** Technológiai és döntéstámogató munkafolyamat biztosítása utazási irodák és független utazásszervezők (travel advisors) számára.
2. **B2C:** Az Optivoya maga is elláthatja az utazási tanácsadó szerepét, közvetlenül a végfelhasználóknak értékesítve a teljes utazástervezést és szolgáltatásokat.

A termék hosszú távú víziója tehát tágabb, mint egy B2B eszköz: egy **end-to-end intelligens utazástervező és ajánló platform**, amelynek kezdeti kereskedelmi belépési pontja a B2B piac.

---

## 👥 Primary Target Customer (Célközönség)

### Kezdeti / Elsődleges Ügyfél — B2B
Utazási irodák és független utazásszervezők, akik rendszeresen készítenek személyre szabott utazási ajánlatokat ügyfeleiknek.

*Alapproblémájuk:* A kutatás és adatgyűjtés számtalan különböző weboldalon és eszközben szétaprózódik, míg az opciók összehasonlítása és egy ügyfélkész ajánlat elkészítése jelentős manuális munkát igényel.

### Jövőbeli Ügyfél / Üzleti Modell — B2C
Az Optivoya a későbbiekben közvetlenül a végfelhasználóknak is nyújthat tanácsadást és utazási termékeket.

*Fontos:* Ez egy **jövőbeli stratégiai irány**, amely nem bővíti automatikusan a jelenlegi béta fejlesztési hatókörét.

---

## 💡 Product Thesis (Terméktézis)

Az Optivoya alapvető értéke **nem csupán több utazási opció megtalálása**.

A valódi érték abban rejlik, hogy segít a felhasználónak **gyorsabban jobb utazási döntést hozni**, és végül megtervezni a teljes utazást.

A termék a töredezett utazási információkat az alábbiakká formálja:
* könnyen érthető ajánlások
* rangsorolt alternatívák
* átlátható kompromisszumok (trade-offs)
* koherens, egybefüggő utazás
* teljes és tételes költségvetés
* végső soron egy komplett útiterv és ajánlat

---

## 🗺️ Current Product Direction (Termékfolyamat)

### Jelenlegi termékfolyamat (Beta Scope):
**Destination Matcher → Flight Intelligence → Accommodation Intelligence → Unified Trip → Proposal**

### Hosszú távú termékfolyamat:
**Destination → Flight → Accommodation → Activities/Programs → Itinerary → Budget → Proposal/Booking**

A program- és élményajánlások a **hosszú távú termékvízió** részei, de nem feltétlenül részei a jelenlegi béta hatókörnek.

---

## 📐 Product Principles (Termékelvek)

* **Decisions over data dumps**: Do not overwhelm the user with raw data. Provide curated, ranked options with clear rationales.
* **Zero Analysis-Paralysis & Guided Progressive Flow**: Mindig legyen egyértelmű, fókuszált útja a felhasználónak. Soha ne terheljük túl egyidejű választási kényszerekkel; az űrlapok és döntési helyzetek fokozatosan (progressive disclosure), lépésről lépésre oldódjanak fel a választások után.
* **Transparency**: Show why a flight or stay is recommended (e.g. AHP weights, PROMETHEE scores, trade-offs).
* **Speed with depth**: Fast initial recommendations with optional deep dives.
* **Agentic workflow**: Users declare constraints and preferences; Optivoya executes the search, scoring, and assembly.
* **Valós adatok a kitalált adatok felett:** Nem használunk mesterséges dummy adatokat; a transzparens valós adatforrások élveznek prioritást.
* **Döntéstámogatás az információtúlterhelés felett:** Rangsorolás, magyarázat és kiemelés a nyers opciók tömege helyett.
* **Egyetlen Terv (UnifiedTrip) mint hiteles forrás:** Minden modul ugyanazt az állapotot gazdagítja és látja.
* **Nincs felesleges adatbekérés:** Kerülni kell a felhasználó újrakérdezését olyan adatokról, amelyeket a rendszer már ismer.
* **Elmagyarázható ajánlások:** A rangsorolások és pontszámok mögötti logika mindig átlátható és indokolható.
* **Munkafolyamatra optimalizálás a funkciószámlálás helyett:** A felhasználó valós folyamatait támogatjuk.
* **Mérhető értékteremtés:** Olyan funkciókat építünk, amelyek mérhető felhasználói vagy üzleti értéket teremtenek.
* **End-to-end koherencia:** Az egybefüggő, koherens élmény prioritást élvez az izolált funkciófejlesztésekkel szemben.

---

## ⏱️ Current Strategic Phase (Jelenlegi Stratégiai Fázis)

**B2B Beta Validáció**

A közvetlen cél annak validálása, hogy az utazási szakemberek használják-e az Optivoyát valós ügyfélutazásokhoz, és hogy a rendszer mérhető értéket teremt-e számukra:
* csökkentett kutatási idő
* gyorsabb ajánlatkészítés
* jobb döntéstámogatás
* ismétlődő használat
* fizetési hajlandóság

A hosszú távú vízió vezérli az architektúrát és a termékdöntéseket, de **a jövőbeli funkcionalitás nem bővítheti feleslegesen a jelenlegi béta hatókört**.

---

## 🛡️ Explicit Scope Principle (Explicit Hatóköri Alapelv)

A hosszú távú víziót nem szabad úgy értelmezni, mintha mindent azonnal meg kellene építeni.

A jelenlegi prioritás a létező:

**Destination → Flight → Accommodation → Trip → Proposal**

munkafolyamat megbízhatóvá, érthetővé és értékessé tétele.

A jövőbeli modulokat — mint a **program/aktivitás ajánlások, automatikus útiterv-generálás, foglalási orkesztráció és B2C direkt értékesítés** — stratégiai irányként kezeljük, és kizárólag validálás és priorizálás után vezetjük be őket.

---

## 🔗 Strategic Relationships (Stratégiai Kapcsolatok)

Erre a stratégiai csomópontra minden releváns termékdöntésnek, architektúra-döntésnek (ADR) és jövőbeli ütemtervnek (roadmap) hivatkoznia kell.

Amikor egy javasolt funkció vagy architekturális döntés ütközik a jelenlegi stratégiával, a konfliktust nyíltan és explicite fel kell tárni.

> **Ökölszabály:** A stratégia a projekt **"miértje és hovája"** (*why & where*); a terméktudás és az ADR-ek határozzák meg a **"mit és hogyant"** (*what & how*).

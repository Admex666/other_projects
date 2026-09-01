---
id: guided-progressive-decision-flow
title: Vezérelt Progresszív Döntési Folyamat (Zero Analysis-Paralysis)
type: concept
category: concepts
tags:
  - ux
  - decision-support
  - progressive-disclosure
  - ahp
  - promethee
relationships:
  part_of: "[[optivoya-strategy]]"
  used_by: "[[master-planner-wizard]]"
  implements: "[[ahp-weighting]]"
  related_to: "[[promethee-ranking]]"
---

# Vezérelt Progresszív Döntési Folyamat (Zero Analysis-Paralysis)


## 🎯 Cél és Alapelv

Az Optivoya alapvető küldetése, hogy **megkönnyítse és felgyorsítsa az utazási döntéseket**, megszüntetve a manuális kutatás és a több tucat nyitott böngészőlap okozta kimerültséget.

> **Alapelv (Zero Analysis-Paralysis):**  
> A felhasználó sosem szembesülhet kognitív túlterheléssel, végtelen egyidejű űrlapmezővel vagy szakzsargonnal. Mindig egyetlen egyértelmű, fókuszált következő lépésnek kell lennie a folyamatban.

---

## 🛠️ Megvalósítási Pillérek

### 1. Fokozatos Feloldás (Progressive Disclosure)
- A döntési modulokban a kérdések és szituációk szekvenciálisan nyílnak meg.
- A következő szituáció (pl. hőmérséklet vagy menetidő) zárolva marad (`opacity: 0.45; pointer-events: none;`) mindaddig, amíg a felhasználó nem válaszol az aktuális kérdésre.
- Ez megelőzi a döntési bénultságot és tiszta, lépésről lépésre vezetett fókuszt biztosít.

### 2. Életszerű Döntési Helyzetek (A & B Kártyák)
- A matematikai függvénytípusok (Type 1–5, kvázi, lineáris, $q, p$) helyett **emberi döntési szituációk** közül választ a felhasználó:
  - 🟢 **A) Kártya (Toleráns)**: *„Egy kisebb különbség még nem számít, de egy bizonyos összeg/idő felett már egyértelműen a jobbik opció kell.”*
  - 🔵 **B) Kártya (Szigorúan lineáris)**: *„Nálam már a legelső forint vagy perc előny is azonnal számít.”*

### 3. Kiemelt Behelyettesítős Mondat (Fill-in-the-Blank)
- A kiválasztott szituáció alatt egy közvetlen léptetőgombokkal (`−` / `+`) ellátott, életszerű mondat jelenik meg, ahol a felhasználó a saját tűréshatárait állítja be.

### 4. Százalékmentes AHP Skála
- A páros összehasonlítások alatt nincsenek zavaró számok és százalékok.
- Csak természetes magyar kifejezések szerepelnek (*„Sokkal inkább”*, *„Kifejezetten inkább”*, *„Egyformán fontos”*).
- A számított súlyszázalékok kizárólag a folyamat legvégén, az összefoglaló kártyán jelennek meg.

### 5. Stepper Lépés-feloldás & Állapotmegőrzés (Step Access Control & State Preservation)
- **Feltételes Lépéselérés (`canAccessStep`):**
  - `0. Preferenciák`: Mindig elérhető.
  - `1. Célállomás`: Csak akkor nyitható, ha lefutott a célállomás-keresés.
  - `2. Járat`: Csak akkor nyitható, ha van kiválasztott célállomás és járatlista.
  - `3. Szállás`: Csak akkor nyitható, ha a járat kiválasztása megtörtént.
  - `4. Kész Terv`: Csak akkor nyitható, ha a szállás is kiválasztásra került.
  - A még fel nem oldott lépések nem kattinthatók (`disabled`, `opacity: 0.45; cursor: not-allowed`).
- **Kétirányú Módosíthatóság & Állapotérvénytelenítés (State Invalidation):**
  - Korábbi lépésre visszalépve az addigi találati lista és a szűrők **változatlanul láthatók**.
  - Bármelyik lépésen választott új opció (pl. új célállomás vagy más járat) azonnal érvényteleníti a későbbi részeredményeket, és a friss választás paramétereivel automatikusan újratölti a rákövetkező lépést.


---

## 🔗 Kapcsolódó Rendszerek

- **Stratégiai kontextus**: `[[optivoya-strategy]]`
- **Fő tervezési folyamat**: `[[master-planner-wizard]]`
- **Matematikai rangsoroló motorok**: `[[ahp-weighting]]`, `[[promethee-ranking]]`


---
id: advisor-proposal-versioning
type: system
name: Advisor Proposal Versioning & Snapshot Engine
status: active

description: Az Optivoya B2B Advisor Workspace immutábilis ajánlati pillanatfelvétel (Proposal Snapshot), elágaztatott verziótörténeti (v1, v2, v3) és re-optimalizálási modellje.

source:
  type: code
  ref: app.services.proposal_service

code:
  - app/services/proposal_service.py
  - app/services/proposal_renderer.py
  - app/services/timeline_reoptimization_service.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[proposal-generation]]"
  - "[[advisor-security-and-multitenancy]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 📑 Advisor Proposal Versioning & Snapshot Engine

Ez a dokumentum specifikálja az **Optivoya Advisor Workspace** ajánlatkészítési, immutábilis pillanatfelvétel-kezelési és verziótörténeti motorját.

---

## 1. Immutábilis Ajánlati Pillanatfelvétel (Immutable Snapshot)

Amikor egy tanácsadó létrehoz egy ajánlatot (`v1`), a rendszer **nem hivatkozásokkal tárolja az opciókat**, hanem teljes, mély másolatot (deep copy snapshot) készít:
- Az ajánlatban szereplő árak, járatok, hotelek és leírások rögzülnek az adott időpontban.
- Ha a háttérben új kutatás indul vagy megváltoznak az API árak, az elküldött `v1` ajánlat tartalma **változatlan marad**.

---

## 2. Elágaztatott Verziótörténet (Branching Versioning)

```text
[Proposal v1] (3 opció: Best Overall, Best Value, Best Experience)
      │
      ▼ Ügyfél visszajelzés: "Túl drága a repülő, nézzünk alternatívát"
[Proposal v2] (Módosított járatok + átszállási opciók, v1 megőrizve)
      │
      ▼ Ügyfél visszajelzés: "Kérjünk tengerre néző szobát"
[Proposal v3] (Prémium szobakategória rögzítve)
```

- Minden verzióhoz rögzíthető a **módosítás oka** (`reason`), ami bekerül az idővonalba.
- Az Advisor bármikor visszanézheti vagy összehasonlíthatja a korábbi verziókat.

---

## 3. Nyomtatási és Export Formátumok

- **A4 Print-Ready HTML/PDF**: Kifejezetten nyomtatási margókra és PDF-konverzióra optimalizált stíluslap ([proposal_print.html](file:///e:/Data/other_projects/dreamtrip/templates/advisor/proposal_print.html)).
- **Ügynökségi Arculat (Branding)**: Logó, cégnév, elérhetőségek és hivatalos lábléc automatikus beillesztése.

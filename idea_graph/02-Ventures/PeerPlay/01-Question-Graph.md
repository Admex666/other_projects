---
type: venture_question_graph
venture: PeerPlay
status: mapped_prompt_01
date: 2026-11-17
opportunity_doc: "[[02-Ventures/PeerPlay/00-Opportunity]]"
assumptions_doc: "[[02-Ventures/PeerPlay/02-Assumptions]]"
---

# PeerPlay — Alkalmazott Hierarchikus Kérdésgráf (Q-001 – Q-706)

Ez a kérdésgráf a Prompt 01 mélyelemzéséből született, részletes kutatási specifikációval.

---

## 1. Vizuális Struktúra (Mermaid)

```mermaid
graph TD
    %% Központi Kérdés
    Q000["Q-000: Érdemes a PeerPlay-ből önálló, skálázható venture-t építeni?"]

    %% 6 Főág
    Q001["Q-001: Létezik eléggé sürgető és fizetőképes vevői probléma?"]
    Q002["Q-002: Elég vonzó és elérhető a célpiac (HU / CEE)?"]
    Q003["Q-003: Valóban hiteles és akcióképes értéket nyújt a szimuláció + ONA?"]
    Q004["Q-004: Megvédhető-e a differenciáció a trénerekkel és ONA szoftverekkel szemben?"]
    Q005["Q-005: Képes-e a modell vonzó pénzügyi mutatókat (margins, LTV) termelni?"]
    Q006["Q-006: Képes-e a szolgáltatás az alapítón túl skálázódni?"]

    %% Keresztmetszeti és Invalidáló kérdések
    Q701["Q-701: A játékbeli viselkedés érvényesen leképezi a valós munkahelyi kapcsolatokat?"]
    Q702["Q-702: A tranzakciós napló alkalmas valódi kommunikációs ONA mérésére?"]
    Q703["Q-703: Megoldható-e a nevesített mérés jogszerűen (GDPR) és a bizalom megtartásával?"]
    Q706["Q-706: Más facilitátorok képesek-e azonos minőségű adatot és élményt hozni?"]

    Q000 --> Q001
    Q000 --> Q002
    Q000 --> Q003
    Q000 --> Q004
    Q000 --> Q005
    Q000 --> Q006

    Q003 --> Q701
    Q003 --> Q702
    Q001 --> Q703
    Q006 --> Q706

    %% Döntési Kapuk (Invalidációs pontok)
    Q001 -.->|Ha nincs fizetési hajlandóság| STOP1["STOP / PIVOT (Nincs piac)"]
    Q701 -.->|Ha a játék nem mutatja a valóságot| STOP2["PIVOT (Csak élményjáték, nem diagnosztika)"]
    Q703 -.->|Ha a munkajog/GDPR tiltja a nevesítést| STOP3["PIVOT (Csak aggregált csoportszintű riport)"]
    Q706 -.->|Ha nem tanítható be külsős tréner| STOP4["BOUTIQUE CONSULTING (Nem skálázható venture)"]
```

---

## 2. A 6 Kutatási Terület Mappája & Kérdéskódjai

* 🧑‍💼 **Customer & Problem (`Research/Customer.md`):** [[02-Ventures/PeerPlay/Research/Customer]]  
  *Kérdések:* `Q-101` – `Q-106` (Ki a büdzséfelelős? Milyen gyakori a probléma? Miért nem jó az ivászat?)
* 📈 **Market Intelligence (`Research/Market.md`):** [[02-Ventures/PeerPlay/Research/Market]]  
  *Kérdések:* `Q-201` – `Q-205` (TAM/SAM/SOM Magyarországon és CEE-ben a 150-500 fős szegmensben, tréning büdzsék)
* 🔬 **Solution & Validity (`Research/Execution.md`):** [[02-Ventures/PeerPlay/Research/Execution]]  
  *Kérdések:* `Q-301` – `Q-307` és `Q-701`, `Q-702`, `Q-705` (Módszertani és ONA validitás, Δ Energia mérés)
* ⚔️ **Competition & Moat (`Research/Competition.md`):** [[02-Ventures/PeerPlay/Research/Competition]]  
  *Kérdések:* `Q-401` – `Q-405` (Csapatépítők vs. Polinode/Worklytics szoftverek vs. OD tanácsadók)
* 💰 **Business Model & Unit Economics (`Research/Business-Model.md` & `Financial.md`):** [[02-Ventures/PeerPlay/Research/Business-Model]] & [[02-Ventures/PeerPlay/Research/Financial]]  
  *Kérdések:* `Q-501` – `Q-507` (400-600k Ft árrése, workshop költség, ismétlődő diagnosztika / Retention)
* ⚖️ **Execution, Scalability & GDPR (`Research/Execution.md`):** [[02-Ventures/PeerPlay/Research/Execution]]  
  *Kérdések:* `Q-601` – `Q-606`, `Q-703`, `Q-706` (Facilitátor hálózat betanítása, GDPR/DPIA adatvédelem)

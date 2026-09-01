---
id: project-graph
aliases:
  - PROJECT_GRAPH
  - AI_NATIVE_GRAPH
type: governance
name: AI-Native Project Graph & Multi-Graph Architecture
status: active

description: A több rétegű projektgráf (Knowledge, Governance, System, Code/File, Data) felépítése, automata indexelése, és navigációs szabályai.

related:
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[ARCHITECTURE_RULES]]"
  - "[[CODE_QUALITY]]"
  - "[[QUALITY_GATES]]"
---

# 🌐 AI-Native Project Graph Governance

## 53. AI-Native Project Graph

A projektet több összefüggő, de eltérő jellegű gráf szövetségeként kell értelmezni:

```text
KNOWLEDGE GRAPH
    Concepts
    Entities
    Processes
    Metrics
    Decisions

        +
        
GOVERNANCE GRAPH
    Principles
    Rules
    Constraints
    Quality Requirements

        +

SYSTEM GRAPH
    Applications
    Services
    Modules
    APIs
    Infrastructure

        +

CODE / FILE GRAPH
    Directories
    Files
    Symbols
    Imports
    Dependencies

        +

DATA GRAPH
    Databases
    APIs
    Files
    Transformations
    Derived Metrics
```

Ezek együtt alkotják a **Project Graph**-ot:

```text
                     PROJECT
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
   KNOWLEDGE         GOVERNANCE        SYSTEMS
        │               │                │
        └───────────────┼────────────────┘
                        │
                        ▼
                 IMPLEMENTATION
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
            CODE      FILES      DATA
              │         │         │
              └─────────┼─────────┘
                        │
                        ▼
                  PROJECT GRAPH
```

A Project Graph célja, hogy emberek és AI ágensek azonnal megválaszolhassák:
* *Mi ez?*
* *Miért létezik?*
* *Mihez kapcsolódik?*
* *Mi függ tőle?*
* *Milyen szabályok vonatkoznak rá?*
* *Hol van implementálva?*
* *Mely fájlok érintettek?*
* *Honnan származnak az adatai?*
* *Mi változik meg, ha módosítjuk?*

---

## 54. Not Every File Is a Knowledge Node

Szigorú megkülönböztetés érvényes: **Egy forrásfájl nem automatikusan knowledge node.**

Példa:
* `Flight` / `Destination` → Domain fogalom (Knowledge Node)
* `app/services/kiwi_flight_service.py` → Implementációs műtermék (Implementation Node)

```text
SEMANTIC NODE
Flight, Destination, Accommodation, Decision DNA

        ↓ implemented by

IMPLEMENTATION NODE
Module, Directory, File, Class, Function, Script, Config, DB Table, API
```

Ez megelőzi, hogy a szemantikai tudásréteget elárasszák az alacsony szintű forráskód-fájlok ezrei.

---

## 55. Automatic Code and File Graph

A projektnek automatikusan kell indexelnie az implementációs műtermékeket, ahol praktikus (Python, JS, HTML, CSS, YAML, JSON, Markdown).

A generált gráf tartalmazza:
* `Directory` *contains* `File`
* `File` *imports* `File`
* `File` *defines* `Symbol`
* `Function` *calls* `Function`
* `File` *reads* `Configuration`
* `File` *writes* `Data`
* `File` *references* `API`

Ezeket a kapcsolatokat a kódkészletből automatikusan kell kinyerni. Nem tartunk karban manuálisan olyan relációkat, amik megbízhatóan levezethetők a kódból.

---

## 56. Semantic Relationships vs Automatic Relationships

A Project Graph két alapvetően különböző kapcsolattípust tartalmaz:

### Automata Kapcsolatok (Mechanikusan Levezethető)
* `imports`, `calls`, `defines`, `extends`, `contains`, `references`, `reads`, `writes`, `uses API`, `uses configuration`

### Szemantikai Kapcsolatok (Értelmezést Igénylő)
* `implements`, `governed_by`, `supports`, `belongs_to`, `responsible_for`, `source_of_truth_for`, `related_to`, `strategically_relevant_to`

A szemantikai kapcsolatokat csak akkor deklaráljuk expliciten, ha valós navigációs értéket nyújtanak.

---

## 57. Project Catalog (Opcionális Réteg)

A projekt katalógus választ ad a kérdésre:
> *Melyek a projekt legfőbb építőkövei és hol találhatók?*

**Fontos irányelv:** A `catalog/` réteg **opcionális**, nem kötelező minden projektben. Kis és közepes projektekben elegendő a `knowledge/`, `governance/`, `work/` és a `PROJECT_MAP.md`. A `catalog/` akkor jelenik meg, ha annyi modul, rendszer és mikroszerviz van, hogy a Project Map és a Knowledge Graph már nem elég az eligazodáshoz.

Struktúra igény esetén:
```text
catalog/
├── INDEX.md
├── systems/
├── modules/
└── services/
```

---

## 58. Module and Directory Identity

A fontosabb moduloknak és könyvtáraknak világos identitással kell rendelkezniük. Ha egy modul célja komplex vagy nem magától értetődő, használható egy rövid `MODULE.md` összefoglaló:
* Modul célja
* Mit implementál (`[[flight]]`, `[[kiwi-scraper]]`)
* Felelősségi körök
* Függőségek
* Vonatkozó governance (`[[ARCHITECTURE_RULES]]`)

Ne hozzunk létre dokumentációs fájlt minden apró mappában; csak a jelentős moduloknál indokolt.

---

## 59. File Purpose Metadata

Egyedi forrásfájlokhoz csak kivételes esetekben szükséges kézi leírás: ha a fájl belépési pont, nem nyilvánvaló a szerepe, több rendszert köt össze, vagy építészetileg kritikus.
A kódstruktúra és az automata indexelés a fájlok 95%-át önmagában megmagyarázza.

---

## 60. Machine-Readable Project Graph Index

A projekt fenntarthat egy gépileg olvasható indexet:
```text
.project/
└── graph/
    ├── project_graph.json
    ├── nodes.json
    ├── edges.json
    └── metadata.json
```
Ez reprodukálható, bármikor újraépíthető a forrásfájlokból, és sosem minősül elsődleges igazságforrásnak.

---

## 61. Graph Node & Edge Model

### Csomópont Típusok (Nodes)
* `knowledge_node`, `governance_node`, `work_item`, `system`, `module`, `directory`, `file`, `symbol`, `function`, `class`, `config`, `database`, `api`, `operation`

### Élek (Edges)
* `implements` / `implemented_by`
* `contains` / `part_of`
* `imports` / `calls` / `defines`
* `depends_on` / `used_by`
* `reads` / `writes`
* `governed_by`
* `replaces` / `supersedes`

---

## 62. Graph Indexing Pipeline & AI Navigation

A folyamat lefutása:
```text
PROJECT FILES → MARKDOWN PARSER (Wikilinks, YAML) → CODE ANALYZER (Imports, AST) → CONFIG/DATA ANALYZER → PROJECT GRAPH JSON
```

Az AI ágenseknek **nem kell a teljes gráfot betölteniük a kontextusba**. Célzott részgráf-lekérdezéseket végeznek (pl. *"Mely fájlok valósítják meg a Decision DNA modult és milyen szabályok vonatkoznak rájuk?"*).

---

## 63. Project Map & Portable Mermaid Views

A projekt ember által könnyen áttekinthető térképpel rendelkezik: `PROJECT_MAP.md`.
A gráfból generálható Mermaid diagramok (`project-graphs/`) vizuális nézetként szolgálnak, nem alternatív igazságforrásként.

---

## 64. Navigáció Két Irányban & Hatáselemzés

A Project Graph lehetővé teszi:
1. **Szemantika → Kód:** `[[kiwi-scraper]]` → `app/services/kiwi_flight_service.py`
2. **Kód → Szemantika:** `app/services/kiwi_flight_service.py` → `[[flight]]`, `[[kiwi-scraper]]`, `[[ARCHITECTURE_RULES]]`
3. **Módosítás előtti hatáselemzés:** Megmutatja, milyen más modulok vagy szabályok érintettek, mielőtt kódot írnánk.

---

## 65. Project Graph Tervezési Alapelvek

1. **Meaning Before Files:** Értsd meg a fogalmat, mielőtt a fájlokban keresgélsz.
2. **Files Before Full Repository Search:** Használd a gráfot a célzott fájlok megtalálásához ahelyett, hogy az egész repót végigszkennelnéd.
3. **Automatic Before Manual:** Ahol lehetséges, a gép kösse össze az importokat és hívásokat.
4. **Intent Before Metadata Volume:** Csak azt dokumentáld kézzel, amit a kód nem tud kifejezni.
5. **Subgraph Before Full Graph:** Mindig a legkisebb elégséges részgráfot töltsd be a kontextusba.
6. **No Enterprise Bureaucracy:** Fokozatosan növekvő, rugalmas AI-native operációs modellt építünk, felesleges bürokrácia nélkül.

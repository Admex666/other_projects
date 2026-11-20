# 🎯 ADR 0003: Fluvia Radar Termékmárka, Színpaletta és Aszinkron Validációs Tölcsér

> **Státusz:** Elfogadva (Accepted)  
> **Dátum:** 2026-11-20  
> **Döntéshozó:** Alapító & Orchestrator  
> **Kapcsolódó dokumentumok:** [0001_mvp_pivot_trading_game_v2.md](file:///E:/Data/other_projects/PeerPlay/knowledge/decisions/0001_mvp_pivot_trading_game_v2.md), [b2b_validation_playbook.md](file:///E:/Data/other_projects/PeerPlay/knowledge/learnings/b2b_validation_playbook.md), [07-Master-Execution-Blueprint.md](file:///E:/Data/other_projects/idea_graph/02-Ventures/PeerPlay/07-Master-Execution-Blueprint.md)

---

## 1. Kontextus és Problémafelvetés

A B2B outreach és validációs folyamat során világossá vált:
1. **Márkaidentitás hiánya:** A korábbi PeerPlay elnevezés mellett hiányzott egy professzionális, B2B enterprise hangulatú ernyőmárka és terméknév.
2. **Túlzó állítások a vezetői riportban:** A korábbi minta PDF virtuális „mennyi értéket termeltünk” dollárhegyei hiteltelenítették a diagnosztikát a komoly C-level döntéshozók előtt.
3. **Hiányzó hálózati vizualizáció:** A hálózati térkép statikus helykitöltő volt ahelyett, hogy valós, tiszta ONA (Organizational Network Analysis) gráfként azonnal szemléltetné a részlegek közötti silókat.
4. **Validációs kapuk hiánya:** A fejlesztés és a piacfelmérés nem kapcsolódott formális, bináris STOP/GO döntési mechanizmushoz.

---

## 2. A Döntés

### 2.1. Termékmárka és Arculat: Fluvia Radar
- **Ernyőcég:** Fluvia Systems (`fluvia.systems@gmail.com`). A név a latin *fluvius* (áramlás, folyamatfolytonosság) szóból ered.
- **Terméknév:** **Fluvia Radar** (Organizational Network Analysis & Szervezeti Röntgen).
- **Hivatalos színpaletta:**
  - **Sötét smaragd / erdőzöld:** `#0d4638` (fejlécek, főcímek, sötét kártyák)
  - **Élénk világoszöld:** `#61f27e` (kiemelések, akcentusok, státusz indikátorok)
  - **Ezüstös szürke:** `#86949f` (finom határolók, táblázat feliratok, metaadatok)
  - **Világos vászon:** `#F8FAFC` és tiszta fehér `#FFFFFF`.
- **Logó:** A hivatalos Fluvia logó (`public/images/fluvia_logo.png`).

### 2.2. Tényszerű Vezetői Diagnosztika (Zéró Túlzás)
A riportban kizárólag objektív, mérhető szervezeti jelenségek szerepelnek:
1. **Siló detekció:** 0 tranzakciós kapcsolat a Termelés és a K+F között, szaggatott piros vonallal és szűk keresztmetszet elemzéssel.
2. **Informális közvetítők (Brokerek):** 100%-os konszenzussal azonosított kulcsemberek idézetekkel és hálózati funkcióval.
3. **Reakcióidő és energiamozgás:** Számszerűsített energiaszint (&Delta; +1.75 pont) és szerződéskötési sebesség.

### 2.3. Aszinkron Validációs Tölcsér & STOP / GO Kapuk
A [07-Master-Execution-Blueprint.md](file:///E:/Data/other_projects/idea_graph/02-Ventures/PeerPlay/07-Master-Execution-Blueprint.md) alapján 14 napos tölcsér:
- **1. Lépés:** 40 hideg megkeresés kemény tárggyal és felnőtt CTA-val.
- **2. Lépés:** Visszaíróknak (15–20% ~ 6–8 cég) azonnal 2 oldalas Fluvia Radar PDF + 3 perces Loom videó link.
- **3. Lépés:** 3 kérdéses mini-űrlap (létszám, osztályok, célhónap).
- **Döntési Kapuk (14. nap):**
  - **STOP / PIVOT:** Ha < 2 cég jelölt csapatot -> Piac nem vevő, azonnali leállás (0 óra hívásveszteség, 0 Ft veszteség).
  - **PROCEED TO BUILD (GO):** Ha >= 2–3 cég regisztrált konkrét csapattal -> Zárt pilot és termékélesítés indul.

---

## 3. Következmények és Állapot

- **PDF Riport:** [Fluvia_Radar_Vezetoi_Mintariport_DEMO01.pdf](file:///E:/Data/other_projects/PeerPlay/public/Fluvia_Radar_Vezetoi_Mintariport_DEMO01.pdf) (1.54 MB, pontosan 2 oldal, nagy felbontású ONA gráffal).
- **Master Suite Felület:** [b2b_validation_suite.html](file:///E:/Data/other_projects/PeerPlay/public/b2b_validation_suite.html) (5 füllel, Fluvia stílussal, interaktív STOP/GO tölcsérrel).
- **Lead Pipeline:** [data/fluvia_radar_outreach_targets.csv](file:///E:/Data/other_projects/PeerPlay/data/fluvia_radar_outreach_targets.csv) (35 magyar cég, 63 validált döntéshozó).
- **Minőségbiztosítás:** `qa-validator` által 100% PASSED minősítéssel ellátva.

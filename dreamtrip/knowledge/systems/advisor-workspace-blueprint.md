---
id: advisor-workspace-blueprint
type: system
name: Optivoya Advisor Workspace Blueprint & Architecture Specification
status: active

description: Az Optivoya B2B Travel Advisor Workspace v1 teljes, átfogó rendszerspecifikációja (Master Architecture Blueprint). Részletezi a termékstratégiát, a 84 specifikációs pontot, a Shared Intelligence réteget, a hard/soft megkötéseket, a 9 kutatási stratégiát, a providencia modellt, a 3-opciós döntési architektúrát, a relatív összehasonlító motort, a feltétel-enyhítési motort, a hibatűrést és az ügyfélajánlat generálást.

source:
  type: code
  ref: app.services.advisor_orchestration_service

code:
  - app/routers/advisor_api.py
  - app/services/advisor_orchestration_service.py
  - app/services/multi_option_engine.py
  - app/services/constraint_relaxation_service.py
  - app/services/verification_service.py
  - app/services/trip_risk_service.py
  - app/services/preference_resolver.py
  - templates/advisor/advisor_workspace.html
  - static/js/advisor/advisor_app.js
  - static/js/advisor/advisor_state.js
  - static/js/advisor/advisor_research.js
  - static/js/advisor/advisor_option_compare.js
  - static/js/advisor/advisor_proposal.js

related:
  - "[[trip-case]]"
  - "[[master-planner-blueprint]]"
  - "[[fastapi-backend]]"
  - "[[supabase-database]]"
  - "[[proposal-generation]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
  - "[[QUALITY_GATES]]"
  - "[[DEFINITION_OF_DONE]]"

used_by:
  - "[[fastapi-backend]]"
---

# Optivoya Advisor Workspace v1 Blueprint

## 1. Termékstratégia & Két Külön Termékélmény
Az Optivoya két külön UX-et biztosít egyetlen közös `Shared Intelligence Layer`-en:
- `/` és `/planner`: **B2C Personal Travel Planner** (lineáris 5-lépéses varázsló).
- `/advisor`: **B2B Advisor Workspace** (Clients $\rightarrow$ Trip Cases $\rightarrow$ Briefs $\rightarrow$ Research $\rightarrow$ 3 Options $\rightarrow$ Comparison $\rightarrow$ Proposal $\rightarrow$ Revisions).

```text
B2C Planner ─────┐
                 ├── Shared Intelligence Layer (AHP, PROMETHEE, Kiwi, Cozy, Meteo, Numbeo, OSM)
Advisor ─────────┘
```

## 2. Core Value Proposition & KPI
- **Elsődleges mérőszám:** *Research Time Saved / Case* (120+ percről <60 percre csökkentve).
- **Értékígéret:** *"Turn a client brief into 3 strong travel options in minutes."*

## 3. Hard vs. Soft Constraint Modell & Költségvetés
- **Hard Constraints:** Szigorú korlátok (költségkeret felső határa, kötelező közvetlen járat, min. 4★ hotel).
- **Soft Preferences:** Súlyozott vágyak (pl. jobb étkezési kultúra preferálása a stranddal szemben).
- **Avoid Rules:** Kifejezetten kizárt elemek (pl. hajnali indulás kerülése).
- **Nice-to-Have:** Opcionális előnyök (pl. wellness/medence).
- **Advisor Overrides:** Tanácsadói manuális felülírások és rögzítések.
- **Költségvetési Módok:**
  - *Mode A:* Teljes utazási költségkeret.
  - *Mode B:* Komponens keretek (járat, szállás, program, transzfer).
  - *Mode C:* Keresési hatókör (Search Scope: tetszőleges komponens-kombináció).

## 4. A 9 Tanácsadói Kutatási Stratégia (Research Workflows)
1. **Destination Discovery:** 45+ célállomás többkritériumos szűrése $\rightarrow$ jelöltek $\rightarrow$ járatok $\rightarrow$ szállások.
2. **Known Destination Research:** Konkrét célállomás mély, több-szállásos és járatos kutatása.
3. **Flight-First Strategy:** Kedvező repülőjegyek felkutatása $\rightarrow$ kapcsolódó csomagok felépítése.
4. **Stay-First Strategy:** Kiemelt szállodák köré épített logisztika és programok.
5. **Full-Trip Optimization:** Teljes csomag párhuzamos matematikai optimalizációja.
6. **Component-Only Research:** Kizárólag repülőjegy vagy kizárólag szálláskeresés adott költségkeretre.
7. **Mixed-Scope Research:** Több város párhuzamos összehasonlítása csak repülő+hotel komponensekre.
8. **Re-Optimization Workflow:** Meglévő eset újraszámolása módosított feltétellel az adatok megőrzésével.
9. **Find Better Workflow:** Egy kiválasztott opció célzott finomhangolása (olcsóbb ár, kényelmesebb járat, jobb hotel).

## 5. Adat-Eredet (Provenance) & Hibatűrés (Resilience)
- **Provenance Modell:** Minden külső elemhez forrás (`source`), szolgáltató (`provider`), lekérés ideje (`checked_at`), lejárati TTL (`expires_at`), hitelesítési státusz (`verification_status`) és nyers referencia tartozik.
- **Resilience Réteg:** Kiwi timeout, Cozycozy részleges eredmények vagy Open-Meteo kiesés esetén a rendszer nem omlik össze, hanem transzparens becsült/stale-cache jelöléssel ad részleges eredményt.

## 6. Döntési Architektúra & Archetípusok
- **3 Opciós Csomag:**
  - *Option A — Best Overall:* Legjobb összesített illeszkedés.
  - *Option B — Best Value:* Költséghatékony, magas ár-érték arány.
  - *Option C — Best Experience:* Maximális élmény- és stílusilleszkedés.
- **Side-by-Side Comparison & Why This Option?:** Adatvezérelt előny/hátrány magyarázatok és relatív különbségek mátrixa.
- **Constraint Relaxation Engine:** 0 találat esetén strukturált ok-okozati diagnózis és 1-kattintásos enyhítési javaslatok (pl. +€40 budget $\rightarrow$ 7 opció).
- **Multi-Option Proposal:** 1–3 opciós ügyfélajánlat szerkesztő, verziókezelés (v1, v2, v3) és nyomtatás/PDF export.

## 7. Dizájnrendszer, Anti-AI-Slop & Minőségbiztosítás
- **Brand & Színvilág (`[[DESIGN_SYSTEM]]`):** Mély fenyőzöld (`--primary: #003710`), Chartreuse akcentus (`--secondary-container: #a7f540`), hivatalos Optivoya logó (`/static/logo.png`).
- **Anti-AI-Slop Invariánsok (`[[ANTI_AI_SLOP_POLICY]]`):** 0% generikus kék/lila neon gradient, 0% emoji-spam, 0% buzzword, funkcionális Material 3 felületi rétegződés.
- **Tipográfiai Hierarchia:** Plus Jakarta Sans (főcímek), Inter (szövegek/gombok), JetBrains Mono (pénzügyi és menetrendi adatok).
- **UX & Plain Language (`[[UX_PRINCIPLES]]`):** 4 valódi állapot (Empty, Loading, Error, Success), kognitív terhelés minimalizálása, szakzsargon mellőzése a felületen.
- **Minőségi Kapuk (`[[QUALITY_GATES]]`, `[[DEFINITION_OF_DONE]]`):** Minden fázis automatizált tesztekkel és 100%-os tudásgráf validációval zárul.


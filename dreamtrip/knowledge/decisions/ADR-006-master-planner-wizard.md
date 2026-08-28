---
id: ADR-006
type: decision
name: "ADR-006: Master Travel Planner Unified Wizard"
status: active
date: 2026-08-28

supersedes: null

related:
  - "[[unified-trip-model]]"
  - "[[master-planner-wizard]]"
  - "[[destination-matching]]"
  - "[[flight-intelligence-workflow]]"
  - "[[accommodation-search-workflow]]"
  - "[[cozycozy-scraper]]"
  - "[[ahp-weighting]]"
  - "[[promethee-ranking]]"
---

# Decision

Létrehoztunk egyetlen összefogó **Master Travel Planner (`/planner`)** folyamatot, amely az elején bekéri az összes felhasználói preferenciát, rugalmas 3-módú dátumkezelést (Flatpickr naptárral), szabad szöveges Kiwi repülőtér-keresést, valamint modális desztináció- és szállásprioritási kérdőíveket biztosít. A lépések között automatikusan végzi a járat- és Cozycozy szálláskeresést manuális űrlapkitöltések nélkül.

# Context

A felhasználónak korábban külön-külön kellett elindítania a 3 modult és manuálisan átmásolnia a paramétereket. A v2 Master Planner:
1. Központi Kiwi autocomplete motorral és saját kör alakú `+`/`−` léptetőkkel illeszkedik a design rendszerbe.
2. Felugró modális prioritásvarázslóval határozza meg a desztináció- és szállássúlyokat emberközeli, szakzsargontól mentes felülettel.
3. 3 dátumkezelési módot támogat (Rugalmas hónap 1–30+ napig, Időintervallum, Pontos dátumok Flatpickr naptárral).
4. Automatikusan továbbítja és zárolja a járatdátumokat a Cozycozy szálláskereséshez (`get_all_stays` / `parse_accommodation_results`).

# Consequences

* 50%-kal gyorsabb utazástervezési folyamat és zéró redundáns adatbevitel.
* Determinisztikus, matematikai többkritériumos döntéstámogatás felhasználóbarát köntösben.
* Inline módosítási lehetőség minden fázisban.

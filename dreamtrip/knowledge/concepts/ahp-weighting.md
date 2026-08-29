---
id: ahp-weighting
type: concept
name: Analytic Hierarchy Process (AHP)
status: active

description: Döntéselméleti matematikai eljárás, amely páros összehasonlító mátrixok sajátvektor-számításával állítja elő a felhasználói kritériumok súlyait.

source:
  type: code
  ref: app.services.scoring_service

code:
  - app/services/scoring_service.py
  - templates/flights/flight_filter.html

related:
  - "[[promethee-ranking]]"
  - "[[flight-intelligence-workflow]]"
  - "[[destination-matching]]"

used_by:
  - "[[fastapi-backend]]"
---

## 3-Pilléres Célállomás Döntési Modell (Master Planner & Destination Matcher)

A redundáns pénz-pénz (repülőjegy vs. napi étkezés) párosítások elkerülésére a célállomás-szintű AHP 3 független, nem átfedő pillérre épül:
1. **💰 Teljes Becsült Utazási Költség (`total_cost`)**: Repülőjegy + Napi megélhetés (Numbeo) + Becsült szállásköltség együttes összege.
2. **☀️ Időjárás / Klíma (`weather`)**: Célhőmérséklethez és napsütéshez való illeszkedés (Open-Meteo).
3. **🛡️ Közbiztonság (`safety`)**: Biztonsági index és utazási nyugalom (Numbeo Safety Index).

Ez mindössze **3 gyors páros kérdést** igényel ($n=3$), miközben a mikroszintű preferenciák (pl. közvetlen járat, hotelcsillag, reggeli) a saját lépéseikben érvényesülnek.

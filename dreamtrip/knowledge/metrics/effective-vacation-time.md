---
id: effective-vacation-time
type: metric
name: Effective Vacation Time
status: active

description: A célállomáson tölthető valós, hasznos nappali nyaralási órák száma, amelyet az odaút érkezési és a visszaút indulási idősávja határoz meg.

source:
  type: code
  ref: app.services.scoring_service

code:
  - app/services/scoring_service.py
  - app/services/trip_scoring_service.py
  - static/js/planner/planner_flights.js

depends_on:
  - "[[flight]]"
  - "[[promethee-ranking]]"

used_by:
  - "[[ahp-weighting]]"
  - "[[flight-intelligence-workflow]]"
  - "[[unified-trip-score]]"
  - "[[proposal-generation]]"
---

# Metric: Effective Vacation Time

A puszta naptári napok helyett az Optivoya a **helyszínen tölthető hasznos nyaralási órákat** méri:

* **Mértékegység**: Óra (óra/út).
* **Számítási elv**:
  - **Érkezési nap bónusz**: A délelőtti érkezés (pl. 09:30) lehetővé teszi egy teljes értékű első nap eltöltését (+8..+12 óra). Késő esti érkezés (pl. 23:45) esetén az első nap elveszik (0 hasznos óra).
  - **Hazaindulási nap bónusz**: Késő délutáni vagy esti visszaindulás (pl. 20:45) egy teljes extra napnyi élményt ad a desztinációban (+8..+10 óra). Kora reggeli indulás (pl. 06:15) esetén az utolsó nap teljes egészében utazási logisztikára megy el.
  - **Összesített bónusz**: Egy optimális menetrendű járatpár akár **+16–22 óra tiszta nyaralási időt** adhat egy kedvezőtlen menetrendű, de azonos napos repülőhöz képest.

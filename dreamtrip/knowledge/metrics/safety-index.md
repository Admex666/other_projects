---
id: safety-index
type: metric
name: Safety Index (Numbeo)
status: active

description: A Numbeo globális adatbázisából származó közbiztonsági index 0–100-as skálán.

source:
  type: file
  ref: data/live_numbeo_indices.json

code:
  - app/services/numbeo_service.py
  - app/services/destination_scoring_service.py

depends_on:
  - "[[numbeo-database]]"

used_by:
  - "[[destination-matching]]"
---

# Metric: Safety Index (Numbeo)

* **Skála**: 0-tól 100-ig (ahol 100 a maximális biztonság).
* **Szerepe**: A Destination Matcherben a biztonságra érzékeny utazók szűrési feltételeként és pontozási tényezőjeként működik.

---
id: promethee-phi-net
type: metric
name: PROMETHEE II Net Flow (Phi Net)
status: active

description: A PROMETHEE II algoritmus által számított nettó kiáramlási folyam érték, amely -1 és +1 (illetve normalizálva 0–100%) között mutatja az adott opció relatív dominanciáját.

source:
  type: code
  ref: app.services.scoring_service

code:
  - app/services/scoring_service.py

depends_on:
  - "[[promethee-ranking]]"
  - "[[ahp-weighting]]"

used_by:
  - "[[flight-intelligence-workflow]]"
---

# Metric: PROMETHEE II Net Flow (Phi Net)

* **Skála**: $\Phi_{net} \in [-1.0, 1.0]$.
* **UI Megjelenítés**: Relevancia százalék:
  $$\text{Relevance \%} = \frac{\Phi_{net} + 1}{2} \times 100\%$$

---
id: promethee-ranking
type: concept
name: PROMETHEE II Ranking Algorithm
status: active

description: Többkritériumos rangsorolási módszer (Preference Ranking Organization METHod for Enrichment Evaluations), amely az alternatívák közötti relatív dominanciát (Net Outranking Flow) számítja ki.

source:
  type: code
  ref: app.services.scoring_service

code:
  - app/services/scoring_service.py

related:
  - "[[ahp-weighting]]"
  - "[[promethee-phi-net]]"
  - "[[flight-intelligence-workflow]]"

used_by:
  - "[[fastapi-backend]]"
---

# Concept: PROMETHEE II Ranking Algorithm

A PROMETHEE II algoritmus a repülőjáratok és szállások többdimenziós értékelésére szolgál.

## Működése

1. **Unimodális / V-alakú preferenciafüggvények**:
   Minden kritériumhoz (ár, menetidő, átszállás, pontosság) tartozik egy közömbösségi ($q$) és preferencia ($p$) küszöb.
2. **Aggregált preferenciaindex**:
   $$\pi(a, b) = \sum_{j=1}^k w_j P_j(a, b)$$
3. **Pozitív és negatív kiáramlási folyamok**:
   $$\Phi^+(a) = \frac{1}{n-1} \sum_{x \in A} \pi(a, x), \quad \Phi^-(a) = \frac{1}{n-1} \sum_{x \in A} \pi(x, a)$$
4. **Nettó kiáramlási folyam (Net Flow, $\Phi_{net}$)**:
   $$\Phi_{net}(a) = \Phi^+(a) - \Phi^-(a)$$
   A $\Phi_{net}$ határozza meg a járatok végső rangsorát és relevancia-százalékát.

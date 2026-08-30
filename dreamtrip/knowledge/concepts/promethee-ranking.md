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

1. **Preferenciafüggvények és Küszöbök ($q, p$)**:
   Minden kritériumhoz (ár, menetidő, átszállás, tartózkodás, indulási idő) meghatározható a preferenciafüggvény típusa:
   - **Type 1 (Usual / Szigorú)**: $p=0, q=0$ (azonnali bináris dominancia)
   - **Type 2 (U-shape / Kvázifüggvény)**: $q$ alatti különbség elhanyagolható, felette azonnali 100% dominancia
   - **Type 3 (V-shape / Lineáris)**: $0$-tól $p$-ig a különbséggel arányosan nő az előny
   - **Type 4 (Level / Lépcsős)**: $q$ és $p$ között közepes (0.5), $p$ felett teljes előny
   - **Type 5 (V-shape with Indifference)**: $q$ alatt közömbös (0%), $q$ és $p$ között lineárisan emelkedő, $p$ felett teljes (100%) preferencia.
2. **Emberi nyelvű Behelyettesítős Varázsló (Fill-in-the-Blank)**:
   A felhasználó nem matematikai szakzsargonnal találkozik, hanem emberi attitűd-kártyákból választ, majd egy kiemelt mondatban közvetlenül léptetőgombokkal állítja be a saját $q$ (tűréshatár) és $p$ (döntő különbség) értékeit.
3. **Aggregált preferenciaindex**:
   $$\pi(a, b) = \sum_{j=1}^k w_j P_j(a, b)$$
4. **Pozitív és negatív kiáramlási folyamok**:
   $$\Phi^+(a) = \frac{1}{n-1} \sum_{x \in A} \pi(a, x), \quad \Phi^-(a) = \frac{1}{n-1} \sum_{x \in A} \pi(x, a)$$
5. **Nettó kiáramlási folyam (Net Flow, $\Phi_{net}$)**:
   $$\Phi_{net}(a) = \Phi^+(a) - \Phi^-(a) \in [-1.0, +1.0]$$
   A $\Phi_{net}$ határozza meg a járatok végső rangsorát és normalizált relevancia-százalékát (45%–99%).


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

# Concept: Analytic Hierarchy Process (AHP)

Az AHP lehetővé teszi, hogy a felhasználó ne absztrakt százalékokat adjon meg, hanem intuitív páros preferenciákat (pl. „Az ár 3-szor fontosabb számomra, mint az átszállások száma”).

## Matematikai Háttér

1. **Páros összehasonlítási mátrix ($A$)**:
   $$a_{ij} = \frac{1}{a_{ji}}, \quad a_{ii} = 1$$
   ahol az értékek a Saaty-féle 1–9-es skálán mozognak.
2. **Súlyvektor ($\mathbf{w}$)**:
   A normalizált geometriai átlagok vagy a mátrix domináns sajátvektora.
3. **Konzisztencia Index ($CI$) és Ráta ($CR$)**:
   Biztosítja, hogy a megadott preferenciák logikailag konzisztensek legyenek ($CR < 0.10$).

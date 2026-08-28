---
id: numbeo-cost-model
type: concept
name: Numbeo Cost of Living Model
status: active

description: A célvárosok hivatalos Numbeo adatbázisán alapuló standard fogyasztói kosár modell, amely pontos matematikai képletekkel határozza meg az étkezési és helyi utazási költségeket.

source:
  type: decision
  ref: "[[ADR-002-deterministic-numbeo-food-pricing]]"

code:
  - app/services/numbeo_service.py
  - static/js/trip_cart.js

related:
  - "[[daily-food-cost]]"
  - "[[daily-transit-cost]]"
  - "[[numbeo-database]]"
  - "[[proposal-generation]]"

used_by:
  - "[[trip-cart-engine]]"
  - "[[destination-matching]]"
---

# Concept: Numbeo Cost of Living Model

Az Optivoya elutasítja a becsült vagy hasraütésszerű költségeket. Az étkezési és helyi közlekedési költségkeret szigorú, reprodukálható Numbeo fogyasztási kosáron alapul.

## Standard Napi Kosár Képletek

### 1. Napi Étkezés (€/fő/nap):
$$\text{Food}_{\text{daily}} = 1.5 \times \text{meal\_inexpensive} + 0.5 \times \text{meal\_midrange} + 2.0 \times \text{coffee}$$
* $1.5\times$ Olcsó éttermi ebéd / street food
* $0.5\times$ Középkategóriás háromfogásos vacsora (2 főre egy teljes vacsora)
* $2.0\times$ Kávé / üdítő napközben

### 2. Napi Helyi Közlekedés (€/fő/nap):
$$\text{Transit}_{\text{daily}} = 2.0 \times \text{transport\_ticket}$$
* $2\times$ egyirányú helyi vonaljegy / metrójegy / villamosjegy naponta.

### 3. Végösszeg Kiszámítása:
$$\text{Total Food HUF} = \text{Food}_{\text{daily}} \times \text{days} \times \text{pax} \times \text{EUR\_HUF\_RATE}$$
$$\text{Total Transit HUF} = \text{Transit}_{\text{daily}} \times \text{days} \times \text{pax} \times \text{EUR\_HUF\_RATE}$$

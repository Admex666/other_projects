---
id: itinerary-optimization
type: process
name: Constraint Itinerary Optimization
status: active

description: Napi útiterv generálása nyitvatartási idők, étkezési slotok, utazási távolságok és felhasználói prioritások figyelembevételével.

source:
  type: code
  ref: app.services.itinerary_service

code:
  - app/services/itinerary_service.py
  - templates/itinerary.html

related:
  - "[[poi]]"
  - "[[google-places-service]]"

used_by:
  - "[[fastapi-backend]]"
---

# Process: Constraint Itinerary Optimization

A napi útiterv-optimalizáló motor a kiválasztott város POI elemeiből logikus napirendet állít össze:

* **Haversine távolságmátrix**: Minimalizálja a látványosságok közötti utazási időt.
* **Nyitvatartási idősávok**: Figyeli a múzeumok és attrakciók zárvatartását.
* **Étkezési slotok**: Automatikusan beilleszt ebéd és vacsora időablakokat a programok közé.
* **Lakatolható (Locked) elemek**: A felhasználó által rögzített programokat nem mozgatja el az újratervezés során.

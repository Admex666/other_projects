---
id: learning-jinja-blocks
type: learning
name: Jinja2 Template Block Inheritance for Trip Workspace
status: active

description: A lebegő kosársáv (Trip Workspace) és szkriptek megbízható betöltése Jinja2 sablonöröklődés esetén.

source:
  type: code
  ref: templates/base.html

code:
  - templates/base.html
  - static/js/trip_cart.js

related:
  - "[[trip-cart-engine]]"
  - "[[fastapi-backend]]"
---

# Learning: Jinja2 Template Block Inheritance for Trip Workspace

* A `trip_cart.js` és `trip_cart.css` fájlokat közvetlenül a `templates/base.html` alaplayoutba kell beágyazni a `{% block scripts %}` előtt.
* Ezzel garantálható, hogy minden aloldalon (Destination Matcher, Flight Intelligence, Accommodation Intelligence) a `window.TripCart` azonnal rendelkezésre áll az oldal egyedi inicializáló szkriptjei lefutásakor.

---
name: skill-jinja-template-block-inheritance
description: >-
  Use this skill when handling learning: jinja2 template block inheritance for trip workspace or related operational workflows in domain 'dreamtrip'. Synthesized from canonical operational learning: jinja-template-block-inheritance.md.
---

# Learning: Jinja2 Template Block Inheritance for Trip Workspace

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `jinja-template-block-inheritance.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
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


## Canonical Source of Truth
- Primary Reference: [jinja-template-block-inheritance.md](./references/jinja-template-block-inheritance.md)
- Original Location: `E:\Data\other_projects\dreamtrip\knowledge\learnings\jinja-template-block-inheritance.md`

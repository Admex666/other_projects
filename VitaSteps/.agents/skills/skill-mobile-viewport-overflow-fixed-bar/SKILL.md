---
name: skill-mobile-viewport-overflow-fixed-bar
description: >-
  Use this skill when handling learning: mobile viewport overflow and fixed floating bars or related operational workflows in domain 'dreamtrip'. Synthesized from canonical operational learning: mobile-viewport-overflow-fixed-bars.md.
---

# Learning: Mobile Viewport Overflow and Fixed Floating Bars

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `mobile-viewport-overflow-fixed-bars.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
---
id: learning-mobile-viewport
type: learning
name: Mobile Viewport Overflow and Fixed Floating Bars
status: active

description: A 440px-es és kisebb mobilképernyőkön tapasztalt kártyaszétcsúszások és lebegő gombok takarási problémáinak megoldása.

source:
  type: code
  ref: static/css/trip_cart.css

code:
  - static/css/trip_cart.css
  - templates/flights/flight_results.html

related:
  - "[[trip-cart-engine]]"
---

# Learning: Mobile Viewport Overflow and Fixed Floating Bars

* A mobil nézetben (pl. iPhone 16 Pro Max, 440px szélesség) a rögzített alsó lebegő sáv könnyen elfedheti az űrlapok alsó „Tovább” / keresés indítása gombjait.
* **Megoldás**:
  1. A tartalmi konténerek aljára kötelező legalább `padding-bottom: 90px;` helyközt hagyni.
  2. A lebegő sáv elrejthető (`hideBar()`), és egy kis lebegő gombbal (`showBar()`) visszanyitható, így sosem akadályozza a görgetést vagy a gombok elérését.


## Canonical Source of Truth
- Primary Reference: [mobile-viewport-overflow-fixed-bars.md](./references/mobile-viewport-overflow-fixed-bars.md)
- Original Location: `E:\Data\other_projects\dreamtrip\knowledge\learnings\mobile-viewport-overflow-fixed-bars.md`

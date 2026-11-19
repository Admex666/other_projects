---
name: skill-leaflet-print-rendering
description: >-
  Use this skill when handling learning: leaflet print & pdf aspect ratio sync or related operational workflows in domain 'vitasteps'. Synthesized from canonical operational learning: leaflet-print-rendering.md.
---

# Learning: Leaflet Print & PDF Aspect Ratio Sync

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `leaflet-print-rendering.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
---
id: leaflet-print-rendering
type: learning
name: Leaflet Print & PDF Aspect Ratio Sync
status: active
description: Solving bounding box cutoffs and tile rendering issues in print stylesheets.
code:
  - landing_predikalo1/nagykevely/kalandkonyv.html
related:
  - "[[campaign-nagykevely|Campaign Nagy-Kevely]]"
---

# Learning: Leaflet Print & PDF Aspect Ratio Sync

When generating printable 6-page adventure guidebooks (`kalandkonyv.html`):

## Problem
In browser print/PDF view, dynamic container sizing and asynchronous map tile loading caused Leaflet maps to crop GPX track extremities and POI markers.

## Solution
1. **Explicit Fixed Height:** Set map containers to exact pixel heights (e.g. `280px`) with `@media print { height: 280px !important; }`.
2. **Geographic Bounding Box Padding:** Use `map.fitBounds(polyline.getBounds().pad(0.18))` to add comfortable margin around all tracks and POI markers.
3. **Fractional Zooming:** Set `zoomSnap: 0.1` and trigger `map.invalidateSize()` inside `window.onbeforeprint`.
4. **Preventing Trailing Empty Pages:** Add `@media print { .page:last-child { page-break-after: avoid !important; } }`.


## Canonical Source of Truth
- Primary Reference: [leaflet-print-rendering.md](./references/leaflet-print-rendering.md)
- Original Location: `E:\Data\other_projects\VitaSteps\knowledge\learnings\leaflet-print-rendering.md`

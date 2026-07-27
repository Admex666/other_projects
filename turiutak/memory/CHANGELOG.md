# CHANGELOG - TuristaÚt Kalandtervező

## [2026-07-25]
### Added
- Canonical `/memory` files: `PROJECT.md`, `STATUS.md`, `DECISIONS.md`, `TASKS.md`, `ARCHITECTURE.md`, `CHANGELOG.md`.
- Implementation Plan and task checklist.
- Fully implemented HTML frontend structure `index.html`.
- Glassmorphic dark/light design system in `index.css`, including custom tooltips, green forest boundary styles, and styled map popups.
- Leaflet map logic, MTSZ REST API integrations, topographic basemap cycling, dynamic OSM Overpass API forest querying (with `out 400 geom` syntax and mirror failover), and spatial click coordinate lookup (using parallel Nominatim + Overpass is_in timeout fallback) in `app.js`.
- XML serialization helper for GPX export in `gpx-exporter.js`.
- Automatic browser-subagent validation tests demonstrating map loading, point positioning, route planning, statistics parsing, and styling correctness.
- Added support for `package.json` to enable starting the local dev server using `npm run dev`.

# PROJECT - TuristaÚt Kalandtervező

## Project Overview
**TuristaÚt Kalandtervező** (Tourist Trail Adventure Planner) is an interactive, premium web-based hiking map and route planner. It leverages the public ArcGIS REST services of `https://turistaterkepek.hu` to visualize the official Hungarian tourist trails, query their details, and calculate optimal hiking routes using elevation-aware walking metrics.

## Goals
- Provide an elegant, state-of-the-art dark-themed dashboard for hikers.
- Visualize Hungarian hiking trails dynamically on a map.
- Search and filter trails by marking symbols (e.g. blue stripe, red cross).
- Allow planning a multi-stop hiking route snapped to the official trail network.
- Display key hike statistics: distance, elevation gain/loss, and 3D walking time.
- Export planned hikes directly as GPX files for Garmin/phone GPS systems.

## Key Technologies
- **Frontend Core**: Vanilla HTML5, CSS3, ES6 JavaScript.
- **Mapping Library**: Leaflet.js with CartoDB Dark Matter tile basemap.
- **ArcGIS Integrations**: Esri Leaflet for loading MapServer and FeatureServer layers from `https://turistaterkepek.hu/server/rest/services`.
- **Styling**: Vanilla CSS with custom glassmorphism components and Outfit/Inter typography.

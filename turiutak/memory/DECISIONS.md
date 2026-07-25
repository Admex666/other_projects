# DECISIONS - TuristaÚt Kalandtervező

## 2026-07-25: Technical Stack Choices
### Leaflet & Esri Leaflet for Mapping
We chose Leaflet.js combined with the official Esri Leaflet plugin.
- **Why**: Leaflet is lightweight and fast. Esri Leaflet provides native bindings to ArcGIS MapServer, FeatureServer, and NetworkAnalysis (NAServer) without requiring the heavyweight ArcGIS Maps SDK.
- **Alternatives Considered**: MapLibre GL JS (more complex custom styling, less direct integration with ESRI Map/Feature Server layers).
- **Expected Impact**: Rapid development, direct compatibility with the target REST server, and high client-side performance.

### Vanilla HTML / CSS / JS (No Framework)
We decided to build this application using clean, modern Vanilla HTML5, CSS3, and ES6 JS.
- **Why**: Keeps page size minimal (<100KB), ensures instant loading, and satisfies the user's focus on premium UI without build tool overhead.
- **Alternatives Considered**: Vite/React (unnecessary for a highly targeted single-page map application).
- **Expected Impact**: Zero installation/build time, easy local deployment, and clear code.

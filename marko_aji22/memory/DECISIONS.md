# Decisions Log

## 2026-08-17 - Project Architecture & Foundations
- **Decision:** React + Vite + Tailwind CSS + PWA with client-side localStorage state.
  - **Reason:** Mobile-first, single-recipient target, fast iterations, works offline, no unnecessary backend/auth complexity.
- **Decision:** Modular configuration file (`questConfig.ts`) containing all customizable texts, placeholders, coordinates, options, and secrets.
  - **Reason:** The final locations, passwords, food options, and texts are undecided/placeholders and need to be easily editable without touching UI code.
- **Decision:** Built-in GPS proximity (Haversine formula), hot/cold HUD, compass bearing calculation, plus desktop testing/dev override controls.
  - **Reason:** Enables testing without walking around physically while providing a fully working mobile experience when deployed.
- **Decision:** Étterem szakasz: "BOWLING UTÁNI TÁPLÁLKOZÁSI STRATÉGIA" 4 fix opcióval (`🥗 1 — Felelős döntés`, `🍜 2 — Normális ember`, `🍔 3 — Leszarom`, `💀 4 — Holnap megbánom`), mindegyik külön célkoordinátával és integrált Radar + Iránytű navigációval.
- **Decision:** Kocsma szakasz: Radar és iránytű NÉLKÜL, kizárólag tiszta Hideg-Meleg termikus érzékelővel (hőmérséklet sáv, státusz, távolság, nyomok).

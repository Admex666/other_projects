# DreamTrip — Változási Napló (Changelog)

## [Unreleased] - 2026-08-13
### Hozzáadva / Módosítva
- **Projekt Architektúra Refaktor**: Szabványos `app/` Python csomagstruktúra kialakítása (`app/services`, `app/scrapers`, `app/models`).
- **Data & Asset Konszolidáció**: Központi `data/` és `notebooks/` mappa létrehozása.
- **Kanonikus Projekt Memória**: `/memory` mappa és strukturált dokumentáció kiépítése.

## [v3.0.0] - 2026-08-01
### Módosítva
- **Őszinte Scraper Mode**: A szállás scraper megszüntette a hibás adatok helyetti kamu (mock) adatgenerálást. Hiba esetén a rendszer transzparens hibaüzenetet ad a felhasználónak.

## [v2.0.0] - 2026-07-10
### Hozzáadva
- **6-Tényezős Városrangsoroló Engine**: Kiwi repjegy, Open-Meteo időjárás, Numbeo megélhetés & biztonság, Walkability és POI sűrűség integráció.
- **Constraint Útiterv Engine**: Napi időablakok, étkezési slotok, utazási idő számítás (Haversine), lelakatolt elemek.
- **V2 Frontend**: Interaktív Drag & Drop útiterv-szerkesztő felület és Leaflet térképes útvonal-megjelenítés.

## [v1.0.0] - 2026-05-15
### Hozzáadva
- Prototípus repjegy és szálláskereső felület és statikus városajánló.

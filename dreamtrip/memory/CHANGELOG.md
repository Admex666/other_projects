# DreamTrip — Változási Napló (Changelog)

## [Unreleased] - 2026-08-19

### Hozzáadva
- **Élő EUR/HUF Árfolyam Lekérő Szolgáltatás ([`app/services/exchange_service.py`](file:///e:/Data/other_projects/dreamtrip/app/services/exchange_service.py))**:
  - Valós idejű, hivatalos **Európai Központi Bank (EKB / Frankfurter API)** devizaárfolyam integráció, automatikus **Open Exchange Rates** tartalékkal és 1 órás memóriagyorsítótárral.
  - A korábbi égetett 400 Ft-os szorzó helyett a teljes rendszer (szállás- és repülőjegy átszámítások, histogram, AHP rangsorolás) a legfrissebb élő árfolyammal számol.
- **Accommodation Intelligence UI Újratervezés (V2.2 Élesítve) & Teljes Éjszakai Mód Támogatás ([`templates/accommodation/accommodation_intelligence.html`](file:///e:/Data/other_projects/dreamtrip/templates/accommodation/accommodation_intelligence.html))**:
  - A korábbi egyszerű űrlap helyett a finomított V2.2 dizájn került élesítésre.
  - Teljes körű **Light & Dark Mode** támogatás a központi változókkal (`var(--bg-surface)`, `var(--bg-surface-subtle)`, `var(--text-main)`, `var(--border-subtle)`), sötét módra optimalizált Flatpickr naptár-felugróval és kontrasztos ikonokkal.
  - Integrálva az egyedi magyar nyelvű dátumtartomány-választó (Flatpickr), szigorú $\pm 1$-es léptető gombok (`stepUp`, `stepDown`), feltételes tizedespontos manuális minőségi értékelés (`[✏️ Saját]` gombbal), és a szinkronizált maximális árbevitel (szerkeszthető Ft mező + csúszka).
  - Teljes körű mobil-reszponzivitás (rugalmas kártyák, érintésbarát gombtávolságok).
- **PROD és DEV Üzemmód**:
  - `DEV` módban (`APP_ENV=development`): Lokális Selenium Chrome fut a szálláskereséshez (0 Browserless quota felhasználás), és a főoldalon minden modul elérhető.
  - `PROD` módban (`APP_ENV=production`): Kizárólag a **Flight Intelligence** és az **Accommodation Intelligence** modulok aktívak és kattinthatók. A többi modul disabled/Hamarosan jelölést kap, a védett útvonalak átirányítanak a `/home`-ra, a szálláskereső pedig felhős Browserless motort használ.
- **Vercel Serverless Konfiguráció ([`vercel.json`](file:///e:/Data/other_projects/dreamtrip/vercel.json), [`api/index.py`](file:///e:/Data/other_projects/dreamtrip/api/index.py))**:
  - Elkészült a Vercel ASGI belépési pont és rewrite szabályrendszer, így a projekt azonnal deployolható a `vercel` CLI paranccsal.
- **Browserless.io Felhős Scraping Integráció**:
  - A szálláskereső scraper mostantól automatikusan a `BROWSERLESS_KEY` környezeti változóval megadott felhős Chrome motort használja, így **100%-ban Vercel- és felhőkompatibilis** (nincs szükség helyi Chrome/Selenium telepítésre).
  - Ha nincs megadva kulcs, a rendszer észrevétlenül visszalép a helyi Selenium Chrome-ra.
- **Szállás Keresési Kínálat & Limit Bővítés ([`app/scrapers/accommodation_scraper.py`](file:///e:/Data/other_projects/dreamtrip/app/scrapers/accommodation_scraper.py), [`templates/accommodation_intelligence.html`](file:///e:/Data/other_projects/dreamtrip/templates/accommodation_intelligence.html))**:
  - A korábbi 500-as pagination limitet 1500-ra növeltük, és kikapcsoltuk a szigorú `instantBooking: true` szűrést.
  - Alapértelmezetten bekapcsoltuk az összes elterjedt szállástípust (Hotel, Apartman, Vendégház, Nyaraló, Hostel), így a találati szám ~495-ről **1477+ valós szállásra** ugrott fel, lefedve a Cozycozy teljes aggregált adatbázisát.
- **Szállás Megtekintés & Közvetlen Link Tisztító**:
  - Megoldva a Booking.com és VRBO általános főoldalra / keresőre való átirányítási problémája.
  - A `clean_hotel_booking_url` automatikusan kibontja a közvetlen cél-URL-eket az affiliate wrapperekből (pl. `prf.hn`, `/redirect?to=`), eltávolítja a Booking által elutasított törött `%CLICK_ID%` makrókat, és fallbackként közvetlen szálláskereső linket képez.
- **Szállás Keresőmező Méret & Duplikáció Javítás**:
  - Az úti cél beviteli mező mostantól teljes szélességű (`width: 100%`, `box-sizing: border-box`), tágasabb belső margókkal és modern fókusz állapottal.
  - Az `/api/locations/autocomplete` végpontban javítva a duplikációs hiba: intelligens kulcs-alapú szűrés (város + ország szerint), így megszűntek az azonos nevű reptér/város duplikációk.
- **Egységesített Szállás Úti Cél Keresőmező**:
  - A korábbi két különálló (Város és Ország) beviteli mező összevonásra került egyetlen intelligens `📍 Úti cél (Város vagy Régió)` keresőmezőbe.
  - Autocomplete javaslatok (város + ország) egy kattintással / billentyűvel kiválaszthatók, a háttérben automatikus felbontással és Cozycozy kompatibilis küldéssel.
- **Cozycozy Scraper Modernizáció & Hiba Javítás ([`app/scrapers/accommodation_scraper.py`](file:///e:/Data/other_projects/dreamtrip/app/scrapers/accommodation_scraper.py))**:
  - Javítva a `searchId` kinyerési logika az új Cozycozy link-struktúrához (`a[href*='searchId=']`).
  - Eltávolítva az elavult és összeomlást okozó Chrome flag-ek (`--single-process`, `--disable-browser-side-navigation`).
  - Automatikus magyar -> angol országfordító szótár (`Magyarország` -> `Hungary`, `Spanyolország` -> `Spain` stb.) a Cozycozy URL-ek 100%-os felismeréséhez.
- **Élő Szűrőszámláló & 0-találatos Védelem (`flight_filter.html`)**:
  - Valós idejű szűrőszámláló banner és `POST /api/preview-filter-count` végpont, amely gépelés/állítgatás közben (<100ms) mutatja a feltételeknek megfelelő járatkombinációk számát.
  - Ha a szűrők miatt 0 járat marad, a rendszer azonnal letiltja a tovább gombot, piros figyelmeztetést jelenít meg, és megakadályozza a továbblépést az AHP és preferenciák oldalra.
  - Biztonsági ellenőrzés a PROMETHEE / AHP számítási taskban (`run_calculation_task`), elkerülve a `KeyError: 'total_price_huf'` hibát.
- **Flight Intelligence Repülőtér Autocomplete & Validáció**:
  - Dinamikus Kiwi Locations API `/api/locations/autocomplete` végpont memóriabeli cache-sel és gyorsjavaslatokkal (Budapest, Bécs, Debrecen, Pozsony stb.).
  - Interaktív billentyűzet- és egérvezérelt typeahead UI a `flight_intelligence.html`-ben IATA kódokkal és város/ország kiemeléssel.
  - Előzetes szerveroldali validáció és közérthető magyar hibaüzenet, ha a megadott településhez nem tartozik repülőtér.
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

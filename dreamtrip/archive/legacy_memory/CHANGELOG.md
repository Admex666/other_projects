# DreamTrip — Változási Napló (Changelog)

## [Unreleased] - 2026-08-21

### Hozzáadva
- **Egységes Trip-Centrikus Architektúra & Végponttól Végpontig tartó Handoff ([`app/models/models.py`](file:///e:/Data/other_projects/dreamtrip/app/models/models.py), [`app/main.py`](file:///e:/Data/other_projects/dreamtrip/app/main.py), [`static/js/trip_cart.js`](file:///e:/Data/other_projects/dreamtrip/static/js/trip_cart.js), [`templates/destination/destination_results.html`](file:///e:/Data/other_projects/dreamtrip/templates/destination/destination_results.html), [`templates/flights/flight_results.html`](file:///e:/Data/other_projects/dreamtrip/templates/flights/flight_results.html), [`templates/accommodation/accommodation_intelligence.html`](file:///e:/Data/other_projects/dreamtrip/templates/accommodation/accommodation_intelligence.html))**:
  - **Közös `UnifiedTrip` Adatmodell**: Bevezettük az explicit `trip_id`, `input`, `destination`, `flight` (search_params, shortlist, selected_flight), `accommodation` (search_params, shortlist, selected_accommodation) és `budget` struktúrát mind backend Pydantic modellekben, mind kliensoldali JavaScript motorban (`TripEngine`).
  - **Automatikus Dátum- és Kontextus-átvitel (Source of Truth)**:
    - Destination Matcher kiválasztáskor a célváros, hónap, időtartam és létszám automatikusan inicializálja a Flight keresőt.
    - Járat kiválasztásakor (pl. Wizz Air szept. 10–17., 7 éj) a szálláskereső automatikusan zárolja a pontos check-in (`2026-09-10`) és check-out (`2026-09-17`) dátumokat és az éjszakák számát.
  - **Egyértelmű Lépésenkénti CTA-k („Mi a következő lépés?”)**:
    - 1. Célállomás után: `🏆 Róma kiválasztása & Járatok összehasonlítása →`
    - 2. Járat után: `→ Szállások keresése (2026. szept. 10–17. · 7 éj)`
    - 3. Szállás után: `→ Utazási terv megnyitása & Ajánlatkészítés`
    - 4. Workspace: `📄 Ügyfélajánlat készítése (Nyomtatás / PDF)`
  - **Shortlist és Numbeo Költségbontás**: A kosár fiók lépésjelzővel (Stepper: Célállomás ✓ | Járat ✓ | Szállás ✓) és tételes matematikai számítási képletekkel prezentálja a végösszeget.
- **Hivatalos Numbeo Étkezési & Közlekedési Adatbázis Bekötése a Kosár Kalkulációba ([`static/js/trip_cart.js`](file:///e:/Data/other_projects/dreamtrip/static/js/trip_cart.js), [`app/services/numbeo_service.py`](file:///e:/Data/other_projects/dreamtrip/app/services/numbeo_service.py))**:
  - **Valós Numbeo Étel- és Jegyárak**: Becsült hasraütés helyett a célváros hivatalos Numbeo Cost of Living komponensei alapján határozzuk meg az étkezést és helyi közlekedést:
    - 🍽️ **Ételek & étkezések**: `Numbeo (1.5× Olcsó étkezés [€] + 0.5× Középkategóriás vacsora [€] + 2× Kávé [€]) / nap / fő × Napok × Utaslétszám`
    - 🚇 **Helyi tömegközlekedés**: `Numbeo Vonaljegyár [€] × 2 jegy/nap/fő × Napok × Utaslétszám`
    - A Drawer és az Ügyfél Ajánlat / PDF kiírja az adott város valós Numbeo éttermi árait (pl. Olcsó étkezés: €16.0, Középkategóriás vacsora: €32.0, Kávé: €1.6) és a `[Numbeo Index]` hitelesítő jelvényt.
- **Destination Matcher Utazási Időszak Módváltó Javítása ([`templates/destination/destination_matcher.html`](file:///e:/Data/other_projects/dreamtrip/templates/destination/destination_matcher.html))**:
  - **Script Blokk Becsomagolása**: A `<script>` szekciót hiányzó `{% block scripts %}` blokkba helyeztük, mivel Jinja sablonöröklésnél a blokkon kívüli kód eldobásra került. Ezzel a 3 utazási időszak fül („📅 Konkrét”, „⏱️ Intervallum”, „🗓️ Hónap”), a dátumválasztó flatpickr naptárak, gyorsgombok és stepperek azonnal interaktívvá és kattinthatóvá váltak.
- **Flight Results Kártyák 440px Mobile (iPhone 16 Pro Max) & Desktop Elrendezésének Finomhangolása ([`templates/flights/flight_results.html`](file:///e:/Data/other_projects/dreamtrip/templates/flights/flight_results.html), [`static/css/trip_cart.css`](file:///e:/Data/other_projects/dreamtrip/static/css/trip_cart.css))**:
  - **440px Képernyőszélesség Túlcsordulás Mentesség**: `html, body { overflow-x: hidden }`, `.route-loc-col` flex oszlopok és rugalmas `35-70px` útvonalvonalak bevezetésével a kártyák mostantól 100%-ban kitöltik a 440px képernyőt anélkül, hogy vízszintesen kilógna bármilyen elem.
  - **Lebegő Trip Bar Mobil Igazítás**: A lebegő utazási kosár mobil nézetben kompakt alsó dokkolt sávvá alakul (`calc(100% - 24px)` szélességben), így nem kényszeríti túl a viewport szélességét.
  - **Desktop Jegybanner**: Asztali gépen tágas, 1-oszlopos jegybanner elrendezés `190px` akciósávval, ahol a „Részletek” és „Utazáshoz adás” gombok kényelmesen elférnek.
- **Perzisztens Utazási Kosár & Unified Workspace (Trip Builder Cart) ([`static/js/trip_cart.js`](file:///e:/Data/other_projects/dreamtrip/static/js/trip_cart.js), [`static/css/trip_cart.css`](file:///e:/Data/other_projects/dreamtrip/static/css/trip_cart.css), [`templates/base.html`](file:///e:/Data/other_projects/dreamtrip/templates/base.html))**:
  - **Lebegő Trip Bar & Slide-Over Drawer**: Minden oldalon elérhető modern lebegő sáv és részletes drawer, amely mutatja a kiválasztott célállomást, a hozzáadott repülőjegyet, a lefoglalt szállást és a becsült összköltséget.
  - **1-Kattintásos Elem Hozzáadás & Törlés**: A Destination Matcherben, Flight Intelligence-ben és Accommodation Intelligence-ben a kártyákhoz hozzáadott „➕ Utazáshoz adás” gombokkal az elemek közvetlenül rögzíthetők a kosárba és bármikor kivehetők.
  - **B2B Ügyfél Ajánlat Export / Nyomtatás**: A drawerből 1 kattintással generálható letisztult, nyomtatható/PDF ügyfél utazási ajánlat tételes kalkulációval.
  - **Teljes Kliensoldali Állapotmegőrzés (`localStorage`)**: Oldalváltáskor és böngésző újratöltéskor sem vesznek el a megadott adatok.
  - **Alsó Kitakarás Javítása & Diszkrét Elrejtés**: Globális `140px` alsó margót/görgetési clearance-t kapott az összes oldal (`/flight-intelligence-filter`, `/flight-intelligence-preferences`, `/flight-intelligence-ahp`, stb.), így a gombok sosem takaródnak ki. Emellett a lebegő sáv jobb szélére felkerült egy letisztult `✕` bezáró gomb, amely a sávot egy diszkrét jobb alsó sarok-gombra (`🛒 Aktív Terv`) cseréli, amivel bármikor újra felugrasztható.
  - **1-Kattintásos Adatátadás**: A kiválasztott város kártyáján lévő „Járatok összehasonlítása” gomb mostantól az összes utazási paramétert (Indulási hely, Célállomás, Felnőtt és Gyermek létszám, Hónapon belüli időablak, Tartózkodási napok száma) adatvesztés és újragépelés nélkül átadja a Flight Intelligence-nek.
  - **Context-Aware Visszanavigáció**: A Flight Intelligence fejlécében megjelenik a „Vissza a célállomások rangsorához” link és egy megerősítő státuszbanner.
  - **Valós Csoportos Árkalkuláció**: A járatkereső motor mostantól a pontos utaslétszámra keresi meg a legkedvezőbb retúr járatokat.
  - Megszüntettük a felesleges 5-napos csonkolást és az 1 másodperces mesterséges alvási várakozásokat (`split_chunks=False`).
  - A Kiwi GraphQL motorja mostantól közvetlenül 1etlen hívással (`limit=20`) kéri le a hónap legolcsóbb járatait (12 API hívás helyett városonként mindössze 2 hívás).
  - Párhuzamos feldolgozási szálak számát megemeltük (`max_workers=10`), így a 40 célállomás teljes retúr kalkulációja drasztikusan lerövidült.
- **Hónapon Belüli Rugalmas Járat- & Ároptimalizáció ([`app/services/destination_scoring_service.py`](file:///e:/Data/other_projects/dreamtrip/app/services/destination_scoring_service.py))**:
  - A szűk 2-napos fix ablak helyett a rendszer mostantól a kiválasztott hónap teljes időszakában (`1 - 24. nap`) keres oda- és visszautakat $\pm 2$ napos rugalmas tartózkodási sávval (`duration_days +- 2 nap`).
  - Ezzel desztinációnként több ezer (akár 12 000+) retúr járatkombinációt vizsgál meg a háttérben, megtalálva az adott hónap ténylegesen legolcsóbb retúr árait (pl. Párizs: 23 506 Ft, Barcelona: 28 243 Ft, Funchal: 58 726 Ft, Dubaj: 117 373 Ft, Tokió: 237 541 Ft).
  - Megszüntettük a töredezett, elavult 4-lépcsős folyamatot (kritérium-válogatás, páros mátrix, dummy vibe/tömeg szűrők).
  - Létrehoztuk a letisztult **2-lépéses B2B Advisor Flow-t**:
    1. **1. lépés:** Indulási hely, Utazási hónap, Tartam ($\pm 1$ stepper), Napi költségkeret csúszka és Régióbeli kizárások.
    2. **2. lépés:** Célhőmérséklet (nappali csúcs) + A 4 valós pillér fontossága (Repülő, Költség, Időjárás, Biztonság) dinamikus csúszkákkal és 1-kattintásos stratégiákkal (*Budget-first*, *Weather-first*, *Safety-first*, *Kiegyensúlyozott*).
- **Destination Matcher Kritikus Adat- és Súlyozásjavítások ([`app/services/destination_scoring_service.py`](file:///e:/Data/other_projects/dreamtrip/app/services/destination_scoring_service.py), [`app/services/numbeo_service.py`](file:///e:/Data/other_projects/dreamtrip/app/services/numbeo_service.py))**:
  - **Repülőjárat kombináció bug javítva**: megszüntettük a pandas DataFrame `ambiguous boolean` kivételt, így a Kiwi valós retúr árai (18 231 Ft – 294 656 Ft) közvetlenül bekerülnek a számításba a 75 000 Ft-os fallback helyett.
  - **Magyar városnév Numbeo leképezés**: minden magyar városnév (Párizs, Bécs, Róma, Lisszabon stb.) közvetlenül megkapja a valós Numbeo költségkosarát (€32.4 – €70.7/nap) és valós biztonsági indexét (43 – 84) a statikus 44.6 € / 60 fallback helyett.
  - **Nem választott szempontok súlyának nullázása**: ha a felhasználó nem választja ki a Biztonságot vagy Repülőjegyet, azok súlya szigorúan `0.00`.
  - **Nappali csúcshőmérséklet**: az időjárási egyezést a nappali hőmérséklet határozza meg, a felületen megjelenítve mind a nappali, mind az éjszakai értékeket (`Nappal: 26°C / Éjjel: 19°C`).
  - **Minden dummy/szubjektív adat kiirtva**: eltávolítottuk a fix `vibe_metrics`, `crowds = 0.5` és elavult statikus mutatókat.
  - **Dinamikus & bővíthető városkezelés**: Madeira (Funchal), Tokió és bármely új desztináció kódmódosítás nélkül azonnal feldolgozható.
  - **Valós Numbeo Költségkosár & Biztonsági Index**: standard utazási kosár ($1.5 \times \text{olcsó étkezés} + 0.5 \times \text{középkategóriás étkezés} + 2 \times \text{kávé} + 2 \times \text{helyi jegy}$) és hivatalos Numbeo Safety Index.
  - **Valós Open-Meteo Klímaarchívum**: havi átlaghőmérséklet és szigorúan monoton normalizált időjárási pontszám.
  - **Transzparens & Reprodukálható Döntési Modell**: $\Sigma w_i \times s_i$ pontszámítás, részletes terminál printeléssel és a valós adatokból generált objektív „Miért ezt ajánljuk?” réteggel.
- **Keresőmező Ikon & Szöveg Átfedés Javítás ([`static/css/components.css`](file:///e:/Data/other_projects/dreamtrip/static/css/components.css))**:
  - Megszüntettük az általános `input[type="text"]` szelektor által okozott CSS prioritási hibát: a `.hero-search-input` mostantól szigorú `padding-left: 64px !important` és `box-sizing: border-box` beállítást kapott, így a szöveges tartalom és a placeholder tökéletes távolságot tart az ikonoktól.
- **Központosított Komponens Rendszer ([`static/css/components.css`](file:///e:/Data/other_projects/dreamtrip/static/css/components.css), [`static/js/components.js`](file:///e:/Data/other_projects/dreamtrip/static/js/components.js), [`templates/base.html`](file:///e:/Data/other_projects/dreamtrip/templates/base.html))**:
  - Az ismétlődő UI elemek (egyedi Flatpickr naptár, magyar lokalizáció, Light & Dark téma felülírások, diszkrét $\pm 1$ léptetők `stepUp`/`stepDown`, debounced autocomplete) központi CSS és JS fájlokba lettek kiszervezve, megszüntetve a HTML oldalak közötti kódismétlést.
- **Destination Matcher UI Újratervezés ([`templates/destination/destination_matcher.html`](file:///e:/Data/other_projects/dreamtrip/templates/destination/destination_matcher.html))**:
  - A célállomás-ajánló felületet is átállítottuk a központi Executive Advisor dizájnrendszerre: Hero indulási autocomplete, Bento-box elrendezésű időzítés & időtartam léptető, szinkronizált napi költségkeret csúszka + mező, modern régióbeli kizárás chipek, teljes Light/Dark mode kompatibilitás.
- **Flight Intelligence UI Újratervezés ([`templates/flights/flight_intelligence.html`](file:///e:/Data/other_projects/dreamtrip/templates/flights/flight_intelligence.html))**:
  - A repülőjegy kereső felületet teljes mértékben hozzáigazítottuk az Accommodation Intelligence V2.2 Executive Advisor dizájnjához: Bento-box elrendezés, központi Flatpickr időablak választó, népszerű indulási és érkezési gyorsgombok, utas- és átszállásszűrők, teljes Light/Dark mode támogatás.
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

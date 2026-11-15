---
id: kitero
type: entity
name: VitaSteps Kitérő
status: active
description: Önvezetett, történetmesélésre és digitális narrációra épülő városi élményséták (szabadság, kényelem és rejtett kulturális felfedezés).
replaces: "[[hosszu-lepesek|Hosszú Lépések]]"
related:
  - "[[strategic-positioning|Strategic Positioning]]"
  - "[[growth-loop|Growth Loop]]"
  - "[[ADR-009-strategic-ecosystem-pivot|ADR-009 Strategic Ecosystem Pivot]]"
  - "[[ADR-010-kitero-validation-architecture|ADR-010 Kitérő Validáció]]"
---

# 🧭 Entity: VitaSteps Kitérő (Digitális Városi Élményséták)

## 1. Üzleti Háttér & Értékajánlat

A VitaSteps Kitérő a márka digitális élményplatformja. A fizikai érmek mellett megnyitja a magas hozzáadott értékű, zéró fizikai készletezési költségű digitális séták piacát.

* **Fő szlogen:** *„Néha a legjobb élmények egy kitérővel kezdődnek.”*
* **A 3 kulcsfontosságú értékajánlat:**
  1. **Kényelem:** Nulla szervezési és kutatási teher; előre kurált prémium útvonalak.
  2. **Valódi Történetek:** Nem száraz évszámok, hanem emberi sorsok, rejtélyek, párbajok és kulisszatitkok.
  3. **Teljes Szabadság:** Saját ritmusban, idegenvezető és időpontkötöttség nélkül bejárható.

---

## 2. Termékarchitektúra & MVP Specifikáció

* **Platform:** Közvetlenül böngészőből futó, mobil-optimalizált PWA (`/app/`), App Store / Google Play letöltés nélkül.
* **Első éles PWA séta (`/app/tour_m1.json`):** *A Kisföldalatti Nyomában*
  * Útvonal: Mexikói úti járműtelep $\rightarrow$ Vörösmarty tér (9 történelmi állomás)
  * Gyalogos távolság: ~4.9 km (234 pontos valódi OSRM gyalogos nyomvonalon, 8 különálló szakaszon: `walking_route` és `walking_legs` — légvonal nélkül)
  * Becsült időtartam: 1.5 – 2 óra
  * Narráció: Stúdióminőségű, helyileg generált **Imre** neurális magyar hang 128 kbps `.mp3` fájlok (`poi_{1..9}_hook.mp3` és `poi_{1..9}_story.mp3`, összesen 18 db túrahang + 18 db egyedi terepteszt hang: `test_{1..9}_hook.mp3` és `test_{1..9}_story.mp3`). A UI-on kizárólag az **„Imre”** név jelenik meg (`02:30 (Imre)`), a technikai `"Piper"` és `"TTS"` elnevezések rejtettek.
  * Helyszíni fotók & Offline Precache (`sw.js` `kitero-pwa-v4`): Network-First stratégia az App Shellre (azonnali verziófrissülés), Cache-First és CORS cache engedélyezés a térképcsempékhez és CDN-ekhez, valamint ArrayBuffer HTTP 206 Partial Content szeletelő a hanganyagok offline lejátszásához és scrubbingjához. PWA ikonok: `assets/icon-192.png` és `assets/icon-512.png`.
  * Helyszíni Megfigyelési Fókusz (`#story-observation-box`): Az Adatmátrix alatt megjelenő **„👀 Mit figyelj meg a helyszínen?”** kártya (`poi.detail`), amely a fizikai épület konkrét részleteire irányítja a sétáló figyelmét.
  * Történet-megjelenítés (**Exkluzív Titok Kártyák / Accordion UX**): A hosszú folyó szövegek helyett megállónként **3 interaktív, kinyitható Titok Kártya** (`secrets` tömb: ikon, cím, évszám/téma badge, „Koppints a titok felfedéséhez” felhívás és forgó nyíl). Egyszerre mindig csak egy kártya van nyitva (automatikus összecsukás).
  * **Sétaválasztó Rendszer (`#screen-tours`):** Az alkalmazás központi élményválasztó felülete, amely közvetlenül elérhető az alsó navigációs sáv első füléről (`Séták`), a fejléc interaktív címkéjéről (`#btn-open-tours-header`: `Kisföldalatti ▾`) vagy a Séta áttekintésből (`#btn-switch-tour-brief`). A választóban kiemelt kártyaként szerepel:
    1. **A Kisföldalatti Nyomában (Éles Séta):** 9 megálló, 3.4 km, 1.5–2 óra, millenniumi történetek, aktív állapotjelzővel és indítással.
    2. **Élő Terepteszt — Saját Környék (Teszt Séta):** Valós utcai GPS teszt, egyedi koordináták, Piper Imre üdvözlő és visszajelző tesztnarrációja (`test_{1..9}_{hook,story}.mp3`), közvetlen gyorsgombokkal (`⚡ 3 megálló lerakása körém`, `🗺️ Megállók kijelölése a térképen`).
    3. **Hamarosan Érkező Séták:** *A Palotanegyed Titkai* és *A Budai Vár Rejtett Udvarai* előnézeti kártyái.
  * Térképmotor: Leaflet + kulcsmentes **Esri Canvas** (`World_Light_Gray_Base` nappali és `World_Dark_Gray_Base` éjszakai csempék `{z}/{y}/{x}` REST koordináta-sorrenddel, CSS invertálás nélkül).
  * Lebegő Globális Mini-Player: A felső telemetria sáv alatt (`top: 64px`, átfedés nélkül) lebegő audio vezérlő, közvetlen **`📖 Történet`** ugrógombbal.
  * **Rejtett Élő Terepteszt Mód (`?test_mode=1`):** Normál felhasználók számára (`/app/`) a teszt gombok (`#test-mode-toggle-btn`, `#btn-open-test`) rejtettek (`display: none`). A `/app/?test_mode=1` URL paraméterrel (vagy aktív `kitero_custom_test_route_v1` `localStorage` útvonal esetén) előhívható a **GPS Teszt Labor**, amelyben:
    1. **🗺️ Megállók kijelölése a térképen (`#test-btn-pick-map`):** Bárhol a saját környéken böködéssel lerakható 2–9 egyedi teszt megálló, amelyek között az app élő OSRM gyalogos útvonalat tervez és elmenti `localStorage`-ba.
    2. **⚡ 3 megálló automatikus lerakása körém (`#test-btn-around-me`):** A telefon valós GPS pozíciója köré ~50–60 méterenként lerak 3 teszt megállót azonnali utcai kipróbáláshoz.
    3. **Valódi Piper Imre Teszthangok (`test_{1..9}_{hook,story}.mp3`):** Saját környékbeli tesztútvonal esetén Imre valódi felolvasott magyar teszthangjai szólnak: *„Ez az első tesztpont, üdvözöllek a VitaSteps Kitérő élő tereptesztjén!...”*, *„Megérkeztél a második tesztpontra!...”*. A megállókártyák és a player szövegei dinamikusan a tesztpontokhoz igazodnak, a *„🔄 Eredeti Kisföldalatti útvonal visszaállítása”* gombbal pedig az eredeti 9 állomás azonnal visszaállítható.
    4. **Mobil Audió Autoplay Feloldás (`unlockMobileAudio()`):** A séta vagy teszt indításakor feloldja az iOS Safari / Android Chrome autoplay zárolását, így 35 méteren belülre érve Imre hangja és a haptikus rezgés (`navigator.vibrate`) automatikusan elindul.
* **Marketing Landing Prototípus séta (`/kitero/`):** *A Palotanegyed Titkai: Arisztokraták és Rejtélyek* (8 állomásos interaktív demó a landing oldalon).
* **Árazási hipotézis:** 3 490 Ft vs 3 990 Ft (A/B tesztelve).

---

## 3. Validációs Kampány & PWA Fájlok

* **Célcsoport:** Elsődlegesen a korábbi VitaSteps fizikai túraérmes vásárlók + városi felfedezők.
* **Biztonságos Címzettazonosítás:** `?cid={{random_token}}` (soha nem kerül személyes adat URL-be).
* **PWA Webapp:** [`landing_predikalo1/app/index.html`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/app/index.html), [`app.js`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/app/app.js), [`style.css`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/app/style.css), [`tour_m1.json`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/app/tour_m1.json)
* **Landing Page:** [`landing_predikalo1/kitero/index.html`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/kitero/index.html)
* **Backend API:** [`landing_predikalo1/api/kitero.js`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/api/kitero.js)
* **E-mail Sablon:** [`landing_predikalo1/email_templates/kitero_validation.html`](file:///C:/Users/Adam/Data/other_projects/VitaSteps/landing_predikalo1/email_templates/kitero_validation.html)

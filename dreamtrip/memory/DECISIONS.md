# DreamTrip — Döntési Napló (Decisions Log)

Ez a dokumentum a projekt hosszú távú architektúrális és fejlesztési döntéseit rögzíti.

---

## 1. Döntés: Destination Matcher B2B Beta Döntések (Nightlife, Vibe, Repülőjegy Modell)
* **Nightlife & Tömegkerülés Eltávolítása (P0):**
  * *Döntés:* A Nightlife (korábban dummy 50.0) és a Tömegkerülés (dummy 0.5) szempontokat teljes mértékben eltávolítottuk a döntési modellből és a felületről.
  * *Indoklás:* B2B bétában nem szerepelhet semmilyen rejtett dummy vagy félkész heurisztika.
* **Vibe-alapú Keresés Halasztása (P1):**
  * *Döntés:* A szubjektív "vibe" (romantikus/party/chill/történelmi) modellezést elhalasztjuk a béta utáni P1 fázisra.
  * *Indoklás:* A B2B béta fókusza a 100%-ban objektív, transzparens adatokon nyugvó döntéstámogatás.
* **Repülőjegy-Költség Definíció (Valós Retúr & Pontos Utasszám):**
  * *Döntés:* A Destination Matcher kizárólag valós Kiwi retúr járatkombinációkat használ a kiválasztott utasszámra és hónapra, ± 2 napos rugalmas tartózkodási ablakkal. Nincs egyirányú proxy ár.

---

## 2. Döntés: Constraint-Alapú Gráf Modell a Generatív AI Helyett

* **Dátum**: 2026-07-05
* **Kontextus**: Sok utazási app LLM- alapú (Prompt/Chat) alapon próbál útitervet generálni, aminek következménye a hallucináció, zárva tartó múzeumok, és a pontatlan utazási idők.
* **Döntés**: A DreamTrip egy **matematikai és geográfiai constraint optimalizáló motor**. A helyszínek csomópontok (nodes), az utazási idők élek (edges). A napiterv nyitvatartási és étkezési korlátok alapján épül fel.
* **Hatás**: Kiszámítható, valósághű és valós időben re-optimalizálható útiterv.

---

## 2. Döntés: 7 Napos Helyi Cache a Google Places API Adatokhoz

* **Dátum**: 2026-07-10
* **Kontextus**: A Google Places Text Search és Place Details API költséges gyakori ismételt hívások esetén.
* **Döntés**: Az ingyenes és gyors futtatás érdekében a lekéri POI-kat a `data/poi_cache.json` fájlban tároljuk 7 napos lejárattal (TTL). Ha nincs API kulcs beállítva, a rendszer mock koordináta-generálásra vált vissza.
* **Hatás**: Minimális API költség és villámgyors fejlesztői tesztelhetőség.

---

## 3. Döntés: V3 "Őszinte Mode" a Szállás Scrapingben (Mock Helyett Hibaüzenet)

* **Dátum**: 2026-08-01
* **Kontextus**: Korábban a szállás scraper Playwright/Selenium összeomlás esetén automatikusan hamis (mock) szállásadatokat generált, ami megtévesztette a tesztelőket.
* **Döntés**: A rendszert visszaállítottuk "ősszinte" hibakezelésre: ha kevés a RAM vagy lejár a timeout, a szerver pontos hibaüzenettel áll le és jelzi a valódi korlátot (`status: "error"`).
* **Hatás**: Átlátható és transzparens tesztelés/demo.

---

## 4. Döntés: Szabványos Python Csomagstruktúra (`app/` Refaktor)

* **Dátum**: 2026-08-13
* **Kontextus**: A projekt prototípus formában, monolitikus `site/main.py` fájllal és lapos könyvtárszerkezettel működött.
* **Döntés**: Átszerveztük a kódkészletet `app/services/`, `app/scrapers/`, `app/models/`, `data/`, `notebooks/` és `memory/` tiszta modulokra.
* **Hatás**: Skálázható, tiszta és fenntartható kódarchitektúra.

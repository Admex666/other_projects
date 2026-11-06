---
id: ADR-010-kitero-validation-architecture
type: decision
name: ADR-010 Kitérő Validáció és Analitikai Architektúra
status: active
date: 2026-11-05
deciders:
  - CEO
  - Lead Architect
consulted:
  - Marketing & Analytics
related:
  - "[[kitero|VitaSteps Kitérő]]"
  - "[[ADR-009-strategic-ecosystem-pivot|ADR-009 Strategic Ecosystem Pivot]]"
  - "[[growth-loop|Growth Loop]]"
---

# ⚖️ ADR-010: VitaSteps Kitérő Validáció & Analitikai Architektúra

## 1. Döntési Kontextus
A VitaSteps növekedési korlátainak feloldására új digitális terméket vezet be **VitaSteps Kitérő** néven. A cél a fizetési hajlandóság és a felhasználói elköteleződés mérése anélkül, hogy a korábbi rendszert megbontanánk vagy felesleges párhuzamos adatbázisokat építenénk.

---

## 2. Meghozott Döntések

### 2.1. Névhasználat & Branding
* **Hivatalos név:** Kizárólag a **Kitérő**, illetve a **VitaSteps Kitérő** név használható.
* A korábbi ideiglenes munkacímek (*Hosszú Lépések*) minden felhasználói és nyilvános felületről törlésre kerültek.

### 2.2. Editorial Travel Design
* A Stitch mockupokból kiindulva a landing page prémium utazási magazin stílust kapott (világos krém háttér `#F8F7F2`, mély erdőzöld akcentus `#365A45`, `Playfair Display` és `Plus Jakarta Sans` betűtípusok).
* Beágyazásra került egy teljes körű, mobilon kiválóan interaktív prototípus (Séta adatlap, Térképes nézet, Festetics-palota mintamegálló, hangos audio előnézet).

### 2.3. Biztonságos Kampányazonosítás (CID)
* Szigorú adatvédelmi szabály: semmilyen e-mail cím vagy személyes adat nem szerepelhet URL paraméterben.
* Helyette véletlenszerű `?cid=...` token azonosítja a kampánycímzettet, amit a backend összekapcsol a meglévő analitikai session-nel és lead rekorddal.

### 2.4. Analitika & Pushbullet Integráció
* A meglévő `analytics.js` és `analytics_events` motor méri a specifikus eseményeket:
  `landing_view`, `scroll_25/50/75/90`, `prototype_start`, `prototype_screen_view`, `map_preview_open`, `audio_preview_play`, `pricing_view`, `cta_click`, `lead_submit`.
* A napi 22:25-kor futó GitHub Actions Pushbullet riport bővült a Kitérő szekcióval (Látogatók, Prototípus indítások, Hangminta lejátszások, Leadek).

### 2.5. Árhorgonyzás és Érték-Összehasonlító Blokk (Value Reframing)
* A korábbi egyszerű árdoboz helyére egy kétoszlopos érték-összehasonlító szekció került:
  1. **Kötött csoportos séta:** 10 000 – 13 000 Ft (5 000 – 6 500 Ft / fő), szigorú fejpénz, merev időbeosztás, 20–30 fős idegen tömeg, eső/lemondás esetén elúszó jegy.
  2. **VitaSteps Kitérő:** 3 490 Ft vs 3 990 Ft / teljes séta (A/B tesztelve), nincs fejpénz (párban ~1 745 Ft – ~1 995 Ft / fő – még mindig olcsóbb, mint egy kávé és süti), 100% szabadság, bármikor megállítható egy kávéra/fagyira, kulcsrakész „adott az élmény” nulla szervezési stresszel, örökös hozzáférés.
* Közvetlenül a blokk alatt helyezkedik el a korai hozzáférés Név + E-mail bekérő űrlapja.

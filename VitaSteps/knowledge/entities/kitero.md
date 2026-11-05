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

* **Platform:** Közvetlenül böngészőből futó, mobil-optimalizált élmény (App Store / Google Play letöltés nélkül).
* **Első pilot séta:** *A Palotanegyed Titkai: Arisztokraták és Rejtélyek*
  * Távolság: 2.8 km
  * Becsült időtartam: 1.5 – 2 óra
  * Megállók: 8 állomás
  * Narráció: Audio fejezetek korhű hangulatfestéssel.
* **Árazási hipotézis:** 2 990 Ft vs 3 490 Ft (A/B tesztelve).

---

## 3. Validációs Kampány Rendszer

* **Célcsoport:** Elsődlegesen a korábbi VitaSteps fizikai túraérmes vásárlók.
* **Biztonságos Címzettazonosítás:** `?cid={{random_token}}` (soha nem kerül személyes adat URL-be).
* **Landing Page:** [`landing_predikalo1/kitero/index.html`](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/kitero/index.html)
* **Backend API:** [`landing_predikalo1/api/kitero.js`](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/api/kitero.js)
* **E-mail Sablon:** [`landing_predikalo1/email_templates/kitero_validation.html`](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/email_templates/kitero_validation.html)

---
id: ADR-011-experience-selector-main-gateway
type: decision
name: ADR-011 Élményközpontú Interaktív Főoldal Választóarchitektúra
status: active
date: 2026-11-05
deciders:
  - CEO
  - Lead Architect
consulted:
  - Marketing & UX
related:
  - "[[strategic-positioning|Strategic Positioning]]"
  - "[[ADR-009-strategic-ecosystem-pivot|ADR-009 Strategic Ecosystem Pivot]]"
  - "[[ADR-010-kitero-validation-architecture|ADR-010 Kitérő Validáció]]"
  - "[[kitero|VitaSteps Kitérő]]"
  - "[[verified-challenge|Verified Challenge]]"
---

# ⚖️ ADR-011: Élményközpontú Interaktív Főoldal Választóarchitektúra (/main)

## 1. Döntési Kontextus és Cél
A korábbi VitaSteps modell egyetlen termékcsoportot (hegyi túraérmeket) értékesített közvetlen hirdetési forgalomból. Az ökoszisztéma-bővítéssel és az új digitális városi élményséta termék (**[[kitero|VitaSteps Kitérő]]**) bevezetésével szükségessé vált egy olyan központi belépési pont (`/main`), amely nem közvetlenül termékeket akar eladni, hanem a látogató belső motivációjából és keresett élményéből indul ki.

A cél:
* Ne azzal kezdjünk, mit árulunk, hanem azzal, hogy **milyen élményt keres a látogató**.
* A két termékvonal (természetjáró fizikai túrák vs. önálló városi séták) közös márkaértékeit mutassuk be (*„MOZOGJ. FEDEZZ FEL. TELJESÍTS.”*).
* Interaktív, 2 lépéses választóval tereljük a látogatót a számára leginkább testhezálló kaland felé.
* Biztosítsunk azonnali, közvetlen választási lehetőséget is azoknak, akik nem kívánnak kérdésekre válaszolni.
* Teljes mérési és analitikai lefedettséget építsünk ki a preferenciák és kattintások monitorozására.

---

## 2. Meghozott Döntések

### 2.1. Nyitóképernyő: Érzelmi Motiváció és Közös Értékajánlat
* **Főcím:** *„Lépj ki a hétköznapokból. Fedezz fel többet!”*
* **Közös misszió:** Útnak indulás, felfedezés, teljesítmény és maradandó emlékek gyűjtése kötöttségek nélkül, 100%-ban saját tempóban.
* **Belépési CTA:** *„Találd meg a hozzád illő kalandot! Válaszolj néhány rövid kérdésre, és megmutatjuk, merre indulj.”* (1 perc, kötelezettségmentes).

### 2.2. Kétlépéses Mobilbarát Interaktív Választó
1. **1. Kérdés (Élmény & Hangulat):**
   * *Kiszakadás & feltöltődés* (természetközeli)
   * *Kihívás & sikerélmény* (teljesítményközpontú)
   * *Új helyek & történetek* (kulturális/felfedező)
2. **2. Kérdés (Helyszín & Mozgásforma):**
   * *Természetben túrázás, csúcshódítás, érem* (Hegyi kihívások)
   * *Városi utcák, rejtett kapualjak, történetek* (VitaSteps Kitérő)
   * *Mindkettő érdekel* (Hibrid ajánlat)
3. **Dinamikus Eredményoldal:**
   * **Elsődleges ajánlat:** A válaszok súlyozása alapján dedikált kártya kiemelt CTA-val (irány `/kitero` vagy `/index.html`).
   * **Másodlagos ajánlat (*„Ez is érdekelhet”*):** A másik termékcsoport alternatívaként felkínálva, megelőzve a látogató elvesztését.
   * **Újrakezdés:** Lehetőség a válaszok törlésére és az azonnali újraválasztásra.

### 2.3. Közvetlen Termékválasztó (Direct Choice Grid)
A főoldal alsó szekciójában a két termékvonal vizuálisan gazdag, egymás melletti kártyaként jelenik meg:
* **VitaSteps Túraérmek:** Prédikálószék Vertical 100, Nagy-Kevély Csillagai, prémium fémérmek, GPX igazolás.
* **VitaSteps Kitérő:** A Palotanegyed Titkai, hangos narráció, interaktív GPS térkép, app-letöltés nélkül.

### 2.4. Szigorú Névhasználati Szabály
* A digitális városi séta termék neve kizárólag **VitaSteps Kitérő** vagy **Kitérő**.
* A korábbi ideiglenes munkacímek (*Hosszú Lépések*) a felhasználói felületen és marketingkommunikációban szigorúan tiltottak.

### 2.5. Analitikai Eseményrendszer
A meglévő `js/tracker.js` infrastruktúrán keresztül a következő eseményeket naplózzuk a Supabase adatbázisba:
* `quiz_start`: Az interaktív választó elindítása (Hero CTA vagy opciókattintás).
* `quiz_answer`: Válaszadás az egyes lépéseknél (`question_id`, `answer_id`).
* `quiz_complete`: A kérdéssor sikeres befejezése az összesített válaszokkal.
* `quiz_result_view`: A megjelenített eredmény típusa (`kitero`, `medals`, `both`).
* `quiz_primary_click`: Az elsődleges ajánlat gombjára történő kattintás.
* `quiz_secondary_click`: A másodlagos (*„Ez is érdekelhet”*) ajánlatra történő kattintás.
* `product_direct_click`: A közvetlen termékkártyákra történő kattintás a lap alján.

---

## 3. Érintett Rendszerek és Fájlok
* **Frontend:** [`landing_predikalo1/main/index.html`](file:///E:/Data/other_projects/VitaSteps/landing_predikalo1/main/index.html)
* **Vercel Routing:** [`landing_predikalo1/vercel.json`](file:///E:/Data/other_projects/VitaSteps/landing_predikalo1/vercel.json) (`/main` rewrite)
* **Tudásbázis:** [`knowledge/concepts/strategic-positioning.md`](file:///E:/Data/other_projects/VitaSteps/knowledge/concepts/strategic-positioning.md), [`knowledge/INDEX.md`](file:///E:/Data/other_projects/VitaSteps/knowledge/INDEX.md)

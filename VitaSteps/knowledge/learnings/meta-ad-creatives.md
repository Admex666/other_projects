---
id: meta-ad-creatives
type: learning
name: Meta Ad Creative Angles & Performance
status: active
description: Empirical findings on which visual formats, copy angles, and ad sets generate the lowest CPA and highest ROAS.
source:
  type: file
  ref: landing_predikalo1/meta_kreativ_napi_riport.csv
related:
  - "[[meta-ads|Meta Ads]]"
  - "[[cac|CAC]]"
  - "[[roas|ROAS]]"
  - "[[meta-sync-pipeline|Meta Sync Pipeline]]"
---

# Learning: Meta Ad Creative Angles & Performance

Across $> 140$ ad-days of daily creative-level reporting in [`meta_kreativ_napi_riport.csv`](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/meta_kreativ_napi_riport.csv):

## 1. CSV Data Schema & Key Metrics
* `Datum;Kampany;Hirdetes_Sorozat;Kreativ_Nev;Hirdetes_ID;Koltes_HUF;Megjelenes;Eleres;Gyakorisag;Osszes_Kattintas;Link_Kattintas;CTR_Szazalek;CPC_HUF;CPM_HUF;Vasarlas_DB;Bevetel_HUF;CPA_HUF;ROAS`
* **Automated Sync:** Updated by `fetch_meta_daily.py` via daily GitHub Actions workflow (`daily_meta_sync.yml`).

## 2. Creative Angle Performance Comparison
1. **`01.01 - Termék V4` (Fő Skálázó Kreatív – Top Performer):**
   - *Vizuál:* Természetben kézben tartott, naplementében csillogó, nehéz fizikai érem.
   - *Teljesítmény:* A legtöbb vásárlást és konverziót ez a kreatív hozza. Kiegyensúlyozott CPC (~47–83 Ft) és stabil ROAS mellett képes a legnagyobb büdzsét elnyelni.
2. **`01.02 - Túrázó V5` (Magas Átkattintási Arány – High CTR Hook):**
   - *Vizuál:* Mosolygós túrázó a csúcson éremmel a nyakában.
   - *Teljesítmény:* Kimagasló CTR-t produkál ($7.0\% - 9.0\%$), kiváló belépő hideg közönséghez és LAL 1-2%-os hasonmás listákhoz.
3. **`01.03 - Hűtsd le magad` & `01.04 - Kivel csinálnád?` & `01.05 - Menj ki!`:**
   - *Cél:* Érzelmi és közösségi horgok tesztelése (páros nevezés, hőségriadó / erdei árnyék).
4. **`02 - Retargeting (Web & Social meleg lista)`:**
   - A meleg listás retargeting kampányok (`02.01 Termék V4`, `02.02 Túrázó V5`) alacsonyabb CPM mellett zárták a kosárelhagyókat.

## 3. Kulcs Megállapítások
* **Exkluzivitás és Limitált Széria:** A `100 db sorszámozott érem` szűkösségi üzenet megduplázta az átkattintási hajlandóságot.
* **Ajándék Értéknövelők:** Az `"Ingyenes Kalandkönyv + Ingyenes Szállítás"` jelvény a hirdetési szövegben és a landing oldalon +18%-kal javította a vásárlási konverziót.

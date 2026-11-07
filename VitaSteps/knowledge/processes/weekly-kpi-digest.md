---
id: weekly-kpi-digest
type: process
name: Weekly KPI Digest & Business Monitoring
status: active
description: Automatikus heti vezetői döntéstámogató riport, szabályalapú fedezetszámítás, adatfrissességi kapu és Pushbullet értesítő rendszer.
code:
  - landing_predikalo1/scripts/weekly_business_digest.py
  - landing_predikalo1/lib/admin/kpi-digest.js
  - landing_predikalo1/api/admin-data.js
  - landing_predikalo1/admin.html
---

# Process: Weekly KPI Digest & Business Monitoring

## 1. Context & Purpose
A **Heti KPI Digest és Üzleti Monitoring** rendszer célja, hogy a cégvezető (Adam) heti rendszerességgel, mindössze 1-2 perc alatt átlássa:
1. **Hol veszít pénzt a vállalkozás?** (kiszivárgások, inaktív akvizíció, elavult adatok, logisztikai torlódások)
2. **Hol van növekedési lehetőség?** (szabad éremkészlet monetizációja, digitális magas fedezetű termékek, magas NPS és ajánlási potenciál)
3. **Mi legyen a konkrét döntési lépés a következő héten?** (prioritásos cselekvési lista)

Kapcsolódó entitások és rendszerek:
* [[admin-panel|Admin Panel]]: Vezetői felület (`admin.html`) élő digest nézettel.
* [[unit-economics|Unit Economics]]: Fedezetszámítási szabályok (CM I és CM II).
* [[fixed-costs|Fixed Costs]] és [[variable-costs|Variable Costs]]: Egységköltség állandók.
* [[customer-funnel|Customer Funnel]]: Tölcsér- és lead konverziós mutatók.
* [[kitero|VitaSteps Kitérő]]: Validációs digitális séma béta kampány és tölcsér.

---

## 2. Zero-Hallucination & Data Freshness Gate
A heti riport kizárólag **tényadatokból és szabályalapú számításokból** építkezik. Nincs becsült vagy generált adat hiányzó források esetén:
* **Data Freshness Gate:**
  - **Supabase Orders:** utolsó fizetett, nem-teszt vásárlás időpontja és kora.
  - **Meta Marketing API / Napi Adatok:** utolsó rögzített hirdetési költés dátuma. Ha az adat > 3 napos, a rendszer explicit figyelmeztetést (`⚠️ Elavult`) jelenít meg, nem becsül költést.
  - **Stripe API:** élő bankszámla és jóváírási egyenleg (`api.stripe.com/v1/balance`).
  - **Supabase Leads & Analytics Events:** feliratkozások és Kitérő események legfrissebb állapota.
  - **Foxpost Logisztika:** `shipments` táblában lévő feladásra váró (`shipped = false`) csomagok száma.

---

## 3. Determinisztikus KPI Definíciók és Képletek

| Mutató | Forrás / Képlet | Magyarázat |
| :--- | :--- | :--- |
| **Bruttó Árbevétel (7d)** | $\sum \text{orders.amount\_total}$ (`stripe_payment_status = 'paid'`, `is_test = false`, utolsó 7 nap) | Ténylegesen befolyt heti árbevétel. |
| **Közvetlen Működési Költség** | $\text{Rendelések} \times (1\,250\,\text{Ft} + 35\,\text{Ft} + 120\,\text{Ft}) + \sum (\text{Árbevétel} \times 1.5\% + 50\,\text{Ft})$ | Foxpost szállítás, Számlázz.hu e-számla, doboz és Stripe díj. |
| **Érem Bekerülési Költség (COGS)** | $\text{Rendelések} \times 1\,630\,\text{Ft}$ | Alibaba éremgyártási bekerülési érték (163 000 Ft / 100 db). |
| **Fedezet I (CM I)** | $\text{Árbevétel} - (\text{Közvetlen Költségek} + \text{Érem COGS})$ | Közvetlen termék- és teljesítési fedezet. |
| **Fedezet I % (CM I %)** | $\frac{\text{CM I}}{\text{Árbevétel}} \times 100$ | Termékszintű bruttó fedezeti hányad. |
| **Meta Hirdetési Költés (7d)** | $\sum \text{meta\_daily\_metrics.spend}$ (utolsó 7 nap) | Meta Ads hirdetési kiadás (ha az adat friss). |
| **Fedezet II (CM II)** | $\text{CM I} - \text{Meta Költés}$ | Marketing kiadások után megmaradó nettó fedezet. |
| **Készlet Kifutás (Runway)** | $\frac{\text{Szabad Készlet}}{\text{Heti Sebesség (utolsó 30 nap simítva)}}$ | Hány hétre / hónapra elegendő a raktáron lévő éremállomány. |
| **Lead Konverziós Ráta** | $\frac{\text{Konvertált Leadek Száma}}{\text{Összes Lead Száma}} \times 100$ | Az ingyenes útvonalat letöltők vásárlási konverziója. |

---

## 4. Kézbesítési Csatornák & Használat

### 1. Pushbullet Mobil Értesítés (Elsődleges)
A heti digest strukturált, lényegretörő push üzenet formájában érkezik a tulajdonos okostelefonjára és számítógépére:
```bash
python landing_predikalo1/scripts/weekly_business_digest.py --push
```

### 2. Admin Felület (`admin.html`)
Az admin felületen a **📊 Vezetői Heti Digest** modulban egy kattintással elérhető:
* Élő Data Freshness Gate jelzőlámpák.
* Részletes pénzügyi és fedezeti kártyák.
* Készlet és kifutási mérők.
* "Pushbullet Küldése Most" azonnali manuális trigger gomb.

### 3. CLI és Automatizáció (Cron / Task Scheduler)
Strukturált JSON kimenet más rendszereknek vagy automatizációknak:
```bash
python landing_predikalo1/scripts/weekly_business_digest.py --json
```

---

## 5. Szabályalapú Döntési Logika (Heurisztikák)
* **Pénzszivárgás riasztás:**
  - Ha a Foxpost feladatlan csomagok száma $> 10$: logisztikai figyelmeztetés (NPS kockázat).
  - Ha a Meta adatok elavultak: riasztás a leállt hirdetéskövetésről / esetleges vakon költésről.
  - Ha a heti új rendelések száma $= 0$: tölcsér és akvizíció újraindítási javaslat.
* **Növekedési lehetőség detektálás:**
  - Ha a Pilis éremkészlet $> 50$ db: dedikált csillagászati / éjszakai túra kampány javaslat.
  - Kitérő digitális élményséta: magas (100%-os) fedezetű upsell meglévő vásárlóknak.
  - Magas NPS ($> 9.5$): ajánlói (referral) kódok és promóciók indítása.

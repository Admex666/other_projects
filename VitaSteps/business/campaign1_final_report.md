# VitaSteps - Prédikálószék Vertical
## Szuper Early Bird Kampány (Lezárva: 2026. május 19. 12:00)
### Hivatalos Üzleti & Konverziós Jelentés

Ez a jelentés a VitaSteps első éles pilot kampányának (Super Early Bird) lezárása után készült, összesítve a Facebook Ads, Vercel Analytics, Tally és Stripe adatokat.

---

## 1. Főbb Mutatók (KPI-ok)

| Mutató | Érték | Értékelés |
| :--- | :--- | :--- |
| **Összes marketing költés** | **7 265 Ft** | Rendkívül hatékony büdzsé-kihasználás. |
| **Összes bevétel** | **111 860 Ft** | 14 sikeres eladás (7 990 Ft / db áron). |
| **ROAS (Hirdetés Megtérülés)** | **15.39x** | Világklasszis e-commerce eredmény (1 Ft elköltött reklám 15.39 Ft-ot hozott). |
| **CAC (Ügyfélszerzési Költség)** | **519 Ft / fő** | A tervezett 2 000 Ft-os CAC mindössze 26%-a! |
| **Tiszta Működési Profit** | **64 527 Ft** | 57.68%-os nettó profithányad a változó költségekből. |
| **Projekt Megtérülési Egyenleg** | **+19 527 Ft** | **A projekt már az első héten teljesen kitermelte az összes induló tőkéjét és fix költségét!** |

---

## 2. A Konverziós Tölcsér (Funnel Analysis)

```mermaid
funnel
    title VitaSteps Super Early Bird Tölcsér
    Látogatók (Vercel): 587 : 100%
    Megtekintések (Facebook): 455 : 77.5%
    Átkattintás a Tally-ra: 108 : 18.4%
    Kosárba helyezés (Ads): 45 : 7.6%
    Checkout kezdeményezés: 23 : 3.9%
    Sikeres kitöltés (Tally): 16 : 2.7%
    Sikeres fizetés (Stripe/Revolut): 14 : 2.39%
```

### Konverziós arányok elemzése:
1.  **Vercel látogató ➡️ Tally látogatás: 18.4%**
    *   *Értékelés:* Zseniális! A mobil-optimalizálási javításaink és a tapadós (sticky) CTA gomb bevezetése után a látogatók csaknem ötöde átkattintott az űrlapra.
2.  **Tally látogatás ➡️ Tally kitöltés: 14.81%**
    *   *Értékelés:* A megadott mezők egyszerűsítése (Foxpost kereső opcionálissá tétele, kártyatulajdonos nevének elhagyása) kiváló eredményt hozott.
3.  **Tally kitöltés ➡️ Sikeres fizetés: 87.5%**
    *   *Értékelés:* A Stripe Tally-ba ágyazásával teljesen elimináltuk a korábbi Revolut Pay manuális fizetési lemorzsolódását. Az elmúlt 24 órában ez a mutató **100%**-os volt!

---

## 3. Pénzügyi Elemzés (Unit Economics)

*   **Egy darab termék eladási ára:** 7 990 Ft
*   **Változó költségek termékenként:**
    *   Landed cost (gyártás + ÁFA + vám): 1 512 Ft
    *   Belföldi szállítás (Foxpost átlag): 1 350 Ft
    *   Ügyfélszerzési költség (CAC): 519 Ft
    *   **Összes változó költség:** 3 381 Ft
*   **Fedezeti árrés termékenként:** **4 609 Ft / db (57.68%)**

### Teljes cash-flow egyenleg:
*   **Bruttó Bevétel:** +111 860 Ft
*   **Landed éremköltség (14 db):** -21 168 Ft
*   **Belföldi postázás (14 db):** -18 900 Ft
*   **Összesített marketing:** -7 265 Ft
*   **Kezdeti tőkeberuházás (weboldal/domain):** -30 000 Ft
*   **Könyvelő (Havi díj):** -15 000 Ft
*   ---
*   **NETTÓ CASH-FLOW EGYENLEG:** **+19 527 Ft (TISZTA HASZON)**

---

## 4. Stratégiai Irányelvek a 2. Kampányhoz (Scale Fázis)

A mai napon 12:00-kor sikeresen elindult a **2. Kampány**, amely immár napi **3 000 Ft-os** kerettel fut (2.5x-es növekedés), és az ár **8 990 Ft-ra** módosult.

### Javasolt teendők a heti skálázáshoz:

1.  **Dátumok kezelése:**
    *   A [main.js](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/main.js) és a [siker.html](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/siker.html) ma 12:00-kor zökkenőmentesen átváltottak a normál árazásra. 
    *   A hirdetésekben most a [ad_creative_predikalo1_final2.png](file:///e:/Data/other_projects/VitaSteps/campaigns/predikalo/ad_creative_predikalo1_final2.png) kép fut, amelyen a határidő **május 27-re** lett kitolva. Ez tökéletes, fenntartja a meleg kampány hangulatot a május 28-i hivatalos rajtig.
2.  **Meta Pixel optimalizáció:**
    *   A megnövelt büdzsével futó másodlagos kampányt már kizárólag **Purchase (Vásárlás)** konverziós eseményre optimalizálva hagyd futni, mivel a [siker.html](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/siker.html) most már tökéletesen és automatikusan jelenti a sikeres Stripe kifizetéseket!
3.  **Készletkezelés:**
    *   Jelenleg a 100 darabos limitált szériából **14 darab elkelt**. Már csak 86 darab érmünk van szabadon!
    *   Ha a napi 3.000 Ft-os büdzsé tartja ezt a kiemelkedő teljesítményt, napi 2-3 eladással kalkulálhatunk a következő héten, így a rajtig elérhetjük a 30-40%-os telítettséget, ami óriási közösségi erőt fog adni a kihívásnak.

*A jelentést összeállította: Antigravity AI Co-Pilot*

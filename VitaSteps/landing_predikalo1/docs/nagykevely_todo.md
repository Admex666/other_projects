# 🏔️ Nagy-Kevély Meta Kampány – Részletes TODO Lista

Ez a dokumentum a Nagy-Kevély csillagai Meta Ads kampány indításához szükséges feladatokat tartalmazza, különválasztva a manuális (Ads Manager, Stripe) és az AI által elvégezhető fejlesztési pontokat.

---

## 👥 1. Közönségek & Célzás (Büdzsé-optimalizálás)
*   [x] **Stripe vevőlista exportálása:** A korábbi Prédikálószék vásárlók e-mail címeinek kinyerése sikeresen megtörtént a Google Sheets-ből: [predikaloszek_emails.csv](file:///e:/Data/other_projects/VitaSteps/landing_predikalo1/docs/predikaloszek_emails.csv).
*   **[Manuális]** **Custom Audience feltöltése:** A legenerált `predikaloszek_emails.csv` feltöltése a Meta Business Managerbe mint *Egyéni célközönség*.
*   **[Manuális]** **Hasonmás Közönség (LAL 1-2%) generálása:** Hasonmás célközönségek képzése a vevőlistából Magyarország területére.
*   **[Manuális]** **Kizárások (Exclusions) beállítása:** A prospecting (hideg) kampányokból a korábbi vevők listájának és a `/siker.html` látogatóinak kifejezett kizárása.
*   **[Manuális]** **Retargeting kampány létrehozása:** Különálló, alacsony költségvetésű kampány beállítása a meleg látogatóknak (kizárva a vásárlókat).

---

## ✍️ 2. Kreatívok & Hirdetésszöveg (Copywriting & Visuals)
*   **[AI]** **Hirdetésszöveg verziók megírása:** Kreatív szövegek írása a fő kampányhoz (evergreen) és a retargeting fázishoz (FOMO).
*   **[AI / Manuális]** **Képi kreatívok / Banner koncepciók:** A hirdetésképek grafikai megtervezése és AI generálása (promptekkel vagy kész képekkel), majd feltöltése az Ads Managerbe.

---

## 🌐 3. Landing Page & Web-oldali FOMO (Frontend fejlesztések)
*   **[AI]** **Kalandkönyv promóció beépítése:** Kiemelt vizuális szekció készítése az ingyenes letölthető túrafüzetről a `nagykevely/index.html` oldalon.
*   **[AI]** **Közösségi statisztika (Social Proof) elhelyezése:** A *1 230 teljesített kilométer* statisztika beépítése a landing oldalra.
*   **[AI]** **Dinamikus Készlet- és Időjelző:** A számlálók (szeptember 6. nevezési zárás és 100 darabos készlet) JS kódjának és HTML elemeinek megírása.
*   **[AI]** **Térkép & GPX frissítése:** A Leaflet térkép felkészítése az új 4 útvonal GPX nyomvonalainak dinamikus megjelenítésére.

---

## ⚙️ 4. Technikai Ellenőrzés (Mérések & Integráció)
*   **[Manuális]** **Stripe kupon ellenőrzése:** A `VSBARAT10` ajánlói kuponkód éles ellenőrzése a Stripe Dashboardon.
*   **[Manuális]** **Pixel Helper ellenőrzés:** Chrome Pixel Helper bővítménnyel a `PageView`, `InitiateCheckout` és `Purchase` (7990 HUF értékkel) események lefutásának tesztelése.

# ADR-012: Menetrendek.hu Live Multi-Modal Transit Engine Integration

## Context
A VitaSteps Kísérő / Companion alkalmazás lényege az "otthontól otthonig" tartó élménytervezés. A korábbi lokális GTFS adatbázis csak a BKK nyílt adatbázisát és a Volánbusz járatait tartalmazta, azonban a MÁV-START elővárosi vasúti hálózata (S72, S76, Z72) zárt GTFS feeden keresztül érhető csak el. Ez azt eredményezte, hogy olyan optimális kapcsolatok, mint az Aquincum átszállás az S76-os vonatra (Pilisborosjenő / Üröm felé) nem jelentek meg a lokális tervezőben.

## Döntés
1. **Élő Menetrendek.hu JSON API integráció:** Nem használunk headless böngészőt (Selenium / Playwright). A Menetrendek.hu belső végpontját (`https://menetrendek.hu/menetrend/newinterface/index.php`) szólítjuk meg közvetlenül a Node.js futtatókörnyezetből (`lib/menetrendek-client.js`).
2. **Teljes Hálózati Lefedettség:** Az összes releváns hálózati azonosító bekapcsolásra került:
   - `1`: Volánbusz helyközi
   - `2`: MÁV-START vasút (S72, S76, Z72, stb.)
   - `10, 24`: BKK agglomerációs buszok (218, 840, stb.)
   - `12`: Villamosok
   - `13`: BKK HÉV (H5, H6, H7, H8, H9)
   - `14`: Metrók
3. **Időrendi Rendezés (`rendezes: 1`):** A szerver felé kötelezően átadjuk a `rendezes: 1` paramétert, amely indulási idő szerint növekvő sorrendbe rendezi az útvonalakat. Ez biztosítja, hogy a gyorsabb, de több átszállásos kombinációk (pl. HÉV + S76 vonat + 218 busz) ne szoruljanak a 20+ találat mögé.
4. **Hibrid Fallback Modell:** Ha a külső hálózati hívás meghiúsulna, a rendszer észrevétlenül visszatér a lokális `companion-service` távolság- és menetrend-alapú becsléséhez.

## Következmények
- **Pozitív:** 100%-ban valós, percrekész MÁV + HÉV + Volánbusz csatlakozások a felhasználói felületen. Pomáz $\rightarrow$ Pilisborosjenő elérése 50 percre csökkent az S76-os vonattal.
- **Kockázat:** Függőség a Menetrendek.hu külső JSON protokolljától. Ezt védi a beépített fallback logika.

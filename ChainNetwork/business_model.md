# ChainNetwork: Implementációs Roadmap & Üzleti Modell

Ez a dokumentum segít átlátni a folyamatot a tulajdonos szempontjából, és megválaszolja a "Hogyan működik ez a gyakorlatban?" kérdést.

## 1. Fázis: A "Profit Audit" (Validáció) - 1 hét
*   **Cél:** Megmutatni a rejtett veszteséget valódi adatokon.
*   **Folyamat:** 
    *   Az étterem küld egy anonim CSV exportot az elmúlt 3-6 hónap tranzakcióiról.
    *   Feltöltjük a ChainNetwork analyzerbe.
    *   Prezentálunk egy jelentést: "Havi X forintot veszítesz a lemorzsolódó törzsvendégeken és az elmaradt upsell-en."
*   **Költség:** Ingyenes.

## 2. Fázis: A "Pilot" Időszak (Mérés) - 1-2 hónap
*   **Cél:** Bizonyítani a modell hatékonyságát élesben, kockázat nélkül.
*   **Integráció:** 
    *   **Light-weight:** QR kódos asztali kártyák / blokkra nyomtatott kód.
    *   **App-mentes:** Apple/Google Wallet alapú hűségkártya regisztráció (1 kattintás).
*   **A/B Teszt beállítása:**
    *   **Group A (5%):** Nem kapnak semmit (Kontroll).
    *   **Group B (95%):** A Decision Engine automatikusan kezeli őket (Intervenciók).
*   **Költség:** Csak egyszeri setup díj (integrációs költség).

## 3. Fázis: "Full Automation" (Skálázás)
*   **Cél:** Maximális profit kitermelése emberi beavatkozás nélkül.
*   **Folyamat:** 
    *   A POS rendszer (Laurel, iiko, rkeeper, stb.) direkt összekötése.
    *   A Decision Engine 24/7-ben figyeli a tranzakciókat.
    *   Automatikus kiküldések (Wallet push, E-mail) a megfelelő pillanatban.
*   **Üzleti modell (Sikerdíj):** 
    *   `Havi Díj = (Profit/User_B - Profit/User_A) * Felhasználók száma * 15%`.
    *   **Tehát:** Csak akkor fizetnek, ha a rendszer bizonyíthatóan több pénzt hozott, mint amennyi magától jött volna be.

---

## Technikai Megvalósítás: A "Frictionless" Loop

### 1. QR -> WebApp -> Wallet folyamat
*   **Egyedi QR a blokkon:** A POS minden tranzakcióhoz egyedi azonosítóval ellátott QR kódot nyomtat.
*   **Zero-Login WebApp:** A szkennelés egy olyan mobiloldalra visz, ahol nincs szükség jelszóra. A tranzakció adatai a URL-ből automatikusan betöltődnek.
*   **Wallet Integráció:** Egy kattintással Apple/Google Wallet kártya generálódik. Ez lesz az állandó azonosító, amihez a későbbi vásárlások és push üzenetek kötődnek.

### 2. Decision Engine Adatpontok
A rendszer az alábbi adatokat elemzi minden tranzakciónál:
*   **Tranzakciós profil:** Időpont, lokáció, kosárérték, pontos tételek.
*   **Viselkedési profil (RFM):** Milyen gyakran jár vissza (Frequency), mikor volt utoljára (Recency), mennyi profitot termelt összesen (Monetary).
*   **Életstílus szegmentáció:** Automatikus címkézés a fogyasztási szokások alapján (Office, Student, Family, Tourist).
*   **Social Graph:** Ajánlási láncok, csoportos fogyasztási mintázatok és hálózati elérés értéke (Network Reach Value).

---

## Miért jó ez az Étteremnek?
1.  **Láthatatlan:** Nem zavarja a napi operációt, a kasszásnak nem kell semmit pluszban csinálnia.
2.  **Biztonságos:** A Pánik gomb és a terhelés-figyelés védi a konyhát.
3.  **Adatvagyon:** Végre tudják, kik a vendégeik, nem csak azt, hogy mit adtak el.
4.  **GDPR Kompatibilis:** Zero-party data gyűjtés (önkéntes hozzájárulás a Wallet mentésekor).

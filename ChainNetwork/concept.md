# ChainNetwork - Friction-Free Éttermi Loyalty & Analytics Koncepció

## 1. Vízió
Egy olyan "súrlódásmentes" (friction-free) hűségprogram és elemző platform, amely nem csupán adatokat gyűjt, hanem automatizált döntéshozatali motorral (decision engine) segíti a kisebb étteremláncok (pl. Bamba Marha, Pesti Pipi) profitabilitásának és bevételének növelését.

**A fő értékajánlat:** *"Havi +10-30% extra bevétel automatizáltan, kézi munka nélkül."*

---

## 2. Adatforrások és Integráció
A rendszer három fő pilléren nyugszik az adatgyűjtés tekintetében:

| Adatforrás | Tartalom | Integrációs megoldás |
| :--- | :--- | :--- |
| **POS Rendszer** | Tranzakciók (idő, összeg, tételek), fizetési mód, lokáció. | Webhook-ok (Laurel, Storebox, iiko, Lightspeed). |
| **Loyalty Azonosítás** | User ID, vásárlás összekapcsolása. | QR a blokkon, telefonszám, bankkártya tokenizáció. |
| **Viselkedési Adat** | App megnyitás, kattintások, kuponhasználat. | In-app eseménykövetés. |

---

## 3. Analitikai Modulok (Actionable Insights)
A platform nem bullshit dashboardokat, hanem konkrét üzleti eredményt produkáló elemzéseket futtat:

*   **RFM Szegmentáció:** Vásárlók csoportosítása (Recency, Frequency, Monetary) alapján. (Pl. VIP-nek nem kell kedvezmény, a lemorzsolódóknak agresszív kupon kell).
*   **Kosárelemzés (Market Basket):** Kapcsolt termékek értékesítése (Upsell). Pl. "Burger mellé 65% eséllyel kérnek kólát" -> Automatikus ajánlat a pénztárnál.
*   **Időalapú Keresletkezelés:** A "holtidők" (pl. 14:00-16:00) monetizálása célzott, csak akkor érvényes ajánlatokkal.
*   **Churn Prediction (AI):** A lemorzsolódás valószínűségének becslése és automatikus visszacsábító kampányok indítása.
*   **Price Sensitivity:** Megkülönbözteti az akciómániásokat a teljes árat fizető törzsvendégektől.

---

## 4. Technológiai Architektúra
1.  **Ingestion:** POS Webhook -> API -> Message Queue (Kafka/PubSub).
2.  **Storage:** Raw Data (S3/BigQuery).
3.  **Processing:** Adattranszformáció (dbt) és ML modellek futtatása.
4.  **Action Layer:** Automatikus push üzenetek, kuponkiküldés, POS szinkronizáció.

---

## 5. Piaci Helyzetkép (Magyarország)
### Versenytársak:
*   **POS-beépített:** BarSoft (Erős integráció, de kevésbé mély analitika).
*   **Standalone Appok:** Revino, Stampet, Yalty (Főleg hűségkártya-pótlók).
*   **Platformok:** Wolt+ (Magas jutalék, de nagy frekvencia).

### Mi az "Edge"?
A legtöbb rendszer csupán egy **eszköz (tool)**. A ChainNetwork egy **döntési motor (decision engine)**, ami nem csak megmutatja a problémát, hanem automatikusan elvégzi a korrekciót (pl. kiküldi a kupont).

---

## 6. Üzleti Modell
*   **SaaS havidíj:** Fix alapdíj az étteremnek.
*   **Revenue Share:** Jutalék a rendszer által generált extra bevételből (pl. visszahozott churned userek).
*   **Premium Analytics:** Haladó elemzések nagyobb láncoknak.

---

## 7. MVP Fókusz (2-3 hónap)
1.  Egyetlen kritikus POS integráció (pl. Laurel vagy iiko).
2.  Friction-free azonosítás (QR kód a blokk alján).
3.  Alap RFM szegmentáció és automatikus kuponküldés.
4.  Egyszerű ROI dashboard a tulajdonosnak.

---

## 8. Kockázatok és Megoldások
*   **POS Integráció Pokol:** Egységesített API réteg kialakítása.
*   **Adatminőség:** SKU normalizáció és adat-tisztítási csatornák.
*   **App Fatigue:** Nincs kötelező app-letöltés; web-alapú, azonnali elérés QR kód után.
*   **GDPR:** Consent-management beépítése az első interakcióba.

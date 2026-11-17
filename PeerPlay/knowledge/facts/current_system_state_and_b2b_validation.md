# 🏛️ Faktuális Rendszerállapot és B2B Validációs Architektúra

> **Dátum:** 2026-11-17  
> **Projekt:** PeerPlay Vállalati Szimuláció (`peerplay`)  
> **Kontextus:** MVP Fejlesztési Állapot, ONA Szociometria, Reprodukálható Diagnosztika és B2B Validációs Pipeline

---

## 1. Vezetői Összefoglaló (A PeerPlay Koncepciója)
A PeerPlay egy adatvezérelt, hibrid **szervezetfejlesztési és csapatdinamikai szimulációs platform**, amely a hagyományos, passzív csapatépítőket váltja fel egy üzleti értékkel bíró diagnosztikai eszközzel.
- **Piaci rés:** A vállalatok milliós büdzséket költenek élményprogramokra, de a részlegek (pl. Pénzügy, Gyártás, K+F) közötti silók hétfőn változatlanul fennmaradnak.
- **Megoldás (Trading Game):** 90 perces intenzív kereskedelmi műhelymunka fizikai eszközökkel (papír, olló, vonalzó, sablonok), ahol a résztvevők aszimmetrikus erőforrásokkal termelnek a Központi Banknak és egymással kénytelenek kooperálni.
- **Mérési réteg (ONA):** A mobil kísérő (PWA HUD) valós időben rögzíti a tranzakciókat és a záró felmérést, amiből a rendszer azonnal felépíti a szervezeti hálózati térképet, azonosítja az informális közvetítőket (brokerek), és kimutatja a mentális energiamozgást ($\Delta$ Energia).

---

## 2. Megvalósított Rendszerkomponensek & Architektúra

### A. Mobil Kísérő & Játékos HUD (`/player`)
- **PWA / Mobil nézet:** Papírmentes tranzakciókezelés, közvetlen numerikus beviteli mezők, érintésbarát gombok.
- **Kérdőív és Felmérés:** 1-érintéses energiaszint skála (pre/post), megbízhatósági értékelés és szöveges peer értékelés a játék végén.
- **Valós Szervezeti Osztály (Department):** A Prisma séma bővítve (`User.department`), így a játékosok valós osztálya (Pénzügy, Gyártás, K+F, Értékesítés, QA, Logisztika stb.) rögzítésre kerül.

### B. Facilitátori Pult & ONA Hálózati Térkép (`TradeNetworkMap.tsx`)
- **Makro nézet:** Vállalatok közötti kereskedelem + Központi Bank kapcsolatok.
- **Mikro / ONA Szociogram nézet (Bizalmas facilitátori nézet):** 
  - Egyéni szintű interakciós gráf.
  - Dinamikus színezés: Szimulációs csapat szerint VAGY Valós szervezeti osztály (Department) szerint.
  - Részletes személyi adatlap (Inspector): Tranzakciós aktivitás, közvetítői státusz, leadott peer értékelések.

### C. Reprodukálható Szimuláció (`DEMO01`)
- **Adatbázis:** SQLite (`prisma/dev.db`), `DEMO01` munkamenet PIN-kód.
- **Szimulációs script:** `scripts/simulate-session.ts` — 8 résztvevő, 8 valós szervezeti egység, $3,050 banki kifizetés, 83.3% hálózati sűrűség, és szándékosan szimulált siló a Gyártás és K+F között.

---

## 3. B2B Értékesítési és Megkeresési Eszköztár

A hideg megkeresés és a pilot zárás támogatására elkészült a teljes operatív eszközkészlet:

| Komponens | Elérési Út | Leírás |
| :--- | :--- | :--- |
| **Vezetői Mintariport (PDF)** | [PeerPlay_Vezetoi_Mintariport_DEMO01.pdf](file:///C:/Users/Adam/Data/other_projects/PeerPlay/public/PeerPlay_Vezetoi_Mintariport_DEMO01.pdf) | 2 oldalas, vektoros nyomtatási PDF (531 KB) valós KPI-kkal, ONA gráffal és 4 HR akciójavaslattal. |
| **Riport HTML Forrás** | [executive_report_demo01.html](file:///C:/Users/Adam/Data/other_projects/PeerPlay/public/executive_report_demo01.html) | Headless böngészővel generálható, print-CSS sablon. |
| **Email Sablon** | [email-pitch-template.html](file:///C:/Users/Adam/Data/other_projects/PeerPlay/public/email-pitch-template.html) | Partneri, B2B pilot felajánlás, beágyazott illusztrációkkal. |
| **Mobil Mockup Kép** | [mockup_mobile_hud.png](file:///C:/Users/Adam/Data/other_projects/PeerPlay/public/images/mockup_mobile_hud.png) | A mobil játékosfelület látványterve. |
| **ONA Mockup Kép** | [mockup_ona_network.png](file:///C:/Users/Adam/Data/other_projects/PeerPlay/public/images/mockup_ona_network.png) | A szociometriai hálózati térkép a valós osztályok színei szerint. |

---

## 4. Algoritmikus Lead Engine & Email Validáció

A közvetlen vezetői elérhetőségek felderítésére kifejlesztett lokális motor:
- **Motor Script:** `scripts/b2b_lead_engine.py`
- **Adatbázis:** `data/b2b_lead_pipeline.db` (SQLite: `companies`, `leads`, `email_candidates`).
- **Dashboard:** [b2b_leads_dashboard.html](file:///C:/Users/Adam/Data/other_projects/PeerPlay/public/b2b_leads_dashboard.html).
- **Működése:**
  1. **DNS & SPF detektálás:** Automatikusan felismeri a vállalati levelezőt (Microsoft 365 vs Google Workspace vs Hibrid szerver).
  2. **Név Normalizáció:** Magyar ékezetmentesítés, titulusok (`Dr.`, `ifj.`) kezelése.
  3. **Permutáció:** 6 vállalati mintát állít elő rangsorolt valószínűséggel (M365/Google esetén `keresztnev.vezeteknev` 85%-os konfidenciával).
  4. **Hálózati Védelmi Felismerés:** Érzékeli a lakossági/irodai internetszolgáltatók kimenő 25-ös TCP port szűrését (`WSAEWOULDBLOCK / 10035`), így biztonságos heurisztikára vált.

---

## 5. B2B Outreach Szabályok és Következő Lépések

1. **Email kézbesítési szabály:** Nem küldünk ki vakon párhuzamos email permutációkat ugyanannak a személynek (a magas bounce rate elkerülése és a domain reputáció védelme érdekében). Csak a legmagasabb konfidenciájú címet használjuk.
2. **Domain védelem:** Tömeges megkereséshez másodlagos domain (Domain Burner stratégia) javasolt.
3. **Konverziós cél:** Az első levélben csupán egy alacsony ellenállású mikrodöntést kérünk (*"Lenne értelme átküldeni a 2 oldalas mintariportot?"*), a mintariport kiküldése után pedig 15 perces strukturált Zoom hívás a zárt pilot partnerség megkötésére.

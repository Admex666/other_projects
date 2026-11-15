# 📱 Mobile Tunnel, Real-Time Phase Sync & Hungarian UI Simplicity

## 1. Kizárólagos Magyar, Közérthető Terminológia a UI-on
A felhasználói felületeken (Facilitátori Irányítópult, Csapatpult, Mobil Kísérő, Kivetítő) **szigorúan tilos** a belső adatbázis-enumok (`PHASE_1_PRE_SURVEY`, `DRAFT`, `CAPITAL`, `PENDING`), specifikációs kódok (`S-MOB-02`, `S-FAC-03`, `S-TEAM-03`) vagy angol munkanevek (`Pre-Game Pulse`, `Post-Game Peer Feedback`, `Debrief`, `Broker`, `Enabler`, `Immediate Escrow`, `Refund`) megjelenítése.

### Kanonikus Központi Szótárak (`src/modules/session/constants.ts`)
Minden UI komponensnek a `src/modules/session/constants.ts` segédfüggvényeit kell használnia:
- **`getPhaseLabel(phase)` (`PHASE_LABELS`)**:
  - `PHASE_0_SETUP`: `'Előkészítés'`
  - `PHASE_1_PRE_SURVEY`: `'Kezdő felmérés'`
  - `PHASE_2_RULES`: `'Szabályismertetés'`
  - `PHASE_3_PLANNING`: `'Csapatstratégia'`
  - `PHASE_4_ROUND_1`: `'1. Kereskedelmi kör'`
  - `PHASE_5_EVENT_1`: `'1. Piaci esemény'`
  - `PHASE_6_ROUND_2`: `'2. Kereskedelmi kör'`
  - `PHASE_7_EVENT_2`: `'2. Piaci esemény'`
  - `PHASE_8_ROUND_3`: `'3. Kereskedelmi kör'`
  - `PHASE_9_BANK_SETTLEMENT`: `'Banki elszámolás'`
  - `PHASE_10_POST_SURVEY`: `'Záró értékelés'`
  - `PHASE_11_DEBRIEF`: `'Eredményhirdetés'`
- **`getStatusLabel(status)` (`SESSION_STATUS_LABELS`)**: `'Előkészítés alatt'`, `'Folyamatban'`, `'Lezárva'`, `'Archivált'`
- **`getProfileLabel(code)` (`TEAM_PROFILE_LABELS`)**: `'Tőkeerős'`, `'Nyersanyag-birtokos'`, `'Technológiai'`, `'Feltörekvő'`
- **`getTradeStatusLabel(status)` (`TRADE_STATUS_LABELS`)**: `'Függőben'`, `'Elfogadva'`, `'Elutasítva'`, `'Visszavonva'`, `'Lejárt (visszatérítve)'`

---

## 2. Minimalista, Minden Képarányban Látható Elrendezés
- A navigációs sávok, fejlécek és munkamenet-listák nem használhatnak fix szélességű, horizontálisan kilógó táblázatokat a kritikus vezérlőgombokhoz.
- Minden kártya és fejléc `flex-wrap` alapú, kompakt elrendezést használ, így keskeny ablakban, osztott képernyőn és mobilon is azonnal, vízszintes görgetés nélkül láthatók az akciók (`Belépés (Konzol)`, `Csapatpult`, `Eredmények`).

---

## 3. 2 Másodperces Valós Idejű Fázis-Szinkronizáció & Mobil Megbízhatóság
### Hogyan biztosítjuk az azonnali (2–3 mp-en belüli) automatikus fázisváltást manuális oldalfrissítés nélkül?
1. **Cache-Control No-Store API válaszok (`GET /api/session/[id]`)**:
   - A végpont explicit `Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate` fejléccel válaszol, a kliensek pedig `?t=${Date.now()}` + `{ cache: 'no-store' }` opcióval kérdeznek le `2000ms`-os SWR intervallummal (`refreshInterval: 2000, dedupingInterval: 1000`). Ez megakadályozza, hogy a mobil böngésző vagy a Cloudflare Quick Tunnel köztes rétege elavult (stale) állapotot adjon vissza.
2. **Azonnali Optimista Mutáció (`onMutate`)**:
   - Amikor a facilitátor fázist léptet (`advanceSessionPhase`), időzítőt módosít (`adjustPhaseTimer`), banki kifizetést rögzít (`executeBatchBankSale`) vagy piaci hírt küld ki (`triggerMarketEvent`), a komponens azonnal meghívja az SWR `mutate()` függvényét (`onMutate`), így a saját konzol 0ms alatt frissül.
3. **Fázis-alapú Mobil Nézetváltás (`SurveyPageClient.tsx`)**:
   - A `PreGamePulseForm` kizárólag a `PHASE_0_SETUP` és `PHASE_1_PRE_SURVEY` fázisokban látható (ha a játékos még nem küldte be).
   - Amint a facilitátor továbblépteti a munkamenetet a `PHASE_2_RULES` vagy bármelyik későbbi (2–9.) fázisra, a játékosok mobilja **2 másodpercen belül automatikusan átvált a `MobileCompanionHUD` nézetre**, még akkor is, ha valaki később csatlakozott és nem töltötte ki a kezdő kérdőívet.
   - A `PHASE_10_POST_SURVEY` fázisba lépve a mobilok automatikusan átváltanak a `PostGamePeerFeedbackForm` záró értékelésre, a `PHASE_11_DEBRIEF` fázisban pedig az eredményhirdetés összegző képernyőre.
4. **0ms-os Érintés- és Csúszka-Reakció (Progressive Enhancement)**:
   - A mobil kérdőívek (`PreGamePulseForm`, `PostGamePeerFeedbackForm`) natív HTML `action="/api/survey" method="POST"` fallbackkel, `1..10` gyorsválasztó gombokkal és hidratáció előtti (inline) DOM-eseménykezelővel működnek, így lassú mobilhálózaton vagy alagúton keresztül is azonnali vizuális visszajelzést adnak.

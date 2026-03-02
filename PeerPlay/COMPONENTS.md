# COMPONENTS.md – UI Komponens Referencia

## Játékos oldal komponensek

### `PlaySessionClient`
**Fájl:** `src/app/(player)/play/[sessionId]/PlaySessionClient.tsx`

Fő játékos nézet. SWR-el pollol session adatot és trade-eket (3s).  
Tartalmaz:
- Bal oszlop: Erőforrás dashboard, ProductionPanel, InventoryPanel
- Jobb oszlop: 3 fülös UI (🤝 Trade / 📬 Ajánlatok / 🏦 Bank)

**Props:** `sessionId`, `initialUserId`, `initialSessionData`

---

### `ProductionPanel`
**Fájl:** `src/components/ProductionPanel.tsx`

Megjeleníti a 4 gyártható terméket (Búza, Kukorica, Napraforgó, Bor).  
- Zöld gomb = gyártható (van elég vetőmag + tech)
- Szürke = nincs elég erőforrás
- `produceItem` server action hívás → inventory-ba kerül a termény

**Props:** `sessionId`, `myParticipant`

---

### `InventoryPanel`
**Fájl:** `src/components/InventoryPanel.tsx`

Megjeleníti a játékos raktárát (legyártott termékek).  
Eladás gomb → `sellToBank` action (de a Bank fülben is elérhető, ott részletesebb).

**Props:** `sessionId`, `userId`, `inventoryJson`

---

### `BankPanel`
**Fájl:** `src/components/BankPanel.tsx`

Banki árfolyam tábla. **Ez a fő eladás/vételi interfész.**

| Sor | Eladás | Vétel |
|---|---|---|
| 🌱 Vetőmag | — | $50/db (fix) |
| 🌾 Búza | alap×eff | alap×1.3 |
| ... | | |

- Eladás: `sellToBank` → tőke nő
- Vétel: `buyFromBank` / `buyRawMaterial` → tőke csökken, inventory nő
- Disabled gomb ha nincs elég tőke/készlet

**Props:** `sessionId`, `userId`, `participant`

---

### `TradeOfferForm`
**Fájl:** `src/components/TradeOfferForm.tsx`

P2P ajánlat küldés más játékosnak.
- "Amit TE adsz" → max értékek a saját készlethez kötve (nem lehet többet kínálni mint amennyi van)
- "Amit KÉRSZ" → szabad (nem tudhatjuk a másik készletét)
- Küld → `sendTradeRequest` action

**Props:** `sessionId`, `currentUserId`, `myParticipant`, `otherParticipants`

---

### `PendingTradesPanel`
**Fájl:** `src/components/PendingTradesPanel.tsx`

Bejövő/kimenő trade ajánlatok listája.
- Bejövő: ✓ Elfogad / ✕ Elutasít gomb
- Kimenő: Visszavon gomb
- Előzmények collapsible szekcióban

**Props:** `sessionId`, `currentUserId`, `trades`

---

## HR oldal komponensek

### `SessionDetailClient`
**Fájl:** `src/app/(hr)/sessions/[id]/SessionDetailClient.tsx`

HR session részletező oldal. SWR polling (5s).  
- Draft: `HRTeamAllocationPanel` megjelenik
- Active/Closed: NetworkGraph + `HRReportPanel` megjelenik

---

### `HRTeamAllocationPanel`
**Fájl:** `src/components/HRTeamAllocationPanel.tsx`

Lobby kiosztás panel. Csak draft session-ben látható.

1. **"Farmok Létrehozása"** (kék gomb) → `createTeamsForSession` → 5 farm slot létrejön DB-ben
2. Dropdown a farmok alatt → `assignParticipantToTeam` → játékos kap farmot
3. ✕ gomb → visszavesz játékost a farmból

> ⚠️ A state `useEffect`-tel szinkronizálódik a SWR prop-okkal, ezért nem kell oldalfrissítés.

**Props:** `sessionId`, `participants`, `teams`

---

### `HRReportPanel`
**Fájl:** `src/components/HRReportPanel.tsx`

Élő csapat rangsor és vagyon aggregáció. Csak active/closed session-ben.

- Rendezi csapatokat: Tőke + Készlet átszámított értéke szerint
- 🥇🥈🥉 jelzés a top 3-nak
- Tag szintű bontás minden csapatnál

**Props:** `teams`, `participants`

---

### `NetworkGraph`
**Fájl:** `src/components/NetworkGraph.tsx`

Interakciós és percepciós network gráf. D3 alapú.  
Csomópontok = játékosok, élek = interakciók / survey válaszok.

---

## Konstans fájlok

### `src/modules/interaction/constants.ts`
```ts
PRODUCTION_RECIPES  // wheat, corn, sunflower, wine receptek
type ProductType    // 'wheat' | 'corn' | 'sunflower' | 'wine'
```

### `src/modules/session/teamProfiles.ts`
```ts
TEAM_PROFILES  // 5 farm profil: type, name, raw, tech, cap, eff
```

### `src/modules/interaction/bankConstants.ts`
```ts
BANK_BUY_MARKUP = 1.3
RAW_MATERIAL_BUY_PRICE = 50
```

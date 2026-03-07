# PeerPlay – Developer README

> Behavioral Simulation Platform for HR & Organizational Diagnostics  
> Flagship scenario: **Global Exchange** (Mezőgazdasági téma)

---

## Quick Start

```bash
npm install
npx prisma generate
npx prisma db push
npm run dev
```

App fut: [http://localhost:3000](http://localhost:3000)

---

## Stack

| Layer | Technológia |
|---|---|
| Framework | Next.js 16 (App Router, Turbopack) |
| Database | SQLite (via Prisma ORM) |
| Styling | Tailwind CSS |
| Polling | SWR (3s interval) |
| Server Actions | Next.js `'use server'` |

---

## Projekt struktúra

```
src/
  app/
    (hr)/          ← HR dashboard oldalak
      dashboard/   ← Szervezet áttekintő
      sessions/    ← Session lista + detail
    (player)/      ← Játékos oldalak
      join/        ← Csatlakozás kóddal
      play/        ← Aktív játék nézet
    survey/        ← Session utáni kérdőív

  components/      ← UI komponensek
    BankPanel.tsx           ← Banki árfolyam tábla (vétel/eladás)
    HRTeamAllocationPanel.tsx ← Lobby kiosztás HR-nek
    HRReportPanel.tsx       ← Csapat rangsor + aggregáció
    InventoryPanel.tsx      ← Játékos raktár
    PendingTradesPanel.tsx  ← Bejövő/kimenő ajánlatok
    ProductionPanel.tsx     ← Termelési panel
    TradeOfferForm.tsx      ← P2P ajánlat küldés

  modules/
    session/
      actions.ts       ← Session CRUD server actions
      teamProfiles.ts  ← TEAM_PROFILES konstans (NEM 'use server')
    interaction/
      bank.ts          ← sellToBank, buyFromBank, buyRawMaterial
      bankConstants.ts ← BANK_BUY_MARKUP, RAW_MATERIAL_BUY_PRICE (NEM 'use server')
      constants.ts     ← PRODUCTION_RECIPES, ProductType
      production.ts    ← produceItem server action
      trade.ts         ← sendTradeRequest, acceptTrade, rejectTrade, cancelTrade

prisma/
  schema.prisma    ← Adatbázis séma
  dev.db           ← SQLite adatbázis fájl
```

---

## ⚠️ Fontos szabályok — `'use server'` fájlok

A Next.js **csak `async function` exportot enged** `'use server'` fájlokból.  
**Konstansokat SOHA ne exportálj `'use server'` fájlból!**

Megoldás: külön `.ts` fájlba (pl. `teamProfiles.ts`, `bankConstants.ts`), onnan importáld mindkét helyen.

---

## Adatbázis kezelés

```bash
# Séma változás után:
npx prisma generate      # Prisma client újragenerálás
npx prisma db push       # DB szinkronizálás (figyelem: data loss!)

# Adatbázis böngészés:
npx prisma studio
```

**DB fájl helye:** `prisma/dev.db`

---

## Game Logic összefoglaló

### Csapatok (TEAM_PROFILES)
5 előre definiált Farm típus különböző erőforrás profillal:
- **Alpha** – High Tech, Low Raw, 1.4x hatékonyság
- **Beta** – High Raw, Low Tech, 0.8x hatékonyság
- **Gamma** – Balanced, 1.0x hatékonyság
- **Delta** – Financial Power (sok tőke), 1.0x hatékonyság
- **Epsilon** – Hidden Innovation (közepes minden), 1.2x hatékonyság

### Termények (PRODUCTION_RECIPES)
| Termék | Vetőmag | Tech req | Alap ár |
|---|---|---|---|
| 🌾 Búza | 1 | 1 | 100 |
| 🌽 Kukorica | 2 | 2 | 250 |
| 🌻 Napraforgó | 1 | 3 | 180 |
| 🍷 Bor | 3 | 4 | 400 |

**Tényleges eladási ár** = alap × `productionEff` (csapatfüggő)  
**Banki vételi ár** = alap × 1.3 (markup)

### Trade rendszer
1. Játékos küld ajánlatot (`sendTradeRequest`) — mit ad, mit kér
2. Fogadó látja `📬 Ajánlatok` tabban (3s polling)
3. Elfogad → atomikus Prisma tranzakció, mindkét inventory frissül
4. Minden elfogadott trade = `Interaction` log bejegyzés

---

## Fejlesztési konvenciók

- Server Actions: `modules/` mappában, `'use server'` fájlonként
- Komponensek: `components/` mappában, `'use client'`
- Polling: SWR `refreshInterval: 3000` mindenhol
- Magyar UI szövegek (a platform célja magyar HR)
- `any` cast: csak `// eslint-disable-next-line @typescript-eslint/no-explicit-any` kommenttel

---

## Következő fejlesztési irányok (backlog)

- [ ] Round management (HR indít/zár köröket)
- [ ] Event engine (Market Shock, Resource Discovery)
- [ ] Időbeli összehasonlítás (két session networkje)
- [ ] WebSocket alapú valós idejű frissítés (SWR polling kiváltása)
- [ ] Automatikus debrief report export (PDF)

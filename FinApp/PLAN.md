# 💰 FinApp – Személyes Pénzügyi PWA: Implementációs Terv

## 🎯 Összefoglaló

Egy **mobil-first Progressive Web App** személyes és vállalkozási pénzügyekhez, amelyet Vercel-en hosztolunk. Két felhasználó (te + párod) osztja meg a rendszert, valós számlákra épülő virtuális zsebekkel, VitaSteps üzleti számviteli modullal és automatikus devizakonverzióval.

---

## 🛠️ Tech Stack

| Réteg | Technológia | Indok |
|---|---|---|
| **Frontend** | Next.js 14 (App Router) + TypeScript | Vercel natív, SSR/SSG, API routes egyben |
| **Styling** | Vanilla CSS + CSS Variables | Dark mode, teljes kontroll, nincs függőség |
| **Database** | MongoDB Atlas (M0 free tier) | Rugalmas séma, ingyenes, jó Next.js integráció |
| **Auth** | NextAuth.js (Credentials provider) | Jelszavas bejelentkezés, session kezelés |
| **PWA** | `next-pwa` plugin | Installálható app, offline cache |
| **Real-time** | MongoDB Change Streams + Server-Sent Events | Valós idejű szinkron a közös zsebek között |
| **Exchange Rates** | Frankfurter API (ingyenes, ECB alapú) | Napi árfolyamok, EUR/HUF/USD/BGN stb. |
| **Charts** | Recharts | React-native, reszponzív grafikonok |
| **Deploy** | Vercel | Ingyenes tier, automatikus CI/CD GitHubról |

---

## 🗄️ Adatmodell (MongoDB Collections)

### `users`
```json
{
  "_id": "ObjectId",
  "email": "adam@example.com",
  "passwordHash": "bcrypt hash",
  "displayName": "Ádám",
  "baseCurrency": "HUF",
  "sharedWith": ["ObjectId"],
  "createdAt": "ISODate"
}
```

### `accounts` (Valós számlák)
```json
{
  "_id": "ObjectId",
  "userId": "ObjectId",
  "name": "Revolut Pro",
  "currency": "HUF",
  "type": "bank | cash | crypto | investment",
  "isBusinessAccount": true,
  "initialBalance": 0,
  "color": "#6C63FF",
  "icon": "💳",
  "isArchived": false
}
```

### `virtualPockets` (Fiktív zsebek)
```json
{
  "_id": "ObjectId",
  "name": "Közös nyaralás alap",
  "currency": "HUF",
  "linkedAccountId": "ObjectId",
  "owners": ["ObjectId", "ObjectId"],
  "targetAmount": 500000,
  "color": "#FF6584",
  "createdAt": "ISODate"
}
```

### `transactions`
```json
{
  "_id": "ObjectId",
  "userId": "ObjectId",
  "type": "income | expense | transfer",
  "date": "ISODate",
  "amount": 19866,
  "currency": "HUF",
  "amountInBaseCurrency": 19866,
  "exchangeRate": 1.0,
  "accountId": "ObjectId",
  "toAccountId": "ObjectId",
  "categoryId": "ObjectId",
  "virtualPocketId": "ObjectId",
  "tags": ["VitaSteps"],
  "note": "Bari repjegyek",
  "isBusinessTransaction": false,
  "createdAt": "ISODate",
  "importedFrom": "xlsx"
}
```

### `categories`
```json
{
  "_id": "ObjectId",
  "userId": "ObjectId",
  "name": "Utazás",
  "type": "income | expense | both",
  "icon": "✈️",
  "color": "#FFB347",
  "parentId": "ObjectId",
  "isBusinessCategory": false
}
```

### `debts` (Splitwise-szerű)
```json
{
  "_id": "ObjectId",
  "fromUserId": "ObjectId",
  "toUserId": "ObjectId",
  "amount": 15000,
  "currency": "HUF",
  "relatedTransactionId": "ObjectId",
  "note": "Vacsora fele",
  "isSettled": false,
  "settledAt": "ISODate"
}
```

### `exchangeRates` (napi cache)
```json
{
  "_id": "ObjectId",
  "date": "2026-05-13",
  "base": "EUR",
  "rates": { "HUF": 395.5, "USD": 1.08, "BGN": 1.956 },
  "fetchedAt": "ISODate"
}
```

---

## 📱 Képernyők & Funkciók

### 1. 🏠 Dashboard
- Összegyenleg kártya (minden számla HUF-ban, devizakonverzióval)
- Személyes vs. VitaSteps egyenleg – külön kártyán
- Havi P/L sáv – bevétel vs. kiadás e hónapban
- Legutóbbi 10 tranzakció gyors listája
- FAB gomb – tranzakció rögzítése 3 koppintással

### 2. 📊 Kimutatások
- Havi P/L BarChart – kategóriánként színezve
- Kategória breakdown – Donut chart
- 12 havi trend – vonaldiagram
- Szűrők: időszak, számla, kategória, személyes/üzleti

### 3. 💼 VitaSteps Modul
- Csak `isBusinessTransaction: true` tranzakciók
- Cashflow kimutatás (hónapra)
- P&L (bevétel - kiadás időszakra)
- Cost breakdown kategóriánként
- Revolut Pro tranzakciók automatikusan szűrhetők

### 4. 🏦 Számlák
- Kártyás lista, aktuális egyenlegek
- Devizás számlák HUF-ban is
- Számla részlet: tranzakciólista, mini grafikon
- Virtuális zsebek az adott számla alatt

### 5. 👛 Virtuális Zsebek
- Fiktív zseb létrehozása (névvel, céllal, célosszeg)
- Megosztás másik userrel → közös zseb (real-time szinkron)
- Progress bar a célösszegre
- Tartozás összesítő: "Te tartozol X-nek 5.000 HUF"

### 6. ➕ Tranzakció rögzítés
- Gyors form: összeg → számla → kategória → megjegyzés
- Deviza automatikus konverzió (látod az árfolyamot)
- Virtuális zsebhez rendelés (opcionális)
- Üzleti tranzakció jelölés (VitaSteps)

### 7. ⚙️ Beállítások
- Alap pénznem
- Számlák, kategóriák CRUD
- User profil, jelszócsere
- Adatexport (CSV)

---

## 🔄 Real-time Szinkron (Közös zsebek)

```
MongoDB Change Stream → Next.js SSE endpoint (/api/sync/stream)
→ useEventSource() hook → React state frissítés
```

Csak közös zsebek és tartozások szinkronizálnak valós időben.

---

## 💱 Devizakezelés

1. **Frankfurter API** (`api.frankfurter.app`) – ingyenes, ECB alapú, napi frissítés
2. Tranzakciónál rögzítjük az aktuális árfolyamot (`exchangeRate` mező)
3. Dashboard: `amount * exchangeRate → baseCurrency` (HUF)
4. `exchangeRates` collection-ben napi cache (1 fetch/nap)
5. Historikus árfolyam: a tranzakció dátumán érvényes rate mentve

---

## 📦 API Routes struktúra

```
/api/auth/[...nextauth]     – bejelentkezés, session
/api/accounts               – CRUD számlák
/api/transactions           – CRUD + szűrők
/api/categories             – CRUD kategóriák
/api/pockets                – CRUD virtuális zsebek
/api/debts                  – tartozások kezelése
/api/reports/monthly        – havi P/L
/api/reports/vitasteps      – VitaSteps kimutatás
/api/rates                  – árfolyam lekérés/cache
/api/sync/stream            – SSE real-time sync
/api/import                 – xlsx migráció (egyszeri)
```

---

## 🚀 Megvalósítási Fázisok

### Fázis 1 – Alap MVP [~2-3 nap kódolás] ✅
- [x] Next.js projekt setup, MongoDB kapcsolat, NextAuth auth
- [x] Számlák, kategóriák CRUD
- [x] Tranzakció rögzítés (kiadás, bevétel, átutalás)
- [x] Dashboard: egyenlegek, legutóbbi tranzakciók
- [x] Dark mode CSS design system (Tailwind v4)
- [x] PWA konfiguráció (manifest, service worker)

### Fázis 2 – Kimutatások & Deviza [~2 nap] ✅
- [x] Recharts grafikonok (Trend diagram kész)
- [x] Frankfurter API integráció + cache
- [x] Alap pénznem konverzió (HUF)
- [x] VitaSteps szűrt nézet + alap kimutatások

### Fázis 3 – Virtuális Zsebek & Multi-user [~2 nap] ✅
- [x] Virtuális zseb CRUD
- [x] User megosztás, közös zseb
- [x] Tartozás kalkuláció (debts)
- [x] SSE real-time sync implementáció

### Fázis 4 – Migráció & Polírozás [~1 nap] ✅
- [x] Excel import script (Node.js, egyszeri)
- [x] UI animációk, micro-interactions
- [x] PWA install prompt
- [x] Vercel deploy + env változók

---

## 📥 Migráció az Excel-ből

Egyszeri Node.js script (`scripts/import-xlsx.ts`):
1. Beolvassa xlsx-et (`xlsx` npm csomag)
2. Számlák és kategóriák deduplikálása → MongoDB
3. Tranzakciók mappelése: Kiadások→expense, Bevétel→income, Átutalás→transfer
4. `importedFrom: "xlsx"` jelölés minden soron
5. Frankfurtertől historikus árfolyamok lekérése a devizás sorokhoz

**Jelenlegi adataid:**
- 449 kiadás (2024 jan – 2026 máj)
- 71 bevétel
- 34 átutalás
- Számlák: OTP, Revolut Pro, Készpénz, PayPal, EUR/BGN valuták

---

## 🎨 Design Rendszer (Dark Mode)

```css
--bg-primary:     #0F0F14   /* sötét alap */
--bg-surface:     #1A1A24   /* kártya háttér */
--bg-elevated:    #242432   /* modal, dropdown */
--accent-primary: #7C6FFF   /* lila fő szín */
--accent-success: #4ADE80   /* bevétel, pozitív */
--accent-danger:  #F87171   /* kiadás, negatív */
--accent-warning: #FBBF24   /* figyelmeztetés */
--text-primary:   #F8F8FF
--text-secondary: #9CA3AF
--border:         rgba(255,255,255,0.08)
```

Tipográfia: **Inter** (Google Fonts)
Ikonok: **Lucide React**

---

## ❓ Nyitott Döntési Pontok

> [!IMPORTANT]
> Ezekre visszaigazolás kell mielőtt nekiállunk!

1. **Projekt neve / domain:** mi legyen? (pl. `finapp.vercel.app` vagy custom domain?)
2. **VitaSteps auto-tag:** Minden Revolut Pro tranzakció automatikusan üzleti legyen, vagy manuálisan jelöljük esetenként?
3. **Párod user:** Ő maga regisztrál, vagy te hozod létre a fiókját adminként?
4. **Ismétlődő tranzakciók** (pl. havi fizetés, bérleti díj): kell az MVP-be?

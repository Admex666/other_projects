# 🖥️ PeerPlay V2 Képernyő-Architektúra & Részletes UI Specifikáció

> **Verzió:** 2.0.0 (MVP)  
> **Státusz:** Kanonikus Specifikáció  
> **Dátum:** 2026-11-12  
> **Design Rendszer:** 1A Stripe Enterprise Standard ([brand_and_design_guidelines.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/brand_and_design_guidelines.md))  
> **Tervezési Szabályzat:** Human-Centered UI/UX ([human_centered_design_standards.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/human_centered_design_standards.md))  
> **Alapdokumentum:** [MVP_PLAN_v2.md](file:///E:/Data/other_projects/PeerPlay/knowledge/MVP_PLAN_v2.md) · [0002_design_system_stripe_enterprise.md](file:///E:/Data/other_projects/PeerPlay/knowledge/decisions/0002_design_system_stripe_enterprise.md)

---

## 1. Rendszerszintű UI/UX Tervezési Alapok

A PeerPlay V2 képernyő-architektúrája 4 dedikált felületcsaládra (Suite) és 14 specializált képernyőre épül. A felületek a **Stripe Enterprise (1A)** szabványt követik:
- **Alapvászon:** `#F8FAFC` (`bg-slate-50`), Daylight-First világos munkafelület (kivetítő- és tréningterem-barát).
- **Kártyák és Konténerek:** `#FFFFFF` (`bg-white`), `1px solid #E2E8F0` (`border-slate-200`), `12px` lekerekítés (`rounded-xl`), finom mikró-árnyék (`shadow-sm`).
- **Elsődleges Akciószín (CTA):** `#2563EB` (`bg-blue-600`), hover: `#1D4ED8` (`hover:bg-blue-700`), fehér szöveggel.
- **Tipográfiai Rendszer:**
  - Címek, navigáció, kenyérszöveg: **Plus Jakarta Sans**, határozott szerkesztői hierarchiával (`font-extrabold` H1, `font-bold` H2).
  - Számadatok, pénzügyi egyenlegek, visszaszámláló időzítő: **JetBrains Mono**, szigorúan tabuláris számokkal (`tabular-nums font-mono`).
- **Emberi Tervezésű (Human-Centered) Szabályok:**
  - **Zéró Emoji:** Szigorúan tilos dekorációs és funkcionális emojik használata a kezelőfelületeken. Helyettük finom 1.25px - 1.5px SVG piktogramok vagy precíz műszaki jelölések szerepelnek.
  - **Higgadt Hangvétel (Tone of Voice):** Nincsenek szórakoztatóipari túlzások ("BUMM!", "Szuper Ajánlat!"). A mikroszövegezés tárgyilagos, higgadt és professzionális.
  - **3 méteres facilitátori olvashatóság:** A teremben mozgó facilitátor számára az időzítő és a kulcsállapotok messziről is azonnal felismerhetők.

---

## 2. Képernyő Mátrix & Globális Navigáció

| Képernyő ID | Képernyő Név | Célfelület | Elsődleges Felhasználó | Fő Funkció |
| :--- | :--- | :--- | :--- | :--- |
| **S-FAC-01** | Session Setup & Csapatelosztás | Laptop / Tablet | Facilitátor | Munkamenet indítása, PIN generálás, 4 aszimmetrikus csapatkiosztás |
| **S-FAC-02** | Fázisvezérlő & Nagyméretű Időzítő | Tablet / Laptop | Facilitátor | 11 fázis állapottérképe, 3 méteres időzítő, audit napló |
| **S-FAC-03** | Központi Bank Minőségátvételi Pult | Tablet / Laptop | Facilitátor / Bankár | Fizikai papírtermékek ellenőrzése, darabszámos stepperek, jóváírás |
| **S-FAC-04** | Piaci Hírek & Sokkok Kiküldője | Tablet / Laptop | Facilitátor | Árváltozások, nyersanyag-sokkok azonnali szinkronizált kiküldése |
| **S-FAC-05** | Helyszíni Debrief Nézet (Kivetítő) | Kivetítő / TV | Facilitátor & Terem | 85-90. perces Daylight eredménytábla, szociogram, energia delta |
| **S-TEAM-01**| Csapat Ledger & HUD | Asztali Tablet | Csapattagok | Pénz, A4 papír, olló, vonalzó, sablonok leltára, időzítő |
| **S-TEAM-02**| P2P Kereskedelmi Központ | Asztali Tablet | Kereskedelmi Tárgyaló | Kétoldalú jóváhagyásos ajánlatküldés, elfogadás, ellenajánlat |
| **S-TEAM-03**| Hivatalos Banki Árfolyamtábla | Asztali Tablet | Csapattagok | Formák átvételi árai, minőségi specifikációk és piaci hirdetmények |
| **S-MOB-01** | Gyors Belépés & GDPR | Okostelefon | Résztvevő | Session kód, név, email, GDPR hozzájárulás (jelszómentes) |
| **S-MOB-02** | Pre-Game Pulse Kérdőív | Okostelefon | Résztvevő | 1. fázis: 2 db csúszka (fizikai energiaszint, bevonódási kedv 1-10) |
| **S-MOB-03** | In-Game Passzív Kísérő | Okostelefon | Résztvevő | Fázisállapot, hátralévő idő, csapatinfó, helyszíni ergonómiai tippek |
| **S-MOB-04** | Post-Game Peer Feedback | Okostelefon | Résztvevő | 10. fázis: Nominációs mátrix (koordinátor, belső támasz, záró energia) |
| **S-ONA-01** | Munkahelyi ONA Kérdőív | Desktop / Mobil Web | Résztvevő (utólag) | 3 kapcsolati dimenzió (operatív, szakmai, innováció) nominálása |
| **S-ONA-02** | Vezetői Diagnosztikai Riport | Desktop Browser | HR Vezető / Tanácsadó | 5 rétegű ONA szintézis, interaktív szociogram, PDF export |

---

## 3. Facilitátori Konzol Suite (S-FAC-01..05)

### S-FAC-01: Munkamenet Indítás & Aszimmetrikus Csapatkiosztás

#### 1. Cél & Szerepkör
Új tréningtermi munkamenet (Session) létrehozása, a résztvevői létszám rögzítése, az aszimmetrikus kezdőcsomagok kiosztása a 4 vállalatnak, valamint a 6 karakteres belépési PIN kód és QR-kód aktiválása.

#### 2. Pontos UI Layout
- **Topbar / Header:**
  - Bal oldal: PeerPlay logó, `Facilitátori Irányítópult · Munkamenet Előkészítés` felirat.
  - Jobb oldal: Munkamenet azonosító generátor chip (`TRD-XXXX` placeholder), rendszerállapot jelzés (`Előkészítés alatt`).
- **Body Grid (2 oszlopos, `grid grid-cols-1 lg:grid-cols-12 gap-6`):**
  - **Bal oldali oszlop (5 col) – Munkamenet Alapadatok (`.theme-card p-6`):**
    - `Vállalati Ügyfél / Szervezet Neve` szöveges beviteli mező (`input text`).
    - `Tervezett Résztvevői Létszám` numerikus mező (`input number`, min: 8, max: 40).
    - `Csapatok Száma` választó (alapértelmezett: 4 vállalat, 2..6 skála).
    - `Belépési PIN Kód`: 6 karakteres monospaced kód (`JetBrains Mono font-bold text-2xl tracking-wider text-slate-900`), mellette `Újrakódolás` és `QR Kód Másolása / Vetítése` gombok.
  - **Jobb oldali oszlop (7 col) – Aszimmetrikus Kezdőcsomagok Kiosztása (`.theme-card p-6`):**
    - 4 aszimmetrikus vállalatkártya egymás mellett vagy 2x2 rácsban:
      1. **Alpha Corp (Tőkeerős Vállalat):** Induló tőke: `$1,500`, Nyersanyag: `2 lap A4`, Eszközök: `0 olló, 0 sablon, 1 vonalzó, 1 ceruza`.
      2. **Beta Industries (Technológiai Bajnok):** Induló tőke: `$300`, Nyersanyag: `3 lap A4`, Eszközök: `2 olló, 2 sablon, 2 vonalzó`.
      3. **Gamma Resources (Nyersanyag-óriás):** Induló tőke: `$200`, Nyersanyag: `15 lap A4`, Eszközök: `0 olló, 0 sablon, 0 vonalzó`.
      4. **Delta Ventures (Feltörekvő Start-up):** Induló tőke: `$500`, Nyersanyag: `5 lap A4`, Eszközök: `1 tompa olló, 1 vonalzó, 0 sablon`.
    - Erőforrás-mérleg ellenőrző panel: Jelzi, hogy a piacon összesen hány olló, sablon és lap van kiosztva.
- **Actions / Footer:**
  - `Munkamenet Aktiválása & Megnyitása Résztvevőknek` (Primary CTA, kék gomb).
  - `Alapértelmezett Egyensúly Visszaállítása` (Secondary gomb).

#### 3. Állapotok
- **Loading:** Skeleton placeholder a vállalatkártyákra és adatokra.
- **Empty:** Még nincs szervezet megadva; a mezők placeholder szöveget mutatnak (`pl. Acme Hungary Zrt.`).
- **Active:** Minden mező érvényes, a PIN generálva van, a QR kód egy kattintással kivetíthető.
- **Error / Blocked:** Ha a tervezett létszám < 8 fő, vagy egy vállalatnál 0 erőforrás sincs; piros hibaüzenet banner (`border-red-200 bg-red-50 text-red-700`).

#### 4. Felhasznált Komponensek és Tailwind Tokenek
- Kártyák: `bg-white border border-slate-200 rounded-xl shadow-sm`.
- Címek: `font-extrabold text-xl tracking-tight text-slate-900`.
- Metaadatok: `text-xs font-mono uppercase text-slate-500 tracking-wider`.
- Kódmező: `bg-slate-100 border border-slate-300 rounded-lg py-2 px-4 text-center font-mono text-2xl font-bold tracking-widest text-slate-900`.
- CTA Gomb: `bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-6 py-3 rounded-lg shadow-sm transition-all`.

#### 5. Validációs Szabályok és Interakciók
- A munkamenet csak akkor aktiválható, ha a szervezet neve legalább 3 karakter.
- A PIN kód egyedi a rendszerben, nagybetűkből és számokból áll (kivéve könnyen téveszthető karakterek: `O`, `0`, `I`, `1`).
- A QR kód gombra kattintva felugrik egy nagyméretű, projektorra küldhető modális ablak a belépési instrukciókkal.

---

### S-FAC-02: Fázisvezérlő & Nagyméretű Időzítő

#### 1. Cél & Szerepkör
A 90 perces szimuláció 11 fázisának kézi és automatikus léptetése. Tartalmazza a tréningteremben 3 méterről is kristálytisztán leolvasható időzítőt, fázis-specifikus facilitátori instrukciókat és az asztalok valós idejű állapotnaplóját.

#### 2. A 11 Fázis Állapottérképe (Phase State Machine)
```text
[F01: Pre-Survey (5p)] ──> [F02: Briefing (8p)] ──> [F03: Strategy (5p)]
         │
         ▼
[F04: Round 1 (15p)] ──> [F05: Market Shock 1 (3p)] ──> [F06: Round 2 (15p)]
         │
         ▼
[F07: Market Shock 2 (3p)] ──> [F08: Round 3 (12p)] ──> [F09: Bank Close (7p)]
         │
         ▼
[F10: Post-Survey & Peer (10p)] ──> [F11: Classroom Debrief (7p)]
```

#### 3. Pontos UI Layout
- **Topbar / Header:**
  - Fázis Előrehaladási Sáv (Stepped Progress Bar): 11 diszkrét lépés horizontálisan. A befejezett fázisok kék pipával, az aktív fázis kék kitöltéssel és fehér számmal, a jövőbeliek vékony szürke kerettel jelennek meg.
- **Hero Timer Panel (`.theme-card p-6 flex flex-col lg:flex-row items-center justify-between gap-6`):**
  - Bal oldal: Aktív fázis sorszáma és megnevezése (`1. Termelési & Kereskedelmi Kör`), alatta célja: `Kereskedelem indítása, fizikai formák kivágása, banki értékesítés`.
  - Közép: **3 Méteres Hero Időzítő Box (`bg-slate-100 border border-slate-200 px-8 py-4 rounded-xl flex items-center gap-6`):**
    - Időzítő címke: `HÁTRALÉVŐ IDŐ`.
    - Érték: `44px - 52px font-mono font-bold tracking-tight text-slate-900 tabular-nums` (pl. `11:42`).
    - Vezérlőgombok: `Szünet / Indítás` (`bg-white border border-slate-300 px-3 py-1.5 rounded-lg text-xs font-semibold`), `+1 perc`, `+2 perc` gyors hozzáadás.
    - Kör azonnali lezárása text link (`text-xs underline text-slate-500 hover:text-slate-900`).
  - Jobb oldal: Fázisléptető gombpár:
    - `← Előző Fázis` (`border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs px-4 py-2.5 rounded-lg font-semibold`).
    - `Következő: Piaci Esemény 1 →` (Primary CTA `bg-blue-600 hover:bg-blue-700 text-white text-xs px-5 py-2.5 rounded-lg font-bold shadow-sm`).
- **Body Grid (2 oszlopos):**
  - **Bal oszlop (7 col) – Facilitátori Forgatókönyv & Instrukciók:**
    - "Mit mondj a teremben most?" pontokba szedett kártya (pl. *„Jelezd a csapatoknak, hogy az első 5 percben a nyersanyaghiány azonnali tárgyalást igényel.”*).
    - Teremfelügyeleti ellenőrzőpontok: Csalásmegelőzés (méretek egyezése), biztonsági szabályok (ollóhasználat).
  - **Jobb oszlop (5 col) – Terem Aktivitási Napló (Live Audit Stream):**
    - Valós idejű eseményfolyam időbélyeggel:
      - `11:40` · Alpha Corp ajánlatot küldött Beta Industries részére ($200 -> 1 Olló).
      - `11:38` · Gamma Resources beváltott 2 db Négyzetet a Banknál (+$600).
- **Actions / Footer:**
  - Vészhelyzeti Munkamenet Megállító gomb (`Szünet minden kliensen`).

#### 4. Állapotok
- **Normal Running:** Fekete időzítő számjegyek (`text-slate-900`), ketyegő számláló másodpercenként.
- **Warning State (2 percnél kevesebb):** Az időzítő kerete és számai borostyánsárgára váltanak (`text-amber-600 bg-amber-50 border-amber-300`).
- **Critical State (utolsó 30 másodperc):** Piros kiemelés (`text-red-600 bg-red-50 border-red-300 animate-pulse`), opcionális diszkrét figyelmeztető hang.
- **Paused:** Statikus felirat: `SZÜNETELTETVE`, sárga badge.

#### 5. Komponensek és Tailwind Tokenek
- Hero Timer: `text-5xl font-mono font-bold tracking-tight text-slate-900 tabular-nums`.
- Badge: `bg-slate-100 text-slate-700 border border-slate-200 text-xs px-2.5 py-0.5 rounded-full font-semibold font-mono`.

#### 6. Validációs Szabályok és Interakciók
- Fázisváltáskor a rendszer megerősítő párbeszédablakot nyit, ha a kör ideje még nem telt le (`"Még 4 perc van hátra. Biztosan lezárod a kört?"`).
- Az időzítő módosításai azonnal, 2 másodpercen belül szinkronizálódnak az asztali tabletekkel és mobilokkal.

---

### S-FAC-03: Központi Bank Minőségátvételi Pult

#### 1. Cél & Szerepkör
A csapatok fizikai papírtermékeinek minőségi ellenőrzése, darabszám szerinti rögzítése és a virtuális kifizetés végrehajtása. Szigorúan egykezes és tabletre optimalizált nagy érintési célpontokkal (stepperek).

#### 2. Pontos UI Layout
- **Topbar / Header:**
  - Cím: `Központi Bank & Minőségátvételi Pult`.
  - Pult státusz jelző chip: `Pult Állapot: Nyitva` (zöld badge `#ECFDF5` / `#059669`).
  - Gyors elszámolási összesítő: Ma kifizetve összesen: `$4,850` · Átvett formák: `23 db`.
- **Csapatválasztó Sáv (Team Selector Tabs):**
  - 4 nagyméretű kártyagomb a 4 vállalatnak:
    - `Alpha Corp` (Tőkeerős)
    - `Beta Industries` (Technológia) – *Kijelölve: 2px kék keret, halványkék háttér*
    - `Gamma Resources` (Nyersanyag)
    - `Delta Ventures` (Start-up)
- **Forma-átvételi Mátrix (Product Intake Table):**
  - Soronként 1 terméktípus:
    1. **Szabályos Négyzet (10 × 10 cm):** Műszaki rajz ikon (`10×10`), érvényes felvásárlási ár: `$300` (piaci eseménynél sárga kiemeléssel `$450`).
    2. **Egyenlő oldalú Háromszög (10 cm):** Műszaki rajz ikon (`▲10`), felvásárlási ár: `$150`.
    3. **Kör (Ø 10 cm sablonnal):** Műszaki rajz ikon (`Ø10`), felvásárlási ár: `$250`.
    4. **Téglalap (5 × 15 cm):** Műszaki rajz ikon (`5×15`), felvásárlási ár: `$100`.
    5. **Prémium Csomag (2▲ + 1⬛):** Ikon csomag, felvásárlási ár: `$800`.
  - Minden sornál jobb oldalon:
    - **Stepperek:** `-` gomb (36×36px), aktuális darabszám (pl. `2 db` font-mono bold), `+` gomb (36×36px).
    - Tételes részösszeg: monospaced, jobbra zárt (pl. `$600`).
- **Kifizetési Összesítő Sáv (Checkout Action Bar):**
  - Bal oldal: Végösszeg megjelenítő: `Kifizetendő összeg (Beta Industries):` felirat alatt `32px font-mono font-bold text-slate-900` (pl. `$750`).
  - Jobb oldal: Műveleti gombok:
    - `Selejt Elutasítása` (Vékony szürke keretes gomb, nem számol fel kifizetést).
    - `Minőség Elfogadása & Kifizetés` (Primary CTA, zöld/kék gomb, `bg-blue-600 text-white font-bold text-sm px-6 py-3 rounded-lg shadow-sm`).
- **Audit Történet (Alsó kártya):**
  - Legutóbbi 5 átvétel listája: `11:35 · Beta Industries · 2 db Négyzet · $600 Jóváírva` visszavonási lehetőséggel (`Visszavonás` link 60 másodpercig).

#### 3. Állapotok
- **Idle (Nincs csapat kiválasztva):** A táblázat inaktív szürke tónusú, figyelmeztetés: *"Válassz csapatot az átvételhez!"*
- **Active / Calculating:** A stepperek növelésével a végösszeg azonnal és animációmentesen frissül (`tabular-nums`).
- **Submitting:** A kifizetés gomb inaktívvá válik és `Rögzítés folyamatban...` feliratot mutat.
- **Success Toast:** Zöld diszkrét értesítés jelenik meg felül: `Sikeres átvétel: $750 jóváírva a Beta Industries egyenlegén.`

#### 4. Komponensek és Tailwind Tokenek
- Stepper konténer: `flex items-center border border-slate-300 rounded-lg bg-white overflow-hidden shadow-xs`.
- Stepper gomb: `w-9 h-9 flex items-center justify-center hover:bg-slate-100 font-mono font-bold text-slate-700 active:bg-slate-200 transition`.
- Végösszeg: `text-3xl font-mono font-bold text-slate-900 tabular-nums`.

#### 5. Validációs Szabályok és Interakciók
- A kifizetés gomb le van tiltva (`disabled`), ha az összes darabszám 0.
- A kifizetés atomikus tranzakcióként fut le a szerveren (`Prisma $transaction`), frissítve a `SessionTeam.cashBalance` mezőt és létrehozva a `BankSale` rekordot.
- A gomb dupla kattintás elleni védelemmel (`debounce` 500ms) van ellátva.

---

### S-FAC-04: Piaci Hírek & Sokkok Kiküldője

#### 1. Cél & Szerepkör
A gazdasági környezet megváltoztatása a körök között vagy alatt. Árváltozások, nyersanyag-embargók és sürgősségi megrendelések azonnali leküldése a csapatok asztali képernyőire.

#### 2. Pontos UI Layout
- **Topbar / Header:**
  - Cím: `Piaci Események & Szabályozói Hírek`.
  - Aktív piaci szabályozók száma chip: `1 Aktív Piaci Módosító Érvényben`.
- **Body Grid (2 oszlopos):**
  - **Bal oszlop (6 col) – Gyors Eseménykatalógus (Előre definiált események):**
    - 4 előre konfigurált eseménykártya:
      1. **Piaci árváltozás (Négyzet Boom):** A négyzetek átvételi ára $300-ról $450-ra nő megnövekedett építőipari kereslet miatt.
      2. **Nyersanyag-korlátozás (Papírembargó):** A Bank papírellátása lezárul; új A4-es papírlapok csak a piacról (Gamma Resources) szerezhetők be.
      3. **Technológiai Szabvány Szigorítás:** A körök felvásárlási ára $350-re nő, de a szabálytalan íveket a Bank kétszeres szigorral bünteti.
      4. **Sürgősségi Exportmegrendelés:** 3 db Háromszög egyidejű leadása azonnali $200 bónuszt fizet.
    - Minden kártyán: Cím, leírás, gazdasági hatás, valamint `Aktiválás Most` gomb.
  - **Jobb oszlop (6 col) – Egyedi Hír Szerkesztő & Broadcast Pult:**
    - `Hír / Esemény Címe` beviteli mező.
    - `Hír Típusa`: Rádiógombok (`Árváltozás`, `Nyersanyag-sokk`, `Szabálymódosítás`).
    - `Részletes Értesítő Szöveg` textarea (higadt mikroszöveg).
    - `Érintett Forma és Új Árfolyam` mezők.
    - `Azonnali Kiküldés a Csapatok Képernyőjére` (Accent Amber CTA gomb `#D97706`).
- **Alsó szekció – Aktív Hirdetmények Kezelése:**
  - Jelenleg érvényben lévő hírek listája `Visszavonás / Piac Normalizálása` akciógombbal.

#### 3. Állapotok
- **Idle:** Nincs aktív hír, a katalógus várakozik.
- **Broadcasting:** A kiküldés megtörtént; a hír sárga kártyaként világít a képernyőn, az érintett csapatoknál azonnal szinkronizál.
- **Reverted / Normal:** Az esemény visszavonva, az árak visszaállnak az alapszintre.

#### 4. Komponensek és Tailwind Tokenek
- Hírkártya (Aktív): `bg-amber-50 border border-amber-300 rounded-xl p-4 text-amber-900`.
- Badge: `bg-amber-100 text-amber-800 text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded`.
- Kiküldő gomb: `bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs px-4 py-2.5 rounded-lg shadow-sm`.

#### 5. Validációs Szabályok és Interakciók
- Egy időben legfeljebb 2 piaci módosító lehet aktív, hogy a játékosok ne veszítsék el a fókuszt.
- Az aktiválás pillanatában a szerver frissíti a `MarketEvent` entitást, és a csapatok tabletjein (S-TEAM-01..03) azonnal lefut a revalidáció.

---

### S-FAC-05: Helyszíni Debrief Nézet (Kivetítőre Optimalizált)

#### 1. Cél & Szerepkör
A 90 perces workshop utolsó szakaszában (85–90. perc) a terem központi kivetítőjére vagy nagy kijelzőjére optimalizált, nagy kontrasztú, Daylight-First szintetizált eredménytábla. Nem igényel görgetést, 5 méterről is olvasható.

#### 2. Kivetítő-Ergonómiai Szabályok
- **Tilos a sötét mód:** Az átlagos tárgyalótermi projektorokon a sötét hátterek alacsony kontrasztú szürke folttá válnak. Kötelező a tiszta fehér (`#FFFFFF`) kártya és hideg szürke (`#F8FAFC`) háttér.
- **Tipográfiai méretküszöb:** Nincs 13px alatti szöveg; a főkategóriák és számok minimális mérete 20px - 36px.

#### 3. Pontos UI Layout
- **Header:**
  - Bal oldal: `The Trading Game · Helyszíni Eredményhirdetés & Hálózati Reflexió`.
  - Jobb oldal: Globális teremstatisztika: `Összes Termelt Érték: $8,450 · Hálózati Sűrűség: 64%`.
- **Fő Képernyőfelület (3 Zónás Grid, `grid grid-cols-12 gap-6`):**
  - **1. Zóna (4 col) – Végleges Gazdasági Rangsor (`.theme-card p-6`):**
    - A 4 vállalat rangsora elért összes vagyon (Készpénz + megmaradt alapanyag értéke) alapján:
      1. Hely: **Beta Industries** – `$2,650` (6 db forma, technológiai dominancia)
      2. Hely: **Alpha Corp** – `$2,100` (Tőkeerős felvásárlások)
      3. Hely: **Gamma Resources** – `$1,850` (Nyersanyag-értékesítés)
      4. Hely: **Delta Ventures** – `$1,150` (Feltörekvő bérgyártás)
    - Tiszta tabuláris elrendezés, vastag számokkal.
  - **2. Zóna (5 col) – Kereskedelmi Hálózati Topológia (Szociogram):**
    - Letisztult, világos hátterű gráf: A 4 vállalat csomópontként jelenik meg.
    - A csomópontok közötti nyilak vastagsága a lezárt P2P tranzakciók számát jelzi.
    - Színjelölés: Kétirányú kereskedelem (zöld folytonos vonal - reciprocitás), egyirányú (szürke szaggatott vonal).
    - Központi informális közvetítő kiemelése: Nagy Anna (Beta Ind.) - *Betweenness Centrality: 0.82*.
  - **3. Zóna (3 col) – Élmény & Energia Dinamika (Pre/Post Delta):**
    - Terem átlagos energiaszint változása: `Kezdéskor: 6.2 / 10` ➔ `Záráskor: 8.4 / 10` (`+2.2 pont emelkedés`, zöld nyíllal).
    - Részvételi elégedettségi index: `92% pozitív élmény`.
- **Alsó Kiemelt Banner – Facilitátori Beszélgetésindító Kérdések:**
  - 3 megfontolandó reflexiós kérdés a közös megbeszéléshez:
    1. *„Hogyan alakult ki a függőség a nyersanyagot birtokló Gamma Resources körül?”*
    2. *„Miért tudott a Beta Industries magasabb árat kérni a sablonjaiért?”*
    3. *„Milyen párhuzamot láttok a játékbeli tárgyalások és a mindennapi munkahelyi együttműködés között?”*

#### 4. Állapotok
- **Generating:** Amíg a Post-Game felmérés utolsó válaszai beérkeznek, elegáns százalékos számláló jelzi a beérkezést (`14 / 16 kitöltve`).
- **Ready / Displayed:** Teljes statikus nézet maximális kontraszttal.

#### 5. Komponensek és Tailwind Tokenek
- Rangsor értékek: `text-2xl font-mono font-bold text-slate-900 tabular-nums`.
- Reflexió banner: `bg-slate-100 border border-slate-300 rounded-xl p-4 text-slate-800 text-sm font-medium`.

---

## 4. Csapat Munkaállomás Suite (S-TEAM-01..03)

### S-TEAM-01: Csapat Ledger & HUD (Pénz, A4 lap, Ollók, Sablonok)

#### 1. Cél & Szerepkör
A csapat asztalán fekvő közös tablet / laptop állandó kijelzője. Folyamatos áttekintést ad a virtuális készpénzről, a fizikai leltárról, a hátralévő időről és a beérkező cserékről.

#### 2. Pontos UI Layout
- **Topbar / Header (`.theme-card p-5 flex items-center justify-between`):**
  - Bal oldal: Csapat megnevezése és asztalszáma (`Beta Industries · 2. Asztal`), mellette az induló archetípus címke (`Technológiai Bajnok` halványkék badge).
  - Közép / Jobb oldal:
    - `Kör Hátralévő Ideje`: `28px font-mono font-bold text-slate-900 tabular-nums` (szinkronban a facilitátorral).
    - `Virtuális Egyenleg`: `28px font-mono font-bold text-slate-900 tabular-nums` (pl. `$1,850`).
- **Készlet Leltár Kártyasor (Inventory HUD - 4 oszlopos grid):**
  - **1. Kártya – Nyersanyag (A4 Papírlap):**
    - Címke: `A4 Papírlap (Nyersanyag)`
    - Darabszám: `text-3xl font-mono font-bold text-slate-900` (pl. `2 lap`).
    - Státuszjelző: `text-amber-600 font-semibold text-xs` (`Kritikus alapanyaghiány`).
  - **2. Kártya – Vágóeszköz (Olló):**
    - Címke: `Vágóeszköz (Olló)`
    - Darabszám: `2 db`.
    - Státusz: `text-slate-500 text-xs` (`Bérbeadható eszköz`).
  - **3. Kártya – Mérőeszköz (Vonalzó):**
    - Címke: `Mérőeszköz (Vonalzó)`
    - Darabszám: `2 db`.
    - Státusz: `text-slate-500 text-xs` (`Aktív termelésben`).
  - **4. Kártya – Geometriai Sablon:**
    - Címke: `Geometriai Sablon (Monopólium)`
    - Darabszám: `2 db`.
    - Státusz: `text-emerald-600 font-semibold text-xs` (`Csúcstechnológia`).
- **Alsó Kétrészes Munkaterület:**
  - Bal oldal (7 col): [S-TEAM-02] Kereskedelmi Központ beágyazva.
  - Jobb oldal (5 col): [S-TEAM-03] Hivatalos Banki Árfolyamtábla beágyazva.

#### 3. Állapotok
- **Live / Polling:** Nyugodt állapot, 2-3 másodpercenként csendes SWR lekérdezéssel.
- **Syncing:** Ha tranzakció történt, a frissülő készletmező egy pillanatra finom kék keretet kap (`ring-1 ring-blue-400`).
- **Offline / Connection Lost:** Ha megszakad a wifi a teremben, felső narancssárga figyelmeztető sáv ugrik fel: `Hálózati kapcsolat megszakadt. Újracsatlakozás... A meglévő egyenleg biztonságban van.`

#### 4. Validációs Szabályok
- A leltár darabszámai szigorúan megegyeznek a DB `SessionTeam` rekordjaival.
- Készlet nem mehet 0 alá semmilyen körülmények között.

---

### S-TEAM-02: P2P Kereskedelmi Központ (Ajánlat-életciklus)

#### 1. Cél & Szerepkör
A csapatok közötti cserekereskedelem hivatalos digitális lebonyolítása. Megakadályozza a vitákat és garantálja a kétoldalú jóváhagyást.

#### 2. Az Ajánlat Teljes Életciklusa (Offer Lifecycle State Machine)
```text
[DRAFT] ──> [SENT] ──> [RECEIVED by Partner]
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      [ACCEPTED]                [DECLINED]
             │                       │
      (ACID Transzfer)          (Érvénytelen)
             ▲
             │
      [COUNTER-OFFER] (Módosított feltételek)
```

#### 3. Pontos UI Layout
- **Beérkezett Ajánlatok Panel (Inbound Proposals - Kiemelt blokk):**
  - Ha van aktív beérkező ajánlat, kiemelt kártyaként jelenik meg a felület tetején:
    - Partner neve: `Gamma Resources ajánlata · 11:38`.
    - Tétel áttekintő:
      - *Amit ők adnak nekünk:* `5 lap A4 papír`.
      - *Amit cserébe kérnek tőlünk:* `1 db Olló használata + $100 készpénz`.
    - Műveleti gombok:
      - `Ajánlat Elfogadása` (Primary CTA kék/zöld).
      - `Elutasítás` (Vékony szürke keretes gomb).
      - `Ellenajánlat Küldése` (Szöveges link, amely átemeli a tételeket a szerkesztőbe).
- **Új Kereskedelmi Ajánlat Indítása (Outbound Proposal Builder):**
  - Form szerkezet:
    - `Partner Vállalat Kiválasztása`: Dropdown lista (`Alpha Corp`, `Gamma Resources`, `Delta Ventures`).
    - 2 oszlopos csereszerkesztő:
      - Bal oszlop – *Amit tőlünk felajánlunk:* Kiválasztható a saját leltárból (Készpénz összeg, papírlapok száma, olló/sablon bérlet vagy végleges átadás).
      - Jobb oszlop – *Amit cserébe kérünk:* Mezők a partner készleteiből igényelt tételekre.
    - `Hivatalos Ajánlat Továbbítása` gomb (`w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg text-xs`).
- **Kereskedelmi Napló (Trade History Table):**
  - Az adott csapat összes korábbi ajánlata státuszcímkével (`Elfogadva` zöld, `Elutasítva` szürke, `Visszavonva` piros).

#### 4. Állapotok
- **No Active Trades:** "Nincs függőben lévő kereskedelmi ajánlatod." felirat diszkrét szürke tónussal.
- **Pending Outbound:** "Ajánlatod elküldve a Gamma Resources csapatnak. Várakozás a jóváhagyásra..." (Inaktív visszavonó gombbal).
- **Accepted Toast:** Hangsúlyos megerősítés: *"Üzlet létrejött! 5 lap papír jóváírva, $100 levonva."*

#### 5. Tranzakciós és Validációs Szabályok
- **Azonnali Letéti Zárolás (Immediate Escrow Reservation):** Amikor a küldő fél ajánlatot indít, a felkínált javak (`offeredItems`) azonnal levonásra és zárolásra kerülnek a küldő szabad készletéből a `TradeTransaction.escrowedItems` mezőbe. Így a küldő nem tudja más ügyletben elkölteni a fedezetet, megelőzve a versenyhelyzeteket és készletduplikációt.
- **Fogadó oldali fedezetellenőrzés & ACID Transzfer:** Amikor a fogadó fél az `Ajánlat Elfogadása` gombra kattint, a backend egyetlen atomi `$transaction` keretében ellenőrzi a fogadó fél fedezetét a kért javakra (`requestedItems`). Ha a fogadó fedezete hiánytalan, levonja azt, és mindkét fél megkapja a neki járó tételeket. Ha a fogadó nem rendelkezik a kért javakkal, az elfogadás hibaüzenettel leáll: *"Nincs elegendő fedezeted az ajánlat elfogadásához."*
- **Elutasítás / Visszavonás esetén visszautalás (Refund):** Ha az ajánlatot elutasítják, visszavonják vagy a fázis lejár, a zárolt letét azonnal és hiánytalanul visszakerül a küldő szabad készletébe.
- **Ellenajánlat kezelése:** A felületen az "Ellenajánlat" gomb az eredeti ajánlat visszautasítását (`REJECTED`) és a szerepek megcserélésével előre kitöltött új ajánlat szerkesztését jelenti.

---

### S-TEAM-03: Hivatalos Banki Árfolyamtábla & Minőségi Specifikációk

#### 1. Cél & Szerepkör
A csapatok eligazítása a gyártandó formák méreteiről, geometriai követelményeiről és az aktuális piaci árakról.

#### 2. Pontos UI Layout
- **Topbar:** `Hivatalos Banki Árfolyamok & Minőségi Követelmények`.
- **Árfolyamtáblázat (Price Index Cards):**
  - **Szabályos Négyzet (10 × 10 cm):** `$300` *(Ha piaci boom van érvényben: `$450` sárga figyelemfelkeltő címkével: `Piaci Áremelkedés`)*.
  - **Egyenlő oldalú Háromszög (10 cm):** `$150`.
  - **Kör (Ø 10 cm sablonnal):** `$250`.
  - **Téglalap (5 × 15 cm):** `$100`.
  - **Prémium Csomag (2▲ + 1⬛):** `$800`.
- **Minőségi Ellenőrzési Standardok Kártya (`bg-slate-50 border border-slate-200 p-4 rounded-xl`):**
  - Tárgyilagos szabályzat a selejtek elkerülésére:
    - *„A Bank a vonalzótól eltérő, hullámos vágású formákat selejtként azonnal elutasítja.”*
    - *„A kör kizárólag sablon segítségével rajzolható és vágható, szabadkézi rajz érvénytelen.”*
    - *„A leadás előtt a méreteket a csapatnak saját vonalzóval ellenőriznie kell.”*

---

## 5. Résztvevői Mobil Suite (S-MOB-01..04)

### S-MOB-01: Gyors Belépés (Kód + Email + Név + GDPR)

#### 1. Cél & Szerepkör
A tréningteremben ülő játékosok villámgyors, jelszómentes becsatlakozása okostelefonról 30 másodperc alatt.

#### 2. Mobile-First Layout (`max-w-[420px] mx-auto p-6 space-y-6`)
- **Header:**
  - Letisztult monokróm felirat: `PeerPlay · The Trading Game`.
  - Alcím: `Csatlakozás a tréningtermi szimulációhoz`.
- **Form Elemek:**
  - `Munkamenet Kód (PIN)`: 6 karakteres mező (`input uppercase font-mono tracking-widest text-xl text-center border-slate-300 rounded-lg p-3`). Ha QR kóddal érkezett, automatikusan kitöltve és zárolva.
  - `Teljes Név`: Szöveges beviteli mező (`Kovács Péter`).
  - `Munkahelyi E-mail Cím`: E-mail beviteli mező (`peter.kovacs@cegnev.hu`).
  - `GDPR & Adatkezelési Hozzájárulás`: Szabványos jelölőnégyzet szöveggel:
    - *„Hozzájárulok a szimulációban való részvételemhez és az eredmények szervezetdiagnosztikai aggregálásához.”*
    - Kattintható link: `Részletes adatkezelési tájékoztató megnyitása`.
- **Action:**
  - `Csatlakozás a Munkamenethez →` (Teljes szélességű Primary gomb, 48px magas érintési zóna a kényelmes hüvelykujjas kezeléshez).

#### 3. Validáció & Hibakezelés
- Érvénytelen PIN esetén: *"A megadott kód nem létezik vagy a munkamenet még nem indult el."*
- Nem céges e-mail formátum esetén figyelmeztetés.
- GDPR pipa nélkül a gomb inaktív.

---

### S-MOB-02: Pre-Game Pulse Felmérés (2 Csúszka)

#### 1. Cél & Szerepkör
A workshop 1. fázisában (5 perc) a résztvevő érkezési energiaszintjének és szubjektív bevonódási kedvének felmérése 2 gyors csúszkával.

#### 2. Mobile Layout
- **Topbar:** `1. Fázis: Hangolódás · Kérdés 1 és 2 / 2`.
- **Kérdés 1 – Fizikai & Mentális Energiaszint:**
  - Kérdés: *„Milyen az energiaszinted jelen pillanatban?”*
  - Skála: 1-től 10-ig állítható csúszka (`type="range"`).
  - Értékmegjelenítés: `JetBrains Mono text-3xl font-bold text-slate-900` (pl. `7 / 10`).
  - Végpontcímkék: Balra: `1 - Kimerült, tompa`, Jobbra: `10 - Tettre kész, energikus`.
- **Kérdés 2 – Részvételi Kedv & Nyitottság:**
  - Kérdés: *„Őszintén, mekkora nyitottsággal és kedvvel érkeztél a mai napra?”*
  - Skála: 1-től 10-ig állítható csúszka.
  - Értékmegjelenítés: `JetBrains Mono text-3xl font-bold text-slate-900` (pl. `8 / 10`).
  - Végpontcímkék: Balra: `1 - Inkább kihagynám`, Jobbra: `10 - Kíváncsi és motivált vagyok`.
- **Action:**
  - `Válaszok Rögzítése →` (Primary CTA gomb).
- **Sikeres beküldési állapot:**
  - Kártya tiszta visszaigazolással: `Köszönjük. A válaszaidat rögzítettük. Most tedd le a telefont, és figyeld a facilitátor instrukcióit!`

---

### S-MOB-03: In-Game Passzív Kísérő Képernyő

#### 1. Cél & Szerepkör
A termelési és kereskedelmi körök alatt futó passzív kísérő. Célja, hogy a játékost visszaterelje a fizikai térbe (papírvágás, tárgyalás), miközben zsebből rápillantva pontos státuszt ad.

#### 2. Mobile Layout
- **Header:**
  - Saját csapat neve: `Beta Industries`.
  - Hozzárendelt asztal: `2. Asztal · Technológia`.
- **Központi Időzítő Kártya:**
  - Fázis megnevezése: `1. Termelési & Kereskedelmi Kör`.
  - Hátralévő idő: `36px font-mono font-bold text-slate-900 tabular-nums` (pl. `11:42`).
- **Ergonómiai Figyelmeztető Kártya (`bg-slate-100 border border-slate-200 p-4 rounded-xl`):**
  - *„A telefonodra most nincs közvetlen szükség. A csereajánlatokat a csapat közös asztali tabletjén kezelitek. Menj át tárgyalni a többi csapathoz vagy segíts a papírformák vágásában!”*
- **Piaci Riasztási Sáv (Feltételes megjelenés):**
  - Ha a facilitátor piaci hírt aktivál, diszkrét borostyánsárga kártyaként rezgéssel megjelenik: `Piaci Értesítés: A négyzetek ára $450-ra emelkedett!`

---

### S-MOB-04: Post-Game Peer Feedback (Nominációs Mátrix)

#### 1. Cél & Szerepkör
A játék lezárása után (10. fázis, 10 perc) minden résztvevő értékeli a társak együttműködését. Ez képezi az ONA 4. rétegének (Peer Percepció) alapját.

#### 2. Mobile Layout (Lépésenkénti Kártyák)
- **1. Lépés – Keresztfunkcionális Koordinátor (Broker Nomináció):**
  - Kérdés: *„Ki segítette leginkább a csapatok közötti információáramlást és a megállapodások létrejöttét?”*
  - Választófelület: A többi résztvevő névlistája kereshető chip-választóval, csapatok szerint csoportosítva (Alpha, Gamma, Delta tagjai).
  - Maximálisan jelölhető személyek: 1 vagy 2 fő.
- **2. Lépés – Belső Csapattámasz (Internal Enabler Nomináció):**
  - Kérdés: *„A saját csapatodon belül ki volt a legfőbb operatív motor vagy támasz?”*
  - Választófelület: Kizárólag a saját csapat tagjainak listája.
- **3. Lépés – Záró Energiaszint (Post-Game Pulse):**
  - Kérdés: *„Milyen az energiaszinted a játék befejezésekor?”*
  - Csúszka 1-től 10-ig (összehasonlítás az S-MOB-02 kezdőértékével).
- **4. Lépés – Minőségi Reflexió (Opcionális):**
  - Kérdés: *„Mi volt a legnagyobb felismerésed vagy meglepetésed a csapatok együttműködésével kapcsolatban?”*
  - Textarea (max. 300 karakter).
- **Action:**
  - `Értékelés Véglegesítése` (Primary CTA gomb).
- **Lábjegyzet az anonimitásról:**
  - *„A visszajelzések anonim módon, kizárólag aggregált hálózati mutatókként kerülnek feldolgozásra.”*

---

## 6. Workshop Utáni & HR Elemzői Suite (S-ONA-01..02)

### S-ONA-01: Munkahelyi ONA Kérdőív Webes Kitöltője

#### 1. Cél & Szerepkör
Napokkal a workshop után a résztvevők e-mailben kapnak egy tokenizált, biztonságos linket. A kérdőív a valós, mindennapi munkahelyi kapcsolathálót méri fel 3 szabványos szociometriai dimenzióban.

#### 2. A 3 ONA Kapcsolati Dimenzió
1. **Operatív Információáramlás:** *„Kikkel kell rendszeresen egyeztetned a mindennapi munkád elvégzéséhez?”*
2. **Szakmai Támogatás & Tanácskérés:** *„Kihez fordulsz a szervezetben, ha összetett szakmai akadályba ütközöl és tanácsra van szükséged?”*
3. **Innováció & Ötletfejlesztés:** *„Kikkel vitatod meg a leggyakrabban az új ötleteidet és folyamatfejlesztési javaslataidat?”*

#### 3. Pontos UI Layout (Desktop & Reszponzív Tablet)
- **Fejléc:**
  - Szervezeti branding és `PeerPlay Munkahelyi Hálózatelemzés` cím.
  - Előrehaladási mutató: `Dimenzió 1 / 3` vékony kék csíkkal.
- **Kérdéskártya (`.theme-card max-w-3xl mx-auto p-8 space-y-6`):**
  - Cím és kontextusleírás (higgadt, tiszta szakmai megfogalmazás).
  - **Munkatárs Kereső & Multi-Select Komponens:**
    - Keresőmező (`input search`): Név vagy részleg beírásakor azonnali szűrés a dolgozói adatbázisból.
    - Kiválasztott személyek listája elegáns chipekként: Név, munkakör, részleg, mellette `x` eltávolítás.
  - **Kapcsolati Gyakoriság Beállító (Minden kiválasztott személy mellett):**
    - Rádióválasztó: `Napi` · `Heti` · `Havi`.
- **Actions:**
  - `Következő Kérdés →` / Utolsó lépésnél `Válaszok Végleges Mentése`.
- **Bizalmi & Adatvédelmi Nyilatkozat:**
  - *„A felmérés célja a szervezeti silók és információs akadályok azonosítása. A válaszokból nem készül egyéni teljesítményértékelés.”*

---

### S-ONA-02: Vezetői Diagnosztikai Riport (Executive HR Dashboard)

#### 1. Cél & Szerepkör
A HR vezetők, C-level döntéshozók és vezetési tanácsadók stratégiai elemző munkafelülete. Összegzi a szimuláció objektív tranzakcióit, a peer percepciókat és a munkahelyi ONA hálózatot.

#### 2. Az 5 Elemzési Réteg Szintézise
```text
[L1: P2P Tranzakciók]  ──┐
[L2: Banki Termelés]   ──┼──> [SZINTETIZÁLÓ MOTOR] ──> [S-ONA-02 HR DASHBOARD]
[L3: Pre/Post Energia] ──┤                                     │
[L4: Peer Percepció]   ──┤                                     ▼
[L5: Munkahelyi ONA]   ──┘                          [Nyomtatóbarát Vezetői PDF]
```

#### 3. Pontos UI Layout
- **Topbar / Header (`.theme-card p-6 flex items-center justify-between`):**
  - Bal oldal: `Szervezetdiagnosztikai Összegzés · PeerPlay Intelligence`, alatta az elemzett szervezet neve és dátuma.
  - Jobb oldal: Akciógombok:
    - `Nyomtatóbarát PDF Export` (Vékony keretes másodlagos gomb).
    - `Adatok Exportálása (CSV)` (Szöveges másodlagos gomb).
    - `Riport Véglegesítése & Megosztása` (Primary CTA gomb).
- **KPI Kártyasor (4 Statisztikai Kártya):**
  - **1. Hálózati Sűrűség (Density):** `64%` (Optimális együttműködési szint).
  - **2. Reciprocitási Ráta:** `78%` (Kölcsönös adok-kapok arány a szimulációban).
  - **3. Átlagos Energia Delta:** `+2.2 pont` (Kezdő 6.2 ➔ Záró 8.4 emelkedés).
  - **4. ONA Kitöltöttségi Arány:** `94%` (15 / 16 munkatárs válaszolt).
- **Fő Elemző Munkaterület (2 Oszlopos Grid):**
  - **Bal oszlop (7 col) – Interaktív Szervezeti Topológia (Szociogram Panel):**
    - Beépített hálózati gráf nézet (Cytoscape / SVG vászon).
    - Szűrőkapcsolók a gráf felett:
      - `[x] Szimulált Kereskedelmi Háló` (Kék élek).
      - `[x] Munkahelyi ONA Háló` (Szürke élek).
      - `[x] Átfedések Kiemelése` (Zöld vastag élek - ahol a játék és a valóság egybeesik).
    - Csomópontok mérete: Centralitás (befolyás és kapcsolatok száma).
    - Kiemelt azonosított szerepek:
      - **Informális Híd (Broker):** Nagy Anna (Beta Ind.) – Magas közvetítői szerep mindkét hálózatban.
      - **Silókockázat:** Delta Ventures / IT Support részleg – Kifele izolált, csak belsőleg kommunikáló egység.
  - **Jobb oszlop (5 col) – Vezetői Diagnosztikai Megállapítások (Actionable Insights):**
    - Kártyák strukturált, szerkesztői stílusú megállapításokkal:
      1. **Kulcsember-függőség az információáramlásban:** Az elemzés kimutatta, hogy a részlegek közötti információcsere 68%-a egyetlen munkatárson fut keresztül. Ez komoly szűk keresztmetszeti kockázat.
      2. **Adatvédelmi és k-Anonimitási Szabályzat ($k \ge 3$):** Bármely olyan részleg vagy alcsoport esetében, amelynek létszáma 3 főnél kisebb ($k < 3$), a riport nem jelenít meg egyéni vagy alcsoport-szintű aggregációt, hanem automatikusan a felettes szervezeti egységbe olvasztja az adatokat a munkavállalói anonimitás megőrzése érdekében.
      2. **Rejtett együttműködési potenciál:** A szimuláció során a Gamma és Beta csapatok között intenzív kooperáció alakult ki, amely a valós munkahelyi ONA adatokban még nem létezik.
      3. **Silókockázat kezelése:** A perifériára szorult csoportok bevonására belső rotáció vagy keresztfunkcionális projektek indítása javasolt.
- **Lábjegyzet:** Metodológiai hitelesítés és ONA matematikai mutatók magyarázata (In-degree, Out-degree, Betweenness).

#### 4. Állapotok
- **Loading:** Gráf renderelés és adatszintézis folyamatjelzővel.
- **Low Sample Warning (<70% ONA válaszadás):** Borostyánsárga figyelmeztetés: *"A munkahelyi kérdőív kitöltöttsége 68%. A diagnosztikai következtetések tájékoztató jellegűek."*
- **Complete:** Teljes interaktív dashboard elérhető.

---

## 7. Rendszerszintű Komponens Szótár & Tailwind Token Referencia

| Komponens Neve | Célja és Megjelenése | Tailwind Osztályok |
| :--- | :--- | :--- |
| **`.theme-card`** | Alapvető felületi konténer | `bg-white border border-slate-200 rounded-xl shadow-sm p-6` |
| **`.btn-primary`** | Elsődleges CTA akció | `bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-5 py-2.5 rounded-lg shadow-sm transition-colors` |
| **`.btn-secondary`** | Másodlagos kezelőgomb | `bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-sm px-4 py-2 rounded-lg transition-colors` |
| **`.timer-hero`** | 3 méterről olvasható facilitátori óra | `text-5xl font-mono font-bold tracking-tight text-slate-900 tabular-nums` |
| **`.badge-green`** | Jóváhagyott, pozitív egyenleg státusz | `bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs px-2.5 py-0.5 rounded-full font-semibold font-mono` |
| **`.badge-amber`** | Piaci esemény, figyelmeztető státusz | `bg-amber-50 text-amber-700 border border-amber-200 text-xs px-2.5 py-0.5 rounded-full font-semibold font-mono` |
| **`.stepper-btn`** | Minőségátvételi darabszám-módosító | `w-9 h-9 flex items-center justify-center hover:bg-slate-100 font-mono font-bold text-slate-700 active:bg-slate-200 transition` |
| **`.tnum`** | Tabuláris számok ugrálásmentes kijelzéshez | `font-variant-numeric: tabular-nums` (`font-mono`) |

---

## 8. Verifikációs Checklista a Megvalósításhoz (`qa-validator` Gate)

Minden fenti képernyő implementálásakor az alábbi minőségbiztosítási szabályok érvényesek:
- [ ] **Zéró Emoji:** Egyetlen gombon, címsoron vagy státuszjelzőn sincs emoji karakter.
- [ ] **Daylight-First:** Az alapértelmezett séma világos (`#F8FAFC`), magas kontrasztú, sötét témába nem esik vissza.
- [ ] **3 méteres Időzítő:** Az `S-FAC-02` képernyőn az időzítő betűmérete minimálisan 44px, monospaced és tabuláris.
- [ ] **Kétoldalú Kereskedelmi Zárás:** Az `S-TEAM-02` tranzakciói kizárólag kölcsönös jóváhagyással és Prisma ACID tranzakcióban futnak le.
- [ ] **GDPR & Anonimitási Küszöb:** Az `S-MOB-01` kötelezővé teszi a hozzájárulást, az `S-ONA-02` pedig nem tesz közzé egyéni negatív minősítést.
- [ ] **Mikroszövegezés:** A hibaüzenetek és instrukciók higgadt, tárgyilagos stílusúak, mentesek a cirkuszi zsargontól.

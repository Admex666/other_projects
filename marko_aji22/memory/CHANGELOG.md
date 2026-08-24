# Changelog

## [1.6.0] - 2026-08-24 - Perzisztencia, Visszalépés & 5 Mystery Kocsma Jellegzetesség
- **1. Állomás (Bowling):** Eltávolítottuk a Google Maps útvonaltervező linket és az „itt találkozunk” szövegeket.
- **Állapotmentés (State persistence):** Minden feloldás (arcfelismerés állapota, pontszámok, étel és kocsma választások) a `localStorage`-ban tárolódik, így oldalfrissítéskor sem vész el semmi.
- **Visszalépés (Back navigation):** A fejlécben elhelyeztünk egy balra mutató nyílgombot, amellyel bármikor vissza lehet lépni a korábbi állomásokra.
- **Hangerő némítás:** Eltávolítottuk a némító gombot a jobb felső sarokból, a hangok mindig aktívak.
- **3. Állomás (5 Mystery Kocsma opció):** Bekerült az 5 megadott rejtélyes mondat külön dummy koordinátákkal a [`questConfig.ts`](file:///e:/Data/other_projects/marko_aji22/src/config/questConfig.ts)-be:
  1. *„az xG mindig nyüzsgő otthona”* (A Grund)
  2. *„Choose your character”* (BarCraft Corvin)
  3. *„nyugalom a káoszban”* (7ker pub)
  4. *„irány a romok közé”* (Füge Udvar)
  5. *„bort iszik és vizet prédikál”* (Humbák Borkápolna)

## [1.5.2] - 2026-08-17 - Vercel Deployment Configuration
- Hozzáadtuk a [`vercel.json`](file:///e:/Data/other_projects/marko_aji22/vercel.json) konfigurációs fájlt SPA útválasztási átirányításokkal (rewrite), HTTPS biztonsági fejlécekkel és az egyedi képek/hangok (`/images`, `/sounds`) gyorsítótárazásával.

## [1.5.1] - 2026-08-17 - 4 Másodperces Arcfelismerő Előkészületi Várakozás
- Az arcfelismerés indításakor az ablak azonnal megnyílik a kamerás célkereszttel és a „Kamera inicializálása és fókuszálás... (Nézz a lencsébe!)” felirattal, majd **4 másodpercig várakozik**, mielőtt elindul a százalékos letapogatási csík.

## [1.5.0] - 2026-08-17 - Mystery Progression & Arcfelismerés utáni Bowling Reveal
- **Titkosított / Meglepetés állomás-sorrend:**
  - Eltávolítottuk a tervezett programok listáját a kezdő képernyőről (`Stage1Intro`), így az induláskor semmi nem derül ki előre.
  - A felső fejléc HUD-ban a jövőbeli állomások nevei rejtve maradnak (`1. Állomás`, `2. Állomás`, `3. Állomás`), amíg el nem érik őket.
- **Bowling leleplezése csak Arcfelismerés után:**
  - Az 1. állomásra érkezve az oldal címe `1. Állomás: Személyazonosítás`, a bowling helyszín és a strike kihívás pedig zárolva van.
  - Csak a biometrikus arcfelismerés (és a meme hang/kép) lefutása és megerősítése után tárul fel a Bowling címe, találkozója és a pontszámláló!

## [1.4.0] - 2026-08-17 - Funny Face Scan & Custom Meme Audio
- **Kamu Arcfelismerés & Személyazonosítás a Bowlingnál:**
  - Hozzáadtuk a `Kötelező Személyazonosítás` funkciót a bowling állomáshoz.
  - Célkeresztes, lézeres keresőanimáció és biometrikus szkennelési állapotok („Arcvonások elemzése...”, „Körözési adatbázis keresése...”).
  - A szkennelés végén felugrik a szülinaposról készült vicces kép, a humoros gyanúsított felirat, és automatikusan elindul a `look_at_this_dude.mp3` hangeffekt!
  - Létrehoztuk a [`public/images/`](file:///e:/Data/other_projects/marko_aji22/public/images) és [`public/sounds/`](file:///e:/Data/other_projects/marko_aji22/public/sounds) mappákat a saját képek és hangok kényelmes bemásolásához.

## [1.3.0] - 2026-08-17 - Arrival Victory Audio & Custom Sound Support
- **Automatikus megérkezési esemény & hangeffekt:**
  - Amikor a csapat 30 méteren belülre ér az étteremhez vagy a kocsmához (vagy a tesztelő csúszkával lecsökkented a távolságot), az app automatikusan:
    1. Lejátssza a győzelmi fanfárt (`sound.playArrivalVictory()`).
    2. Aktiválja a telefon rezgését (`triggerHaptic('success')`).
    3. Konfetti robbanást lő ki a képernyőre (`fireConfettiBurst()`).
    4. Leleplezi a helyszín nevét, pontos címét és a térképes útvonal gombot.
- **Egyedi audio fájlok támogatása:**
  - Létrehoztuk a [`public/sounds/`](file:///e:/Data/other_projects/marko_aji22/public/sounds) mappát. Ha ide bemásolsz egy `arrival.mp3` vagy `victory.mp3` fájlt, az app azonnal azt fogja lejátszani; ha nincs feltöltve fájl, automatikusan a beépített Web Audio szinti-fanfár szólal meg.

## [1.2.0] - 2026-08-17 - Design De-slopping & Native Mobile Polish
- **Dizájn és felület letisztítása:**
  - Eltávolítottuk az AI-sablonos háttér blur fényfoltokat (`blur-[120px]`), a neon glow árnyékokat és a túlzó glassmorphism-et.
  - Bevezettük a szilárd felületi rétegződést (`surface-card`, `surface-elevated`) és a tiszta, határozott mikrovonalakat (`border-slate-800`).
  - Megszüntettük a monoton 3-4 kártyás egymásra halmozást és a túlzó középre igazítást; helyette természetes, balra zárt tipográfiai ritmust és egybefüggő forgatókönyv paneleket alkottunk.
  - Kikapcsoltuk a felesleges állandó lebegő/villogó mikromozgásokat és díszítő ikonokat (`Sparkles`).
- **Autentikus születésnapi szövegezés:**
  - Lecseréltük a sablonos „Top Secret Agent” szövegeket közvetlen, baráti és vicces születésnapi hangvételre.
- **Teljesítmény:**
  - A CSS bundle mérete ~30%-kal csökkent a felesleges animációk és glow filterek kigyomlálásával.

## [1.1.0] - 2026-08-17
- Átstrukturáltuk a 2. és 3. állomást a kérés szerint:
  - **Étterem szakasz (2. Állomás):** A címe "BOWLING UTÁNI TÁPLÁLKOZÁSI STRATÉGIA" lett a kért 4 fix opcióval (`🥗 1 — Felelős döntés`, `🍜 2 — Normális ember`, `🍔 3 — Leszarom`, `💀 4 — Holnap megbánom`).
  - Minden étkezési stratégiához egyedi GPS koordináták és helyszín tartozik a `questConfig.ts`-ben.
  - A választás után a beépített **Radar és Iránytű** HUD vezet el a kiválasztott étteremhez, majd célba éréskor leleplezi az éttermet.
  - **Kocsma szakasz (3. Állomás):** Eltávolítottuk a radart és az iránytűt; kizárólag egy letisztult **Hideg-Meleg termikus érzékelő** kijelző (hőmérséklet sáv, állapot, távolság, nyomok) vezeti a csapatot.

## [1.0.1] - 2026-08-17
- Javítottuk a képernyők felső térközét és margóit:
  - Növeltük a `.safe-top` dinamikus és alapértelmezett felső margóját a notch-ok és status bar-ok kényelmes kezeléséhez (`src/index.css`).
  - Növeltük a fix fejrész (`HeaderHUD.tsx`) belső paddingjét és alsó árnyékát.
  - A fő tartalomkonténer (`App.tsx`) és minden egyes állomáskomponens (`Stage0Teaser` - `Stage5Finale`) bőséges felső térközt kapott, így a tartalom nem tapad rá a fejlécre mobil eszközökön és asztali nézetben sem.

## [1.0.0] - 2026-08-17
- Built complete React + Vite + TypeScript + Tailwind CSS PWA birthday quest application for Marko's 22nd birthday.
- Implemented full quest flow:
  - **Teaser & Lock:** Locked status with tactile keypad passcode entry.
  - **Mission Briefing:** Cyber-mission narrative, rules of engagement, inventory checklist.
  - **1. Bowling Showdown:** Fixed meetup location, map directions link, strike milestone counter.
  - **2. Food Choice:** Multi-card interactive meal selector with venue reveal upon selection.
  - **3. Bar Radar:** Proximity radar HUD (Haversine formula), compass heading indicator, progressive clue unlocker, and venue reveal.
  - **4. Grand Finale:** Confetti animation, Level 22 badge, evening stats recap, and native sharing.
- Added Web Audio API synthesizer for tactile SFX and vibration API haptics.
- Added `DevDrawer` for testing/simulation (stage jumping, distance slider, orientation angle).
- Created centralized, modular `questConfig.ts` isolating all `PLACEHOLDER` secrets, venues, and texts.
- Verified TypeScript compilation and PWA service worker build.

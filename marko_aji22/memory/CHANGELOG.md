# Changelog

## [1.9.11] - 2026-08-27 - Nulla Késleltetésű Globális GPS Gyorsítótár
- Bevezettünk egy globális memóriabeli GPS cache-t és folyamatos háttérfigyelőt (`singleton watchPosition`):
  - Amint az alkalmazás az első kéréskor megkapja a valós GPS pozíciót, a koordináták azonnal mentésre kerülnek a globális állapotba.
  - A 2. és 3. kocsmaállomásra lépéskor **0 másodperc késleltetéssel**, azonnal az ismert valós koordinátákból számolja a távolságot anélkül, hogy újra lekérdezési várakozásba vagy töltőképernyőbe kezdene!

## [1.9.10] - 2026-08-27 - Kettős GPS Fallback & Asztali PC Tesztelés Támogatás
- **Kettős GPS Lekérés:** Ha a böngésző asztali gépen elakad a precíz hardveres GPS lekérésén (mivel a PC-kben nincs GPS chip), a rendszer automatikusan átvált normál Wi-Fi/IP alapú helymeghatározásra.
- **Asztali PC Tesztelés Gomb:** Közvetlen egykattintásos tesztelési lehetőség a kártyán, ami azonnal beállítja a Kálvin téri pozíciót a Hideg-Meleg funkció kipróbálásához.
- **Mobil optimalizáció:** Mobiltelefonon nyitva azonnal a telefon valós beépített GPS-ét használja.

## [1.9.9] - 2026-08-27 - 3 Kocsma Állomásra Zárás & Valós GPS Helyadat Kérés
- **Valós GPS integráció:**
  - A kocsmatúra keresője mostantól aktívan kéri és figyeli a valós műholdas GPS pozíciót (`HighAccuracy: true`, élő pontosság kijelzés).
  - Ha a böngészőben le van tiltva a helyhozzáférés, egy kiemelt gomb segítségével azonnal felugrik az engedélykérés.
- **3 Kocsma Állomás (6. állomás / 4. kocsma eltávolítva):**
  - A küldetés sorrendje: `Teaser` ➔ `Intro` ➔ `1. Állomás: Biliárd` ➔ `2. Állomás: Vacsora` ➔ `3. Állomás: 1. Kocsma` ➔ `4. Állomás: 2. Kocsma` ➔ `5. Állomás: 3. Kocsma` ➔ `6. Zárás: Grand Finale`.

## [1.9.8] - 2026-08-27 - PASTA. Opció Eltávolítása a Vacsora Listából
- Eltávolítottuk a `PASTA.` tésztázót a 2. állomás választható opciói közül. A 4 aktív lehetőség: **`Kálvin Kebab`**, **`Wrapido`**, **`Heybao`**, **`Burger King`**.

## [1.9.7] - 2026-08-27 - Kép Előtöltés & Hang Szinkronizálás az 1. Állomásnál
- Beépítettünk egy kép-előtöltőt (`Image` preload) az arcfelismeréshez:
  - Az alkalmazás betöltésekor és a scan indításakor a böngésző a háttérben azonnal letölti és memóriában tartja a képet.
  - A progress bar lefutásakor a kód megvárja, hogy a kép **100%-osan, fixen betöltsön**, és csak a kép sikeres renderelésekor indul el a hang és a leleplezés.

## [1.9.6] - 2026-08-27 - Felesleges Térközök Megszüntetése & Kocsma Loop Újraindítási Javítás
- **Felső térközök javítása:** Eltávolítottuk a képernyők közötti felesleges margókat és `justify-between` elrendezést. A felső fejlécek és a kártyák mostantól kompakt, természetes távolságban követik egymást.
- **Kocsma Loop Javítás:**
  - Biztosítottuk, hogy a következő kocsmaállomásra lépéskor (`bar1` ➔ `bar2` ➔ `bar3` ➔ `bar4`) a képernyő **mindig tiszta Mystery Választással induljon**.
  - A loop lépései:
    1. **Mystery választás:** 3 opció közül választás ➔ `KOCSMA KIVÁLASZTÁSA & KERESÉS INDÍTÁSA`
    2. **Hideg-Meleg / Radar:** Követitek a távolságot ➔ 30m alá érve VAGY `MEGÉRKEZTÜNK! (CHECK-IN)` megnyomásakor
    3. **Helyszín Felfedve:** Csak a kocsma neve ➔ rányom a `KÖVETKEZŐ ITAL ➔` gombra
    4. **Új Mystery Választás:** Azonnal a következő állomás 3 jelige-választójával nyit!

## [1.9.5] - 2026-08-27 - Pontos Kocsma Koordináták & Letisztult Felfedés (Csak Név)
- **1. Kocsma lehetőségek rögzítve:**
  - *„Imádom Csehországot”* ➔ **Prága Pub** (`47.489690, 19.063920`)
  - *„Imádom Írországot”* ➔ **Harat’s Pub Budapest** (`47.489073, 19.061649`)
  - *„Csapról kérném”* ➔ **MONYO Tap House** (`47.488715, 19.061126`)
- **2. Kocsma lehetőségek rögzítve:**
  - *„Irány bölcsészkedni”* ➔ **Zuzmó** (`47.487275, 19.070044`)
  - *„Choose your character”* ➔ **BarCraft Corvin** (`47.484505, 19.069262`)
  - *„az xG-kért bármit megteszek”* ➔ **A Grund** (`47.485192, 19.076712`)
- **3. Kocsma lehetőségek rögzítve:**
  - *„nyugalom a káoszban”* ➔ **Hétker pub** (`47.497731, 19.069439`)
  - *„irány a romok közé”* ➔ **Füge Udvar** (`47.498438, 19.066556`)
  - *„bort iszik és vizet prédikál”* ➔ **Humbák Borkápolna** (`47.500232, 19.069864`)
- **Felfedési képernyő tisztítása:** Eltávolítottuk a címet és a Google Maps gombot; megérkezéskor kizárólag a kocsma neve látható tisztán, az alján lévő `KÖVETKEZŐ ITAL ➔` gombbal!

## [1.9.4] - 2026-08-27 - Kocsma Loop: Mystery ➔ Radar ➔ Helyszín Felfedve ➔ Következő Ital
- **„Keleti felé” eltávolítása:** Minden szövegből és címből kivettük a „Keleti felé” megfogalmazást.
- **Pontos Kocsmatúra Loop:**
  1. **Mystery választás:** 3 rejtélyes jelige közül választás.
  2. **Hideg-Meleg / Radar:** Követik a távolságot és a hőmérsékletet (30 méteren belülre érve vagy a `MEGÉRKEZTÜNK! (CHECK-IN)` gombra nyomva lelepleződik a hely).
  3. **Helyszín Felfedve:** Ünneplő képernyő, zene, konfetti, pontos kocsmanév és leírás.
  4. **`KÖVETKEZŐ ITAL ➔` gomb:** Rákattintva automatikusan elindul a következő kocsmaállomás újra a Mystery választással!

## [1.9.3] - 2026-08-27 - Vacsora Radar Eltávolítása & „Jó utat és jó étvágyat” Képernyő
- A 2. állomásnál eltávolítottuk a radart és az iránytűt.
- A vacsora kiválasztása után egy barátságos **„Jó utat és jó étvágyat!”** képernyő jelenik meg a választott hellyel, alján pedig az **`A HASAK MÁR MEGTELTEK`** továbbvezető gombbal!

## [1.9.2] - 2026-08-27 - Vacsora Kártyák Letisztítása
- Eltávolítottuk a felesleges badge-eket és kategória címkéket (pl. „MEXIKÓI”, „BK GRILL”, „FAVORIT”) a vacsora választó kártyákról, így csak a tiszta név, leírás és ikon látható.

## [1.9.1] - 2026-08-27 - Vacsora Opciók Címeinek Tisztítása
- A 2. állomásnál eltávolítottuk az idézőjeles és szlogenes feliratokat a címekből; mostantól tisztán az éttermek nevei szerepelnek: **`Kálvin Kebab`**, **`Wrapido`**, **`Heybao`**, **`PASTA.`**, **`Burger King`**.

## [1.9.0] - 2026-08-27 - All-inn Pub & 4 Kocsma Állomás a Keleti Felé
- **1. Állomás (Biliárd - All-inn Pub):**
  - Beállítottuk a helyszín nevét: **`All-inn Pub`**.
  - Rögzítettük a pontos koordinátákat: `lat: 47.4892848, lng: 19.0628989`.
  - A címet teljesen elrejtettük a felületről.
- **4 Kocsma Állomás (Kálvintól a Keleti felé):**
  - Kibővítettük a küldetést **4 egymást követő kocsmaállomásra** (`bar1`, `bar2`, `bar3`, `bar4`).
  - Mind a 4 állomáson **3 különálló rejtélyes választási lehetőség** (placeholder névvel, koordinátákkal és jeligékkel) érhető el.
  - Mind a 4 állomáson a Hideg-Meleg termikus navigáció vezeti el a csapatot a kiválasztott célponthoz!

## [1.8.0] - 2026-08-27 - Teljes Biliárd Átállás & Számláló Eltávolítása
- **Biliárd refactor a teljes kódbázisban:**
  - Minden bowling hivatkozást, típust és szöveget átírtunk **biliárdra** (`billiard`).
  - Eltávolítottuk a beütött golyók / partik számlálóját a biliárd állomásról; mostantól egy letisztult meccs- és helyszínleírást kapnak, a következő állomásra vezető gombbal.
- **Tiszta építés:** Felesleges korábbi komponensek eltávolítva, production build 100%-ban sikeres.

## [1.7.0] - 2026-08-27 - Kálvin Téri Kezdés: Biliárd Showdown & Új Vacsora Opciók
- **1. Állomás (Biliárd):**
  - Átkereteztük a kezdő állomást: Kálvin téri **Biliárd Showdown** (golyóbelökések / partigyőzelmek számlálóval, a bowling helyett).
  - Az arcfelismerés utáni leleplezés mostantól az azonnali biliárdozást írja elő.
- **2. Állomás (Kálvin Téri Gasztro Stratégia):**
  - Fő favoritként kiemelve: **Kálvin Kebab** (A Királyi Választás).
  - Mellette bekerültek a kért alternatívák a pontos megjelenő szövegekkel és valós Kálvin környéki koordinátákkal:
    1. **Kálvin Kebab**: *„A Királyi Választás”*
    2. **Wrapido mexikói étterem**: *„latin-amerika itt kezdődik”*
    3. **Heybao kínai étterem**: *„az ősi kínai eledel”*
    4. **PASTA. tésztázó**: *„Itáliától Thaiföldig”*
    5. **Burger King**: *„Junk food a grillről”*

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

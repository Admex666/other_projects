# 🏛️ Human-Crafted UI/UX Alapelvek: Az "AI-Generált Hatás" Felszámolása

> **Státusz:** Inviolable Design Rule (Kanonikus Tervezési Szabály)  
> **Dátum:** 2026-11-12  
> **Cél:** A generikus AI sablonok ("AI Slop") kiküszöbölése és egy hiteles, emberi kézzel tervezett, professzionális szervezetdiagnosztikai termékélmény kialakítása.

---

## 1. A Diagnózis: Miért tűnik egy felület "AI-generáltnak"? (A 7 Fő Bűn)

Az LLM-ek és kódgeneráló ágensek (v0, Claude, GPT, Cursor) alapértelmezetten a betanítási statisztikai átlagot ("a 2021–2024-es Tailwind SaaS boilerplate-ek középértékét") reprodukálják. Ennek felismerhető stílusjegyei:

| "AI Slop" Ismertetőjegy | Miért csinálja az AI? | Miért rombolja a minőséget? |
| :--- | :--- | :--- |
| **1. Sci-Fi Void & Dark Mode Default** | A fekete háttér lila/kék gradienssel látványosnak tűnik egy kis thumbnailben. | Egy fizikai tréningteremben, projektoron vagy nappali fényben kivetítve olvashatatlan, mesterkélt és komolytalan. |
| **2. Emoji Pankráció (The Emoji Crutch)** | Az AI nem tud finom ikongráfiát rajzolni, ezért minden gombra és címre emojit pakol (`👑`, `👥`, `🏦`, `⚡`, `🏆`). | A professzionális enterprise szoftvert (Stripe, Linear, Slido) azonnal óvodai vagy hackathon-szintű játékká silányítja. |
| **3. Kártya-apokalipszis (Card-within-card)** | Az AI dobozokban gondolkodik: minden adat köré `rounded-2xl border bg-slate-900` kártyát húz. | Strukturális zűrzavar: a szem nem tud pihenni, megszűnik a természetes hierarchia, minden doboz verseng a figyelemért. |
| **4. "Minden egyszerre fontos" hiba** | Az AI minden címkére pulzáló pontot (`animate-ping`), színes taget és neon árnyékot tesz. | Ha minden villog és színes, semmi sem fontos. Nincs vezérfókusz. |
| **5. Játékshow / Hype Mikroszövegek** | "BUMM!", "Piaci Sokk!", "Szuper Ajánlat!", "Vezérlőpult". | Hitelteleníti az appot. A HR vezetők és vezetési tanácsadók komoly módszertant keresnek, nem cirkuszi hangulatot. |
| **6. Tipográfiai Uniformitás** | Kizárólag standard sans-serif (Inter/Geist) használata, azonos súlyokkal és betűközzel. | Hiányzik az egyedi karakter, a szerkesztői (editorial) kifinomultság és az emberi döntés nyoma. |
| **7. Kontextusidegen Mock Grafika** | 4 kör közé rajzolt véletlenszerű SVG vonalakkal illusztrálja a "hálózatot". | Nem valós elemzés, hanem olcsó vizuális helykitöltő. |

---

## 2. A Megoldás: Emberi Tervezésű (Human-Crafted) UI Alapelvek a PeerPlay számára

### 1. Elv: Fizikai & Taktilis Ihletés (Tangible / Editorial Warmth)
- **A termék kontextusa:** A résztvevők fizikai papírból, vonalzóval dolgoznak az asztaloknál. A szoftvernek ennek a természetes partnerének kell lennie, nem egy sci-fi űrhajónak.
- **Színvilág:** Letisztult, világos, papír-ihlette alaptónusok (meleg törtfehér: `#FBFBFA` / `#F8FAFC`, natúr papír és selymes vászon textúrák).
- **Kontrasztok:** Mély szénszürke és tintafekete tipográfia (`#111827`, `#0F172A`).
- **Gradiens-stop:** Zéró háttérgradiens, zéró neon ragyogás (`glow`). A felületek textúrája tiszta, matt és nyomdai precizitású legyen.

---

### 2. Elv: Tipográfiai Karakter és Szerkesztői Rangsor (Editorial Typography)
Az AI sosem mer bátor betűpárosítást választani. A PeerPlay-nek határozott identitást kell adni:
- **Címek & Fő narratíva:** Prémium szerkesztői betűtípus (pl. *Newsreader*, *Instrument Serif*, vagy karakteres modern groteszk mint a *Cabinet Grotesk* vagy *General Sans*). Ez azonnal közvetíti, hogy ez egy komoly diagnosztikai módszertan.
- **Adatok, Időzítő & Pénzügy:** Monospaced, feszes számjegyek (*JetBrains Mono*, *Geist Mono* vagy tabuláris számok: `font-feature-settings: "tnum"`).
- **Kenyérszöveg & Űrlapok:** Végtelenül olvasható, neutrális groteszk feszes sorközzel.

---

### 3. Elv: Zéró Emoji – Precíziós Vizuális Nyelv
- **Szabály:** Szigorúan tilos dekorációs célú emojikat használni a felületen.
- **Ikonok:** Kizárólag funkcionális, 1.25px - 1.5px vonalvastagságú mikro-SVG ikonok (pl. finom Lucide/Heroicons), vagy a tiszta tipográfia önmagában.
- **Formák:** A geometriai formákat valódi méretarányos, tiszta fekete-fehér vagy finom vonalas műszaki rajzként kell ábrázolni, mint egy tervrajzon, nem pedig színes matricaként.

---

### 4. Elv: Strukturális Aszimmetria és "Negatív Tér" a Kártyák helyett
- Nem kell minden elemnek külön dobozban lennie. A határokat a **térközök (whitespace)**, a finom horizontális választóvonalak (`1px solid #E2E8F0`) és a betűméretek jelölik ki.
- **Változatos sűrűség:** 
  - Ahol tranzakciókat fogadunk: kompakt, feszes adat-táblázat (mint egy Bloomberg vagy Linear terminálban).
  - Ahol a facilitátor olvas vagy instrukciót ad: tágas, nyugodt, könyvszerű tér.

---

### 5. Elv: Valós Műhelymunkás Ergonómia (Real-world Workshop Utility)

| Eszköz / Szerep | Tipikus valós szituáció | UI Tervezési Követelmény |
| :--- | :--- | :--- |
| **Facilitátori Tablet / Laptop** | A facilitátor a teremben sétál, asztalokhoz lép, messziről pillant a képernyőre, közben a kezében tarthatja. | **Óriási, kontrasztos időzítő** (3 méterről is olvasható). Minőségátvételnél nagy érintési célpontok (tap targets), 1 kattintásos jóváhagyás. Nincsenek apró dropdownok. |
| **Kivetítő / Terem Főképernyője** | Gyakran olcsóbb beamer vagy tárgyalótermi TV, ahol a sötét mód kontraszttalan szürke paca lesz. | **Kötelező magas kontrasztú Daylight (Világos) mód**. Tiszta fehér alap, fekete számok, messziről látható fázisállapot. |
| **Résztvevői Mobiltelefon** | A játékos a papírvágás közben gyorsan rápillant, vagy a 10 perces blokkban reflexiót ad. | **Typeform/Slido-szerű minimalizmus**. Egy kérdés egyszerre, kényelmes hüvelykujj-zóna, semmi animációs cirkusz vagy terelő elem. |

---

### 6. Elv: Higgadt, Humánus Mikroszövegezés (Tone of Voice)

| ❌ Kerülendő "AI-slop" szöveg | ✅ Helyes, emberi szakmai mikroszöveg |
| :--- | :--- |
| *"Építőipari Bum: Négyzet Áremelkedés! Bónusz dollárok várnak!"* | *"Piaci árváltozás: A Bank átvételi árfolyama a szabályos négyzetekre ideiglenesen $450-ra emelkedett."* |
| *"Alapanyag Válság (Papírembargó) Aktiválva!"* | *"Nyersanyag-korlátozás: A Bank papírellátása lezárult. Új készletek kizárólag P2P kereskedelemben érhetők el."* |
| *"The Trading Game Szuper Vezérlő"* | *"Facilitátori Irányítópult · 1. Session"* |
| *"Válaszok Sikeresen Elküldve! Köszönjük a fantasztikus részvételt!"* | *"Visszajelzés rögzítve. A válaszok névtelenül aggregálódnak a záró riportban."* |

---

## 3. Minőségbiztosítási Checkliste a Frontend Megvalósításhoz

Mielőtt egy képernyőt vagy komponenst elkészültnek nyilvánítunk (`qa-validator`), ellenőrizni kell:
- [ ] Nem tartalmaz-e dekorációs célú emojit a felület?
- [ ] Nem esett-e vissza sötét cyberpunk/neon sémába ott, ahol tiszta világos munkafelület szükséges?
- [ ] Nincs-e 3-nál több egymásba ágyazott kártyakeret?
- [ ] Valóban olvasható-e a facilitátori időzítő és státusz 2 méter távolságból?
- [ ] A szövegezés higgadt, professzionális és tárgyilagos-e?
- [ ] Van-e határozott, karakteres tipográfiai hierarchia?

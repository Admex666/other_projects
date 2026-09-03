---
id: LEARNING-003-stitch-ui-design-principles
aliases:
  - LEARNING-003-stitch-ui-design-principles
  - LEARNING-003
type: learning
name: "LEARNING-003 — Stitch Design Benchmark: AI-Slop vs. Prémium Tech-SaaS Felület"
status: active


description: A Stitch UI mockupok elemzéséből származó tanulságok a tipográfia, vektoros ikonok, mobil reszponzivitás és színrétegződés területén, amelyek megkülönböztetik az Optivoyát a generikus AI-sablonoktól.

source:
  type: code
  ref: static/css/theme.css

related:
  - "[[DESIGN_SYSTEM]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[UX_PRINCIPLES]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[master-planner-wizard]]"


used_by:
  - "[[DESIGN_SYSTEM]]"
  - "[[master-planner-wizard]]"
---

# 💡 LEARNING-003: Stitch Design Benchmark & Anti-Slop Elemzés

## 1. Context (Kontextus)
A korai fejlesztési fázisban a felhasználói felületre több ponton bekerültek tipikus „AI-os” stílusjegyek:
* Kevert betűméretek, a `Plus Jakarta Sans` általános, szűretlen alkalmazása minden szövegre és számra.
* Platformfüggő színes operációsrendszer-emojik (`📅`, `⏱️`, `🎯`, `✨`) használata gombokon és füleken.
* Merev kétoszlopos rácsok mobilon, ahol a hosszú magyar szövegek (pl. *„⏱️ Időintervallum & Tartózkodási Keret”*) 3-4 csonka sorba törtek.
* Generikus smaragdzöld paletta steril szürke kontrasztokkal.

A [`tests/stitch-designs/`](file:///e:/Data/other_projects/dreamtrip/tests/stitch-designs/) mappa professzionális utazástechnológiai mockupjainak vizsgálata világossá tette a minőségi szakadék okait.

---

## 2. Kulcsfontosságú Felfedezések (Core Learnings)

### 1. Szigorú 3-as Tipográfiai Szereposztás
* **Headlines / Display:** `Plus Jakarta Sans` (600/700) feszes, negatív letter-spacinggel (`-0.01em`, `-0.02em`).
* **Body / Labels / Gombok:** `Inter` (400/500), semleges, professzionális és kiválóan olvasható.
* **Adatok / Számok / Árak / Dátumok:** `JetBrains Mono` (450/500). Minden ár, időtartam és pontszám monospaced karakterekkel jelenik meg, ami azonnali mérnöki pontosságot és pénzügyi/analitikai hitelességet sugároz.

### 2. 0% Emoji, 100% Vektoros Ikonográfia
* Az emojik helyett kizárólag **Material Symbols Outlined** (vagy egységes SVG) glifák használhatók (`text-[16px]`, `text-[18px]`, `text-[24px]`).
* A monokróm, felülethez igazodó vonalas ikonok nem bontják meg a vizuális hierarchiát és minden platformon azonos minőségben jelennek meg.

### 3. Feszes Mikro-szövegezés és Törésbiztos Mobil Layout
* Gombokon és tabokon tilos 25 karakternél hosszabb szövegeket használni:
  * ❌ *„⏱️ Időintervallum & Tartózkodási Keret”* (37 karakter)
  * ✅ *„Időablak”* vagy *„Rugalmas keret”*
* Mobilon a tabok vagy rugalmas `flex-wrap` layoutot kapnak, vagy egymás alá rendeződnek, elkerülve a szétcsúszást.

### 4. Mély Tónusú Fenyőzöld és Anyagszerű Rétegződés
* A generikus világoszöld helyett mély fenyőzöld alapszínek (`#003710`, `#1c4e24`), friss lime/chartreuse akcentusok (`#a7f540`) és tónusos háttérszintek (`surface-container-lowest` $\to$ `surface-container-high`) teremtenek valódi prémium SaaS hatást.

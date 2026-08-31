---
id: anti-ai-slop-policy
aliases:
  - ANTI_AI_SLOP
  - ANTI_SLOP
  - ANTI_AI_SLOP_POLICY
type: governance
name: Anti AI Slop Policy & Authentic Design Invariants
status: active

description: Kötelező érvényű minőségbiztosítási és dizájn-irányelv, amely tiltja a generikus, AI-szagú dizájnsablonokat, buzzwordöket, trendhalmozást és kamu adatokat.

governs:
  - "[[DESIGN_PRINCIPLES]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[UX_PRINCIPLES]]"
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[QUALITY_GATES]]"

related:
  - "[[honest-scraping-policy]]"
  - "[[numbeo-cost-model]]"
  - "[[REVIEW_PROTOCOL]]"
  - "[[DEFINITION_OF_DONE]]"
---

# 🛡️ Governance: Anti AI Slop Policy & Authentic Design Invariants

Ez a szabályzat garantálja, hogy az Optivoya soha ne váljon egy generikus, sablonos, trendeket gondolkodás nélkül egymásra halmozó „AI-slop” alkalmazássá. 

A cél nem pusztán az, hogy a termék *„ne nézzen ki AI által generáltnak”*, hanem az, hogy **úgy nézzen ki és úgy működjön, mintha egy mély termékismerettel rendelkező szakember konkrétan ezt az utazási döntési problémát, ezt az utazót és ezt a döntéstámogató munkafolyamatot akarta volna precízen megoldani.**

---

## 🏛️ A Legfőbb Szabály (The Core Invariants)

$$\text{Specificity} > \text{Trendiness}$$
$$\text{Function} > \text{Decoration}$$
$$\text{Character} > \text{Sterile Polish}$$
$$\text{Real Data} > \text{Placeholder Content}$$
$$\text{Intentionality} > \text{Default Templates}$$

---

## 1. 🎨 Vizuális Design (Visuals & Aesthetics)

* **Nincs automatikus lila–kék AI-gradient**: Tilos a klisés „AI lila-kék neon” színátmenet használata kizárólag azért, mert modernnek tűnik. A termék saját, kurált, harmonikus palettáját kell használni.
* **Nincs univerzális `rounded-2xl` minden elemen**: Az elemek lekerekítésének funkcionális hierarchiát kell követnie; nem lehet minden kártya, gomb, badge és konténer túlkerekített bubble-forma.
* **Nincs indokolatlan árnyékhalmozás**: Nem kaphat minden kártya és doboz vastag drop-shadowt lapos felületeken.
* **Tilos a Glassmorphism halmozás**: A navbar + sidebar + card + modal + input együttes glassmorphic homályosítása tipikus AI-slop hiba. Az áttetszőség és háttérelmosás csak célzott rétegzésre (pl. lebegő sáv, modális ablak) használható.
* **Nincs minden gomb pill-alakúra kényszerítve**: A gombok formája fejezze ki a prioritást (elsődleges, másodlagos, kontextuális).
* **Nincs indokolatlan Glow/Neon effekt**: Ne használj fluoreszkáló fényt vagy homályos fényudvart pusztán dekorációként.
* **Nincs gradient szöveg a főcímeken funkció nélkül**: A szöveges tartalom legyen éles, kontrasztos és jól olvasható.
* **Nincs indokolatlan Mesh/Aurora/Blob háttér és Blueprint rács**: A háttér szolgálja az adatvizualizációt és a fókuszt, ne vonja el a figyelmet véletlenszerű színes foltokkal.
* **Trendhalmozás tilalma**: A *Gradient + Glass + Glow + Blur + 3D kártya + Noise háttér* egyidejű használata szigorúan tilos.

---

## 2. 🔤 Tipográfia & Szövegezés (Typography & Copywriting)

* **Egyedi tipográfiai karakter**: Kerüljük az unalmas, steril, alapértelmezett betűkészleteket (pl. Geist vagy standard Inter túlerőltetése). Legyen az appnak tiszta, utazási döntéstámogató karaktere (Plus Jakarta Sans, JetBrains Mono adatmegjelenítéshez).
* **Valódi tipográfiai hierarchia**: A vizuális súlyok és betűméretek tükrözzék az adatok fontosságát, ne legyen minden szöveg azonos optikai súlyú.
* **Nincsenek óriási 80px-es marketing címek termékfelületeken**: A munkafelületen az információsűrűség és átláthatóság az első.
* **„AI-szagú” Buzzwordök szigorú tiltása**: Tilos az olyan elcsépelt, üres marketinges szavak használata, mint:
  * ❌ *Unlock*, *Elevate*, *Empower*, *Revolutionize*, *Seamlessly*, *Next-generation*, *Supercharge*
* **Nincsenek marketinges triádok**: ❌ *„Build faster. Ship smarter. Scale further.”* helyett konkrét, tényalapú leírások szükségesek.
* **Túlzó emoji-használat szigorú mellőzése**: Tilos minden gombra, címre, listaelemre és badge-re válogatás nélkül emojikat pakolni (pl. 🚀 ✨ 💡 🔮 🏆 halmozása tipikus AI-slop tünet). Az emojik helyett preferáljuk a tiszta, konzisztens SVG ikonokat vagy a felesleges vizuális zajtól mentes, letisztult tipográfiát. Egy felületen csak akkor használható szimbólum, ha annak valódi funkcionális felismerhetőségi értéke van (pl. ✈️ járat, 🏨 szállás).
* **Tudományos zsargon és rövidítések mellőzése a felületen (Plain Language Invariant)**:
  * Tilos a felhasználói felület főcímein, gombjain és leírásain tudományos rövidítéseket (AHP, PROMETHEE, MCDM) vagy akadémikus zsargont használni.
  * A gombok és szövegek legyenek olyan egyszerűek és természetesek, hogy **egy 12 éves is azonnal megértse** (pl. *„1. Saját szempontok és prioritások beállítása →”* ahelyett, hogy *„Döntési Profil (AHP + PROMETHEE)”*).
* **Konkrét, numerikus adatok**: 
  * *Helyes:* „150 járatkombináció elemzése 0.007 mp alatt a megadott prioritásaid szerint”
  * *Helytelen (Slop):* „Forradalmasítsd az utazásaidat a legújabb generációs AI intelligenciával”

---

## 3. 🧱 Layout, Struktúra & Ritmus (Layout & Components)

* **Nincs klisés SaaS landing-sablon**: Nem indulhat minden nézet úgy, hogy *navbar → középre zárt hero → 2 óriási CTA gomb → 3 egyforma kártya / Bento grid*.
* **Nincs kényszerített Bento Grid**: A layout kövesse a döntési folyamat lépéseit (Intake → Célállomások → Járatok → Szállások → Összegzés), nem pedig egy divatos Dribbble trendet.
* **Nem lehet minden komponens vizuálisan egyenrangú**: Minden képernyőn legyen pontosan egy domináns fókuszpont.
* **Nincs üresfehér „álprémium” térközpazarlás**: A whitespace nem arra való, hogy ürességet leplezzen; szolgálja az olvashatóságot és az adatok csoportosítását.

---

## 4. 🧩 UX, Interakciók & Állapotkezelés (UX & States)

* **Zéró halott gomb**: Tilos olyan gombot, kapcsolót vagy linket kirakni, ami nem csinál semmit vagy nincs mögötte működő kód.
* **Nincsenek sehová sem vezető menüpontok**: Minden menüelem valódi, működő funkcióra mutasson.
* **Nem csak a Happy Path létezik**: Minden modulnak kötelezően rendelkeznie kell 4 valódi állapottal:
  1. **Empty State** (Üres állapot): Magyarázó, segítőkész üzenet és indítási gomb.
  2. **Loading State** (Betöltési állapot): Valódi folyamatjelző vagy szekvenciális státuszüzenet.
  3. **Error State** (Hibaállapot): Emberi nyelven megfogalmazott hiba és helyreállítási / benchmark opció.
  4. **Success State** (Sikeres állapot): Tiszta, rangsorolt eredmények.
* **Funkcionális mikróanimációk**: Nincs minden elemre és hoverre rátéve a `scale-105` ugrálás vagy végtelen scroll fade-in. Az animáció kizárólag a figyelem irányítását vagy az állapotváltást (pl. kosár frissülés, fiók nyitás) szolgálhatja.

---

## 5. 📊 Tartalom & Adathitelesség (Content & Authenticity)

* **Soha ne találj ki kamu véleményeket (Testimonials)**: Tilos fiktív ügyfélidézeteket vagy kamu értékeléseket generálni.
* **Nincsenek kamu statisztikák**: ❌ *„Trusted by 10,000+ travelers worldwide”* tiltott, ha nem valós mérőszám.
* **Nincsenek generált stock avatarok valódi profilként**.
* **Nincs fiktív mock adat valódi adatként feltüntetve**: Az Optivoya kizárólag valós Kiwi repjegyeket, valós Cozycozy szállásokat, valós Numbeo költségeket és valós Open-Meteo klímaadatokat használ az [[honest-scraping-policy]] szerint. Ha fallbackre van szükség, azt transzparensen `[Piaci Benchmark]` címkével kell ellátni.
* **Nincs Lorem Ipsum vagy „Your title goes here”**.

---

## 6. ♿ Minőség & Hozzáférhetőség (Quality & Responsiveness)

* **Valódi reszponzivitás**: Az appnak minden kijelzőméreten (360px mobil, 768px tablet, 1280px laptop, 1920px monitor) tökéletesen, törések és vízszintes túlcsordulások nélkül kell működnie.
* **Kontrasztarány és olvashatóság**: Nem áldozzuk fel a szövegkontrasztot a divatos szürke-a-szürkén minimalizmus kedvéért (minimum WCAG AA kontraszt).
* **Karakter és egyediség teszt**: Ha a logót és a márkanevet lecserélve a felület megkülönböztethetetlen lenne egy tetszőleges generikus AI startuptól, a dizájn megbukott. Az Optivoya kifejezetten a strukturált többkritériumos utazási döntéstámogatás eszköze.

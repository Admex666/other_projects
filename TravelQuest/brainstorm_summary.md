# Összefoglaló: TravelQuest Brainstorming

Ez a dokumentum a `brainstorm.md` fájlban rögzített ötleteléseink és stratégiai megbeszéléseink kivonata. A projekt célja az utazás és a városfelfedezés játékosítása (gamification), a *Jet Lag: The Game* című sorozat mechanikáiból merítve inspirációt.

## 1. Alapkoncepció
Egy mobilalapú platform, amely a valós teret (városokat) játéktérré alakítja. A cél nem csak a nézelődés, hanem aktív, stratégiai döntéseken alapuló küldetések teljesítése.

### Főbb játékelemek:
*   **Küldetések (Quests):** Helyszínhez kötött feladatok (pl. keress egy 4.5 csillag feletti kávézót, fotózz le egy 1900 előtti szobrot).
*   **Minijátékok:** Olyan speciális játékmódok, mint a *Rail Rush* (tömegközlekedési stratégiai verseny) vagy a *Hide & Seek* (GPS alapú bújócska).
*   **Események (Events):** Váratlan fordulatok (pl. bónuszpontok egy bizonyos járat használatáért, vagy "lezárások", amik korlátozzák a közlekedést).

---

## 2. Termékstratégia és Skálázhatóság
A beszélgetés egyik legfontosabb felismerése, hogy nem manuálisan kell minden városhoz küldetéseket írni, hanem egy **moduláris, procedurális rendszert** kell építeni.

*   **Végtelen tartalom:** Sablonok és AI segítségével a rendszer automatikusan generál egyedi küldetéssorozatokat (run-okat) a Google Maps és más API-k adatai alapján.
*   **Adaptív nehézség:** A játék a felhasználó tapasztalatához igazítja a kihívásokat.
*   **Gyors skálázás:** Mivel a rendszer algoritmusokon alapul, Budapest után Bécs, Berlin vagy bármely más város könnyen bevonható.

---

## 3. Üzleti Modell (Monetizáció)
A termék nem "napi használatos" appként (mint az Instagram), hanem **"alkalmi élményként"** (mint egy szabadulószoba vagy bowling) funkcionál.

*   **Session Pass:** Időalapú korlátlan hozzáférés (pl. 2 órás vagy 1 napos pass 3-5 euróért).
*   **Group Pass:** Csapatok számára kedvezményes közös jegy, ami ösztönzi a közösségi élményt és a viralitást.
*   **City Unlock:** Egy adott város összes tartalmának végleges feloldása.
*   **Amit kerülünk:** A kezdeti kemény fizetési falat (hard paywall) és a reklámokat, mert elrontják az élményt.

---

## 4. Validációs Terv
Mielőtt komoly kódolás indulna, a cél az "élmény" tesztelése:
*   **Fake Gameplay videók:** TikTok-stílusú rövid videók, amik megmutatják a játék hangulatát (pl. visszaszámlálás a Deákon, futás a villamoshoz).
*   **Smoke testing:** Landing page-ek segítségével mérni a CTR-t (kattintási arányt) és a fizetési hajlandóságot különböző árpontokon.

---

## 5. Jogtiszta Megvalósítás
Bár az inspiráció a *Jet Lag*, a megvalósításnak egyedi vizuális és hangzásvilággal kell rendelkeznie. A játékmechanikák (mint a pontgyűjtés vagy GPS-alapú keresés) nem védettek, de a grafikai stílusnak és a brandnek teljesen sajátnak kell lennie.

---

### Következő lépések (ajánlott):
1.  Egy konkrét, 60-90 perces budapesti "Rail Rush" forgatókönyv kidolgozása.
2.  Az első validációs videó elkészítése.
3.  A procedurális generáló motor logikai vázának felépítése.

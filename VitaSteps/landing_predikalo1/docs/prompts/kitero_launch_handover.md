# Handover – VitaSteps Kitérő: MVP-tervezés és piacra lépés

## 1. Kiindulási helyzet

A VitaSteps egy új digitális termékkel, a Kitérővel szeretne piacra lépni.

A Kitérő egy önállóan bejárható, történetmesélésre épülő városi sétaélmény:

- Előre összeállított városi útvonalak.
- Interaktív térkép és GPS-alapú navigáció.
- Érdekes történetek és információk az egyes megállóknál.
- Hangos felolvasás.
- Saját tempóban teljesíthető élmény.

A jelenlegi állapot:

- Elkészültek a Stitch UI-mockupok.
- A mockupok integrálásával elkészült egy jó alapot adó landing page.
- Még nincs működő termék és nincs elkészült, végigjárható séta.
- A fejlesztés nagyrészt vibe codinggal történik.
- A meglévő alapokra építve várhatóan gyorsan elkészíthető egy első prototípus.

Az első útvonal egyértelműen Budapesten lesz.

## 2. Miért merült fel a mostani tervezés?

A fő stratégiai kérdés az volt, hogy:

- Először fejlesszük le a terméket, és csak utána indítsunk hirdetéseket?
- Vagy már működő termék nélkül kezdjünk hirdetni, és csak érdeklődőket gyűjtsünk?

Az érdeklődésgyűjtés előnye, hogy kisebb fejlesztési befektetéssel tesztelhető a piaci érdeklődés. Hátránya, hogy a feliratkozás nem bizonyítja a fizetési hajlandóságot, így a hirdetési pénz könnyen olyan érdeklődőkre mehet el, akik később nem vásárolnak.

A teljes termék előzetes lefejlesztése viszont túl nagy kockázatot jelentene egy még nem validált ötletnél.

A közösen kialakított irány: egyetlen működő MVP-séta elkészítése, majd valódi vásárlásokkal történő validáció.

Nem kell előre egy komplett platformot építeni, de az első vásárlónak már valódi, teljesíthető élményt kell kapnia.

## 3. Az első termék technológiai iránya

Az első verzióban:

- Mobilra optimalizált webapp készül.
- Nem fejlesztünk külön natív iOS- vagy Android-alkalmazást.
- Nem cél az offline használat.
- A webapp a meglévő weboldalba integrálható, például külön `/app` útvonalon.
- A vásárló böngészőből használja a sétát.

A későbbi natív alkalmazás és offline működés csak akkor kerül elő, ha a termék már bizonyította a piaci életképességét.

## 4. A Kitérő teljes rendszere

Nem csupán a sétát kell elkészíteni, hanem a teljes vásárlói és üzleti folyamatot.

A rendszer öt fő elemből áll:

1. Marketingweboldal: termékbemutatás, útvonalak, árak, vásárlási CTA.
2. Webapp: térkép, GPS, megállók, történetek, hanganyagok, haladás.
3. Backend és adatbázis: felhasználók, vásárlások, jogosultságok, útvonalak és használati adatok.
4. Fizetés és automatizmusok: fizetés, számlázás, hozzáférés, emailek.
5. Analitika: hirdetési eredmények, vásárlások, sétaindítások, teljesítések és nyereségesség.

## 5. A tervezett ügyfélút

Meta-hirdetés vagy organikus tartalom

Landing page

Séta kiválasztása és vásárlás

Stripe fizetés

Automatikus számlázás és hozzáférés

Emailes belépés a webappba

Budapesti séta elindítása

Megállók és történetek teljesítése

Visszajelzés és későbbi újravásárlás

A cél a teljes automatizálás: vásárlás után ne kelljen manuálisan hozzáférést adni vagy számlát küldeni.

A fizetést szerveroldali webhook ellenőrzi, és csak hitelesített sikeres fizetés után jön létre a séta használatához szükséges jogosultság.

## 6. Az MVP funkciói

| Funkció                        | Prioritás |
| ------------------------------ | --------- |
| Mobilra optimalizált webapp    | Kötelező  |
| Interaktív térkép              | Kötelező  |
| GPS-helymeghatározás           | Kötelező  |
| Megállók és koordináták        | Kötelező  |
| Történetek megjelenítése       | Kötelező  |
| Hangos felolvasás              | Kötelező  |
| Audiolejátszó                  | Kötelező  |
| Haladás követése               | Kötelező  |
| Séta folytatása                | Kötelező  |
| Vásárlás és jogosultságkezelés | Kötelező  |
| Több útvonal                   | Később    |
| Offline mód                    | Később    |
| Natív alkalmazás               | Később    |
| Gamifikáció                    | Később    |
| Felhasználói közösség          | Később    |

Külön technikai szempont, hogy a böngészős GPS és háttérben történő működés nem minden telefonon garantálható. Az MVP-nek ezért akkor is használhatónak kell maradnia, ha a felhasználó időnként visszatér a webappba.

## 7. Hangalámondás

A javasolt megoldás az előre elkészített AI-narráció.

Folyamat:

1. Történetek megírása és szerkesztése.
2. Végleges szövegek elkészítése.
3. AI hanggenerálás.
4. Kiejtési és minőségellenőrzés.
5. Hangfájlok tárolása.
6. Hanganyagok lejátszása a megfelelő megállóknál.

Nem valós időben generáljuk a hangokat, hanem előre elkészített audiofájlokat használunk.

A többnyelvűség későbbi lehetőség, különösen a turisták célcsoportja miatt.

## 8. Fizetés és automatizáció

Javasolt folyamat:

- Stripe Checkout.
- Szerveroldali webhook.
- Vásárlás rögzítése az adatbázisban.
- Jogosultság automatikus létrehozása.
- Automatikus számlázás (Számlázz.hu vagy Billingo).
- Visszaigazoló email.
- Biztonságos emailes belépés.
- Séta használata.

A fizetési folyamatnak kezelnie kell a sikertelen tranzakciókat, duplikált webhookokat és visszatérítéseket is.

## 9. Üzleti modell és árazás

Korábban felmerült tervezett egyedi sétaár:

- 2 990 Ft.
- 3 490 Ft.

Ezek közül még nincs végleges döntés.

Vizsgált csomagötletek:

| Termék     | Példaként felmerült ár |
| ---------- | ---------------------- |
| Egy séta   | 2 990 Ft               |
| Két séta   | 4 990 Ft               |
| Három séta | 6 990 Ft               |

A csomagárak egyelőre hipotézisek. Többsétás csomagot csak akkor érdemes értékesíteni, ha ténylegesen rendelkezésre áll hozzá a tartalom.

A felhasználó feltételezése szerint egy vásárló átlagosan legfeljebb havonta egyszer vásárolhat sétát. Az első üzleti modellben ezért az egyszeri vásárlásra kell építeni, a visszatérő vásárlást pedig pozitív többletként kezelni.

## 10. Nyereségesség és CAC

A korábbi számítások illusztratív feltételezései:

- Egy séta ára: 2 990 Ft.
- Fizetési és számlázási változó költség: 150 Ft/rendelés.
- Havi fix költség: kb. 15 000 Ft.

A 15 000 Ft havi fix költség mellett a CAC jelentősen befolyásolja a gazdaságosságot.

| CAC      | Egy rendelés fedezete a CAC után |
| -------- | -------------------------------- |
| 500 Ft   | 2 340 Ft                         |
| 1 000 Ft | 1 840 Ft                         |
| 1 500 Ft | 1 340 Ft                         |
| 2 000 Ft | 840 Ft                           |
| 2 500 Ft | 340 Ft                           |

Ezek leegyszerűsített számok, adózás és egyéb költségek előtt.

A további üzleti modellben külön kell kezelni:

- CAC.
- Átlagos kosárérték.
- Vásárlónkénti vásárlási gyakoriság.
- 12 havi árbevétel-LTV.
- Ügyfelenkénti fedezet.
- Fix költségek.
- Refund arány.
- Marketingköltés.
- Sétaindítási és teljesítési arány.

Három kampányszcenáriót is vizsgáltunk 30 000 Ft hirdetési költéssel:

| Forgatókönyv | CAC      | Vásárlás | Árbevétel  |
| ------------ | -------- | -------- | ---------- |
| Optimista    | 750 Ft   | 40       | 119 600 Ft |
| Közepes      | 1 500 Ft | 20       | 59 800 Ft  |
| Gyenge       | 3 000 Ft | 10       | 29 900 Ft  |

Ezek nem piaci előrejelzések, csak a modell érzékenységét szemléltetik.

## 11. Marketing és Meta-kreatívok

Három lehetséges kommunikációs irányt azonosítottunk, amelyek közül még nem választottunk véglegesen:

1. Felfedezés: Budapest rejtett történetei és kevésbé ismert helyei.
2. Közös program: pároknak, barátoknak, családoknak szóló élmény.
3. Turisztikai élmény: Budapest önálló felfedezése, saját tempóban.

Első kreatívcsomagként felmerült:

- 3 rövid videó.
- 3 statikus hirdetés.
- 3 carousel vagy többképes kreatív.

A kreatívokban már a valódi webappot és a tényleges budapesti útvonalat kell bemutatni, nem kizárólag a mockupokat.

## 12. Javasolt technológiai stack

Egy lehetséges kiinduló technológiai összeállítás:

| Terület     | Javaslat                                   |
| ----------- | ------------------------------------------ |
| Frontend    | A meglévő technológia / Next.js            |
| Backend     | Supabase                                   |
| Adatbázis   | PostgreSQL                                 |
| Auth        | Supabase Auth                              |
| Térkép      | Mapbox vagy Google Maps                    |
| Fizetés     | Stripe                                     |
| Számlázás   | Számlázz.hu vagy Billingo                  |
| Email       | Resend                                     |
| Narráció    | AI TTS                                     |
| Analitika   | GA4 + Meta Pixel + szerveroldali események |
| Hibakövetés | Sentry                                     |

Ezt még nem véglegesítettük. Először a meglévő landing page és kódbázis technológiáját kell megvizsgálni. Nem cél a már működő alapok felesleges lecserélése.

## 13. Tervezett fejlesztési ütemezés

| Időszak  | Feladat                                    |
| -------- | ------------------------------------------ |
| 0. hét   | Rendszertervezés és specifikáció           |
| 1. hét   | Webapp, térkép, GPS, megállók              |
| 2. hét   | Tartalom, narráció, fizetés, automatizáció |
| 3. hét   | Teljes tesztelés, hibajavítás, analitika   |
| 3–4. hét | Kreatívok és első marketingkampány         |

Ez egy feszes célbecslés, nem garantált határidő.

# 14. Következő lépés – hol tartunk most?

A beszélgetés végén hat kérdést tettünk fel, amelyekre még várjuk a válaszokat:

1. Milyen technológiával készült a jelenlegi landing page?
2. Emailes mágikus linkkel vagy jelszavas regisztrációval történjen a belépés?
3. Magyarul vagy magyarul és angolul induljon az első séta?
4. Milyen hosszú legyen a séta: 60, 90 vagy 120 perc?
5. Hány megálló legyen: 6–8, 9–12 vagy 13–16?
6. Mekkora fejlesztési és marketingkeret áll rendelkezésre?

A következő feladat nem a fejlesztés azonnali megkezdése, hanem a teljes MVP-specifikáció elkészítése.

Ennek tartalmaznia kell:

- Rendszerarchitektúra és technológiai döntések.
- Adatbázis-struktúra.
- Webapp képernyőinek és funkcióinak specifikációja.
- Backend és API-k.
- Fizetési és számlázási folyamat.
- Emailautomatizmusok.
- Analitikai események.
- Üzleti modell, CAC-, LTV- és profitabilitási kalkulátor.
- Marketing- és kreatívgyártási terv.
- Prioritásokra bontott fejlesztési backlog, amelyet az AI coding agenteknek lehet kiosztani.

Végső cél: a jelenlegi mockupokból a lehető leggyorsabban eljutni egy működő, értékesíthető budapesti Kitérő-sétáig, amelynek nemcsak a technológiája, hanem a vásárlási, kiszolgálási és mérési rendszere is készen áll a piacra lépésre.
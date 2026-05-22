# Last-Minute Wellness - Validációs Stratégia

Ez a dokumentum összefoglalja a "Last-Minute Wellness" (idle capacity marketplace) koncepció keresleti (demand) és kínálati (supply) oldalának legköltséghatékonyabb, gyakorlati validációs lépéseit és elvárt metrikáit.

## 1. Keresleti Oldal (Demand) Validálása
**Módszer:** "Fake Door" (Ál-ajtó) teszt, Supabase / Tally integrációval, alacsony (napi 1.000 - 2.000 Ft) Facebook/Instagram hirdetési büdzsével.

### Go / No-Go Metrikák (Döntési pontok)

*   **CTR (Átkattintási arány a hirdetésen)**
    *   🟢 **GO (Tovább): > 1.5%** -> Valós a probléma, az ajánlat ("last minute masszázs kedvezménnyel") vonzó.
    *   🔴 **NO-GO (Kuka/Újratervezés): < 0.5%** -> Érdektelenség, vagy rossz a hirdetési üzenet (value proposition).
*   **CAC (Ügyfélszerzési Költség / Feliratkozó)**
    *   🟢 **GO: < 2.500 Ft** -> A tervezett ~2.100 Ft-os jutalékkal (take rate) és némi visszatérési rátával (repeat usage) a modell nyereséges tud lenni.
    *   🔴 **NO-GO: > 4.000 Ft** -> Túl drága az akvizíció, a modell minden új usert veszteséggel hozna be.
*   **CVR (Konverziós ráta a landing oldalon)**
    *   🟢 **GO: > 5%** -> Magas vásárlási szándék (High Intent). A userek a konkrét árak (10.500 Ft) és a "betelt" státusz ellenére is megadják az email címüket.
    *   🔴 **NO-GO: < 1-2%** -> Sok az "ablakvásárló" és az árérzékeny kuponvadász, akik lepattannak a konkrétumoknál.
*   **WTP (Fizetési hajlandóság és AOV)**
    *   🟢 **GO:** A userek legalább 30%-a a drágább opciót (pl. 90 perc) vagy az upsellt (pl. aromaterápia) választja.

---

## 2. Kínálati Oldal (Supply) Validálása
**Módszer:** A "Trójai Faló - Ár-teszt" (B opció) megközelítés. 
Nem partnerséget és platformot árulunk, hanem az első keresleti tesztből beeső valós érdeklődőket használjuk fel a szalonok "fájdalomküszöbének" tesztelésére.

### A Validálandó Feltevés
A szalonok hajlandóak az eredeti ár 56%-áért (30% diszkont + 20% platform jutalék levonása után) is odaadni az üresen maradt (idle) kapacitásukat. Egy 15.000 Ft-os szolgáltatásnál ez nettó **8.400 Ft** bevételt jelent a szalonnak. Ezt a konkrét, nettó értéket (8.400 Ft) kell elfogadtatni velük a teszt során.

### A Teszt Folyamata ("B" opció)
Amint a "Fake Door" landing oldalon beesik egy valós név/telefonszám, aki ma estére foglalna 10.500 Ft-ért:
1. Felhívunk egy környékbeli masszázsszalont, vagy rájuk írunk Instagram DM-ben (hogy kikerüljük a recepcióst és a tulajdonost érjük el).
2. **A Pitch:** *"Szia! Van egy vendégem, aki ma este 18:00-ra keres masszázst, de a kerete szigorúan 8.400 Ft. Tudom, hogy ez a listaáratok alatt van, de ha véletlenül pont van egy üres helyetek, befogadjátok ennyiért? Ha nem, semmi gond, hívom a következőt."*
3. Ha ezen a teszten elküldjük a vendéget 8.400 Ft-ért (a platform itt most nem rak el jutalékot, a vendég fizet 8.400-at a helyszínen), tisztán validáltuk a szalon **tényleges ár-érzékenységét** és fájdalomküszöbét.

### Go / No-Go Metrikák a Szalonoknál
*   🟢 **GO:** Ha 10 felkeresett szalonból/masszőrből legalább **2-3 darab** azt mondja, hogy *"inkább 8.400 Ft, mint az üres szék, jöjjön!"*. Ebben az esetben a kínálati oldal árazása és hajlandósága validált.
*   🔴 **NO-GO:** Ha 10-ből 0 szalon fogadja el, és mind a brand/presztízs védelmére hivatkozva utasítja el a diszkontot. Ekkor a 20%-os take rate-et vagy a diszkont mértékét újra kell számolni a modellben.

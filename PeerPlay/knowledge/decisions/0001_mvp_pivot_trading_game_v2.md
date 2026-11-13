# ADR 0001: Pivot to Hybrid Trading Game & 5-Layer ONA Platform (V2)

## Státusz
Elfogadva (Accepted)

## Dátum
2026-11-12

## Kontextus
A PeerPlay eredeti MVP terve (V1) egy tisztán virtuális, kattintás-alapú mezőgazdasági termelési és kereskedelmi szimuláció volt (Global Exchange: vetőmagok, technológiák, termények eladása a böngészőben).
A validációs interjúk és a szakterületi követelmények ([APP_PLAN_v2.md](file:///E:/Data/other_projects/PeerPlay/APP_PLAN_v2.md)) alapján a tisztán képernyős játék nem biztosít kellően természetes, mély és stresszhelyzeti csoportdinamikát egy 90 perces szervezetdiagnosztikai workshop során. 

A klasszikus, fizikailag papírból és sablonokból formákat előállító szimuláció (The Trading Game) bizonyítottan intenzív valós interakciókat vált ki, amely digitális tranzakciós naplózással ötvözve pontos, objektív hálózati adatokat generál.

## Döntés
1. **Hibrid Működési Modell:**
   - A fizikai gyártás papírból, ollóval és sablonokkal történik.
   - A digitális alkalmazás a tranzakciókat (P2P eszköz- és pénzcsere), a facilitátori bankfelvásárlást, a fázisvezérlést, az időzítőt, az esemény-broadcastot és a felméréseket kezeli.
2. **Kliens és Eszköz Modell:**
   - Csapatonként 1 közös munkaállomás (tablet/laptop) a készlet és a P2P kereskedés vezérléséhez.
   - Egyéni mobiltelefonok a résztvevők számára: gyors csatlakozás (kód + email), Pre-survey, Post-survey és Peer Feedback kitöltése.
   - Facilitátori konzol: fázisok léptetése, Breaking News broadcast, minőségellenőrzés és banki jóváírás.
3. **5 Elemzési Réteg és ONA Integráció:**
   - P2P tranzakciós hálózat
   - Gazdasági eredmények
   - Elő- és utólagos kérdőívek (energia, részvétel változása)
   - Peer feedback (szerepek, segítőkészség, koordináció)
   - Workshop utáni Munkahelyi ONA modul (valós kapcsolati háló)
   - Eredmények szintézise: Azonnali Debrief Nézet a 90. percben + Vezetői Diagnosztikai Riport a HR Dashboardon.

## Következmények
- A korábbi V1 mezőgazdasági adatmodellt és UI-t leváltjuk a V2-es formakészítő és P2P eszközcserélő architektúrára.
- Új modulok jönnek létre: Fázisvezérlő, Időzítő, Formaminősítés és Bankfelvásárlás, Peer Feedback és Munkahelyi ONA modul.
- Növekszik az ügyfélérték: nemcsak szórakoztató játékot adunk, hanem valós ONA-val validált diagnosztikát.

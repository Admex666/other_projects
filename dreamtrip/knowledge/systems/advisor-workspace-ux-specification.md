---
id: advisor-workspace-ux-specification
type: system
name: Advisor Workspace UX Interaction Specification
status: active

description: Az Optivoya B2B Advisor Workspace asztali felületének, információsűrű vezérlőpultjának, progresszív kibontási folyamatainak, auto-save állapotkezelésének, Find Better interakcióinak és a belső vs. ügyfél tartalom elválasztásának részletes UX specifikációja.

source:
  type: code
  ref: templates/advisor/advisor_workspace.html

code:
  - templates/advisor/advisor_workspace.html
  - templates/advisor/proposal_print.html
  - templates/hub.html
  - static/js/advisor/

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[UX_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[DESIGN_PRINCIPLES]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[app-hub-and-workspace-switcher]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 🖥️ Advisor Workspace UX Interaction Specification

Ez a dokumentum rögzíti az **Optivoya B2B Advisor Workspace** teljes felületi és interakciós szerződését. A felület célja nem egy B2C fogyasztói wizard utánzása, hanem egy professzionális, asztali munkaállomás (pro-desktop dashboard) biztosítása a tanácsadók számára.

---

## 1. Desktop-First Workspace Shell

Az Advisor Workspace minimum 1280px+ széles képernyőre optimalizált, állandó kontextus-sávval rendelkező, 3 zónás elrendezést használ:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ [Optivoya Agency Brand]   Ügy: Kovács Család (BUD→BCN, 350k Ft)  [Adam]│
├──────────────┬─────────────────────────────────────────────────────────┤
│ 📊 Dashboard │                                                         │
│ 👥 Kliensek  │                     AKTÍV MUNKATÉR                      │
│ 📁 Ügyek     │                                                         │
│ 🔍 Kutatás   │  - Brief & Megkötések Szerkesztése                      │
│ 🗂️ Opciók    │  - 3 Archetípus Kártya (Összehasonlítás)                │
│ ⚖️ Matrix    │  - Relatív Eltérések & Trade-offok                      │
│ 📄 Ajánlatok │  - Keresési Eredmények & Pinned Elemek                  │
│ ⏱️ Idővonal  │                                                         │
│ ⚙️ Beállítás │                                                         │
└──────────────┴─────────────────────────────────────────────────────────┘
```

### Állandó Case Kontextus Sáv
A munkaterület tetején minden nézetben megjelenik:
- **Kliens neve & címkék**: pl. *Kovács Péter (Family, Luxury)*
- **Ügy címe & fókusz**: *Spanyol Tengerpart (Barcelona / Costa Brava)*
- **Költségkeret & pénznem**: *350 000 Ft (Group, Hard Ceiling)*
- **Utazási dátumok & létszám**: *2026.06.12 – 2026.06.19 (2 felnőtt, 1 gyerek)*
- **Aktív Research Státusz**: *COMPLETED (3 opció kész)*

---

## 2. Progresszív Kibontás (Non-Linear Workflow)

A munkafolyamat logikailag egymásra épül, de az Advisor **bármikor szabadon navigálhat** a fázisok között anélkül, hogy az adatok elvesznének:

```text
Kliens Kiválasztása → Ügy Létrehozása → Brief & Megkötések → Kutatás Futtatása → 3 Opció Elemzése → Összehasonlítás → Ajánlat Generálása & Megosztás
```

- **Brief fázis**: Alapadatok, 4 rétegű preferenciák (Hard, Soft, Avoid, Nice-to-have), költségkeret.
- **Kutatás fázis**: Élő szolgáltatói lekérdezések (Kiwi, Cozycozy, Open-Meteo, POI-k) és kandidátus kosarak.
- **Opciók fázis**: 3 döntési archetípus (Best Overall, Best Value, Best Experience) egyidejű kártyanézete.
- **Összehasonlítás fázis**: Relatív különbségek (árkülönbözet, utazási idő, hotel rating).
- **Ajánlat fázis**: Verziózott (v1, v2) ügyfél-ajánlat szerkesztése, nyomtatási előnézet és kriptográfiai megosztás.

---

## 3. Server-Persisted Auto-Save

A felületen minden módosítás automatikusan perzisztálódik a backend adatbázisban:
- **Állapotjelzők az UI-n**:
  - `Mentve` (zöld pipa ikon)
  - `Mentés folyamatban...` (pulzáló pont)
  - `Mentve 14 mp-el ezelőtt`
  - `Mentési hiba!` (azonnali piros figyelmeztetés retry gombbal)
- A tanácsadónak nem kell mentés gombokat keresgélnie; a brief, a jegyzetek és az override-ok azonnal a `TripCase` aggregátumba íródnak.

---

## 4. "Find Better" Célzott Finomhangolási UX

Ha egy generált opció valamelyik része nem ideális, a "Find Better" funkció **nem indítja újra vakon a teljes kutatási folyamatot**, hanem megőrzi a globális kontextust és csak az adott komponenst optimalizálja:

```text
[Jelenlegi Opció: Best Overall — 342 000 Ft]
 └─ Hotel: 4★ Hotel Central (€140/éj)

[Find Better Gomb Megnyomása]
 ├─ Cél Kiválasztása:
 │   [ ] Alacsonyabb ár keresése
 │   [x] Jobb elhelyezkedés / magasabb értékelés keresése
 │   [ ] Medencés / tengerparti alternatíva
 └─ Megőrzendő Invariánsok:
     [x] Járatmenetrend & Légitársaság megőrzése
     [x] Utazási dátumok megőrzése
     [x] Költségkeret hard ceiling megőrzése
```

---

## 5. Feltétel-enyhítési UX (0-Találat Esetén)

Ha a megadott megkötések túl szigorúak és 0 érvényes kombináció maradt (Dead-End), a rendszer strukturált diagnózist és 1-kattintásos javaslatokat ad:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠️ 0 Találat a Megadott Feltételekkel                                  │
│ A közvetlen járat + 5★ hotel + 150 000 Ft keret nem teljesíthető.      │
├────────────────────────────────────────────────────────────────────────┤
│ Feloldási Lehetőségek (1-Kattintásos Elfogadás):                      │
│                                                                        │
│ 1. [Keret Bővítése] +25 000 Ft (+16%) emelés → 6 új opció oldódik fel  │
│ 2. [Átszállás Engedélyezése] 1 átszállás → 11 új járat nyílik meg      │
│ 3. [Hotel Kategória] 4★ szálloda engedélyezése → 8 új opció válik elérhetővé│
└────────────────────────────────────────────────────────────────────────┘
```
**Szigorú szabály**: Semmilyen feltétel nem enyhül automatikusan; kizárólag a tanácsadó jóváhagyásával alkalmazható patch!

---

## 6. Tanácsadói Felülbírálás (Override & Pinned) UX

Minden generált elem (város, járat, szállás, program) mellett közvetlen műveleti gombok találhatók:
- **📌 Rögzítés (Pin)**: Az elem fixálása az ügyhöz, így a későbbi újragenerálások nem cserélik le.
- **🔄 Csere (Replace)**: Alternatív kandidátus választása a kutatási medencéből.
- **❌ Eltávolítás (Remove)**: Kizárás az ügyből.
- **📝 Auditált felülbírálás**: Ha az Advisor kézzel ír felül egy árat vagy szállást, a rendszer rögzíti az indoklást és az audit naplóba menti (`AdvisorOverrideEntry`).

---

## 7. Belső Tanácsadói vs. Ügyfél Tartalom Elválasztása

A felületen szigorú vizuális és adatszintű elválasztás érvényesül:

| Tartalom Típusa | Belső Munkaállomás (Advisor Only) | Ügyfél Ajánlat (Client Proposal) |
| :--- | :--- | :--- |
| **Kutatási telemetria** | Látható (kiwi ms, provider kódok) | **Szigorúan rejtve** |
| **Belső jegyzetek** | Szerkeszthető, privát sárga kártya | **Szigorúan leválasztva** |
| **Kockázati elemzés** | Részletes figyelmeztetések | Csak releváns ügyfélinformáció |
| **Opció leírása** | Teljes trade-off elemzés | Pozitív, előnyökre fókuszáló szöveg |
| **Szolgáltatói linkek** | Foglalási és közvetlen aggregátor link | Hivatalos ügynökségi linkek |

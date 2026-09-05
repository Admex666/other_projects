---
id: optivoya-strategy
aliases:
  - optivoya-strategy
  - OPTIVOYA_STRATEGY
type: strategy
name: Optivoya Canonical Strategic Context & Product Direction
status: active

description: Az Optivoya kanonikus stratégiai forrása és termékiránya — North Star (Stratégiai & Üzleti), Travel Decision Engine vízió, B2B beachhead use case, H1-H6 validációs hipotézisek, M1-M5 roadmap és döntési szabályok.

related:
  - "[[NORTH_STAR]]"
  - "[[TARGET_CUSTOMER]]"
  - "[[VALUE_PROPOSITION]]"
  - "[[BUSINESS_MODEL]]"
  - "[[OBJECTIVES]]"
  - "[[PRIORITIES]]"
  - "[[CONSTRAINTS]]"
  - "[[CURRENT_STATE]]"
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[unified-trip-model]]"
  - "[[master-planner-wizard]]"

used_by:
  - "[[ADR-001-unified-trip-architecture]]"
  - "[[ADR-006-master-planner-wizard]]"
---

# 🛬 Optivoya — DreamTripPlanner

> **North Star:** egy profitábilis, alacsony founder-inputtal működő lifestyle business.  
> **Első nagy cél:** $\ge 600k$ Ft MRR, $\le 10$ founder óra/hét.  
> **Jelenlegi fókusz:** B2B validation $\to$ első fizető ügyfél.  

---

# 1. NORTH STAR

## Stratégiai North Star

Az Optivoya hosszú távú célja egy **end-to-end Travel Decision Engine** felépítése, amely egy természetes nyelven megfogalmazott utazási igényből személyre szabott, kutatott, optimalizált és végrehajtható utazási ajánlatot állít elő.

Nem egyszerűen utazást „tervezünk”, hanem segítünk eldönteni:
- hova érdemes menni,
- mikor érdemes menni,
- hogyan érdemes odajutni,
- hol érdemes megszállni,
- mit érdemes ott csinálni,
- és hogyan álljon ezekből össze a legjobb teljes utazás.

## Üzleti North Star

Egy kis, profitábilis, nagyrészt automatizált travel-tech business:
- $\ge 600k$ Ft MRR
- $\le 10$ founder óra / hét
- magas profitmargin
- alacsony support- és operációs igény
- automatizálható acquisition és működés

## Nem cél

- VC / fundraising
- nagy csapat
- agresszív növekedés
- felesleges feature-fejlesztés
- founder-intenzív agency business

---

# 2. MIT ÉPÍTÜNK?

## Hosszú távú termék

Az Optivoya egy **Travel Decision Engine**, amely az utazási igénytől a kész, személyre szabott és végrehajtható utazási ajánlatig segít.

```text
UTAZÁSI IGÉNY
      ↓
DESTINATION INTELLIGENCE
Hova menjek?
      ↓
FLIGHT INTELLIGENCE
Hogyan jutok oda?
      ↓
ACCOMMODATION INTELLIGENCE
Hol aludjak?
      ↓
EXPERIENCE / ACTIVITY INTELLIGENCE
Mit csináljak ott?
      ↓
ITINERARY ENGINE
Hogyan álljon össze?
      ↓
OPTIMIZED TRIP
KÉSZ, SZEMÉLYRE SZABOTT UTAZÁS
```

A hosszú távú cél tehát **nem egy flight + hotel kereső**, hanem egy olyan döntéstámogató rendszer, amely az utazás teljes összeállításában segít.

## Jelenlegi beachhead

A hosszú távú vízió B2C és B2B2C irányban is használható, de a jelenlegi elsődleges beachhead:

**B2B Travel Advisor / Travel Agency**

A B2B nem a végső piac-definíció, hanem a jelenlegi legjobb belépési pont.

A travel advisoron keresztül tudjuk először validálni:
- a valódi travel-planning workflow-t,
- a research problémákat,
- a döntési logikát,
- az output minőségét,
- a time savinget,
- és a willingness to pay-t.

Később ugyanez a decision engine közvetlenül az utazó számára is használható (`B2B → B2B2C → B2C`).

## B2B elsődleges use case

$$\text{Ügyféligény} \longrightarrow \text{research} \longrightarrow \text{összehasonlítás} \longrightarrow \text{kombináció} \longrightarrow \text{shortlist} \longrightarrow \text{advisor review} \longrightarrow \text{ügyfélajánlat}$$

Az Optivoya célja nem az advisor lecserélése, hanem annak elérése, hogy ugyanazt a professzionális munkát **lényegesen gyorsabban és jobb döntéstámogatással** tudja elvégezni.

## Fő érték

Nem az API válaszidejét mérjük, hanem a **teljes munkafolyamat során megtakarított időt**.

$$T_{\text{manual}} = \text{teljes manuális research} + \text{összehasonlítás} + \text{shortlist készítés}$$

$$T_{\text{Optivoya}} = \text{Optivoya futtatás} + \text{verification} + \text{editing} + \text{finalization}$$

### Fő KPI
**Total Time Saved / Client:**
$$\text{Total Time Saved} = T_{\text{manual}} - T_{\text{Optivoya}}$$

### Másodlagos KPI-k
- Time Reduction %
- Verification Time
- Edit Time
- Shortlist Acceptance Rate
- Advisor Rejection / Edit Rate
- Factual Error Rate
- Missing Option Rate
- Time to Client-Ready Proposal

A valódi érték nem az, hogy az Optivoya milyen gyorsan generál outputot, hanem az, hogy **mennyi idő alatt jut el az advisor egy ügyfélnek elküldhető, megbízható ajánlatig.**

---

# 3. JELENLEGI BETA

## Cél

Nem teljes travel planner építése.  
A beta célja annak bizonyítása, hogy a jelenlegi motorokkal az advisor **valódi ügyfélkérést gyorsabban és jobb minőségben tud feldolgozni**.

## Beta MUST HAVE

### Destination Matcher
- desztinációk személyre szabott rangsorolása
- releváns flight árak
- fő döntési szempontok kezelése

### Flight Intelligence
- valós flight adatok
- ár
- menetidő
- átszállás
- időzítés
- személyre szabott rangsor

### Accommodation Intelligence
- releváns szállások
- ár
- értékelés
- lokáció
- személyre szabott rangsor

### Unified workflow
A három motor ne különálló tool legyen:
> **Human-in-the-loop:** Optivoya $\to$ candidate solutions $\to$ ranking $\to$ trade-offs $\to$ advisor verification $\to$ advisor edit/approval $\to$ client proposal.

> A beta nem azt bizonyítja, hogy az AI tud-e utazási ajánlatot generálni. Azt bizonyítja, hogy az advisor **gyorsabban tud-e jobb ügyfélajánlatot készíteni** az Optivoya segítségével.

## Még NEM szükséges

- teljes itinerary engine
- komplex TSP / VRPTW
- teljes programtervezés
- mobilapp
- chatbot
- enterprise funkciók
- komplex CRM
- egyéb „nice-to-have” feature

> **Vezérelv:** Új feature csak akkor kerülhet a beta scope-ba, ha valódi user bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.

---

# 4. MIT AKARUNK BIZONYÍTANI?

## H1 — A probléma létezik
A travel advisorok valódi ügyfélkérések feldolgozásakor jelentős időt töltenek:
- research-csel,
- flight és accommodation kereséssel,
- alternatívák összehasonlításával,
- kombinációk ellenőrzésével,
- shortlist készítésével.

**Bizonyíték:**
- Manual Time / Client
- workflow breakdown
- ismétlődő pain pointok

---

## H2 — Az Optivoya ténylegesen időt takarít meg
A teljes workflow rövidebbé válik az Optivoya használatával.

**Fő mérőszám:**
- Total Time Saved / Client
- Time Reduction %

**Kritikus ellenőrzés:**
- Verification Time
- Edit Time

---

## H3 — Az output elég jó ahhoz, hogy használható legyen
Az advisor nem csak érdekesnek találja az outputot, hanem azt tényleges munkában felhasználja.

**Mérőszám:**
- Shortlist Acceptance Rate
- Advisor Edit Rate
- Factual Error Rate
- Missing Option Rate
- „Would you send this to your client?”

---

## H4 — A workflow ismételhető
Az advisor több valódi ügyfélkérésnél is használja a rendszert.

**Mérőszám:**
- Repeat Usage
- Requests / Advisor
- Weekly Usage
- Retention

---

## H5 — A létrehozott értékért fizetnek
Az időmegtakarítás és workflow-érték elég nagy ahhoz, hogy az advisor vagy agency ténylegesen fizessen.

**Mérőszám:**
- Paid Pilot
- Willingness to Pay
- Paid Conversion
- ARPU
- Churn

---

## H6 — Az ügyfélszerzés megismételhető
Nem csak személyes kapcsolatokból lehet ügyfelet szerezni.

**Mérőszám:**
- Qualified Leads
- Reply Rate
- Demo / Pilot Conversion
- Paid Conversion
- CAC
- Founder Hours / Customer

---

## Validációs alapelv

Nem a feature-ök számát, az AI válaszidejét vagy a fejlesztési sebességet tekintjük bizonyítéknak.

**A döntési sorrend:**
$$\text{Problem} \longrightarrow \text{Value} \longrightarrow \text{Quality} \longrightarrow \text{Repeat Usage} \longrightarrow \text{Payment} \longrightarrow \text{Repeatable Acquisition}$$

---

# 5. VALIDATION ROADMAP

## M1 — B2B Beta Validation
**Cél:** Bizonyítani, hogy az Optivoya valódi munkában használható és mérhető értéket teremt.

### Siker
- 20–30 releváns lead elérése
- $\ge 10$ valódi beszélgetés
- $\ge 5$ aktív beta user
- $\ge 3$ ismételt használó
- mérhető time saving
- pozitív érték-visszajelzés
- $\ge 2$ komoly fizetési hajlandóság
- lehetőleg $\ge 1$ fizető ügyfél  
$$\longrightarrow \textbf{Go / Iterate / Pivot / Stop}$$

## M2 — First Paid Customers
**Cél:** Bizonyítani, hogy az Optivoyáért ténylegesen fizetnek.

### Siker
- első fizető ügyfél
- működő pricing hypothesis
- bizonyított customer value
- működő beta $\to$ paid folyamat

## M3 — Repeatable Acquisition
**Cél:** Mérhető, részben automatizált ügyfélszerzés.

### Siker
- stabil leadforrás
- mérhető outbound funnel
- elfogadható CAC
- visszatérő ügyfelek
- csökkenő founder effort / customer

## M4 — $\ge 600k$ Ft MRR
Példa: $20 \times 30k \text{ Ft} = 600k \text{ Ft MRR}$

Fő metrikák:
- MRR
- Paid Customers
- ARPU
- Churn
- CAC
- Gross Margin

## M5 — Lifestyle Business
$$\ge 600k \text{ Ft MRR} + \le 10 \text{ founder óra/hét}$$

Fő metrikák:
- Founder Hours / Week
- Support Hours
- Profit
- Gross Margin
- Automation Rate
- Churn

---

# 6. DÖNTÉSI SZABÁLY

Minden milestone végén:

### 🟢 GO
A bizonyíték elég erős $\to$ tovább.

### 🟡 ITERATE
Van érték, de valami akadályozza a használatot / fizetést $\to$ csak ezt javítjuk.

### 🟠 PIVOT
A probléma / ICP / use case másnak bizonyul $\to$ módosítjuk az irányt.

### 🔴 STOP
Nincs elég bizonyíték valódi problémára, értékre vagy fizetési hajlandóságra.

> **Döntési elv:** Nem fejlesztési mennyiség alapján döntünk, hanem bizonyíték alapján.

---

# 7. AKTUÁLIS PRIORITÁS

## Egyetlen stratégiai kérdés

> **„Tudjuk-e bizonyítani, hogy az Optivoya egy valódi travel advisor számára lényegesen lerövidíti a teljes research → shortlist → client proposal workflow-t úgy, hogy az output minősége elég magas legyen a tényleges használathoz és fizetéshez?”**

### Minden jelenlegi munka ezt kell, hogy segítse:
1. valódi advisorok elérése
2. valódi ügyfélkérések begyűjtése
3. manuális baseline mérése
4. Optivoya workflow mérése
5. verification + editing idő mérése
6. output quality mérése
7. repeat usage mérése
8. willingness to pay tesztelése

**Minden más másodlagos.**

### Stratégiai emlékeztető
**B2B Travel Advisor = jelenlegi beachhead.**  
Nem ez az Optivoya teljes víziója.

A cél egy olyan Travel Decision Engine felépítése, amely később:
$$\text{B2B} \longrightarrow \text{B2B2C} \longrightarrow \text{B2C}$$
irányban is használható, és a flight + accommodation mellett az **experience/activity + itinerary + teljes end-to-end trip planning** problémát is kezeli.

---
id: optivoya-strategy
aliases:
  - optivoya-strategy
  - OPTIVOYA_STRATEGY
type: strategy
name: Optivoya Canonical Strategic Context & Product Direction
status: active

description: Az Optivoya kanonikus stratégiai forrása és termékiránya — North Star (≥600k MRR, ≤10h/hét), B2B advisor use case, H1-H6 validációs hipotézisek, M1-M5 roadmap és döntési szabályok.

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

# 🛬 Optivoya — DreamTripPlanner Strategic Blueprint

> **North Star:** Egy profitábilis, alacsony founder-inputtal működő lifestyle business.  
> **Első nagy cél:** $\ge 600k$ Ft MRR, $\le 10$ founder óra / hét.  
> **Jelenlegi fókusz:** B2B validation $\to$ első fizető ügyfél.

---

# 1. NORTH STAR

## Üzleti cél
Egy kis, profitábilis, nagyrészt automatizált travel-tech SaaS:
- $\ge 600k$ Ft MRR
- $\le 10$ founder óra / hét
- Magas profitmargin
- Alacsony support- és operációs igény
- Automatizálható acquisition és működés

## Nem cél
- VC / fundraising
- Nagy csapat
- Agresszív növekedés
- Felesleges feature-fejlesztés
- Founder-intenzív agency business

---

# 2. MIT ÉPÍTÜNK?

## Hosszú távú termék
Az Optivoya egy **travel decision-support engine**, amely az utazási igénytől a kész, személyre szabott utazási ajánlatig segít.

```text
UTAZÁSI IGÉNY
      ↓
Hova menjek?
      ↓
DESTINATION MATCHER
      ↓
Hogyan jutok oda?
      ↓
FLIGHT INTELLIGENCE
      ↓
Hol aludjak?
      ↓
ACCOMMODATION INTELLIGENCE
      ↓
Mit csináljak ott?
      ↓
EXPERIENCE / ACTIVITY INTELLIGENCE
      ↓
Hogyan álljon össze?
      ↓
ITINERARY ENGINE
      ↓
KÉSZ, SZEMÉLYRE SZABOTT UTAZÁS
```

## B2B elsődleges use case
A travel advisor munkájának felgyorsítása:
$$\text{ügyféligény} \longrightarrow \text{research} \longrightarrow \text{összehasonlítás} \longrightarrow \text{shortlist} \longrightarrow \text{ajánlat}$$

### Fő érték
**Time Saved / Client:**
$$\text{Time Saved} = T_{\text{manual}} - T_{\text{Optivoya}}$$

---

# 3. JELENLEGI BETA

## Cél
Nem teljes travel planner építése.  
A beta célja annak bizonyítása, hogy a jelenlegi motorokkal az advisor **valódi ügyfélkérést gyorsabban és jobb minőségben tud feldolgozni**.

## Beta MUST HAVE
* **Destination Matcher:** Desztinációk személyre szabott rangsorolása, releváns flight árak, fő döntési szempontok (klíma, költség, biztonság) kezelése.
* **Flight Intelligence:** Valós flight adatok, ár, menetidő, átszállás, időzítés, személyre szabott rangsor.
* **Accommodation Intelligence:** Releváns szállások, ár, értékelés, lokáció, személyre szabott rangsor.
* **Unified workflow:** A három motor ne különálló tool legyen:  
  $$\text{ügyféligény} \longrightarrow \text{destination} \longrightarrow \text{flight} \longrightarrow \text{accommodation} \longrightarrow \text{shortlist / proposal}$$

## Még NEM szükséges
* Teljes itinerary engine
* Komplex TSP / VRPTW útvonaloptimalizáció
* Teljes programtervezés
* Mobilapp
* Chatbot
* Enterprise funkciók
* Komplex CRM
* Egyéb „nice-to-have” feature

> **Vezérelv:** Új feature csak akkor kerülhet a beta scope-ba, ha valódi user bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.

---

# 4. MIT AKARUNK BIZONYÍTANI?

## H1 — A probléma létezik
A travel advisorok jelentős időt töltenek travel research-csel.  
*Bizonyíték:* Manual Research Time / Client, Research workflow, ismétlődő pain pointok.

## H2 — Az Optivoya értéket teremt
A rendszer csökkenti a researchhez szükséges időt.  
*Fő mérőszám:* $\text{Time Saved / Client}$ és $\text{Time Reduction \%}$.

## H3 — Használható
A user valódi ügyfélkérésen végig tud menni a workflow-n.  
*Mérőszám:* Activation, Successful Search, Error Rate, Time to First Value.

## H4 — Visszatérnek
A termék nem egyszeri érdekesség.  
*Mérőszám:* Weekly Usage, Repeat Usage.

## H5 — Fizetnek
Az érték elég nagy ahhoz, hogy pénzt adjanak érte.  
*Mérőszám:* Willingness to Pay, Paid Conversion, első tényleges fizetés.

## H6 — Megismételhető az acquisition
Nem csak személyes kapcsolatokból lehet ügyfelet szerezni.  
*Mérőszám:* Qualified Leads, Reply Rate, Beta Conversion, Paid Conversion, CAC, Founder Hours / Customer.

---

# 5. VALIDATION ROADMAP

## M1 — B2B Beta Validation
*Cél:* Bizonyítani, hogy az Optivoya valódi munkában használható és mérhető értéket teremt.  
*Sikerfeltételek:*
- 20–30 releváns lead elérése
- $\ge 10$ valódi beszélgetés
- $\ge 5$ aktív beta user
- $\ge 3$ ismételt használó
- Mérhető time saving
- Pozitív érték-visszajelzés
- $\ge 2$ komoly fizetési hajlandóság
- Lehetőleg $\ge 1$ fizető ügyfél  
$$\longrightarrow \textbf{Go / Iterate / Pivot / Stop}$$

## M2 — First Paid Customers
*Cél:* Bizonyítani, hogy az Optivoyáért ténylegesen fizetnek.  
*Sikerfeltételek:* Első fizető ügyfél, működő pricing hypothesis, bizonyított customer value, működő beta $\to$ paid folyamat.

## M3 — Repeatable Acquisition
*Cél:* Mérhető, részben automatizált ügyfélszerzés.  
*Sikerfeltételek:* Stabil leadforrás, mérhető outbound funnel, elfogadható CAC, visszatérő ügyfelek, csökkenő founder effort / customer.

## M4 — $\ge 600k$ Ft MRR
*Példa:* $20 \text{ ügyfél} \times 30k \text{ Ft} = 600k \text{ Ft MRR}$  
*Fő metrikák:* MRR, Paid Customers, ARPU, Churn, CAC, Gross Margin.

## M5 — Lifestyle Business
$$\ge 600k \text{ Ft MRR} + \le 10 \text{ founder óra/hét}$$
*Fő metrikák:* Founder Hours / Week, Support Hours, Profit, Gross Margin, Automation Rate, Churn.

---

# 6. DÖNTÉSI SZABÁLY

Minden milestone végén:

* 🟢 **GO:** A bizonyíték elég erős $\to$ tovább.
* 🟡 **ITERATE:** Van érték, de valami akadályozza a használatot / fizetést $\to$ csak ezt javítjuk.
* 🟠 **PIVOT:** A probléma / ICP / use case másnak bizonyul $\to$ módosítjuk az irányt.
* 🔴 **STOP:** Nincs elég bizonyíték valódi problémára, értékre vagy fizetési hajlandóságra.

> **Döntési alapelv:** Nem fejlesztési mennyiség alapján döntünk, hanem bizonyíték alapján.

---

# 7. AKTUÁLIS PRIORITÁS

## Egyetlen kérdés

> **„Hajlandó-e egy travel advisor pénzt fizetni azért, hogy az Optivoya segítségével lényegesen kevesebb idő alatt készítsen személyre szabott utazási ajánlatot?”**

Minden jelenlegi fejlesztésnek, outreachnek és beta tesztnek ezt kell segítenie megválaszolni.  
**Minden más másodlagos.**

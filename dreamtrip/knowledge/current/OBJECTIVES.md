---
id: current-objectives
aliases:
  - OBJECTIVES
type: strategic_concept
name: Objectives & Validation Roadmap
status: active

description: A jelenlegi fázis konkrét célkitűzései, a H1-H6 validációs hipotézisek, az M1-M5 roadmap és a döntési szabályok.

related:
  - "[[CURRENT_STATE]]"
  - "[[PRIORITIES]]"
  - "[[NORTH_STAR]]"
  - "[[optivoya-strategy]]"
---

# 🎯 Objectives: Hipotézisek & Validációs Roadmap

## 🧪 Mit Akarunk Bizonyítani? (H1–H6 Hipotézisek)

1. **H1 — A probléma létezik:** A travel advisorok valódi kérések feldolgozásakor jelentős időt töltenek research-csel, összehasonlítással és shortlist készítéssel.  
   *Mérőszámok:* Manual Time / Client ($T_{\text{manual}}$), workflow breakdown, ismétlődő pain pointok.
2. **H2 — Az Optivoya ténylegesen időt takarít meg:** A teljes workflow rövidebbé válik az Optivoya használatával.  
   *Fő mérőszámok:* Total Time Saved / Client ($T_{\text{manual}} - T_{\text{Optivoya}}$), Time Reduction %, Verification Time, Edit Time.
3. **H3 — Az output elég jó ahhoz, hogy használható legyen:** Az advisor nemcsak érdekesnek találja, hanem tényleges munkában használja az ajánlatot.  
   *Mérőszámok:* Shortlist Acceptance Rate, Advisor Rejection / Edit Rate, Factual Error Rate, Missing Option Rate, „Would you send this to your client?”.
4. **H4 — A workflow ismételhető:** Az advisor több valódi ügyfélkérésnél is használja a rendszert.  
   *Mérőszámok:* Repeat Usage, Requests / Advisor, Weekly Usage, Retention.
5. **H5 — A létrehozott értékért fizetnek:** Az időmegtakarítás elég nagy ahhoz, hogy ténylegesen fizessenek érte.  
   *Mérőszámok:* Paid Pilot, Willingness to Pay, Paid Conversion, ARPU, Churn.
6. **H6 — Az ügyfélszerzés megismételhető:** Nem csak személyes kapcsolatokból lehet ügyfelet szerezni.  
   *Mérőszámok:* Qualified Leads, Reply Rate, Demo / Pilot Conversion, Paid Conversion, CAC, Founder Hours / Customer.

> **Validációs Alapelv:** Nem a feature-ök számát vagy az AI sebességét tekintjük bizonyítéknak:  
> $$\text{Problem} \longrightarrow \text{Value} \longrightarrow \text{Quality} \longrightarrow \text{Repeat Usage} \longrightarrow \text{Payment} \longrightarrow \text{Repeatable Acquisition}$$

---

## 🗺️ Validációs Roadmap (M1–M5)

### 🏁 M1: B2B Beta Validation (Aktuális Mérföldkő)
* **Cél:** Bizonyítani, hogy az Optivoya valódi munkában használható és mérhető értéket teremt.
* **Sikerkritériumok:**
  * 20–30 releváns lead elérése
  * $\ge 10$ valódi beszélgetés
  * $\ge 5$ aktív beta user
  * $\ge 3$ ismételt használó
  * Mérhető time saving ($T_{\text{manual}} - T_{\text{Optivoya}}$)
  * Pozitív érték-visszajelzés
  * $\ge 2$ komoly fizetési hajlandóság
  * Lehetőleg $\ge 1$ fizető ügyfél  
  $$\longrightarrow \textbf{Go / Iterate / Pivot / Stop döntés}$$

### 🚀 M2: First Paid Customers
* **Cél:** Bizonyítani, hogy az Optivoyáért ténylegesen fizetnek.
* **Sikerkritériumok:** Első fizető ügyfél, működő pricing hypothesis, bizonyított customer value, működő beta $\to$ paid folyamat.

### 📈 M3: Repeatable Acquisition
* **Cél:** Mérhető, részben automatizált ügyfélszerzés.
* **Sikerkritériumok:** Stabil leadforrás, mérhető outbound funnel, elfogadható CAC, visszatérő ügyfelek, csökkenő founder effort / customer.

### 💰 M4: $\ge 600k$ Ft MRR
* **Példa:** $20 \times 30k \text{ Ft} = 600k \text{ Ft MRR}$
* **Fő metrikák:** MRR, Paid Customers, ARPU, Churn, CAC, Gross Margin.

### 🏖️ M5: Lifestyle Business
* **Feltétel:** $\ge 600k \text{ Ft MRR} + \le 10 \text{ founder óra/hét}$
* **Fő metrikák:** Founder Hours / Week, Support Hours, Profit, Gross Margin, Automation Rate, Churn.

---

## 🚦 Döntési Szabály (Minden Mérföldkő Végén)

* 🟢 **GO:** A bizonyíték elég erős $\to$ tovább a következő mérföldkőre.
* 🟡 **ITERATE:** Van érték, de valami akadályozza a használatot / fizetést $\to$ csak ezt a szűk keresztmetszetet javítjuk.
* 🟠 **PIVOT:** A probléma / ICP / use case másnak bizonyul $\to$ módosítjuk az irányt.
* 🔴 **STOP:** Nincs elég bizonyíték valódi problémára, értékre vagy fizetési hajlandóságra.

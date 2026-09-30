---
id: lead-nurturing-sequence
type: process
name: Lead Nurturing Sequence
status: active
description: The 6-step automated onboarding email sequence & downstream attribution quality tracking for lead magnet subscribers.
code:
  - landing_predikalo1/api/capture-lead.js
  - landing_predikalo1/scripts/send_lead_conversion_email.js
  - landing_predikalo1/email_templates/lead_routes_kalandkonyv.html
  - landing_predikalo1/email_templates/lead_conversion_reminder.html
related:
  - "[[growth-loop|Growth Loop]]"
  - "[[lead-magnet-intent|Lead Magnet Intent]]"
  - "[[email-templates|Email Templates]]"
---

# Process: Lead Nurturing Sequence (Lead Gondozási E-mail Automatizáció)

## 1. Sequence Roadmap (0–10 Napos Automata Folyamat)

A lead magnet ([[campaign-nagykevely|Kalandfüzet & GPX letöltés]]) nem önmagában végpont, hanem a bizalomépítés és a konverzió nyitánya.

```mermaid
sequenceDiagram
    autonumber
    actor User as Érdeklődő
    participant Sys as VitaSteps Automata
    
    User->>Sys: Lead Űrlap kitöltése (Név + Email)
    Sys-->>User: ✉️ 0. Nap: Azonnali hozzáférés (GPX csomag + Kalandfüzet PDF)
    Note over User,Sys: +1 Nap
    Sys-->>User: ✉️ 1. Nap: Hasznos tippek a túrához (felszerelés, parkolás, szint)
    Note over User,Sys: +3 Nap
    Sys-->>User: ✉️ 3. Nap: A VitaSteps küldetése (Miért nem verseny, miért élmény?)
    Note over User,Sys: +5 Nap
    Sys-->>User: ✉️ 5. Nap: Az elismerés filozófiája (A megérdemelt érem jelentősége)
    Note over User,Sys: +7 Nap
    Sys-->>User: ✉️ 7. Nap: Releváns kihívás ajánlása (Távválasztó segédlet)
    Note over User,Sys: +10 Nap
    Sys-->>User: ✉️ 10. Nap: Sürgősségi / limitált készlet emlékeztető
```

---

## 2. A Levelek Részletes Tartalma

| Időzítés | Tárgy & Cél | Tartalom fókusz |
| :--- | :--- | :--- |
| **0. Nap (Azonnal)** | *🗺️ Nagy-Kevély Túraútvonalak és Kalandfüzet* | Letöltési linkek átadása, azonnali pozitív élmény. |
| **1. Nap (+24h)** | *🎒 Így hozd ki a legtöbbet a hétvégi túrádból* | Hasznos útmutató: hol érdemes megállni, rejtett látnivalók, biztonsági tippek. |
| **3. Nap (+72h)** | *🌲 Miért hoztuk létre a VitaSteps-et?* | Hiteles márkatörténet, a saját tempójú felfedezés öröme, kiszakadás a hétköznapokból. |
| **5. Nap (+120h)** | *🏅 Egy emlék, ami kézzelfoghatóvá teszi a teljesítményedet* | Miért fontos megünnepelni a célba érést? A kézzel festett érem mint életre szóló emlék. |
| **7. Nap (+168h)** | *🧭 Családi séta vagy félmaraton? Találd meg a távodat!* | Távok bemutatása, kedvezményes páros/családi nevezési lehetőségek ismertetése. |
| **10. Nap (+240h)** | *⏳ Már csak kevés érem maradt a szériából!* | Készletkorlát (100 db) és nevezési határidő hangsúlyozása, direkt CTA a checkoutra. |

---

## 3. Downstream Minőség & Konverzió Mérés

A lead kampányok sikerességét nem csupán a feliratkozási költség (CPL) alapján ítéljük meg, hanem a teljes életciklus konverziós láncán:

$$\text{Lead Created} \longrightarrow \text{Magnet Download} \longrightarrow \text{Email Open} \longrightarrow \text{Email Click} \longrightarrow \text{Landing Visit} \longrightarrow \text{Checkout Start} \longrightarrow \text{Purchase}$$

### Mérési Dimenziók:
1. **First-Touch Attribution:** Melyik organikus poszt vagy hirdetés hozta be az érdeklődőt?
2. **Last-Touch Attribution:** Melyik e-mail vagy retargeting hirdetés váltotta ki a közvetlen fizetést?
3. **Engagement Score:** Letöltötte-e a Kalandfüzetet? Megnyitotta-e a leveleket?

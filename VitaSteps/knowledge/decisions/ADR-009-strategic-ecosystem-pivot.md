---
id: ADR-009-strategic-ecosystem-pivot
type: decision
name: ADR-009 Strategic Ecosystem Pivot
status: active
date: "2026-09-30"
description: Architectural and business decision to transition VitaSteps from a single-product physical challenge webshop into a multi-entry movement, discovery, and achievement ecosystem.
related:
  - "[[strategic-positioning|Strategic Positioning]]"
  - "[[growth-loop|Growth Loop]]"
  - "[[customer-funnel|Customer Funnel]]"
---

# ADR-009: Strategic Ecosystem Pivot (Stratégiai Ökoszisztéma Átállás)

## 1. Context (Kontextus)

A VitaSteps kezdeti szakasza kizárólag a **fizikai túrakihívások és érmek** értékesítésére épült (`Meta Ads -> Landing Page -> Purchase -> Complete -> Medal -> End`).
Bár ez a modell működőképes és nyereséges volt, stratégiailag túl szűknek bizonyult:
* Kizárta azokat, akik nem tudtak a helyszínre utazni, nem akartak azonnal fizetni, vagy inkább városi sétát/futást kerestek.
* A vásárlás és éremkézbesítés után a kapcsolat gyakran megszakadt.
* A növekedés túlzott mértékben függött a fizetett hirdetésektől (Meta Ads).

---

## 2. Decision (Döntés)

Átállítjuk a VitaSteps modellt egy **mozgás-, felfedezés- és teljesítésközpontú élményrendszerré** (*„MOZOGJ. FEDEZZ FEL. TELJESÍTS.”*), amely 5 integrált belépési pillérre épül:
1. **Valós túrakihívások** ([[verified-challenge|Verified Challenge]]): Nagy-Kevély, Prédikálószék és jövőbeli csúcsok prémium érmekkel.
2. **Virtuális kihívások** ([[virtual-challenge|Virtual Challenge]]): Helyszínfüggetlen kilométer-kihívások jelvényekkel és opcionális éremmel.
3. **Hosszú Lépések** ([[hosszu-lepesek|Hosszú Lépések]]): Önvezetett tematikus városi audioséták.
4. **Ingyenes tartalmak**: Kalandfüzetek, GPX útvonalcsomagok, túratippek.
5. **Közösség & UGC**: Teljesítési élmények, közösségi motiváció, ajánlási motor.

A növekedési modellt egy összekapcsolt többcsatornás hurokká ([[growth-loop|Growth Loop]]) alakítjuk:
$$\text{Organic} + \text{Community} + \text{Lead Magnet} + \text{Email Automation} + \text{Meta Ads} + \text{UGC} + \text{Referrals}$$

---

## 3. Implementation Roadmap & Boundaries

### 🟢 1. Fázis: Alapok & Növekedési Motorok (Priority 0–1)
* Stratégiai pozicionálás és dokumentáció rögzítése.
* Organikus tartalomgyártási rendszer kialakítása ([[organic-content-pillars|Organic Content Pillars]], [[organic-content-workflow|Organic Content Workflow]]).
* Közösségi jelenlét 10 Facebook-csoportban ([[community-engagement-protocol|Community Engagement Protocol]]).
* Lead nurturing e-mail automatizáció ([[lead-nurturing-sequence|Lead Nurturing Sequence]]).

### 🟡 2. Fázis: Növekedési Hurok & UGC (Priority 1–2)
* UGC gyűjtés és beépítése a marketingbe ([[ugc-referral-engine|UGC & Referral Engine]]).
* Teljesítés $\rightarrow$ Következő kihívás ajánlási motor erősítése.

### 🟠 3. Fázis: Termékfejlesztési MVP-k (Priority 2–3)
* Virtuális kihívás MVP (manuális adatbevitel, progress bar, jelvények).
* Hosszú Lépések MVP (1 város, 1 séta, audio lejátszó).

---

## 4. Explicit Anti-Scope (Amit MOST NEM csinálunk)
* **NEM** építünk saját natív mobilalkalmazást.
* **NEM** kódolunk automatikus Strava/Garmin integrációkat a manuális MVP sikeres validációja előtt.
* **NEM** készítünk napi szintű tartalmat (heti 1 órás batch gyártás érvényes).
* **NEM** végzünk tömeges hideg DM üzenetküldést.

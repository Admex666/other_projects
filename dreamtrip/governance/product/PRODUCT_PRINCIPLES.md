---
id: product-principles
aliases:
  - PRODUCT_PRINCIPLES
type: governance
name: Product Principles & Decision Invariants
status: active

description: A termékfejlesztést és funkcionalitást vezérlő kötelező szabályok és döntési invariánsok (Total Time Saved, Human-in-the-Loop, Scope Rule, Evidence over Volume).

related:
  - "[[THESIS]]"
  - "[[VALUE_PROPOSITION]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[honest-scraping-policy]]"
  - "[[optivoya-strategy]]"
---

# 📦 Product Governance: Product Principles

1. **Fő Érték és KPI: Total Time Saved / Client:**
   * Nem az API válaszidejét mérjük, hanem a **teljes munkafolyamat során megtakarított időt**:
     $$T_{\text{manual}} = \text{teljes manuális research} + \text{összehasonlítás} + \text{shortlist készítés}$$
     $$T_{\text{Optivoya}} = \text{Optivoya futtatás} + \text{verification} + \text{editing} + \text{finalization}$$
     $$\text{Total Time Saved} = T_{\text{manual}} - T_{\text{Optivoya}}$$
   * A valódi érték az, hogy mennyi idő alatt jut el az advisor egy ügyfélnek kiküldhető, megbízható ajánlatig (`Time to Client-Ready Proposal`).

2. **Human-in-the-Loop Döntéstámogatás (Advisor Enablement Invariant):**
   * Az Optivoya célja nem az emberi travel advisor lecserélése, hanem annak elérése, hogy ugyanazt a minőségi munkát lényegesen gyorsabban és jobb döntéstámogatással tudja elvégezni.
   * A munkafolyamat kötelező lépése:  
     $$\text{Optivoya jelöltek} \longrightarrow \text{Rangsor \& Trade-offs} \longrightarrow \text{Advisor ellenőrzés/szerkesztés} \longrightarrow \text{Ügyfélajánlat}$$

3. **Szigorú Beta Scope Szabály (Anti-Feature-Bloat Invariant):**
   * Új feature csak akkor kerülhet a beta scope-ba, ha valódi user bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.
   * A bétában kifejezetten NEM szükségesek: teljes itinerary engine, komplex TSP/VRPTW útvonaloptimalizáció, teljes programtervezés, mobilapp, chatbot, enterprise funkciók, komplex CRM.

4. **Bizonyíték-Alapú Döntéshozatal (Evidence over Volume):**
   * Nem fejlesztési mennyiség alapján döntünk, hanem bizonyíték alapján:
     $$\text{Problem} \longrightarrow \text{Value} \longrightarrow \text{Quality} \longrightarrow \text{Repeat Usage} \longrightarrow \text{Payment} \longrightarrow \text{Repeatable Acquisition}$$
   * Minden mérföldkő végén a döntési kapu:
     * 🟢 **GO:** Erős bizonyíték $\to$ tovább a következő mérföldkőre.
     * 🟡 **ITERATE:** Van érték, de akadály merült fel $\to$ kizárólag a szűk keresztmetszet javítása.
     * 🟠 **PIVOT:** Más az ICP vagy use case $\to$ irány módosítása.
     * 🔴 **STOP:** Nincs bizonyíték valós problémára vagy fizetési hajlandóságra.

5. **Döntések az Adathalmok Helyett (Decisions over Data Dumps):**
   * A rendszer nem egy ömlesztett aggregátor (nem sima flight+hotel kereső). Mindig a preferenciák alapján legjobban rangsorolt opciókat emeljük ki világos indoklással és kompromisszumokkal (trade-offs).

6. **Őszinte és Valós Adatok Elve (Honest Data Invariant):**
   * Tilos mesterséges vagy hallucinált árakat/járatokat megjeleníteni. Ha egy adatbázis vagy API nem érhető el, a rendszer transzparens hibaüzenetet ad a felhasználónak.

7. **Végponttól Végpontig Tartó Integritás (Unified End-to-End Coherence):**
   * Az utazás minden eleme (célállomás, járat, szállás, költségek) egyetlen szerves egészet alkot (`UnifiedTrip`). Egy elem változása automatikusan és konzisztensen frissíti a függő állapotokat.

---
id: product-principles
aliases:
  - PRODUCT_PRINCIPLES
type: governance
name: Product Principles & Decision Invariants
status: active

description: A termékfejlesztést és funkcionalitást vezérlő kötelező szabályok és döntési invariánsok (Time Saved, Evidence-based Decision, Scope Rule).

related:
  - "[[THESIS]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[honest-scraping-policy]]"
  - "[[optivoya-strategy]]"
---

# 📦 Product Governance: Product Principles

1. **Elsődleges Érték: Időmegtakarítás Ügyfelenként (Time Saved / Client):**
   * Minden termékfejlesztésnek és funkciónak csökkentenie kell az utazásszervező által ráfordított kutatási és ajánlatkészítési időt:
     $$\text{Time Saved} = T_{\text{manual}} - T_{\text{Optivoya}}$$
2. **Szigorú Béta Scope Szabály (Anti-Feature-Bloat Invariant):**
   * Új feature csak akkor kerülhet a béta scope-ba, ha valódi felhasználó bizonyíthatóan emiatt nem tud értéket kapni vagy fizetni.
3. **Bizonyíték-Alapú Döntéshozatal (Evidence over Volume):**
   * Nem fejlesztési mennyiség alapján döntünk, hanem bizonyíték alapján. Minden mérföldkő végén a döntési kapu:
     * 🟢 **GO:** Erős bizonyíték $\to$ tovább.
     * 🟡 **ITERATE:** Van érték, de akadály merült fel $\to$ csak az akadály javítása.
     * 🟠 **PIVOT:** Más az ICP vagy use case $\to$ irány módosítása.
     * 🔴 **STOP:** Nincs bizonyíték valós problémára vagy fizetési hajlandóságra.
4. **Döntések az Adathalmok Helyett (Decisions over Data Dumps):**
   * A felhasználót nem árasztjuk el száz megválogatatlan opcióval. Mindig a preferenciák alapján legjobban rangsorolt opciókat emeljük ki világos indoklással.
5. **Őszinte és Valós Adatok Elve (Honest Data Invariant):**
   * Tilos mesterséges vagy hallucinált árakat/járatokat megjeleníteni. Ha egy adatbázis vagy API nem érhető el, a rendszer transzparens hibaüzenetet ad a felhasználónak.
6. **Végponttól Végpontig Tartó Integritás (Unified End-to-End Coherence):**
   * Az utazás minden eleme (célállomás, járat, szállás, költségek) egyetlen szerves egészet alkot. Egy elem változása automatikusan és konzisztensen frissíti a függő állapotokat.

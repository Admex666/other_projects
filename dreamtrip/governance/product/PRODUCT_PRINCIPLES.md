---
id: product-principles
aliases:
  - PRODUCT_PRINCIPLES
type: governance
name: Product Principles & Decision Invariants
status: active

description: A termékfejlesztést és funkcionalitást vezérlő kötelező szabályok és alapelvek.

related:
  - "[[THESIS]]"
  - "[[DEFINITION_OF_DONE]]"
  - "[[honest-scraping-policy]]"
---

# 📦 Product Governance: Product Principles

1. **Döntések az Adathalmok Helyett (Decisions over Data Dumps):**
   * A felhasználót nem árasztjuk el száz megválogatatlan opcióval. Mindig a preferenciák alapján legjobban rangsorolt opciókat emeljük ki világos indoklással.
2. **Őszinte és Valós Adatok Elve (Honest Data Invariant):**
   * Tilos mesterséges vagy hallucinált árakat/járatokat megjeleníteni. Ha egy adatbázis vagy API nem érhető el, a rendszer transzparens hibaüzenetet ad a felhasználónak.
3. **Funkcióegyszerűsítés (Complexity Limit):**
   * Ne adjunk hozzá új konfigurációs gombot vagy mezőt, hacsak nem teremt bizonyított és egyértelmű értéket a döntéshozatalban.
4. **Végponttól Végpontig Tartó Integritás (End-to-End Coherence):**
   * Az utazás minden eleme (célállomás, járat, szállás, költségek) egyetlen szerves egészet alkot. Egy elem változása automatikusan és konzisztensen frissíti a függő állapotokat.

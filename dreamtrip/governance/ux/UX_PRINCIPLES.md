---
id: ux-principles
aliases:
  - UX_PRINCIPLES
type: governance
name: UX Principles
status: active

description: A felhasználói élmény és interakciótervezés kötelező alapelvei.

related:
  - "[[UX_PATTERNS]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[PRODUCT_PRINCIPLES]]"
---

# 🖱️ UX Governance: UX Principles

1. **Kognitív Terhelés Minimalizálása:**
   * A felhasználót lépésről lépésre vezetjük (Progressive Disclosure). Egyszerre csak egy döntési szint aktív.
2. **Elsődleges Akció (Primary CTA) Nyilvánvalósága:**
   * Minden nézeten pontosan egy domináns, kiemelt művelet gomb létezik (pl. "Járatok keresése →", "Szállások kiválasztása →").
3. **Azonnali Visszajelzés & Átlátható Állapot:**
   * Minden aszinkron művelet (keresés, rangsorolás, mentés) egyértelmű szöveges állapotvisszajelzést vagy progress indikátort kap.
4. **Visszalépés és Módosítás Szabadsága:**
   * A felhasználó bármikor visszatérhet az előző döntési lépésekhez az addig kiválasztott adatok elvesztése nélkül.
5. **Közérthető Nyelvezet és Tudományos Zsargon Mellőzése a Felületen (Plain Language Invariant):**
   * A felhasználói felületen, gombokon, címeken és kártyákon tilos tudományos rövidítéseket és szakzsargont használni (pl. AHP, PROMETHEE II, MCDM, Outranking Flow).
   * A gombok és magyarázatok szövege legyen olyan egyszerű és természetes, hogy **egy 12 éves is azonnal megértse** (pl. *„1. Saját szempontok és prioritások beállítása →”* ahelyett, hogy *„Döntési profil (AHP + PROMETHEE)”*).
   * A matematikai apparátus kizárólag a szakértői mélyfúrásnál vagy szolid információs buborékban `[ℹ️]` jelenhet meg a hitelesség igazolására.

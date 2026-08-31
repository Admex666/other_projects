---
id: code-quality
aliases:
  - CODE_QUALITY
type: governance
name: Code Quality & Refactoring Standards
status: active

description: Kódminőségi és modulméretezési szabályok.

related:
  - "[[ENGINEERING_PRINCIPLES]]"
  - "[[TESTING]]"
---

# 🧹 Engineering Governance: Code Quality

1. **Egyértelmű Modulfunkció (Single Coherent Responsibility):**
   * Egy modul ne keverjen adatbáziskezelést, webes HTML generálást és matematikai optimalizációt.
2. **Kódduplikáció Tilalma (DRY):**
   * A repülőjegy- és szálláskombinációs számítások egyetlen közös szervizben (`app/services/`) élnek.
3. **Karbantartható Refaktorálás:**
   * Ha egy funkció kiegészítése felborítaná a meglévő modúlhatárokat, a határt tisztán refaktorálni kell ahelyett, hogy egy meglévő óriásfájl végére ragasztunk toldozott kódot.
4. **Biztonság és Időtúllépések:**
   * Minden külső HTTP hívásnak kötelező `timeout` paramétert kapnia (alapértelmezetten $\le 15$ mp).

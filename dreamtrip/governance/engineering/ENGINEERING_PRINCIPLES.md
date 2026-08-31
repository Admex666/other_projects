---
id: engineering-principles
aliases:
  - ENGINEERING_PRINCIPLES
type: governance
name: Engineering Principles
status: active

description: A szoftverfejlesztési minőség és karbantarthatóság alapelvei.

related:
  - "[[ARCHITECTURE_RULES]]"
  - "[[CODE_QUALITY]]"
  - "[[TESTING]]"
---

# 🛠️ Engineering Governance: Engineering Principles

1. **Separation of Concerns (Felelősségi körök szétválasztása):**
   * A frontend / UI réteg kizárólag a megjelenítésért és az interakcióért felel.
   * Az aggregáció, pontszámítás és AHP/PROMETHEE algoritmusok a Python backend és domain modulokban élnek.
2. **Kanonikus Forrás Elsőbbsége:**
   * Egyetlen adatot sem tárolunk párhuzamosan több helyen.
3. **Vektorizáció és Aszinkronitás a Lassú Ciklusok Helyett:**
   * Nagyméretű kombinációknál (pl. több ezer járatpár) tilos lassú Python for-ciklusokat futtatni. Vektorizált NumPy műveleteket vagy szálankénti párhuzamosítást (`ThreadPoolExecutor`) alkalmazunk.
4. **Hibakezelés és Fail-Fast:**
   * Külső API hiba esetén világos státuszkódot és emberileg olvasható hibaüzenetet küldünk, elkerülve a néma összeomlásokat.

---
id: adr-010-dual-auth-and-app-switcher
aliases:
  - ADR-010
type: decision
name: Kettős Bejelentkezés, Alkalmazásválasztó Hub és Szerepkör-alapú Hozzáféréskezelés
status: accepted

governed_by:
  - "[[ARCHITECTURE_RULES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[PRODUCT_PRINCIPLES]]"
  - "[[DEFINITION_OF_DONE]]"

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[master-planner-blueprint]]"
  - "[[app-hub-and-workspace-switcher]]"
  - "[[fastapi-backend]]"
  - "[[ADR-007-fastapi-router-modularization]]"
---

# 📜 ADR-010: Kettős Bejelentkezés, Alkalmazásválasztó Hub és Szerepkör-alapú Hozzáféréskezelés

## 📌 Kontextus (Context)
Az Optivoya termékportfóliója két alapvető felületből áll:
1. **Master Travel Planner:** Egyéni és B2C utazástervező varázsló (célállomás keresés, járatok, szállások, költségek).
2. **Advisor Workspace:** Professzionális B2B tanácsadói munkaterület (ügyfél CRM, brief-intelligencia, 3 döntési archetípus, tételes ajánlatgenerálás).

Korábban a felhasználók bejelentkezés után egységesen a `/planner` felületre érkeztek, és nem volt strukturált szerepkör-megkülönböztetés az egyéni utazók és a B2B tanácsadók között, sem pedig gyorsváltó mechanizmus a két munkaterület között.

---

## 🎯 Döntés (Decision)

1. **Szerepkör-alapú Jogosultságmodell (`beta_users.role`):**
   * **`advisor` / `admin`:** Teljes hozzáféréssel rendelkezik mind a Master Plannerhez (`/planner`), mind az Advisor Workspace-hez (`/advisor`).
   * **`planner` (standard felhasználó):** Kizárólag a Master Plannerhez (`/planner`) fér hozzá.

2. **Intelligens Bejelentkezési Útválasztás (`/login`):**
   * Ha a bejelentkező felhasználó **advisor / admin:** Automatikusan az új **Alkalmazásválasztó Hubra (`/hub`)** kerül, ahol kiválaszthatja a kívánt munkaterületet.
   * Ha a felhasználó **NEM advisor:** Zökkenőmentesen, azonnal a **Master Planner (`/planner`)** felületre irányítja a rendszer.

3. **Alkalmazásválasztó Portál (`/hub`):**
   * Tiszta, prémium kártyás felület a Master Planner és az Advisor Workspace közötti választáshoz.
   * A felület mentes a tudományos és algoritmus-zsargontól a `[[ANTI_AI_SLOP_POLICY]]` és `[[UX_PRINCIPLES]]` szabályai szerint.

4. **App Switcher & Átjárhatóság:**
   * Mindkét felület (Master Planner navbar és Advisor Workspace sidebar) közvetlen gyorsváltó gombokkal rendelkezik a másik alkalmazásba és a Hubba az advisor felhasználók számára.

5. **Adminisztrációs Szerepkör-kezelés (`/admin`):**
   * Az admin felületen új fiók létrehozásakor beállítható a jogosultság (`B2B Tanácsadó` vs `Standard Felhasználó`).
   * A felhasználói listában látható a szerepkör jelvény, és inline API végponton (`POST /api/admin/users/{user_id}/role`) keresztül azonnal módosítható a jogosultság.

6. **Útvonal-védelem:**
   * A `/advisor` és `/hub` végpontok szerveroldali szerepkör-ellenőrzéssel védettek, jogosulatlan próbálkozás esetén biztonságos átirányítással.

---

## ⚖️ Következmények & Előnyök (Consequences & Benefits)
* **Tiszta felhasználói szegregáció:** A végfelhasználók nem látnak felesleges B2B kezelőszerveket, míg a tanácsadók teljes funkcionalitást kapnak.
* **Gyors navigáció:** Az advisorok egyetlen kattintással mozoghatnak az egyéni utazástervező és az ügynökségi pult között.
* **Skálázható jogosultságkezelés:** Mind Supabase Cloud PostgreSQL, mind lokális SQLite környezetben egységesen kezelt szerepkörök.

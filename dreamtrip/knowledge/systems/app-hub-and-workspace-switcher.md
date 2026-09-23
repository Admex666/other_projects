---
id: app-hub-and-workspace-switcher
aliases:
  - app-hub
  - workspace-switcher
type: system
name: Alkalmazásválasztó Hub és Munkaterület-Gyorsváltó Rendszer
status: active

governed_by:
  - "[[ARCHITECTURE_RULES]]"
  - "[[UX_PRINCIPLES]]"
  - "[[DESIGN_SYSTEM]]"
  - "[[ANTI_AI_SLOP_POLICY]]"

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[master-planner-blueprint]]"
  - "[[fastapi-backend]]"
  - "[[ADR-010-dual-auth-and-app-switcher]]"
---

# 🏛️ Alkalmazásválasztó Hub és Munkaterület-Gyorsváltó Rendszer

## 📌 Áttekintés
Az Alkalmazásválasztó Hub és a Munkaterület-Gyorsváltó az Optivoya termékcsalád két központi alkalmazása — a **Master Travel Planner** és a **B2B Advisor Workspace** — közötti navigációt és jogosultság-alapú elválasztást biztosítja.

---

## 🏗️ Architektúra és Működés

```text
Felhasználó Bejelentkezés (/login)
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[Advisor / Admin]   [Planner-Only]
    │                   │
    ▼                   ▼
/hub (Alkalmazásválasztó)  /planner (Master Planner)
 ├─ Master Planner (→ /planner)
 └─ Advisor Workspace (→ /advisor)
```

### 1. Alkalmazásválasztó Portál (`/hub`)
* **Sablon:** `templates/hub.html`
* **Funkció:** Kártyás belépési pont az advisor fiókok számára.
* **Védelem:** Nem bejelentkezett felhasználók a `/` login oldalra, nem-advisor felhasználók közvetlenül a `/planner`-re irányítódnak.
* **Nyelvi követelmény (`[[ANTI_AI_SLOP_POLICY]]`):** A kártyák és feliratok mentesek a belső algoritmusnevektől (nincs PROMETHEE, AHP a UI szövegekben), helyette az emberi és funkcionális értékeket kommunikálják.

### 2. Kétirányú App Switcher
* **Master Planner felületén (`templates/base.html`):**
  * Ha `is_advisor == True`: felső navigációs gomb és profilmenü opció az Advisor Workspace és a Hub eléréséhez.
* **Advisor Workspace felületén (`templates/advisor/advisor_workspace.html`):**
  * Bal oldali oldalsáv és felső fejrész gyorsváltó gombokkal a Master Plannerbe és a Hubba.

### 3. Jogosultságok és Szerepkörök
* **Backend:** `app/core/auth.py` (`get_user_role`, `is_advisor_user`)
* **Adatbázis:** `beta_users.role` oszlop (`advisor`, `planner`, `admin`) Supabase Cloud PostgreSQL és SQLite támogatással.
* **Admin felület:** `/admin` dashboard felhasználó-létrehozási és inline szerepkör-módosítási funkciókkal.

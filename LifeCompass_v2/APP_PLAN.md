# APP_PLAN.md
# 🧭 LifeCompass v2 – Foundations

---

# 1️⃣ PROBLÉMA DEFINÍCIÓ

A LifeCompass v2 egy **személyes élet-operációs rendszer**, amely segít az embereknek összekötni a hosszú távú céljaikat a napi cselekvéseikkel.

A célcsoport olyan ambiciózus emberek, akik:

* több projekten dolgoznak egyszerre
* pénzügyi és személyes céljaik vannak
* szeretnék tudatosan irányítani az életüket
* de a jelenlegi eszközeik szét vannak szórva

Ma az emberek külön appokban kezelik:
* feladataikat (Todoist, Things)
* jegyzeteiket (Notion, Obsidian)
* pénzügyeiket
* szokásaikat
* céljaikat

Ez **kontextusfragmentációt** okoz.

A LifeCompass ezt oldja meg azzal, hogy egy rendszerbe kapcsolja:
* célok, projektek, feladatok, szokások, pénzügyi haladás.

Így a felhasználó mindig látja:
> Amit ma csinálok, az hogyan visz közelebb az életcéljaimhoz.

A LifeCompass nem egy újabb productivity app. Ez egy **direction system**.

---

# 2️⃣ SCOPE LOCK (mit NEM csinál az app?)

### ❌ Nem lesz benne az első verzióban:
* **Jegyzet rendszer** (nincs rich text, nincs dokumentum kezelés)
* **Komplex projektmenedzsment** (nincs kanban, nincs team collaboration)
* **Teljes pénzügyi tracking** (nincs bank API, nincs transaction tracking)
* **Komplex habit system** (nincs statisztikai dashboard, nincs gamification)
* **AI** (nincs AI assistant az első verzióban)

---

### ✔ Az MVP fókusza
Egyetlen kérdés:
> Mit csináljak ma, ami közelebb visz az életcéljaimhoz?

---

# 3️⃣ DOMAIN MODELL

Minden tábla tartalmaz `updated_at` és `is_deleted` mezőket.

## Fő entitások

### 👤 User
attribútumok
```
id
name
pin_code (hashed)
is_biometric_enabled (boolean)
created_at
updated_at
```

---

### 🎯 Goal
A célok hierarchikusak (pl. 5 éves → 1 éves → havi). A haladás manuálisan frissítendő.

attribútumok
```
id
parent_goal_id (opcionális)
title
type (financial / career / mental / physical / spiritual / time)
horizon (vision (5y+) / strategy (1-3y) / objective (1y) / quarter / month)
target_value
target_type
target_date
progress (manually updated %)
last_reviewed_at
updated_at
is_deleted
```

**Színkódolás (Goal Types):**
* Financial: **Emerald**
* Career/Work: **Indigo**
* Mental/Spiritual: **Amber**
* Physical/Body: **Crimson**
* Social/Relationship: **Rose**

---

### 🚀 Project
attribútumok: id, title, goal_id, status, priority, created_at, updated_at, is_deleted.

---

### ✅ Task
attribútumok: id, title, project_id, due_date, status, priority, updated_at, is_deleted.

---

### 🔁 Habit
Ismétlődő viselkedés. Visszamenőlegesen is vezethető.
attribútumok: id, title, goal_id, frequency, streak, updated_at, is_deleted.

---

### 🧠 Daily Intention
A nap fókusza.
attribútumok: id, date, content, is_completed, updated_at.

---

# 4️⃣ USE CASE → FLOW DESIGN

## Use Case 1 — Biometric/PIN Login
trigger: `User opens app`
flow: `System checks for Biometric auth -> fallback to PIN code`

## Use Case 2 — Goal Review & Hierarchy
trigger: `Weekly notification OR Manual trigger`
flow: `User reviews project/habit performance in hierarchy -> updates goal progress %`

## Use Case 3 — Data Backup
trigger: `User opens settings -> export data`
flow: `Generate encrypted JSON/CSV containing all app data -> Share/Save to cloud`

---

# 5️⃣ ARCHITEKTÚRA DÖNTÉSEK

## 5.1 Platform & Design
* **Flutter** (iOS + Android)
* **Font**: Inter (Modern, Clean)
* **Layout**: Sleek Dark Mode (Glassmorphism elements)
* **Navigation**: `go_router`

## 5.2 State management
* **Riverpod** (Scalable, DI friendly)

## 5.3 Storage & Backup
* **Storage**: Local-first (Drift / SQLite)
* **Backup**: Manual Export/Import to JSON/CSV (Settings)

## 5.4 Security
* **Access**: Biometric Authentication + Secure PIN Fallback
* **Storage**: `flutter_secure_storage` a PIN-nek és titkosítási kulcsoknak

## 5.5 Notifications
* **System**: Local Notifications
* **Settings**: Állítható reggeli (Intention), esti (Habit check) és vasárnapi (Goal review) emlékeztetők.

## 5.6 i18n
* English code, comments, database.
* Hungarian primary UI, fallback English.

---

# 6️⃣ UI STRUKTÚRA

## Navigation (5 tab):
1. **Today**: Intention, Due tasks, Habit check.
2. **Goals**: Hierarchical list (Horizon based), Manual progress updates.
3. **Projects**: Active initiatives.
4. **Habits**: Retrospective calendar/checklist.
5. **Settings**: Biometrics, Notifications, Backup, Profile.

---

# 7️⃣ ITERÁCIÓS STRATÉGIA

## Iteration 1: Foundations
* Flutter setup + Font (Inter) + Base Theme
* Secure Storage + PIN/Biometric setup
* Localization (i18n)

## Iteration 2: Core Data
* Drift DB setup with sync/soft-delete fields
* Hierarchical Goal & Project CRUD (including horizon logic)

## Iteration 3: Daily Systems
* Daily Intention logic
* Habit system (retrospective + streak calculation)

## Iteration 4: Support Systems
* Local Notifications (Scheduled reminders)
* Data Export/Import (JSON Backup)

## Iteration 5: Polish
* Premium UI refinements (Goal color coding, Animations)
* Final testing & APK Update bot setup

---

# 🧭 Strategic Advice
Az MVP legyen **"Daily Direction App"**. Angol alapú kódolás, magyar felhasználóknak, maximális adatbiztonsággal (Local + Encrypted PIN).
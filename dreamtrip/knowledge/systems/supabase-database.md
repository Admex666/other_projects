---
id: supabase-database
aliases:
  - supabase-database
  - SUPABASE_DATABASE
type: system
name: Supabase Cloud PostgreSQL & PostgREST Database
status: active

description: Az Optivoya éles felhős adatbázis- és telemetria-rétege (PostgreSQL & PostgREST API). Kezeli a béta felhasználókat, hitelesítést, munkameneteket és a használati analitikát.

related:
  - "[[fastapi-backend]]"
  - "[[PROJECT_GRAPH]]"
  - "[[optivoya-strategy]]"
  - "[[master-planner-wizard]]"

used_by:
  - "[[fastapi-backend]]"
  - "[[master-planner-wizard]]"
---

# 🗄️ Supabase Cloud PostgreSQL & PostgREST Database

Az Optivoya kanonikus perzisztens adatbázisa és felhasználói hitelesítési rétege a **Supabase Cloud PostgreSQL**.

---

## 🎯 Felelősségi Kör (Responsibilities)
1. **Béta Tanácsadók & Felhasználókezelés (`public.beta_users`):**
   * Felhasználónév, jelszóhash, cég/iroda neve, e-mail cím, jogosultsági kör és utolsó aktivitás.
2. **Telemetria & Használati Analitika (`public.telemetry_events`):**
   * Keresési lekérdezések paraméterei (JSONB), válaszidők ($\text{duration\_ms}$), modulhasználat, sikerességi állapotok és hibák.
3. **Munkamenetek (`public.user_sessions`):**
   * Béta felhasználók munkamenet-követése és visszatérési gyakorisága (Repeat Usage — H4 Hipotézis).

---

## 🔌 Kapcsolódás és Kliens
* **Kliens modul:** [`app/core/supabase.py`](file:///e:/Data/other_projects/dreamtrip/app/core/supabase.py)
* **Környezeti változók:** `SUPABASE_URL` és `SUPABASE_KEY` / `SUPABASE_SERVICE_ROLE_KEY`.
* **API:** PostgREST REST API és hivatalos `supabase-py` SDK.
* **Fallback:** Helyi fejlesztéskor offline SQLite fallback (`data/analytics.db`).

---

## 📊 Kapcsolódó Sémák
* [`supabase_schema.sql`](file:///e:/Data/other_projects/dreamtrip/supabase_schema.sql) — 1-kattintásos PostgreSQL DDL séma.
* [`scripts/migrate_sqlite_to_supabase.py`](file:///e:/Data/other_projects/dreamtrip/scripts/migrate_sqlite_to_supabase.py) — 1-kattintásos SQLite $\to$ Supabase szinkronizáló eszköz.

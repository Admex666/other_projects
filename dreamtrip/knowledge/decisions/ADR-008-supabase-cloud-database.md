---
id: ADR-008-supabase-cloud-database
aliases:
  - ADR-008-supabase-cloud-database
  - ADR-008
type: decision
name: ADR-008 — Supabase Cloud PostgreSQL & Telemetry Adatbázis Bevezetése
status: active

description: A helyi SQLite cseréje Supabase felhős PostgreSQL és PostgREST architektúrára a B2B béta felhasználók, hitelesítés és használati telemetria perzisztens tárolásához.

related:
  - "[[supabase-database]]"
  - "[[fastapi-backend]]"
  - "[[optivoya-strategy]]"
  - "[[master-planner-wizard]]"

used_by:
  - "[[fastapi-backend]]"
---

# 📜 ADR-008: Supabase Cloud PostgreSQL & Telemetry Adatbázis Bevezetése

## 1. Context (Kontextus)
Az Optivoya B2B validációs fázisában elengedhetetlen, hogy a béta tanácsadók (`beta_users`), keresési eseményeik (`telemetry_events`) és munkameneteik (`user_sessions`) egy megbízható, felhős, perzisztens adatbázisban legyenek tárolva, amely Vercel Serverless környezetben is zökkenőmentesen elérhető és nem veszíti el az adatokat az instance-ok újraindulásakor.

## 2. Decision (Döntés)
A helyi SQLite fájl helyett a **Supabase Cloud PostgreSQL** szolgáltatást választottuk kanonikus adattárolóként a hivatalos PostgREST REST API és `supabase-py` SDK segítségével:
* **`public.beta_users`**: Tanácsadói fiókok és hitelesítés.
* **`public.telemetry_events`**: Részletes keresési paraméterek (JSONB), latenciák, modulinformációk és hibák.
* **`public.user_sessions`**: Munkamenetek és visszatérési gyakoriság (Repeat Usage).
* **Offline Fallback**: Offline fejlesztéskor automatikus SQLite fallback.

## 3. Consequences (Következmények)
* **Előnyök:**
  * Vercel Serverless környezetben 100%-ban stabil és perzisztens.
  * Az adminisztrátor közvetlenül a Supabase webes felületéről vagy az Optivoya Admin Dashboardról kezelheti a felhasználókat.
  * Valós idejű telemetria és KPI aggregációk.
* **Invariánsok:**
  * Minden érzékeny adatot `.env` és Vercel Secret változók védenek (`SUPABASE_URL`, `SUPABASE_KEY`).

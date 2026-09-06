# Product Specification & Decisions

## 1. Product Brief
* **One-sentence pitch:** Több email fiók napi szintű automatikus figyelése és AI-alapú összefoglalása sürgősség, teendők és határidők szerint.
* **Problem statement:** Több, különböző célú email fiók figyelése nehezen átlátható, és könnyű elszalasztani fontos vagy határidős teendőket.
* **Target audience:** Egyetlen felhasználó, aki személyes, munkahelyi, egyetemi és projekt email fiókokat kezel.

## 2. Functional Spec
* **Must-have features:**
  * Több email fiók figyelése (személyes, munka, egyetem, projekt, egyéb).
  * Új emailek begyűjtése és feldolgozása.
  * Emailek kategorizálása: személyes, munka, egyetem, projekt, egyéb.
  * Sürgősség és fontosság meghatározása.
  * Teendők felismerése (`action items`).
  * Határidők felismerése (`deadlines`).
  * Rövid email-összefoglalók készítése.
  * Napi összesített jelentés készítése.
  * Push értesítés küldése Pushbulleten keresztül.
  * Groq API használata az AI-alapú elemzéshez.
* **Out of scope:**
  * Email reply draftok készítése.
  * Automatikus email-küldés.

## 3. Technical Constraints
* Python 3.10+
* Groq API (felhő alapú ingyenes/gyors LLM következtetés).
* Pushbullet API.
* `.env` fájlban tárolt tokenek.
* IMAP over SSL / Microsoft Graph fiók csatlakozáshoz.
* Napi egy futás elegendő.
* Nincs erős lokális LLM vagy fizetős API.

## 4. Decision Log
* **Explicit döntések:**
  * Több fiók kezelése független konfigurációval.
  * Idempotens állapotkezelés helyi SQLite adatbázissal (`data/emails.db`).
  * Pushbullet értesítés küldése az aggregált teendőkről és sürgős elemekről.
  * Reply draftok és automatikus küldés elutasítva.

# Product Specification & Decisions

## 1. Product Brief
* **One-sentence pitch:** Több email fiók napi szintű automatikus figyelése és AI-alapú összefoglalása sürgősség, teendők és határidők szerint.
* **Problem statement:** Több, különböző célú email fiók figyelése nehezen átlátható, és könnyű elszalasztani fontos vagy határidős teendőket.
* **Target audience:** Egyetlen felhasználó, aki személyes, munkahelyi, egyetemi és projekt email fiókokat kezel.

## 2. Functional Spec
* **Must-have features:**
  * Több email fiók figyelése (személyes, munka, egyetem, projekt, hírlevelek, egyéb).
  * Új emailek begyűjtése és feldolgozása.
  * Emailek kategorizálása és prioritási pontozása (1-10 skála).
  * Válaszkötelezettség felismerése (`needs_reply`: true/false) – a választ igénylő levelek előre vétele.
  * Releváns, érdekes hírek és cikkek felismerése (`is_interesting_news`: true/false) és szekcióba gyűjtése.
  * Sürgősség és fontosság meghatározása.
  * Teendők felismerése (`action items`) és határidők kinyerése (`deadlines`).
  * Rövid, 1-2 mondatos magyar kivonatok készítése.
  * Napi priorizált Daily Digest készítése (Választ igénylő levelek -> Sürgős ügyek -> Határidők -> Teendők -> Releváns hírek).
  * Push értesítés küldése Pushbulleten keresztül.
  * Google AI Studio (Gemini API) használata strukturált JSON elemzéshez és intelligens fallbackhez.
* **Out of scope:**
  * Email reply draftok készítése.
  * Automatikus email-küldés.

## 3. Technical Constraints
* Python 3.10+
* Google Gemini API (`google-genai` SDK, `gemini-3.5-flash-lite` és fallback modellek).
* Pushbullet API.
* `.env` és Doppler konfigurációkezelés (`GEMINI_API_KEY`, `PUSHBULLET_ACCESS_TOKEN`).
* IMAP over SSL / Microsoft Graph fiók csatlakozáshoz.
* Napi egy futás elegendő.
* Nincs fizetős API kényszer (Google AI Studio ingyenes keret).

## 4. Decision Log
* **Explicit döntések:**
  * Több fiók kezelése független konfigurációval (`accounts.yaml`).
  * Idempotens állapotkezelés helyi SQLite adatbázissal (`data/emails.db`), kibővítve prioritási és válaszkötelezettségi oszlopokkal.
  * Groq helyett Google AI Studio Gemini API használata strukturált outputtal és fallback mechanizmussal.
  * Pushbullet értesítés aggregált, priorizált Daily Digestként működik (kiemelve: választ igénylő levelek, releváns szakmai hírek, határidők).
  * Reply draftok és automatikus küldés elutasítva.

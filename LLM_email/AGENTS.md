# LLM_email Project Governance

## 1. Project Identity & Purpose
* **Name**: LLM_email
* **Purpose**: Napi szintű több-fiókos email figyelés, AI-alapú intelligens kategorizálás, sürgősség- és határidő-meghatározás, valamint aggregált napi értesítés küldése Pushbulleten keresztül.
* **Target Audience**: Egyetlen felhasználó, aki személyes, munkahelyi, egyetemi és projekt email fiókokat kezel párhuzamosan.

## 2. Architecture & Ownership Boundaries
* `src/fetchers/`: Felelős az emailek biztonságos és hatékony lekéréséért (IMAP SSL / Microsoft Graph OAuth2). Nem végez üzleti logikát vagy AI hívásokat.
* `src/storage/`: Felelős az üzenet-állapotok (Message-ID, feldolgozási dátum, hash) perzisztálásáért SQLite-ban. Biztosítja az idempotenciát (ne dolgozzon fel kétszer egy levelet).
* `src/analyzer/`: Felelős a Groq API-val való kommunikációért és a strukturált JSON eredmények kinyeréséért.
* `src/notifier/`: Felelős a Pushbullet API értesítések formázásáért és kiküldéséért.
* `src/orchestrator.py`: Az alkalmazás use-case rétege, amely koordinálja a begyűjtést, szűrést, elemzést, mentést és értesítést.
* `main.py`: CLI belépési pont.

## 3. Engineering & Quality Standards
* **Python**: Python 3.10+ szabványos kódolási elvek, típusannotációk (`typing`), Pydantic modellek használata a strukturált adatokhoz.
* **Hibakezelés**: Egy-egy fiók elérhetetlensége vagy egy-egy email elemzési hibája nem döntheti be a teljes napi feldolgozási folyamatot. Logolás szükséges.
* **Biztonság**: Semmilyen érzékeny adat (jelszó, API kulcs, email tartalom) nem kerülhet verziókezelésbe. Minden titok `.env` vagy gitignore-olt konfigurációs fájlban marad.
* **Idempotencia**: Minden futás determinisztikus; a már feldolgozott üzeneteket kihagyja a rendszer.

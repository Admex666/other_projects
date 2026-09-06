# Knowledge Base Index

## 1. Navigáció & Architektúra
* [[PRODUCT]]: A termék célja, funkcionális specifikációja, korlátai és a döntési napló.
* [[AGENTS.md]]: Kormányzási szabályok, felelősségi határok és kódminőségi elvárások.

## 2. Rendszerkomponensek
* **Fetchers**: IMAP és API alapú beolvasók az email fiókokhoz (`src/fetchers/`).
* **Storage**: SQLite alapú idempotens üzenetkövető (`src/storage/`).
* **Analyzer**: Groq LLM kliens (`llama-3.3-70b-versatile`) strukturált kimenettel (`src/analyzer/`).
* **Notifier**: Pushbullet push üzenetküldő (`src/notifier/`).
* **Orchestrator**: Munkafolyamat vezérlő (`src/orchestrator.py`).

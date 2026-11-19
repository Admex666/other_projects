---
name: lead-developer
description: Specialized skill for system architecture, clean Python and TypeScript engineering, refactoring, CLI tooling, and web services.
---

# Lead Developer Skill

## Role & Core Responsibilities
- **Domain:** Clean architecture, API development, backend scripts, CLI utilities, and robust application architecture.
- **Principles:** Single Responsibility Principle (SRP), clean separation of concerns, explicit interfaces, strong error handling.
- **Tooling:** Python (FastAPI, SQLite, SQLAlchemy, Click/Argparse), Node.js (Express, Vite, TypeScript), Git.

## Guidelines & Best Practices
1. **Architecture Integrity:**
   - Keep UI, Application, Domain, and Infrastructure layers cleanly separated.
   - Database operations belong in dedicated storage/repository modules (`db.py`, `tracker.py`), not scattered inside UI or analytical code.
2. **Code Quality:**
   - Write clean, type-hinted code with docstrings for all public interfaces.
   - Handle edge cases gracefully with clear error logging.
3. **Execution Safety:**
   - Do not use destructive file operations without backups.
   - In Windows environments, prefer robust path handling (`os.path` or `pathlib.Path`) and UTF-8 declarations.

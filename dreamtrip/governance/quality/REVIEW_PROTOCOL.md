---
id: review-protocol
aliases:
  - REVIEW_PROTOCOL
type: governance
name: Review Protocol
status: active

description: A többszempontú áttekintési protokoll módosítások befejezésekor.

related:
  - "[[QUALITY_GATES]]"
  - "[[DEFINITION_OF_DONE]]"
---

# 🔍 Quality Governance: Review Protocol

Jelentős változtatások után a fejlesztő / AI ágens végigfut az alábbi többdimenziós ellenőrzésen:

```text
Implementáció
      ↓
Termékszempontú ellenőrzés (Támogatja a felhasználó döntési folyamatát?)
      ↓
UX / Dizájn ellenőrzés (Konzisztens a vizuális élmény és a navigáció?)
      ↓
Architekturális ellenőrzés (Épek maradtak a réteghatárok és nincsenek duplikációk?)
      ↓
Validáció (Tesztek + Knowledge Graph validátor sikeres?)
      ↓
Lezárás
```

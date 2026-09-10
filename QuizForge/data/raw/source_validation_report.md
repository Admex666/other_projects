# QuizForge - 1. Fázis: Adatforrás Validációs Jelentés

*Generálva: 2026-09-10 08:23:58 UTC*

*Nyers adatok helye: `validation_report_20260910_082358.json`*

## 1. Források Összehasonlítása

| Forrás Neve | Típus | Elérhető | Válaszidő (ms) | Rekordok | KG Alkalmasság | Megjegyzés |
|---|---|:---:|:---:|:---:|:---:|---|
| **Wikidata SPARQL** | `wikidata` | ✅ | 250.41 | 3 | 100% | Sikeres adatkinyerés: 4 entitás, 3 reláció generálva a mintából. |
| **Magyar Wikipédia API** | `wikipedia` | ✅ | 458.42 | 3 | 100% | Sikeres adatkinyerés: 4 entitás, 3 reláció generálva a mintából. |
| **OSZK MEK Portál** | `mek` | ✅ | 84.96 | 3 | 100% | Sikeres adatkinyerés: 4 entitás, 3 reláció generálva a mintából. |
| **Open Trivia DB** | `open_trivia` | ✅ | 898.89 | 3 | 100% | Sikeres adatkinyerés: 6 entitás, 3 reláció generálva a mintából. |

## 2. Kvízkorpusz Tesztkészlet
- **Magyar Pub Quiz Seed Korpusz:** 5 különböző mechanizmusú kérdés definiálva (ABCD, Becslés, Sorrend, Párosítás, Kapcsolat).

## 3. Következtetések és Javasolt Következő Lépések
1. **Wikidata SPARQL:** Kiemelkedően alkalmas közvetlen Knowledge Graph tripletek kinyerésére (személyek, helyek, díjak, évszámok).
2. **Magyar Wikipédia:** Kiválóan alkalmas kategóriafák és kontextuális leírások/kivonatok gyűjtésére.
3. **OSZK MEK:** Magyar kulturális, szépirodalmi és történelmi művek/szerzők gazdag forrása.
4. **Kvízkorpusz:** A mechanizmus-sémák készen állnak a DuckDB tárolásra és a kérdésgenerátor illesztésére.
from migration import migrate_data
from excel_builder import build_excel
import os


def main():
    print("=" * 50)
    print("  Finance OS Generator")
    print("=" * 50)

    data = migrate_data()
    build_excel(data, output_file='../Finance_OS.xlsx')

    readme = """\
# Finance OS – Gyors Útmutató

## Lapok és szerepük

| Lap              | Mit csinálsz itt?            | Szerkeszthető? |
|------------------|------------------------------|----------------|
| 00_Dashboard     | Naponta nézed                | ❌ Csak olvasható |
| 01_Transactions  | Ide viszed fel a kiadásokat  | ✅ Igen |
| 02_Accounts      | Bankszámlák listája          | ✅ Igen |
| 03_BudgetsGoals  | Célok és havi limitek        | ✅ Igen |
| 04_Pockets       | Borítékos rendszer           | ✅ Igen |
| 90_Settings      | Kategóriák, People, stb.    | ✅ Igen |
| 91_Data_ExRates  | Devizaárfolyamok (háttér)   | ❌ |
| 91_Data_IDMap    | Mongo ID mapping (háttér)   | ❌ |

## Manuális teendők (Google Sheets feltöltés után)

A legördülő menük (Category, Account, stb.) Excelben azonnal működnek.
Google Sheets-ben 1-2 dropdown esetleg manuális aktiválást igényel:
1. Jelöld ki az oszlopot (pl. Category a 01_Transactions-ban)
2. Adatok → Adatok érvényesítése
3. Forrás: 90_Settings B oszlopa (kategóriák)

## Bővítés

- Új kategória: 90_Settings → Categories oszlopba írni
- Új számla: 02_Accounts-ba felvenni
- Új zseb: 04_Pockets-ba felvenni

A script bármikor újrafuttatható az adatbázis friss állapotával:
  python src/main.py
"""
    with open('../README.md', 'w', encoding='utf-8') as fp:
        fp.write(readme)

    print("\nKesz! Finance_OS.xlsx, README.md frissitve.")
    print("=" * 50)


if __name__ == '__main__':
    main()

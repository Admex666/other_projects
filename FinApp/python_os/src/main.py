from migration import migrate_data
from excel_builder import build_excel
import os

def main():
    print("Starting Finance OS generation...")
    data_dict = migrate_data()
    build_excel(data_dict, output_file='../Finance_OS.xlsx')
    
    # Write README
    readme = """# Finance OS

## Hogyan használd?
A legenerált `Finance_OS.xlsx` egy moduláris, Google Sheets kompatibilis pénzügyi rendszer.

- **01_Transactions**: Ide rögzítsd az új tranzakciókat. A legördülő menük a többi fülről veszik az adatokat.
- **00_Dashboard**: Teljesen automatizált (🔒), ne szerkeszd kézzel!
- **10_Accounts, 12_Categories, 14_Pockets**: Ha új kategóriát vagy számlát szeretnél, ide írd be, és automatikusan megjelenik a Transactions legördülőiben.

## Fontos (Manuális Teendő Google Sheets-ben)
Mivel az Excel adatérvényesítését (Data Validation) konvertáljuk Google Sheets formátumra, feltöltés után előfordulhat, hogy a legördülő menük "Másik munkalapra" mutató hivatkozásai nem egyből kattinthatók. 

**Teendő:**
1. Jelöld ki a *Category* oszlopot a `01_Transactions` fülön.
2. Kattints: Adatok -> Adatok érvényesítése.
3. A kritériumnál válaszd: "Legördülő menü (tartományból)", majd válaszd ki a `12_Categories` lap C oszlopát.
4. Ezt tedd meg az *Account* és *Pocket* oszlopoknál is a `10_Accounts` és `14_Pockets` lapokra mutatva.

Jó pénzügyezést!
"""
    with open('../README.md', 'w', encoding='utf-8') as f:
        f.write(readme)
        
    print("Done! Check Finance_OS.xlsx, Migration_Report.txt, and README.md in the FinApp root.")

if __name__ == "__main__":
    main()

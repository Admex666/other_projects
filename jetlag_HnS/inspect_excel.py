import pandas as pd
import sys

file_path = r'c:\Users\Adam\Data\other_projects\jetlag_HnS\Jet Lag The Game.xlsx'

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names: {xls.sheet_names}")
    
    for sheet_name in xls.sheet_names:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(df.head().to_string(index=False))
        print(f"\nColumns: {list(df.columns)}")
        
except Exception as e:
    print(f"Error reading Excel file: {e}")

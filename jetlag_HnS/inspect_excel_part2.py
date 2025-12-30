import pandas as pd
import sys

file_path = r'c:\Users\Adam\Data\other_projects\jetlag_HnS\Jet Lag The Game.xlsx'

try:
    for sheet_name in ['Hider Deck', '💀Curses']:
        print(f"\n--- Sheet: {sheet_name} ---")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        # Drop completely empty rows/cols to clean up view
        df = df.dropna(how='all').dropna(axis=1, how='all')
        print(df.head(10).to_string(index=False))
        
except Exception as e:
    print(f"Error reading Excel file: {e}")

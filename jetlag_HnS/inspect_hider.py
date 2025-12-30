import pandas as pd

file_path = r'c:\Users\Adam\Data\other_projects\jetlag_HnS\Jet Lag The Game.xlsx'

try:
    print("\n--- Sheet: Hider Deck ---")
    df = pd.read_excel(file_path, sheet_name='Hider Deck')
    # Print first 20 rows of the first few columns
    print(df.iloc[:, :4].head(20).to_string(index=False))
        
except Exception as e:
    print(f"Error reading Excel file: {e}")

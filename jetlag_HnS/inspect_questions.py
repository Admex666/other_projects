import pandas as pd

file_path = r'c:\Users\Adam\Data\other_projects\jetlag_HnS\Jet Lag The Game.xlsx'

question_sheets = ['1. Matching', '2. Measuring', '3. Thermometer', '4. Radar', '5. Tentacles', '6. Photos']

try:
    for sheet_name in question_sheets:
        print(f"\n=== Sheet: {sheet_name} ===")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        # The first few rows usually contain the card metadata (Cost, Time, Question template)
        # The rest of the columns seem to be the variable data.
        
        # Print first 5 rows to see metadata
        print("-- Metadata/Header --")
        print(df.head(5).to_string(index=False))
        
        # It looks like the lists start lower down or in specific columns. 
        # Let's see non-null values in columns to understand the lists.
        print("\n-- Content Snippet --")
        # Print a few rows from row 6 onwards to see the list items
        print(df.iloc[5:].head(10).to_string(index=False))

except Exception as e:
    print(f"Error: {e}")

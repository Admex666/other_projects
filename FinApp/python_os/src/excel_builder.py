import pandas as pd
from formatting import apply_formats
from dashboard import build_dashboard

def build_excel(data_dict, output_file='Finance_OS.xlsx'):
    print(f"Building {output_file}...")
    
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        workbook = writer.book
        formats = apply_formats(workbook)
        
        # 1. Create Dashboard first
        dash_ws = workbook.add_worksheet('00_Dashboard')
        build_dashboard(workbook, dash_ws, formats)
        
        # 2. Write all other dataframes
        for sheet_name, df in data_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            
            # Format headers and freeze panes
            for col_num, value in enumerate(df.columns):
                # Put lock emoji if automatic
                header_text = value
                if value in ['TransactionID', 'BaseAmount', 'ExchangeRate', 'CreatedAt', 'AccountID', 'CategoryID', 'PocketID', 'CurrentBalance', 'TotalSpent']:
                    header_text = value + ' 🔒'
                
                worksheet.write(0, col_num, header_text, formats['header'])
                
            worksheet.freeze_panes(1, 0)
            
            # Write formulas row by row
            num_rows = len(df)
            for row_idx in range(num_rows):
                row_num = row_idx + 2
                
                if sheet_name == '01_Transactions':
                    fallback_rate = df.iloc[row_idx]['ExchangeRate']
                    if pd.isna(fallback_rate) or fallback_rate == '': fallback_rate = 1
                    
                    # ExchangeRate (Column J - index 9)
                    formula_rate = f'=IF(H{row_num}="HUF", 1, IFERROR(VLOOKUP(B{row_num}&H{row_num}, \'22_ExchangeRates\'!A:E, 5, FALSE), {fallback_rate}))'
                    worksheet.write_formula(row_idx + 1, 9, formula_rate, formats['auto_num'])
                    
                    # BaseAmount (Column I - index 8)
                    formula_base = f'=G{row_num} * J{row_num}'
                    worksheet.write_formula(row_idx + 1, 8, formula_base, formats['auto_num'])
                    
                elif sheet_name == '10_Accounts':
                    # CurrentBalance (Column H - index 7)
                    # OpeningBalance is G (index 6), Name is B (index 1)
                    # Income - Expense - Transfer(Out) + Transfer(In)
                    formula_bal = f'=G{row_num} + SUMIFS(\'01_Transactions\'!G:G, \'01_Transactions\'!E:E, B{row_num}, \'01_Transactions\'!C:C, "Income") - SUMIFS(\'01_Transactions\'!G:G, \'01_Transactions\'!E:E, B{row_num}, \'01_Transactions\'!C:C, "Expense") - SUMIFS(\'01_Transactions\'!G:G, \'01_Transactions\'!E:E, B{row_num}, \'01_Transactions\'!C:C, "Transfer") + SUMIFS(\'01_Transactions\'!G:G, \'01_Transactions\'!F:F, B{row_num}, \'01_Transactions\'!C:C, "Transfer")'
                    worksheet.write_formula(row_idx + 1, 7, formula_bal, formats['auto_num'])
                    
                elif sheet_name == '12_Categories':
                    # TotalSpent (Column D - index 3)
                    # Name is C (index 2)
                    formula_spent = f'=SUMIFS(\'01_Transactions\'!I:I, \'01_Transactions\'!K:K, C{row_num}, \'01_Transactions\'!C:C, "Expense")'
                    worksheet.write_formula(row_idx + 1, 3, formula_spent, formats['auto_num'])
                    
                elif sheet_name == '14_Pockets':
                    # CurrentBalance (Column E - index 4, wait GoalAmount is index 4. Name is B(1), Owner C(2), Curr D(3), Goal E(4), Bal F(5))
                    # Let's check migration.py Pocket columns: PocketID, Name, Owner, Currency, GoalAmount, CurrentBalance, Type, Active
                    # So CurrentBalance is index 5
                    formula_pocket = f'=SUMIFS(\'01_Transactions\'!I:I, \'01_Transactions\'!L:L, B{row_num}, \'01_Transactions\'!C:C, "Transfer") - SUMIFS(\'01_Transactions\'!I:I, \'01_Transactions\'!L:L, B{row_num}, \'01_Transactions\'!C:C, "Expense")'
                    worksheet.write_formula(row_idx + 1, 5, formula_pocket, formats['auto_num'])
            
            # Auto format columns width
            for col_num, col_name in enumerate(df.columns):
                # Set width
                max_len = max(
                    df[col_name].astype(str).map(len).max() if not df.empty else 10,
                    len(col_name) + 2
                )
                worksheet.set_column(col_num, col_num, min(max_len + 2, 40))
                
            # If transactions, add data validation
            if sheet_name == '01_Transactions':
                # Type validation (Column C - index 2)
                worksheet.data_validation(1, 2, 1048576, 2, {
                    'validate': 'list',
                    'source': ['Income', 'Expense', 'Transfer', 'Investment']
                })
                # Category Validation from 12_Categories C column (Name) (Transactions Category is column K - index 10)
                worksheet.data_validation(1, 10, 1048576, 10, {
                    'validate': 'list',
                    'source': "='12_Categories'!$C$2:$C$1000"
                })
                
                # Account Validation from 10_Accounts B column (Name) (Transactions Account is E - 4, ToAccount is F - 5)
                worksheet.data_validation(1, 4, 1048576, 4, {
                    'validate': 'list',
                    'source': "='10_Accounts'!$B$2:$B$100"
                })
                worksheet.data_validation(1, 5, 1048576, 5, {
                    'validate': 'list',
                    'source': "='10_Accounts'!$B$2:$B$100"
                })
                
                # Pocket Validation from 14_Pockets B column (Transactions Pocket is L - index 11)
                worksheet.data_validation(1, 11, 1048576, 11, {
                    'validate': 'list',
                    'source': "='14_Pockets'!$B$2:$B$100"
                })
                
        print("Excel built successfully.")

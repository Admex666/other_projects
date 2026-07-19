def build_dashboard(workbook, worksheet, formats):
    # Set column widths
    worksheet.set_column('A:A', 30)
    worksheet.set_column('B:B', 25)
    
    # Write titles
    worksheet.write('A1', '💰 FŐ MUTATÓK (🔒 Auto)', formats['dash_title'])
    worksheet.write('A2', 'Összes Bevétel (Income)', formats['auto'])
    worksheet.write_formula('B2', '=SUMIFS(\'01_Transactions\'!I:I, \'01_Transactions\'!C:C, "Income")', formats['auto_num'])
    
    worksheet.write('A3', 'Összes Kiadás (Expense)', formats['auto'])
    worksheet.write_formula('B3', '=SUMIFS(\'01_Transactions\'!I:I, \'01_Transactions\'!C:C, "Expense")', formats['auto_num'])
    
    worksheet.write('A4', 'Net Worth (Nettó Vagyon)', formats['auto'])
    worksheet.write_formula('B4', '=B2-B3', formats['dash_metric'])
    
    worksheet.write('A6', '🎯 VIRTUÁLIS ZSEBEK (🔒 Auto)', formats['dash_title'])
    # For pockets, we will do a simple example that checks 'Pocket' column (column L is index 11 -> so L:L in Excel)
    worksheet.write('A7', 'Zsebek Összesen', formats['auto'])
    worksheet.write_formula('B7', '=SUMIFS(\'01_Transactions\'!I:I, \'01_Transactions\'!L:L, "<>")', formats['auto_num'])
    
    # Protect dashboard
    worksheet.protect()

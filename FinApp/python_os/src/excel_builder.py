import pandas as pd
from formatting import apply_formats
from dashboard import build_dashboard


# Columns that are auto-computed – shown with 🔒 in header
AUTO_COLS = {'ID', 'BaseAmount', 'CreatedAt', 'CurrentBalance', 'TotalSpent', '_MongoID', 'LookupKey'}

# Dropdown sources per sheet → column name → (source_sheet, source_col_letter, max_row)
DROPDOWNS = {
    '01_Transactions': {
        'Type':     ['Income', 'Expense', 'Transfer', 'Investment'],
        'Account':  "='02_Accounts'!$A$2:$A$200",
        'Currency': ['HUF', 'EUR', 'USD', 'GBP'],
        'Category': "='90_Settings'!$B$2:$B$200",
        'Pocket':   "='04_Pockets'!$A$2:$A$100",
        'Owner':    "='90_Settings'!$A$2:$A$20",
    },
    '02_Accounts': {
        'Type':     ['Bank', 'Cash', 'Crypto', 'Investment', 'CreditCard', 'Loan'],
        'Currency': ['HUF', 'EUR', 'USD', 'GBP'],
        'Owner':    "='90_Settings'!$A$2:$A$20",
    },
    '03_BudgetsGoals': {
        'Type':   ['Budget', 'Goal'],
        'Owner':  "='90_Settings'!$A$2:$A$20",
        'Period': ['Monthly', 'Yearly', 'One-time'],
    },
    '04_Pockets': {
        'Owner':    "='90_Settings'!$A$2:$A$20",
        'Currency': ['HUF', 'EUR', 'USD'],
    },
}

# Which column index (0-based) maps to a column name for each sheet
COL_ORDERS = {
    '01_Transactions': ['Date','Type','Account','Amount','Currency','Category','Pocket','Merchant','Owner','Note','ID','BaseAmount','CreatedAt'],
    '02_Accounts':     ['Name','Type','Currency','Owner','OpeningBalance','IsArchived','_MongoID'],
    '03_BudgetsGoals': ['Name','Type','Owner','Target','Period','Note'],
    '04_Pockets':      ['Pocket','Owner','Currency','Target','_MongoID'],
    '90_Settings':     None,   # handled separately
    '91_Data_ExRates': None,
    '91_Data_IDMap':   None,
}


def _col_letter(idx):
    """0-based index → Excel column letter."""
    letters = ''
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _write_sheet(workbook, writer, sheet_name, df, f):
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
    ws = writer.sheets[sheet_name]
    ws.freeze_panes(1, 0)

    col_order = COL_ORDERS.get(sheet_name)
    if col_order:
        col_indices = {c: i for i, c in enumerate(col_order)}
    else:
        col_indices = {c: i for i, c in enumerate(df.columns)}

    # ── Headers ───────────────────────────────────────────────────────────
    for col_name, col_idx in col_indices.items():
        if col_name not in df.columns:
            continue
        label = col_name + ' 🔒' if col_name in AUTO_COLS else col_name
        ws.write(0, col_idx, label, f['header'])

    # ── Formulas for 01_Transactions ─────────────────────────────────────
    if sheet_name == '01_Transactions':
        for row_idx, row in df.iterrows():
            r = row_idx + 2  # Excel row (1-based, +1 for header)

            # ExchangeRate lookup → write into a helper column (N, index 13)
            fallback = row.get('BaseAmount', row.get('Amount', 0))
            rate_formula = (
                f'=IF(E{r}="HUF", 1, '
                f'IFERROR(VLOOKUP(A{r}&E{r}, \'91_Data_ExRates\'!A:D, 4, FALSE), 1))'
            )
            ws.write_formula(row_idx + 1, 13, rate_formula, f['auto_num'])

            # BaseAmount (col L, index 11)
            ws.write_formula(row_idx + 1, 11,
                f'=D{r}*N{r}', f['auto_num'])

    # ── Auto column widths ─────────────────────────────────────────────────
    for col_name, col_idx in col_indices.items():
        if col_name not in df.columns:
            continue
        max_len = max(
            df[col_name].astype(str).map(len).max() if not df.empty else 10,
            len(col_name) + 4
        )
        ws.set_column(col_idx, col_idx, min(max_len + 2, 42))

    # ── Data Validations ──────────────────────────────────────────────────
    dv_map = DROPDOWNS.get(sheet_name, {})
    for col_name, source in dv_map.items():
        if col_name not in col_indices:
            continue
        col_idx = col_indices[col_name]
        if isinstance(source, list):
            ws.data_validation(1, col_idx, 1048575, col_idx,
                               {'validate': 'list', 'source': source})
        else:
            ws.data_validation(1, col_idx, 1048575, col_idx,
                               {'validate': 'list', 'source': source})


def _write_settings(workbook, writer, df, f):
    """90_Settings gets a special block layout. Sheet already created by df.to_excel."""
    ws = writer.sheets['90_Settings']
    ws.set_column('A:A', 18)
    ws.set_column('B:B', 24)
    ws.set_column('C:C', 20)
    ws.set_column('D:D', 16)

    headers = list(df.columns)
    for col_idx, h in enumerate(headers):
        ws.write(0, col_idx, h, f['settings_block'])

    for row_idx, row in df.iterrows():
        for col_idx, h in enumerate(headers):
            val = row[h] if not pd.isna(row[h]) else ''
            ws.write(row_idx + 1, col_idx, val, f['settings_val'])


def build_excel(data_dict, output_file='Finance_OS.xlsx'):
    print(f"Building {output_file}...")

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        workbook = writer.book
        f = apply_formats(workbook)

        # 00_Dashboard first
        pocket_names = []
        pockets_df = data_dict.get('04_Pockets')
        if pockets_df is not None and not pockets_df.empty and 'Pocket' in pockets_df.columns:
            pocket_names = pockets_df['Pocket'].dropna().tolist()
        
        dash_ws = workbook.add_worksheet('00_Dashboard')
        build_dashboard(workbook, dash_ws, f, pocket_names=pocket_names)

        # Write all data sheets
        for sheet_name, df in data_dict.items():
            if sheet_name == '90_Settings':
                # needs special treatment
                df.to_excel(writer, sheet_name='90_Settings', index=False)
                _write_settings(workbook, writer, df, f)
                continue

            df.to_excel(writer, sheet_name=sheet_name, index=False)
            _write_sheet(workbook, writer, sheet_name, df, f)

        print("Excel built successfully.")

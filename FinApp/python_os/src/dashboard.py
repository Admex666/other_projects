TX  = "'01_Transactions'"
POC = "'04_Pockets'"
SET = "'90_Settings'"


def _ref_date(offset):
    """Excel expression for the 1st of the month at offset months from today."""
    if offset == 0:
        return 'DATE(YEAR(TODAY()),MONTH(TODAY()),1)'
    return f'DATE(YEAR(TODAY()),MONTH(TODAY())+({offset}),1)'


def _month_label(offset):
    return f'=TEXT({_ref_date(offset)},"YYYY-MM")'


def _sumif_type_month(tx_type, offset):
    """SUMPRODUCT for income/expense filtered to a given month.
    Uses YEAR()+MONTH() comparison – works for both date serials and text dates."""
    rd = _ref_date(offset)
    return (
        f'=SUMPRODUCT(({TX}!B$2:B$5000="{tx_type}")*'
        f'(YEAR({TX}!A$2:A$5000)=YEAR({rd}))*'
        f'(MONTH({TX}!A$2:A$5000)=MONTH({rd}))*'
        f'{TX}!L$2:L$5000)'
    )


def _sumif_cat_month(cat_ref, offset):
    rd = _ref_date(offset)
    return (
        f'=IFERROR(SUMPRODUCT(({TX}!F$2:F$5000={cat_ref})*'
        f'(YEAR({TX}!A$2:A$5000)=YEAR({rd}))*'
        f'(MONTH({TX}!A$2:A$5000)=MONTH({rd}))*'
        f'{TX}!L$2:L$5000),0)'
    )


def build_dashboard(workbook, ws, f, pocket_names=None):
    if pocket_names is None:
        pocket_names = []

    # ── Column widths ────────────────────────────────────────────────────────
    ws.set_column('A:A', 2)    # left gutter
    ws.set_column('B:B', 26)   # left labels
    ws.set_column('C:C', 18)   # left values
    ws.set_column('D:D', 3)    # spacer
    ws.set_column('E:E', 26)   # right labels
    ws.set_column('F:F', 18)   # right values
    ws.set_column('G:G', 3)    # spacer
    ws.set_column('H:H', 16)   # trend row labels
    ws.set_column('I:I', 13)
    ws.set_column('J:J', 13)
    ws.set_column('K:K', 13)
    ws.set_column('L:L', 13)
    ws.set_column('M:M', 13)
    ws.set_column('N:N', 13)
    ws.set_row(0, 6)           # top gutter

    # ── Helpers ──────────────────────────────────────────────────────────────
    def lbl(row, col, text, fmt='kpi_label'):
        ws.write(row, col, text, f[fmt])

    def fml(row, col, formula_str, fmt='kpi_green'):
        ws.write_formula(row, col, formula_str, f[fmt])

    def section2(row, col, text):
        """Merges 2 columns."""
        ws.merge_range(row, col, row, col + 1, text, f['section_title'])

    def section6(row, col, text):
        """Merges 6 data columns + 1 label = 7 cols."""
        ws.merge_range(row, col, row, col + 6, text, f['section_title'])

    # ═══════════════════════════════════════════════════════════════════════
    # LEFT PANEL  B:C
    # ═══════════════════════════════════════════════════════════════════════

    # ── All-time totals ──────────────────────────────────────────────────────
    section2(1, 1, '  Osszes Ido  [Auto]')
    lbl(2, 1, 'Osszes Bevetel (HUF)')
    fml(2, 2, f'=SUMIFS({TX}!L:L,{TX}!B:B,"Income")', 'kpi_green')
    lbl(3, 1, 'Osszes Kiadas (HUF)')
    fml(3, 2, f'=SUMIFS({TX}!L:L,{TX}!B:B,"Expense")', 'kpi_red')
    lbl(4, 1, 'Netto Vagyon (HUF)')
    fml(4, 2, '=C3-C4', 'kpi_blue')

    # ── Current month ─────────────────────────────────────────────────────────
    section2(6, 1, '  Aktualis Honap  [Auto]')
    lbl(7, 1, 'Havi Bevetel')
    fml(7, 2, _sumif_type_month('Income',  0), 'kpi_green')
    lbl(8, 1, 'Havi Kiadas')
    fml(8, 2, _sumif_type_month('Expense', 0), 'kpi_red')
    lbl(9, 1, 'Havi Cashflow')
    fml(9, 2, '=C8-C9', 'kpi_blue')

    # ═══════════════════════════════════════════════════════════════════════
    # RIGHT PANEL  E:F
    # ═══════════════════════════════════════════════════════════════════════

    # ── Top categories (current month) ───────────────────────────────────────
    section2(1, 4, '  Top Kategoriak – aktualis honap  [Auto]')
    for i in range(6):
        row = 2 + i
        cat_ref = f'{SET}!B{i+2}'
        ws.write_formula(row, 4, f'=IFERROR({cat_ref},"")', f['kpi_label'])
        fml(row, 5, _sumif_cat_month(cat_ref, 0), 'kpi_red')

    # ── Pockets ──────────────────────────────────────────────────────────────
    poc_start = 9
    section2(poc_start, 4, '  Virtualis Zsebek  [Auto]')
    for i, name in enumerate(pocket_names):
        row = poc_start + 1 + i
        poc_ref = f'{POC}!A{i+2}'
        ws.write_formula(row, 4, f'=IFERROR({poc_ref},"")', f['kpi_label'])
        fml(row, 5,
            f'=IFERROR(SUMPRODUCT(({TX}!G$2:G$5000={poc_ref})*{TX}!L$2:L$5000),0)',
            'kpi_neutral')

    # ═══════════════════════════════════════════════════════════════════════
    # TREND PANEL  H:N  (col 7..13)
    # Layout:
    #   Col H  = row label
    #   Col I-N = months (offset -5 .. 0)
    # ═══════════════════════════════════════════════════════════════════════
    OFFSETS = [-5, -4, -3, -2, -1, 0]

    # Section header
    section6(1, 7, '  6 Honapos Trend  [Auto]')

    # Month header row (row 2)
    lbl(2, 7, '', 'header')  # empty corner
    for m, off in enumerate(OFFSETS):
        fml(2, 8 + m, _month_label(off), 'header')

    # Income row (row 3)
    lbl(3, 7, 'Bevetel')
    for m, off in enumerate(OFFSETS):
        fml(3, 8 + m, _sumif_type_month('Income', off), 'kpi_green')

    # Expense row (row 4)
    lbl(4, 7, 'Kiadas')
    for m, off in enumerate(OFFSETS):
        fml(4, 8 + m, _sumif_type_month('Expense', off), 'kpi_red')

    # Cashflow row (row 5)
    lbl(5, 7, 'Cashflow')
    for m, off in enumerate(OFFSETS):
        inc = _sumif_type_month('Income',  off).lstrip('=')
        exp = _sumif_type_month('Expense', off).lstrip('=')
        fml(5, 8 + m, f'={inc}-{exp}', 'kpi_blue')

    # ── Category × month breakdown ───────────────────────────────────────────
    section6(7, 7, '  Kategoriak – 6 honapos bontasban  [Auto]')

    # Month header row for cat section (row 8)
    lbl(8, 7, 'Kategoria', 'header')
    for m, off in enumerate(OFFSETS):
        fml(8, 8 + m, _month_label(off), 'header')

    # 6 category rows (rows 9-14)
    for i in range(6):
        row = 9 + i
        cat_ref = f'{SET}!B{i+2}'
        ws.write_formula(row, 7, f'=IFERROR({cat_ref},"")', f['kpi_label'])
        for m, off in enumerate(OFFSETS):
            fml(row, 8 + m, _sumif_cat_month(cat_ref, off), 'kpi_red')

    ws.protect()

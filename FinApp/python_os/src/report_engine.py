"""
FinSpace Report Engine
======================
Deterministic report generators for Weekly, Monthly, and Quarterly financial reports.
All calculations are Python-based. Insights are short, objective, data-driven statements.
"""
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _safe_pct_change(current, previous):
    """Calculate percentage change, handling zero division."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / abs(previous)) * 100


def _top_n(series, n=5):
    """Return top N items from a Series, sorted descending."""
    return series.nlargest(n)


def _filter_real(df):
    """Exclude internal allocations and transfers from P&L calculations."""
    if df.empty:
        return df
    return df[~df['IsInternal'] & (df['Type'] != 'transfer')]


def _net_worth_at_period_end(df_tx, acc_docs, period_end_date):
    """
    Reconstruct net worth at a given date by subtracting all cashflow
    that occurred AFTER that date from current account balances.
    """
    current_nw = sum(a.get('balanceInBase', 0) for a in acc_docs
                     if not a.get('isArchived') and not a.get('isBusinessAccount'))

    if df_tx.empty:
        return current_nw

    # Sum all real income/expense after the period end
    df_r = df_tx[~df_tx['IsInternal'] & (df_tx['Type'] != 'transfer')]
    df_after = df_r[df_r['Date'] > period_end_date]

    if df_after.empty:
        return current_nw

    post_income = df_after[df_after['Type'] == 'income']['AmountBase'].sum()
    post_expense = df_after[df_after['Type'] == 'expense']['AmountBase'].sum()
    post_cashflow = post_income - post_expense

    return current_nw - post_cashflow


def _period_flow(df, period_col, period_val):
    """Calculate income, expense, cashflow for a given period."""
    df_r = _filter_real(df)
    df_p = df_r[df_r[period_col] == period_val] if not df_r.empty else df_r

    inc = df_p[df_p['Type'] == 'income']['AmountBase'].sum() if not df_p.empty else 0.0
    exp = df_p[df_p['Type'] == 'expense']['AmountBase'].sum() if not df_p.empty else 0.0
    return inc, exp, inc - exp


def _category_breakdown(df, period_col, period_val, n=10):
    """Top N expense categories for a period with amounts and percentages."""
    df_r = _filter_real(df)
    df_p = df_r[(df_r[period_col] == period_val) & (df_r['Type'] == 'expense')]
    if df_p.empty:
        return pd.DataFrame(columns=['Category', 'Amount', 'Pct', 'TxCount'])

    cat = df_p.groupby('Category').agg(
        Amount=('AmountBase', 'sum'),
        TxCount=('AmountBase', 'count')
    ).sort_values('Amount', ascending=False).head(n).reset_index()

    total = cat['Amount'].sum()
    cat['Pct'] = (cat['Amount'] / total * 100) if total > 0 else 0.0
    return cat


def _category_comparison(df, period_col, current_val, previous_val, n=10):
    """Top categories with current vs previous period comparison."""
    curr = _category_breakdown(df, period_col, current_val, n)
    prev_df = _filter_real(df)
    prev_p = prev_df[(prev_df[period_col] == previous_val) & (prev_df['Type'] == 'expense')]
    prev_cat = prev_p.groupby('Category')['AmountBase'].sum() if not prev_p.empty else pd.Series(dtype=float)

    if not curr.empty:
        curr['PrevAmount'] = curr['Category'].map(lambda c: prev_cat.get(c, 0.0))
        curr['Change'] = curr.apply(lambda r: _safe_pct_change(r['Amount'], r['PrevAmount']), axis=1)
    return curr


def _merchant_breakdown(df, period_col, period_val, n=10):
    """Top N merchants by spend for a period."""
    df_r = _filter_real(df)
    df_p = df_r[(df_r[period_col] == period_val) & (df_r['Type'] == 'expense')]
    if df_p.empty:
        return pd.DataFrame(columns=['Merchant', 'Amount', 'TxCount'])

    merch = df_p.groupby('Merchant').agg(
        Amount=('AmountBase', 'sum'),
        TxCount=('AmountBase', 'count')
    ).sort_values('Amount', ascending=False).head(n).reset_index()
    return merch


def _top_expenses(df, period_col, period_val, n=5):
    """Top N largest individual expense transactions."""
    df_r = _filter_real(df)
    df_p = df_r[(df_r[period_col] == period_val) & (df_r['Type'] == 'expense')]
    if df_p.empty:
        return pd.DataFrame(columns=['Date', 'AmountBase', 'Category', 'Merchant', 'Note'])

    top = df_p.nlargest(n, 'AmountBase')[['Date', 'AmountBase', 'Category', 'Merchant', 'Note']].copy()
    top['Date'] = top['Date'].dt.strftime('%Y-%m-%d')
    return top.reset_index(drop=True)


def _account_balances(acc_docs):
    """Current account balances summary."""
    rows = []
    for a in acc_docs:
        if a.get('isArchived'):
            continue
        rows.append({
            'Account': a['name'],
            'Currency': a.get('currency', 'HUF'),
            'Balance': a.get('balanceInBase', 0),
            'IsBusiness': bool(a.get('isBusinessAccount')),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=['Account', 'Currency', 'Balance', 'IsBusiness'])


def _pocket_summary(poc_docs):
    """Virtual pockets summary."""
    rows = []
    for p in poc_docs:
        target = float(p.get('targetAmount', 0))
        current = float(p.get('currentAmountInBase', p.get('currentAmount', 0)))
        rows.append({
            'Pocket': p.get('name', ''),
            'Current': current,
            'Target': target,
            'Pct': (current / target * 100) if target > 0 else 100.0,
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=['Pocket', 'Current', 'Target', 'Pct'])


def _get_prev_week(week_str):
    """Given '2026-W32', return '2026-W31'."""
    year, w = int(week_str.split('-W')[0]), int(week_str.split('-W')[1])
    d = datetime.strptime(f'{year}-W{w:02d}-1', '%G-W%V-%u')
    prev = d - timedelta(weeks=1)
    return f"{prev.isocalendar()[0]}-W{prev.isocalendar()[1]:02d}"


def _get_prev_month(month_str):
    """Given '2026-08', return '2026-07'."""
    dt = datetime.strptime(month_str + '-01', '%Y-%m-%d')
    prev = (dt.replace(day=1) - timedelta(days=1))
    return prev.strftime('%Y-%m')


def _get_prev_quarter(quarter_str):
    """Given '2026-Q3', return '2026-Q2'."""
    year, q = int(quarter_str.split('-Q')[0]), int(quarter_str.split('-Q')[1])
    if q == 1:
        return f"{year - 1}-Q4"
    return f"{year}-Q{q - 1}"


def _get_year_start_quarter(quarter_str):
    """Given '2026-Q3', return '2026-Q1'."""
    year = int(quarter_str.split('-Q')[0])
    return f"{year}-Q1"


# ═════════════════════════════════════════════════════════════════════════════
# INSIGHT GENERATORS (rule-based, max 5 short statements)
# ═════════════════════════════════════════════════════════════════════════════

def _weekly_insights(report):
    """Generate max 5 short objective insights for weekly report."""
    insights = []

    # 1. Biggest category change vs previous week
    cats = report.get('categories', pd.DataFrame())
    if not cats.empty and 'Change' in cats.columns:
        biggest_up = cats[cats['Change'] > 15].head(1)
        if not biggest_up.empty:
            r = biggest_up.iloc[0]
            insights.append(f"{r['Category']} költés {r['Change']:+.0f}% az előző héthez képest ({r['Amount']:,.0f} Ft)")

        biggest_down = cats[cats['Change'] < -15].sort_values('Change').head(1)
        if not biggest_down.empty:
            r = biggest_down.iloc[0]
            insights.append(f"{r['Category']} költés {r['Change']:+.0f}% az előző héthez képest")

    # 2. Savings info
    cashflow = report.get('cashflow', 0)
    if cashflow > 0:
        insights.append(f"Pozitív cashflow: +{cashflow:,.0f} Ft megtakarítás ezen a héten")
    elif cashflow < -50000:
        insights.append(f"Negatív cashflow: {cashflow:,.0f} Ft — a kiadások meghaladták a bevételt")

    # 3. Transaction volume
    tx_count = report.get('tx_count', 0)
    prev_tx_count = report.get('prev_tx_count', 0)
    if prev_tx_count > 0:
        tx_change = _safe_pct_change(tx_count, prev_tx_count)
        if abs(tx_change) > 20:
            insights.append(f"Tranzakciók száma {tx_change:+.0f}% az előző héthez képest ({tx_count} db)")

    # 4. Top merchant dominance
    merchants = report.get('merchants', pd.DataFrame())
    total_exp = report.get('expense', 0)
    if not merchants.empty and total_exp > 0:
        top = merchants.iloc[0]
        pct = top['Amount'] / total_exp * 100
        if pct > 30:
            insights.append(f"A kiadások {pct:.0f}%-a egyetlen helyen: {top['Merchant']}")

    return insights[:5]


def _monthly_insights(report):
    """Generate max 5 short objective insights for monthly report."""
    insights = []

    # 1. Savings rate
    sr = report.get('savings_rate', 0)
    if sr > 0:
        insights.append(f"Megtakarítási ráta: {sr:.1f}%")

    # 2. Net worth change
    nw_change = report.get('net_worth_change_pct', 0)
    if abs(nw_change) > 0.5:
        insights.append(f"Nettó vagyon változás: {nw_change:+.1f}% az előző hónaphoz képest")

    # 3. Category vs 12-month average
    cats = report.get('categories_vs_avg', pd.DataFrame())
    if not cats.empty and 'VsAvgPct' in cats.columns:
        above = cats[cats['VsAvgPct'] > 25].head(2)
        for _, r in above.iterrows():
            insights.append(f"{r['Category']}: {r['VsAvgPct']:+.0f}% a 12 havi átlaghoz képest ({r['Amount']:,.0f} Ft)")

    # 4. Pocket progress
    pockets = report.get('pockets', pd.DataFrame())
    if not pockets.empty:
        near_goal = pockets[pockets['Pct'] >= 80]
        for _, p in near_goal.head(1).iterrows():
            insights.append(f"{p['Pocket']} zseb {p['Pct']:.0f}%-on áll a célhoz képest")

    # 5. Cashflow trend
    cashflow = report.get('cashflow', 0)
    prev_cashflow = report.get('prev_cashflow', 0)
    if prev_cashflow != 0:
        cf_change = _safe_pct_change(cashflow, prev_cashflow)
        if abs(cf_change) > 20:
            insights.append(f"Cashflow {cf_change:+.0f}% az előző hónaphoz képest")

    return insights[:5]


def _quarterly_insights(report):
    """Generate max 5 short objective insights for quarterly report."""
    insights = []

    # 1. Net worth growth
    nw_growth = report.get('net_worth_ytd_change_pct', 0)
    if abs(nw_growth) > 0.1:
        insights.append(f"Nettó vagyon YTD változás: {nw_growth:+.1f}%")

    # 2. Quarterly savings
    savings = report.get('cashflow', 0)
    if savings > 0:
        insights.append(f"Negyedéves megtakarítás: {savings:,.0f} Ft")

    # 3. Top changing categories vs previous quarter
    cats = report.get('categories', pd.DataFrame())
    if not cats.empty and 'Change' in cats.columns:
        biggest = cats[cats['Change'].abs() > 20].head(2)
        for _, r in biggest.iterrows():
            insights.append(f"{r['Category']}: {r['Change']:+.0f}% az előző negyedévhez képest")

    # 4. Average monthly savings rate
    avg_sr = report.get('avg_savings_rate', 0)
    if avg_sr > 0:
        insights.append(f"Átlagos havi megtakarítási ráta: {avg_sr:.1f}%")

    return insights[:5]


# ═════════════════════════════════════════════════════════════════════════════
# 1. WEEKLY REPORT
# ═════════════════════════════════════════════════════════════════════════════

def generate_weekly_report(df_tx, acc_docs, poc_docs, rates, target_week=None):
    """
    Generate a weekly financial report.

    Args:
        df_tx: Prepared transaction DataFrame
        acc_docs: Account documents from MongoDB
        poc_docs: Virtual pocket documents
        rates: Exchange rates dict
        target_week: Week string like '2026-W32'. If None, uses current week.

    Returns:
        dict with all report sections
    """
    if target_week is None:
        now = datetime.now()
        target_week = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"

    prev_week = _get_prev_week(target_week)

    # KPIs
    income, expense, cashflow = _period_flow(df_tx, 'Week', target_week)
    prev_inc, prev_exp, prev_cf = _period_flow(df_tx, 'Week', prev_week)

    df_r = _filter_real(df_tx)
    tx_count = len(df_r[df_r['Week'] == target_week]) if not df_r.empty else 0
    prev_tx_count = len(df_r[df_r['Week'] == prev_week]) if not df_r.empty else 0

    savings = max(0, cashflow)

    # Top expenses
    top_expenses = _top_expenses(df_tx, 'Week', target_week, 5)

    # Categories with comparison
    categories = _category_comparison(df_tx, 'Week', target_week, prev_week, 10)

    # Merchants
    merchants = _merchant_breakdown(df_tx, 'Week', target_week, 10)
    merchants_by_count = pd.DataFrame()
    df_r_w = _filter_real(df_tx)
    df_w = df_r_w[(df_r_w['Week'] == target_week) & (df_r_w['Type'] == 'expense')] if not df_r_w.empty else pd.DataFrame()
    if not df_w.empty:
        merchants_by_count = df_w.groupby('Merchant').size().reset_index(name='TxCount').sort_values('TxCount', ascending=False).head(5)

    # Pockets
    pockets = _pocket_summary(poc_docs)

    # Account balances
    accounts = _account_balances(acc_docs)

    report = {
        'type': 'weekly',
        'period': target_week,
        'prev_period': prev_week,
        # KPIs
        'income': income,
        'expense': expense,
        'cashflow': cashflow,
        'savings': savings,
        'tx_count': tx_count,
        'prev_tx_count': prev_tx_count,
        # Deltas
        'income_change': _safe_pct_change(income, prev_inc),
        'expense_change': _safe_pct_change(expense, prev_exp),
        'cashflow_change': _safe_pct_change(cashflow, prev_cf),
        # Sections
        'top_expenses': top_expenses,
        'categories': categories,
        'merchants': merchants,
        'merchants_by_count': merchants_by_count,
        'pockets': pockets,
        'accounts': accounts,
    }

    report['insights'] = _weekly_insights(report)
    return report


# ═════════════════════════════════════════════════════════════════════════════
# 2. MONTHLY REPORT
# ═════════════════════════════════════════════════════════════════════════════

def generate_monthly_report(df_tx, acc_docs, poc_docs, rates, target_month=None):
    """
    Generate a monthly financial report.

    Args:
        target_month: Month string like '2026-08'. If None, uses current month.

    Returns:
        dict with all report sections
    """
    if target_month is None:
        target_month = datetime.now().strftime('%Y-%m')

    prev_month = _get_prev_month(target_month)
    year_str = target_month[:4]

    # ── Cashflow ──
    income, expense, cashflow = _period_flow(df_tx, 'Month', target_month)
    prev_inc, prev_exp, prev_cf = _period_flow(df_tx, 'Month', prev_month)

    savings_rate = (cashflow / income * 100) if income > 0 else 0.0

    # ── Net Worth (reconstructed at end of each month) ──
    # Calculate the last day of the target month
    dt_target_start = datetime.strptime(target_month + '-01', '%Y-%m-%d')
    if dt_target_start.month == 12:
        dt_target_end = datetime(dt_target_start.year + 1, 1, 1) - timedelta(seconds=1)
    else:
        dt_target_end = datetime(dt_target_start.year, dt_target_start.month + 1, 1) - timedelta(seconds=1)

    personal_nw = _net_worth_at_period_end(df_tx, acc_docs, dt_target_end)

    # Previous month end
    dt_prev_start = datetime.strptime(prev_month + '-01', '%Y-%m-%d')
    if dt_prev_start.month == 12:
        dt_prev_end = datetime(dt_prev_start.year + 1, 1, 1) - timedelta(seconds=1)
    else:
        dt_prev_end = datetime(dt_prev_start.year, dt_prev_start.month + 1, 1) - timedelta(seconds=1)

    prev_nw = _net_worth_at_period_end(df_tx, acc_docs, dt_prev_end)
    nw_change_pct = _safe_pct_change(personal_nw, prev_nw) if prev_nw != 0 else 0.0

    # YTD: net worth at end of previous December vs now
    jan1 = datetime(int(year_str), 1, 1) - timedelta(seconds=1)
    jan_nw = _net_worth_at_period_end(df_tx, acc_docs, jan1)
    nw_ytd_change_pct = _safe_pct_change(personal_nw, jan_nw) if jan_nw != 0 else 0.0

    # ── Accounts ──
    accounts = _account_balances(acc_docs)

    # ── Pockets ──
    pockets = _pocket_summary(poc_docs)

    # ── Categories vs previous month ──
    categories = _category_comparison(df_tx, 'Month', target_month, prev_month, 10)

    # ── Categories vs 12-month average ──
    categories_vs_avg = pd.DataFrame()
    df_r = _filter_real(df_tx)
    if not df_r.empty:
        # Get last 12 months
        dt_target = datetime.strptime(target_month + '-01', '%Y-%m-%d')
        months_12 = []
        for i in range(1, 13):
            m = (dt_target.replace(day=1) - timedelta(days=1))
            dt_target = m
            months_12.append(m.strftime('%Y-%m'))

        df_12 = df_r[(df_r['Month'].isin(months_12)) & (df_r['Type'] == 'expense')]
        if not df_12.empty:
            avg_by_cat = df_12.groupby('Category')['AmountBase'].sum() / len(set(df_12['Month']))
            curr_cats = _category_breakdown(df_tx, 'Month', target_month, 10)
            if not curr_cats.empty:
                curr_cats['AvgAmount'] = curr_cats['Category'].map(lambda c: avg_by_cat.get(c, 0))
                curr_cats['VsAvgPct'] = curr_cats.apply(
                    lambda r: _safe_pct_change(r['Amount'], r['AvgAmount']), axis=1)
                categories_vs_avg = curr_cats

    # ── Merchants ──
    merchants = _merchant_breakdown(df_tx, 'Month', target_month, 10)

    # ── Top expenses ──
    top_expenses = _top_expenses(df_tx, 'Month', target_month, 5)

    # ── Cashflow trend (last 6 months) ──
    cashflow_trend = []
    dt_cursor = datetime.strptime(target_month + '-01', '%Y-%m-%d')
    for i in range(5, -1, -1):
        m = dt_cursor - timedelta(days=30 * i)
        m_str = m.strftime('%Y-%m')
        m_inc, m_exp, m_cf = _period_flow(df_tx, 'Month', m_str)
        cashflow_trend.append({'Month': m_str, 'Income': m_inc, 'Expense': m_exp, 'Cashflow': m_cf})
    cashflow_trend_df = pd.DataFrame(cashflow_trend)

    # ── TX count ──
    tx_count = len(df_r[df_r['Month'] == target_month]) if not df_r.empty else 0

    report = {
        'type': 'monthly',
        'period': target_month,
        'prev_period': prev_month,
        # Net Worth
        'net_worth': personal_nw,
        'net_worth_change_pct': nw_change_pct,
        'net_worth_ytd_change_pct': nw_ytd_change_pct,
        # Cashflow
        'income': income,
        'expense': expense,
        'cashflow': cashflow,
        'prev_cashflow': prev_cf,
        'savings_rate': savings_rate,
        'tx_count': tx_count,
        # Deltas
        'income_change': _safe_pct_change(income, prev_inc),
        'expense_change': _safe_pct_change(expense, prev_exp),
        # Sections
        'accounts': accounts,
        'pockets': pockets,
        'categories': categories,
        'categories_vs_avg': categories_vs_avg,
        'merchants': merchants,
        'top_expenses': top_expenses,
        'cashflow_trend': cashflow_trend_df,
    }

    report['insights'] = _monthly_insights(report)
    return report


# ═════════════════════════════════════════════════════════════════════════════
# 3. QUARTERLY REPORT
# ═════════════════════════════════════════════════════════════════════════════

def generate_quarterly_report(df_tx, acc_docs, poc_docs, rates, target_quarter=None):
    """
    Generate a quarterly strategic financial report.

    Args:
        target_quarter: Quarter string like '2026-Q3'. If None, uses current quarter.

    Returns:
        dict with all report sections
    """
    if target_quarter is None:
        now = datetime.now()
        target_quarter = f"{now.year}-Q{(now.month - 1) // 3 + 1}"

    prev_quarter = _get_prev_quarter(target_quarter)
    year_str = target_quarter[:4]

    # ── Cashflow ──
    income, expense, cashflow = _period_flow(df_tx, 'Quarter', target_quarter)
    prev_inc, prev_exp, prev_cf = _period_flow(df_tx, 'Quarter', prev_quarter)

    # ── Net Worth (reconstructed at end of quarter) ──
    year, q = int(target_quarter.split('-Q')[0]), int(target_quarter.split('-Q')[1])
    q_end_month = q * 3
    if q_end_month == 12:
        dt_q_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        dt_q_end = datetime(year, q_end_month + 1, 1) - timedelta(seconds=1)

    personal_nw = _net_worth_at_period_end(df_tx, acc_docs, dt_q_end)

    # Previous quarter end
    prev_y, prev_q = int(prev_quarter.split('-Q')[0]), int(prev_quarter.split('-Q')[1])
    prev_q_end_month = prev_q * 3
    if prev_q_end_month == 12:
        dt_pq_end = datetime(prev_y + 1, 1, 1) - timedelta(seconds=1)
    else:
        dt_pq_end = datetime(prev_y, prev_q_end_month + 1, 1) - timedelta(seconds=1)

    prev_nw = _net_worth_at_period_end(df_tx, acc_docs, dt_pq_end)
    nw_change_pct = _safe_pct_change(personal_nw, prev_nw)

    # YTD: end of previous December
    jan1 = datetime(year, 1, 1) - timedelta(seconds=1)
    jan_nw = _net_worth_at_period_end(df_tx, acc_docs, jan1)
    nw_ytd_change_pct = _safe_pct_change(personal_nw, jan_nw)

    # ── Asset Allocation ──
    asset_alloc = []
    for a in acc_docs:
        if a.get('isArchived') or a.get('isBusinessAccount'):
            continue
        a_type = a.get('type', 'bank').capitalize()
        asset_alloc.append({'Type': a_type, 'Balance': a.get('balanceInBase', 0)})

    asset_df = pd.DataFrame(asset_alloc)
    if not asset_df.empty:
        asset_df = asset_df.groupby('Type')['Balance'].sum().reset_index()
        total = asset_df['Balance'].sum()
        asset_df['Pct'] = (asset_df['Balance'] / total * 100) if total > 0 else 0
    else:
        asset_df = pd.DataFrame(columns=['Type', 'Balance', 'Pct'])

    # ── Savings trend (by month within quarter) ──
    year, q = int(target_quarter.split('-Q')[0]), int(target_quarter.split('-Q')[1])
    q_months = [f"{year}-{m:02d}" for m in range((q - 1) * 3 + 1, q * 3 + 1)]

    savings_trend = []
    for m_str in q_months:
        m_inc, m_exp, m_cf = _period_flow(df_tx, 'Month', m_str)
        sr = (m_cf / m_inc * 100) if m_inc > 0 else 0
        savings_trend.append({'Month': m_str, 'Income': m_inc, 'Expense': m_exp,
                              'Cashflow': m_cf, 'SavingsRate': sr})
    savings_trend_df = pd.DataFrame(savings_trend)

    avg_savings_rate = savings_trend_df['SavingsRate'].mean() if not savings_trend_df.empty else 0

    # ── Categories ──
    categories = _category_comparison(df_tx, 'Quarter', target_quarter, prev_quarter, 10)

    # ── Pockets / Goals ──
    pockets = _pocket_summary(poc_docs)

    # ── Cashflow trend (last 4 quarters) ──
    cashflow_trend = []
    for i in range(3, -1, -1):
        q_val = q - i
        y_val = year
        while q_val <= 0:
            q_val += 4
            y_val -= 1
        q_str = f"{y_val}-Q{q_val}"
        q_inc, q_exp, q_cf = _period_flow(df_tx, 'Quarter', q_str)
        cashflow_trend.append({'Quarter': q_str, 'Income': q_inc, 'Expense': q_exp, 'Cashflow': q_cf})
    cashflow_trend_df = pd.DataFrame(cashflow_trend)

    report = {
        'type': 'quarterly',
        'period': target_quarter,
        'prev_period': prev_quarter,
        # Net Worth
        'net_worth': personal_nw,
        'net_worth_change_pct': nw_change_pct,
        'net_worth_ytd_change_pct': nw_ytd_change_pct,
        # Cashflow
        'income': income,
        'expense': expense,
        'cashflow': cashflow,
        'savings_rate_avg': avg_savings_rate,
        'avg_savings_rate': avg_savings_rate,
        # Deltas
        'income_change': _safe_pct_change(income, prev_inc),
        'expense_change': _safe_pct_change(expense, prev_exp),
        # Sections
        'asset_allocation': asset_df,
        'savings_trend': savings_trend_df,
        'categories': categories,
        'pockets': pockets,
        'cashflow_trend': cashflow_trend_df,
    }

    report['insights'] = _quarterly_insights(report)
    return report


# ═════════════════════════════════════════════════════════════════════════════
# TEXT FORMATTER (for Pushbullet notifications)
# ═════════════════════════════════════════════════════════════════════════════

def format_weekly_notification(report):
    """Format weekly report as short plain text for push notification."""
    lines = [f"📊 FinSpace Weekly — {report['period']}"]
    lines.append("")
    lines.append(f"Cashflow: {report['cashflow']:+,.0f} Ft")
    lines.append(f"Bevétel: {report['income']:,.0f} Ft | Kiadás: {report['expense']:,.0f} Ft")
    lines.append(f"Tranzakciók: {report['tx_count']} db")
    lines.append("")

    cats = report.get('categories', pd.DataFrame())
    if not cats.empty:
        top = cats.iloc[0]
        lines.append(f"Top kategória: {top['Category']} ({top['Amount']:,.0f} Ft)")

    top_exp = report.get('top_expenses', pd.DataFrame())
    if not top_exp.empty:
        t = top_exp.iloc[0]
        lines.append(f"Legnagyobb kiadás: {t['Merchant']} ({t['AmountBase']:,.0f} Ft)")

    lines.append("")
    for ins in report.get('insights', [])[:3]:
        lines.append(f"⚡ {ins}")

    lines.append("")
    lines.append("Nyisd meg a FinSpace Reports oldalt a részletekért.")

    return "\n".join(lines)

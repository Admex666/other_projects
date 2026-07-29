import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta

# ─── Currency Helpers ─────────────────────────────────────────────────────────
def convert_val(amt, from_curr, to_curr, rates):
    if not amt: return 0.0
    if from_curr == to_curr: return float(amt)
    eur = amt / rates[from_curr] if from_curr != 'EUR' and from_curr in rates else amt
    if to_curr == 'EUR': return eur
    return eur * rates[to_curr] if to_curr in rates else eur

def prepare_tx_dataframe(transactions, acc_map, cat_map, poc_map, rates):
    """Converts MongoDB transaction docs into a rich Pandas DataFrame for BI analysis."""
    rows = []
    for tx in transactions:
        d = tx.get('date')
        if not d: continue
        dt = d if isinstance(d, datetime) else datetime.combine(d, datetime.min.time()) if isinstance(d, date) else pd.to_datetime(d)

        curr = tx.get('currency', 'HUF')
        amt  = float(tx.get('amount', 0.0))
        amt_base = tx.get('amountInBaseCurrency')
        if not amt_base:
            amt_base = convert_val(amt, curr, 'HUF', rates)
        else:
            amt_base = float(amt_base)

        cat_name = cat_map.get(str(tx.get('categoryId', '')), 'Egyéb')
        acc_name = acc_map.get(str(tx.get('accountId', '')), 'Ismeretlen')
        poc_name = poc_map.get(str(tx.get('virtualPocketId', '')), 'Nincs zseb')
        merchant = tx.get('merchant') or tx.get('note') or cat_name

        rows.append({
            '_id': str(tx['_id']),
            'Date': dt,
            'Year': dt.year,
            'Quarter': f"{dt.year}-Q{(dt.month-1)//3 + 1}",
            'Month': dt.strftime('%Y-%m'),
            'YearMonth': dt.strftime('%Y-%m'),
            'Week': f"{dt.year}-W{dt.isocalendar()[1]:02d}",
            'Day': dt.strftime('%Y-%m-%d'),
            'DayOfWeek': dt.strftime('%A'),
            'Type': tx.get('type', 'expense'),
            'Amount': amt,
            'Currency': curr,
            'AmountBase': amt_base,
            'Account': acc_name,
            'Category': cat_name,
            'Pocket': poc_name,
            'Merchant': merchant,
            'Note': tx.get('note', ''),
            'Owner': 'Adam',
            'IsInternal': bool(tx.get('isInternalAllocation')),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=['_id', 'Date', 'Year', 'Quarter', 'Month', 'YearMonth', 'Week', 'Day',
                                     'DayOfWeek', 'Type', 'Amount', 'Currency', 'AmountBase', 'Account',
                                     'Category', 'Pocket', 'Merchant', 'Note', 'Owner', 'IsInternal'])
    return df

# ─── 1. Executive Dashboard Analytics ──────────────────────────────────────────
def get_executive_kpis(df_tx, accounts, pockets, rates):
    now = datetime.now()
    cy, cm = now.year, now.month
    curr_month_str = now.strftime('%Y-%m')

    # Accounts
    pers_accounts_base = 0.0
    for acc in accounts:
        if acc.get('isArchived') or acc.get('isBusinessAccount'): continue
        acc_curr = acc.get('currency', 'HUF')
        # Balance in HUF
        bal = acc.get('balanceInBase', 0)
        pers_accounts_base += bal

    # Pockets
    total_pocket_base = sum(max(0.0, p.get('currentAmountInBase', p.get('currentAmount', 0))) for p in pockets)

    free_cash = pers_accounts_base - total_pocket_base

    # Current Month Flow (excluding internal transfers)
    df_real = df_tx[~df_tx['IsInternal']] if not df_tx.empty else df_tx
    df_m = df_real[df_real['Month'] == curr_month_str] if not df_real.empty else df_real

    m_inc = df_m[df_m['Type'] == 'income']['AmountBase'].sum() if not df_m.empty else 0.0
    m_exp = df_m[df_m['Type'] == 'expense']['AmountBase'].sum() if not df_m.empty else 0.0
    m_cashflow = m_inc - m_exp
    savings_rate = (m_cashflow / m_inc * 100) if m_inc > 0 else 0.0

    return {
        'net_worth': pers_accounts_base,
        'free_cash': free_balance if 'free_balance' in locals() else free_cash,
        'pockets_total': total_pocket_base,
        'm_income': m_inc,
        'm_expense': m_exp,
        'm_cashflow': m_cashflow,
        'savings_rate': savings_rate,
    }

# ─── 3. Pivot Builder Engine ──────────────────────────────────────────────────
def build_pivot_table(df_tx, rows_col, cols_col, val_col, agg_func='sum'):
    if df_tx.empty:
        return pd.DataFrame()
    pivot = pd.pivot_table(
        df_tx,
        index=rows_col,
        columns=cols_col,
        values=val_col,
        aggfunc=agg_func,
        fill_value=0
    )
    return pivot

# ─── 5. Merchant Explorer Analytics ──────────────────────────────────────────
def get_merchant_stats(df_tx, merchant_name):
    df_m = df_tx[(df_tx['Merchant'] == merchant_name) & (df_tx['Type'] == 'expense')]
    if df_m.empty:
        return None

    total_spent = df_m['AmountBase'].sum()
    tx_count    = len(df_m)
    avg_basket  = df_m['AmountBase'].mean()
    max_purchase= df_m.loc[df_m['AmountBase'].idxmax()]
    last_purchase= df_m.sort_values('Date', ascending=False).iloc[0]

    # Peak Month & Day
    month_sums = df_m.groupby('Month')['AmountBase'].sum()
    peak_month = month_sums.idxmax() if not month_sums.empty else 'N/A'

    day_counts = df_m.groupby('DayOfWeek')['AmountBase'].count()
    peak_day   = day_counts.idxmax() if not day_counts.empty else 'N/A'

    categories = df_m['Category'].unique().tolist()

    # Yearly breakdown
    yearly = df_m.groupby('Year')['AmountBase'].sum().reset_index()

    return {
        'total_spent': total_spent,
        'tx_count': tx_count,
        'avg_basket': avg_basket,
        'max_purchase': max_purchase,
        'last_purchase': last_purchase,
        'peak_month': peak_month,
        'peak_day': peak_day,
        'categories': categories,
        'yearly': yearly,
        'df': df_m
    }

# ─── 6. Category Explorer Analytics ──────────────────────────────────────────
def get_category_stats(df_tx, cat_name):
    df_c = df_tx[(df_tx['Category'] == cat_name) & (df_tx['Type'] == 'expense')]
    if df_c.empty:
        return None

    total_spent  = df_c['AmountBase'].sum()
    monthly_sums = df_c.groupby('Month')['AmountBase'].sum()
    m_avg        = monthly_sums.mean() if not monthly_sums.empty else 0.0
    median_val   = df_c['AmountBase'].median()
    largest_tx   = df_c.loc[df_c['AmountBase'].idxmax()]

    # Forecast for next month based on 3-month moving average
    last_3_m = monthly_sums.tail(3)
    forecast_val = last_3_m.mean() if not last_3_m.empty else m_avg

    merchants_breakdown = df_c.groupby('Merchant')['AmountBase'].sum().reset_index().sort_values('AmountBase', ascending=False)
    accounts_breakdown  = df_c.groupby('Account')['AmountBase'].sum().reset_index().sort_values('AmountBase', ascending=False)

    return {
        'total_spent': total_spent,
        'monthly_avg': m_avg,
        'median': median_val,
        'largest_tx': largest_tx,
        'forecast': forecast_val,
        'merchants': merchants_breakdown,
        'accounts': accounts_breakdown,
        'monthly_sums': monthly_sums.reset_index(),
        'df': df_c
    }

# ─── 7. Budget Center Forecasting ────────────────────────────────────────────
def get_budget_insights(df_tx, category_budgets):
    """
    category_budgets: list of dicts {'Category': name, 'Limit': amount}
    Calculates current spend, run-rate forecast, and overspend warnings.
    """
    now = datetime.now()
    cm_str = now.strftime('%Y-%m')
    day_of_month = now.day
    days_in_month = 31 # approximate

    df_m = df_tx[(df_tx['Month'] == cm_str) & (df_tx['Type'] == 'expense')]

    results = []
    for b in category_budgets:
        cat = b['Category']
        limit = float(b['Limit'])
        if limit <= 0: continue

        spent = df_m[df_m['Category'] == cat]['AmountBase'].sum() if not df_m.empty else 0.0
        pct = (spent / limit) * 100

        # Forecast
        daily_rate = spent / day_of_month if day_of_month > 0 else 0
        forecast_end = daily_rate * days_in_month
        forecast_pct = (forecast_end / limit) * 100
        overspend_amt = max(0.0, forecast_end - limit)

        results.append({
            'Category': cat,
            'Limit': limit,
            'Spent': spent,
            'Pct': pct,
            'ForecastEnd': forecast_end,
            'ForecastPct': forecast_pct,
            'Overspend': overspend_amt
        })

    return results

# ─── 8. Pocket Center ETA Forecast ───────────────────────────────────────────
def get_pocket_etas(pockets, df_tx):
    """Calculates ETA and monthly contributions for each virtual pocket."""
    now = datetime.now()
    results = []
    for p in pockets:
        name = p.get('name', 'Zseb')
        target = float(p.get('targetAmount', 0.0))
        current = float(p.get('currentAmountInBase', p.get('currentAmount', 0.0)))
        poc_id = str(p['_id'])

        # Monthly contribution over last 3 months
        df_p = df_tx[df_tx['Pocket'] == name]
        if not df_p.empty:
            last_3 = df_p.groupby('Month')['AmountBase'].sum().tail(3)
            m_contrib = last_3.mean() if not last_3.empty else 0.0
        else:
            m_contrib = 0.0

        remaining = max(0.0, target - current)
        months_needed = (remaining / m_contrib) if m_contrib > 0 else 999

        if months_needed < 999:
            eta_date = now + timedelta(days=int(months_needed * 30.5))
            eta_str  = eta_date.strftime('%Y-%m')
        else:
            eta_str = 'Nincs aktív megtakarítás'

        results.append({
            'Name': name,
            'Current': current,
            'Target': target,
            'MonthlyContrib': m_contrib,
            'MonthsNeeded': months_needed,
            'ETA': eta_str,
            'Pct': (current / target * 100) if target > 0 else 100.0
        })
    return results

# ─── 10. Compare Mode Engine ─────────────────────────────────────────────────
def compare_periods(df_tx, group1_filter, group2_filter, dimension='Category'):
    """
    Compares two filtered subsets of transactions (e.g. 2025 vs 2026 or OTP vs Revolut)
    by a chosen dimension (Category, Merchant, Account).
    """
    df1 = df_tx[group1_filter & (df_tx['Type'] == 'expense')] if not df_tx.empty else pd.DataFrame()
    df2 = df_tx[group2_filter & (df_tx['Type'] == 'expense')] if not df_tx.empty else pd.DataFrame()

    g1 = df1.groupby(dimension)['AmountBase'].sum() if not df1.empty else pd.Series()
    g2 = df2.groupby(dimension)['AmountBase'].sum() if not df2.empty else pd.Series()

    all_keys = list(set(g1.index).union(set(g2.index)))
    comp_data = []

    for k in all_keys:
        val1 = float(g1.get(k, 0.0))
        val2 = float(g2.get(k, 0.0))
        diff = val2 - val1
        pct_change = ((val2 - val1) / val1 * 100) if val1 > 0 else (100.0 if val2 > 0 else 0.0)

        comp_data.append({
            dimension: k,
            'Period_A': val1,
            'Period_B': val2,
            'Difference': diff,
            'PctChange': pct_change
        })

    df_comp = pd.DataFrame(comp_data)
    if not df_comp.empty:
        df_comp = df_comp.sort_values('Period_B', ascending=False)
    return df_comp

# ─── 11. Automated Insights Generator ────────────────────────────────────────
def generate_insights(df_tx, pockets):
    insights = []
    if df_tx.empty:
        return ["💡 Üdvözlünk a FinSpace-ben! Tölts fel tranzakciókat az elemzésekhez."]

    now = datetime.now()
    cm_str = now.strftime('%Y-%m')
    lm_date = now.replace(day=1) - timedelta(days=1)
    lm_str  = lm_date.strftime('%Y-%m')

    df_exp = df_tx[df_tx['Type'] == 'expense']

    # 1. Top Category Change (Current vs Last Month)
    cm_cat = df_exp[df_exp['Month'] == cm_str].groupby('Category')['AmountBase'].sum()
    lm_cat = df_exp[df_exp['Month'] == lm_str].groupby('Category')['AmountBase'].sum()

    for cat, val in cm_cat.items():
        lm_val = lm_cat.get(cat, 0.0)
        if lm_val > 0:
            pct = ((val - lm_val) / lm_val) * 100
            if pct > 20 and val > 10000:
                insights.append(f"💡 Ebben a hónapban **{pct:.0f}%-kal többet költöttél** erre: **{cat}** (összesen: {val:,.0f} Ft).")

    # 2. Largest Recent Expense
    if not df_exp.empty:
        top_tx = df_exp.loc[df_exp['AmountBase'].idxmax()]
        insights.append(f"💡 Az eddigi legnagyobb kiadásod: **{top_tx['AmountBase']:,.0f} Ft** ({top_tx['Category']} - {top_tx['Merchant']}).")

    # 3. Savings Rate
    inc_sum = df_tx[(df_tx['Type'] == 'income') & (df_tx['Month'] == cm_str)]['AmountBase'].sum()
    exp_sum = df_tx[(df_tx['Type'] == 'expense') & (df_tx['Month'] == cm_str)]['AmountBase'].sum()
    if inc_sum > 0:
        s_rate = (inc_sum - exp_sum) / inc_sum * 100
        insights.append(f"💡 Az e havi **megtakarítási rátád: {s_rate:.1f}%**.")

    # 4. Pocket goal insights
    for p in pockets:
        tgt = float(p.get('targetAmount', 0))
        cur = float(p.get('currentAmountInBase', p.get('currentAmount', 0)))
        if tgt > 0 and cur < tgt:
            pct = (cur / tgt) * 100
            if pct >= 80:
                insights.append(f"🎯 Már **{pct:.0f}%-on állsz** a(z) **{p.get('name')}** célodnál!")

    if not insights:
        insights.append("💡 Minden pénzügyi mutatód a normál tartományban mozog.")

    return insights

import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os
import sys

# Import BI analytics engine
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from bi_analytics import (
    convert_val, prepare_tx_dataframe, get_executive_kpis, build_pivot_table,
    get_merchant_stats, get_category_stats, get_budget_insights,
    get_pocket_etas, compare_periods, generate_insights
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='FinSpace BI Suite',
    page_icon='💎',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ─── Streamlit Secrets Password Gate ──────────────────────────────────────────
def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if st.session_state['authenticated']:
        return True

    correct_password = None
    try:
        correct_password = st.secrets.get("APP_PASSWORD")
    except Exception:
        pass
    if not correct_password:
        correct_password = os.getenv("APP_PASSWORD", "adam")

    st.markdown('<div style="max-width:400px;margin:80px auto;padding:30px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;text-align:center">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#0f172a;margin-bottom:8px">🔒 FinSpace Belépés</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#64748b;font-size:0.85rem">Kérlek add meg a jelszót a pénzügyi adatok eléréséhez!</p>', unsafe_allow_html=True)
    entered_pw = st.text_input("Jelszó", type="password", key="login_password_input")
    if st.button("Belépés", type="primary", use_container_width=True):
        if entered_pw == correct_password:
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error("❌ Helytelen jelszó!")
    st.markdown('</div>', unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# ─── Light Theme Styling ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: #f1f5f9;
    padding: 6px 12px;
    border-radius: 10px;
    margin-bottom: 16px;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b;
    font-weight: 600;
    padding: 6px 16px;
    border-radius: 6px;
}
.stTabs [aria-selected="true"] {
    background: #2563eb !important;
    color: white !important;
}

/* Metric Cards */
[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
[data-testid="metric-container"] label { color: #64748b !important; font-size: 0.8rem; font-weight: 600; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #0f172a; font-size: 1.4rem; font-weight: 700; }

/* Section Headers */
.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    border-left: 4px solid #2563eb;
    padding-left: 10px;
    margin: 18px 0 10px 0;
}

/* Insight Cards */
.insight-card {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
    color: #1e3a8a;
    font-size: 0.95rem;
}

/* Buttons */
div.stButton > button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─── DB Connection ────────────────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env.local'))

MONGO_URI = None
try:
    MONGO_URI = st.secrets.get("MONGODB_URI")
except Exception:
    pass

if not MONGO_URI:
    MONGO_URI = os.getenv('MONGODB_URI')

@st.cache_resource
def get_db():
    if not MONGO_URI:
        st.error('❌ MONGODB_URI hiányzik! Kérlek állítsd be a Streamlit Cloud Secrets menüpontjában.')
        st.stop()
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Ping server to verify network connectivity
        client.admin.command('ping')
        try:    return client.get_default_database()
        except: return client.get_database('test')
    except Exception as err:
        st.error('❌ **Nem sikerült csatlakozni a MongoDB Atlas-hoz!** (Network Timeout / IP Blocked)\n\n'
                 '**Megoldás a MongoDB Atlas-on:**\n'
                 '1. Nyisd meg a [MongoDB Atlas](https://cloud.mongodb.com) felületét.\n'
                 '2. A bal oldali menüben kattints a **Network Access** lehetőségre.\n'
                 '3. Kattints az **Add IP Address** gombra.\n'
                 '4. Válaszd az **ALLOW ACCESS FROM ANYWHERE (`0.0.0.0/0`)** opciót, majd mentsd el!')
        st.stop()

def get_user():
    return get_db().users.find_one({'username': 'adam'})

@st.cache_data(ttl=30)
def load_data(user_id_str):
    db = get_db()
    uid = ObjectId(user_id_str)

    acc_docs = list(db.accounts.find({'userId': uid}))
    cat_docs = list(db.categories.find({'userId': uid}))
    poc_docs = list(db.virtualpockets.find({'owners': uid}))
    tx_docs  = list(db.transactions.find({'userId': uid}).sort('date', -1))

    rates_doc = db.exchangerates.find_one(sort=[('date', -1)])
    rates = rates_doc['rates'] if (rates_doc and 'rates' in rates_doc) else {'HUF': 390.0, 'USD': 1.1, 'EUR': 1.0, 'BGN': 1.95}

    acc_map = {str(a['_id']): a['name'] for a in acc_docs}
    cat_map = {str(c['_id']): c['name'] for c in cat_docs}
    poc_map = {str(p['_id']): p['name'] for p in poc_docs}

    # Compute account balances in base currency
    for acc in acc_docs:
        acc_id = str(acc['_id'])
        acc_curr = acc.get('currency', 'HUF')
        bal = float(acc.get('initialBalance') or 0.0)
        for tx in tx_docs:
            if tx.get('isInternalAllocation'): continue
            tx_acc    = str(tx.get('accountId', ''))
            tx_to_acc = str(tx.get('toAccountId', ''))
            tx_curr   = tx.get('currency', 'HUF')
            tx_amt    = float(tx.get('amount', 0.0))
            tx_type   = tx.get('type', '')

            if tx_acc == acc_id:
                amt_in_acc = convert_val(tx_amt, tx_curr, acc_curr, rates)
                if tx_type == 'income': bal += amt_in_acc
                elif tx_type in ['expense', 'transfer']: bal -= amt_in_acc

            if tx_to_acc == acc_id and tx_type == 'transfer':
                amt_in_acc = convert_val(tx_amt, tx_curr, acc_curr, rates)
                bal += amt_in_acc

        acc['balance'] = bal
        acc['balanceInBase'] = convert_val(bal, acc_curr, 'HUF', rates)

    # Compute pocket balances in base currency
    for poc in poc_docs:
        poc_id = str(poc['_id'])
        poc_curr = poc.get('currency', 'HUF')
        p_bal = 0.0
        for tx in tx_docs:
            if str(tx.get('virtualPocketId', '')) == poc_id:
                tx_curr = tx.get('currency', 'HUF')
                tx_amt  = float(tx.get('amount', 0.0))
                tx_type = tx.get('type', '')
                amt_in_poc = convert_val(tx_amt, tx_curr, poc_curr, rates)
                if tx_type in ['income', 'transfer']: p_bal += amt_in_poc
                elif tx_type == 'expense': p_bal -= amt_in_poc

        poc['currentAmount'] = max(0.0, p_bal)
        poc['currentAmountInBase'] = convert_val(max(0.0, p_bal), poc_curr, 'HUF', rates)

    return acc_map, acc_docs, cat_map, cat_docs, poc_map, poc_docs, tx_docs, rates

def fmt_huf(val):
    try: return f"{val:,.0f} Ft".replace(',', '\u00a0')
    except: return str(val)

TYPE_OPTIONS = ['income', 'expense', 'transfer', 'investment']
TYPE_LABELS  = {'income': '📈 Bevétel', 'expense': '📉 Kiadás',
                'transfer': '🔄 Átvezetés', 'investment': '💼 Befektetés'}
CURRENCY_OPTIONS = ['HUF', 'EUR', 'USD', 'GBP']

# ─── Transaction Form ─────────────────────────────────────────────────────────
def tx_form(user_id, acc_map, acc_docs, cat_map, cat_docs, poc_map, poc_docs,
            existing=None, key_prefix='add'):
    is_edit = existing is not None
    with st.form(key=f'{key_prefix}_form', clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        default_date = date.today()
        if is_edit and existing.get('date'):
            d = existing['date']
            default_date = d.date() if hasattr(d, 'date') else date.today()
        tx_date = c1.date_input('Dátum', value=default_date)

        type_default_idx = TYPE_OPTIONS.index(existing.get('type', 'expense')) if (is_edit and existing.get('type') in TYPE_OPTIONS) else 1
        tx_type = c2.selectbox('Típus', TYPE_OPTIONS, index=type_default_idx, format_func=lambda x: TYPE_LABELS[x])
        tx_currency = c3.selectbox('Deviza', CURRENCY_OPTIONS, index=CURRENCY_OPTIONS.index(existing.get('currency', 'HUF')) if (is_edit and existing.get('currency') in CURRENCY_OPTIONS) else 0)

        c4, c5 = st.columns(2)
        tx_amount = c4.number_input('Összeg', min_value=0.0, step=100.0, value=float(existing.get('amount', 0)) if is_edit else 0.0)

        acc_names = [d['name'] for d in acc_docs]
        acc_default = 0
        if is_edit:
            ex_acc = acc_map.get(str(existing.get('accountId', '')), '')
            if ex_acc in acc_names: acc_default = acc_names.index(ex_acc)
        tx_account = c5.selectbox('Számla', acc_names, index=acc_default)

        c6, c7 = st.columns(2)
        cat_names = ['(nincs)'] + [d['name'] for d in cat_docs]
        cat_default = 0
        if is_edit:
            ex_cat = cat_map.get(str(existing.get('categoryId', '')), '')
            if ex_cat in cat_names: cat_default = cat_names.index(ex_cat)
        tx_category = c6.selectbox('Kategória', cat_names, index=cat_default)

        poc_names = ['(nincs)'] + [d['name'] for d in poc_docs]
        poc_default = 0
        if is_edit:
            ex_poc = poc_map.get(str(existing.get('virtualPocketId', '')), '')
            if ex_poc in poc_names: poc_default = poc_names.index(ex_poc)
        tx_pocket = c7.selectbox('Zseb', poc_names, index=poc_default)

        to_acc_name = None
        if tx_type == 'transfer':
            to_acc_name = st.selectbox('Cél Számla', acc_names)

        tx_note = st.text_input('Megjegyzés', value=existing.get('note', '') if is_edit else '')
        submitted = st.form_submit_button('💾 Mentés', type='primary', use_container_width=True)

    if submitted:
        acc_id = next((d['_id'] for d in acc_docs if d['name'] == tx_account), None)
        cat_id = next((d['_id'] for d in cat_docs if d['name'] == tx_category), None)
        poc_id = next((d['_id'] for d in poc_docs if d['name'] == tx_pocket), None)
        to_acc_id = next((d['_id'] for d in acc_docs if d['name'] == to_acc_name), None) if to_acc_name else None

        return {
            'userId':          user_id,
            'date':            datetime.combine(tx_date, datetime.min.time()),
            'type':            tx_type,
            'amount':          tx_amount,
            'currency':        tx_currency,
            'amountInBaseCurrency': tx_amount,
            'exchangeRate':    1,
            'accountId':       acc_id,
            'toAccountId':     to_acc_id,
            'categoryId':      cat_id,
            'virtualPocketId': poc_id,
            'note':            tx_note,
            'isBusinessTransaction': False,
        }
    return None

# ─── Initialize User & Data ───────────────────────────────────────────────────
user = get_user()
if not user:
    st.error('Adam felhasználó nem található a MongoDB-ben!')
    st.stop()

user_id = user['_id']
user_id_str = str(user_id)
db = get_db()

acc_map, acc_docs, cat_map, cat_docs, poc_map, poc_docs, tx_docs, rates = load_data(user_id_str)
df_tx = prepare_tx_dataframe(tx_docs, acc_map, cat_map, poc_map, rates)

# ─── Sidebar Navigation & Drill-Down State ─────────────────────────────────────
if 'page' not in st.session_state:
    st.session_state['page'] = '1. Executive Dashboard'

NAV_OPTIONS = [
    '1. Executive Dashboard',
    '2. Spending Explorer ⭐',
    '3. Pivot Builder',
    '4. Time Explorer',
    '5. Merchant Explorer',
    '6. Category Explorer ⭐',
    '7. Budget Center',
    '8. Pocket Center',
    '9. Net Worth Explorer',
    '10. Compare Mode ⭐',
    '11. Automated Insights',
    '📋 Tranzakciók (CRUD)',
    '⚙️ Beállítások',
]

with st.sidebar:
    st.title('💎 FinSpace BI')
    selected_page = st.selectbox('Navigáció', NAV_OPTIONS,
                                 index=NAV_OPTIONS.index(st.session_state['page']) if st.session_state['page'] in NAV_OPTIONS else 0)
    st.session_state['page'] = selected_page
    st.markdown('---')
    if st.button('🔒 Kijelentkezés', use_container_width=True):
        st.session_state['authenticated'] = False
        st.rerun()
    st.caption('💡 Kattints bármelyik mutatón vagy grafikonton a lefúráshoz!')

page = st.session_state['page']

def navigate_to(target_page, **kwargs):
    st.session_state['page'] = target_page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# 1. EXECUTIVE DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
if page == '1. Executive Dashboard':
    st.markdown('<h2 style="color:#0f172a">📊 Executive Dashboard</h2>', unsafe_allow_html=True)

    kpis = get_executive_kpis(df_tx, acc_docs, poc_docs, rates)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric('Szabad Egyenleg', fmt_huf(kpis['free_cash']), help='Személyes vagyon mínusz zsebekben lekötött összeg')
    c2.metric('Személyes Vagyon', fmt_huf(kpis['net_worth']))
    c3.metric('Megtakarítási Ráta', f"{kpis['savings_rate']:.1f}%")
    c4.metric('Havi Bevétel', fmt_huf(kpis['m_income']))
    c5.metric('Havi Kiadás', fmt_huf(kpis['m_expense']))
    c6.metric('Havi Cashflow', fmt_huf(kpis['m_cashflow']), delta=fmt_huf(kpis['m_cashflow']))

    st.markdown('---')
    col_chart, col_drill = st.columns([7, 5])

    with col_chart:
        st.markdown('<div class="section-title">Havi Trendek & Cashflow</div>', unsafe_allow_html=True)
        now = datetime.now()
        df_real = df_tx[~df_tx['IsInternal']]
        months_data = []
        for offset in range(5, -1, -1):
            mo = now.month - offset
            yr = now.year
            while mo <= 0: mo += 12; yr -= 1
            m_str = f'{yr}-{mo:02d}'
            df_m = df_real[df_real['Month'] == m_str]
            inc = df_m[df_m['Type'] == 'income']['AmountBase'].sum() if not df_m.empty else 0
            exp = df_m[df_m['Type'] == 'expense']['AmountBase'].sum() if not df_m.empty else 0
            months_data.append({'Month': m_str, 'Bevétel': inc, 'Kiadás': exp, 'Cashflow': inc - exp})

        df_m_trend = pd.DataFrame(months_data)
        fig = go.Figure()
        fig.add_bar(x=df_m_trend['Month'], y=df_m_trend['Bevétel'], name='Bevétel', marker_color='#10b981')
        fig.add_bar(x=df_m_trend['Month'], y=df_m_trend['Kiadás'],  name='Kiadás',  marker_color='#ef4444')
        fig.add_scatter(x=df_m_trend['Month'], y=df_m_trend['Cashflow'], name='Cashflow', mode='lines+markers', line=dict(color='#2563eb', width=2))
        fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='#0f172a', barmode='group', margin=dict(t=20, b=20, l=0, r=0), height=320)
        fig.update_xaxes(gridcolor='#e2e8f0'); fig.update_yaxes(gridcolor='#e2e8f0')
        st.plotly_chart(fig, use_container_width=True)

    with col_drill:
        st.markdown('<div class="section-title">🔍 Gyors Lefúrás Kategóriákra</div>', unsafe_allow_html=True)
        df_exp = df_tx[(df_tx['Type'] == 'expense') & (~df_tx['IsInternal'])]
        curr_m = datetime.now().strftime('%Y-%m')
        df_m_exp = df_exp[df_exp['Month'] == curr_m]

        if not df_m_exp.empty:
            cat_sum = df_m_exp.groupby('Category')['AmountBase'].sum().reset_index().sort_values('AmountBase', ascending=False)
            for _, r in cat_sum.head(5).iterrows():
                cc1, cc2 = st.columns([3, 1])
                cc1.write(f"**{r['Category']}**: {fmt_huf(r['AmountBase'])}")
                if cc2.button('Lefúrás ➔', key=f'drill_dash_{r["Category"]}'):
                    navigate_to('6. Category Explorer ⭐', sel_cat=r['Category'])
        else:
            st.info('Nincs kiadás az aktuális hónapban.')

# ═════════════════════════════════════════════════════════════════════════════
# 2. SPENDING EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '2. Spending Explorer ⭐':
    st.markdown('<h2 style="color:#0f172a">🔍 Spending Explorer</h2>', unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    sel_acc  = fc1.multiselect('Számla', df_tx['Account'].unique().tolist())
    sel_cat  = fc2.multiselect('Kategória', df_tx['Category'].unique().tolist(),
                               default=[st.session_state.get('sel_cat')] if st.session_state.get('sel_cat') in df_tx['Category'].unique() else None)
    sel_type = fc3.multiselect('Típus', ['expense', 'income', 'transfer'], default=['expense'])

    df_filt = df_tx.copy()
    if sel_acc:  df_filt = df_filt[df_filt['Account'].isin(sel_acc)]
    if sel_cat:  df_filt = df_filt[df_filt['Category'].isin(sel_cat)]
    if sel_type: df_filt = df_filt[df_filt['Type'].isin(sel_type)]

    st.markdown('<div class="section-title">Hierarchikus Költési Fa (Category ➔ Merchant ➔ Tranzakció)</div>', unsafe_allow_html=True)

    if not df_filt.empty:
        df_tree = df_filt[df_filt['Type'] == 'expense'].groupby(['Category', 'Merchant'])['AmountBase'].sum().reset_index()
        fig_tree = px.treemap(df_tree, path=['Category', 'Merchant'], values='AmountBase',
                              color='AmountBase', color_continuous_scale='Blues')
        fig_tree.update_layout(paper_bgcolor='white', font_color='#0f172a', margin=dict(t=10, b=10, l=0, r=0), height=400)
        st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown('<div class="section-title">Szűrt Tranzakciók Listája</div>', unsafe_allow_html=True)
        st.dataframe(df_filt[['Date', 'Type', 'AmountBase', 'Category', 'Merchant', 'Account', 'Note']], use_container_width=True)
    else:
        st.info('Nincs találat a beállított szűrőkre.')

# ═════════════════════════════════════════════════════════════════════════════
# 3. PIVOT BUILDER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '3. Pivot Builder':
    st.markdown('<h2 style="color:#0f172a">🎲 Pivot Builder</h2>', unsafe_allow_html=True)
    st.write('Készíts teljesen egyedi Pivot táblát tetszőleges dimenziókkal!')

    pc1, pc2, pc3, pc4 = st.columns(4)
    row_dim = pc1.selectbox('Sorok (Index)', ['Category', 'Merchant', 'Account', 'Pocket', 'Owner', 'Type'], index=0)
    col_dim = pc2.selectbox('Oszlopok', ['Month', 'Year', 'Quarter', 'DayOfWeek', 'Type', 'Account'], index=0)
    val_dim = pc3.selectbox('Érték', ['AmountBase', 'Amount'], index=0)
    agg_fn  = pc4.selectbox('Összegzés', ['sum', 'mean', 'count', 'max', 'min'], index=0)

    if not df_tx.empty:
        pivot_df = build_pivot_table(df_tx, row_dim, col_dim, val_dim, agg_fn)
        st.dataframe(pivot_df.style.background_gradient(cmap='Blues'), use_container_width=True)

        csv = pivot_df.to_csv().encode('utf-8')
        st.download_button('📥 Pivot Letöltése CSV-ként', data=csv, file_name='finspace_pivot.csv', mime='text/csv')
    else:
        st.info('Nincs adat a pivot generálásához.')

# ═════════════════════════════════════════════════════════════════════════════
# 4. TIME EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '4. Time Explorer':
    st.markdown('<h2 style="color:#0f172a">⏳ Time Explorer</h2>', unsafe_allow_html=True)
    time_grain = st.radio('Időbeli Felbontás', ['Year', 'Quarter', 'Month', 'Week', 'Day'], index=2, horizontal=True)

    if not df_tx.empty:
        df_time = df_tx[~df_tx['IsInternal']].groupby([time_grain, 'Type'])['AmountBase'].sum().reset_index()
        fig_time = px.bar(df_time, x=time_grain, y='AmountBase', color='Type', barmode='group',
                          color_discrete_map={'income': '#10b981', 'expense': '#ef4444', 'transfer': '#3b82f6'})
        fig_time.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='#0f172a', height=400)
        fig_time.update_xaxes(gridcolor='#e2e8f0'); fig_time.update_yaxes(gridcolor='#e2e8f0')
        st.plotly_chart(fig_time, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# 5. MERCHANT EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '5. Merchant Explorer':
    st.markdown('<h2 style="color:#0f172a">🏪 Merchant Explorer</h2>', unsafe_allow_html=True)
    merchants = df_tx[df_tx['Type'] == 'expense']['Merchant'].dropna().unique().tolist()
    sel_merchant = st.selectbox('Válassz Kereskedőt', sorted(merchants))

    if sel_merchant:
        stats = get_merchant_stats(df_tx, sel_merchant)
        if stats:
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric('Összes Költés', fmt_huf(stats['total_spent']))
            mc2.metric('Vásárlások Száma', f"{stats['tx_count']} db")
            mc3.metric('Átlagos Kosár', fmt_huf(stats['avg_basket']))
            mc4.metric('Legnagyobb Vásárlás', fmt_huf(stats['max_purchase']['AmountBase']))

            st.markdown('---')
            col_chart, col_details = st.columns([7, 5])

            with col_chart:
                st.markdown('<div class="section-title">Éves Költési Trend</div>', unsafe_allow_html=True)
                fig_m = px.bar(stats['yearly'], x='Year', y='AmountBase', text_auto=True, color_discrete_sequence=['#2563eb'])
                fig_m.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='#0f172a', height=300)
                st.plotly_chart(fig_m, use_container_width=True)

            with col_details:
                st.markdown('<div class="section-title">Részletek & Statisztikák</div>', unsafe_allow_html=True)
                st.write(f"**Legcsúcsabb hónap:** {stats['peak_month']}")
                st.write(f"**Leggyakoribb nap:** {stats['peak_day']}")
                st.write(f"**Kapcsolódó kategóriák:** {', '.join(stats['categories'])}")
                st.write(f"**Utolsó vásárlás:** {stats['last_purchase']['Date'].strftime('%Y-%m-%d')} ({fmt_huf(stats['last_purchase']['AmountBase'])})")

# ═════════════════════════════════════════════════════════════════════════════
# 6. CATEGORY EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '6. Category Explorer ⭐':
    st.markdown('<h2 style="color:#0f172a">🏷️ Category Explorer</h2>', unsafe_allow_html=True)
    categories = df_tx[df_tx['Type'] == 'expense']['Category'].dropna().unique().tolist()
    default_cat = st.session_state.get('sel_cat') if st.session_state.get('sel_cat') in categories else categories[0]
    sel_cat = st.selectbox('Válassz Kategóriát', sorted(categories), index=sorted(categories).index(default_cat))

    if sel_cat:
        stats = get_category_stats(df_tx, sel_cat)
        if stats:
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric('Összes Költés', fmt_huf(stats['total_spent']))
            cc2.metric('Havi Átlag', fmt_huf(stats['monthly_avg']))
            cc3.metric('Medián', fmt_huf(stats['median']))
            cc4.metric('Várható Következő Hónap', fmt_huf(stats['forecast']))

            st.markdown('---')
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown('<div class="section-title">Kereskedők szerinti bontás</div>', unsafe_allow_html=True)
                fig_merch = px.bar(stats['merchants'].head(10), x='AmountBase', y='Merchant', orientation='h', color_discrete_sequence=['#3b82f6'])
                fig_merch.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='#0f172a', height=320)
                st.plotly_chart(fig_merch, use_container_width=True)

            with col_right:
                st.markdown('<div class="section-title">Havi Trend & Vízesés (Waterfall)</div>', unsafe_allow_html=True)
                fig_wf = go.Figure(go.Waterfall(
                    x=stats['monthly_sums']['Month'],
                    y=stats['monthly_sums']['AmountBase'],
                    connector={'line': {'color': '#94a3b8'}}
                ))
                fig_wf.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='#0f172a', height=320)
                st.plotly_chart(fig_wf, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# 7. BUDGET CENTER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '7. Budget Center':
    st.markdown('<h2 style="color:#0f172a">🎯 Budget Center & Forecast</h2>', unsafe_allow_html=True)
    budgets = [
        {'Category': 'Étel-ital', 'Limit': 180000},
        {'Category': 'Utazás', 'Limit': 100000},
        {'Category': 'Szórakozás', 'Limit': 60000},
    ]

    insights = get_budget_insights(df_tx, budgets)
    for b in insights:
        st.markdown(f"### {b['Category']}")
        bc1, bc2, bc3 = st.columns(3)
        bc1.metric('Költés / Keret', f"{fmt_huf(b['Spent'])} / {fmt_huf(b['Limit'])}")
        bc2.metric('Jelenlegi Állapot', f"{b['Pct']:.1f}%")
        bc3.metric('Várható Hónap Végi', f"{b['ForecastPct']:.1f}%", delta=f"{fmt_huf(b['Overspend'])} túllépés" if b['Overspend']>0 else "Kereten belül")

        st.progress(min(1.0, b['Spent'] / b['Limit']))
        if b['Overspend'] > 0:
            st.error(f"⚠️ **Figyelmeztetés:** Ebben a költési tempóban kb. **{fmt_huf(b['Overspend'])}** összeppel fogod túllépni a keretet!")
        st.markdown('---')

# ═════════════════════════════════════════════════════════════════════════════
# 8. POCKET CENTER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '8. Pocket Center':
    st.markdown('<h2 style="color:#0f172a">👝 Pocket Center & ETA Forecast</h2>', unsafe_allow_html=True)
    etas = get_pocket_etas(poc_docs, df_tx)
    for p in etas:
        st.markdown(f"### {p['Name']}")
        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.metric('Egyenleg / Cél', f"{fmt_huf(p['Current'])} / {fmt_huf(p['Target'])}")
        pc2.metric('Havi Átlagos Megtakarítás', fmt_huf(p['MonthlyContrib']))
        pc3.metric('Elkészültségi Ráta', f"{p['Pct']:.1f}%")
        pc4.metric('Várható Befejezés (ETA)', p['ETA'])
        st.progress(min(1.0, p['Pct'] / 100.0))
        st.markdown('---')

# ═════════════════════════════════════════════════════════════════════════════
# 9. NET WORTH EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
elif page == '9. Net Worth Explorer':
    st.markdown('<h2 style="color:#0f172a">💎 Net Worth Explorer</h2>', unsafe_allow_html=True)
    df_acc_types = []
    for a in acc_docs:
        if a.get('isArchived') or a.get('isBusinessAccount'): continue
        df_acc_types.append({'Account': a['name'], 'Type': a.get('type', 'bank').capitalize(), 'BalanceHUF': a['balanceInBase']})

    df_at = pd.DataFrame(df_acc_types)
    if not df_at.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">Vagyon Összetétele Típusonként</div>', unsafe_allow_html=True)
            fig_at = px.pie(df_at, names='Type', values='BalanceHUF', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_at.update_layout(paper_bgcolor='white', font_color='#0f172a', height=320)
            st.plotly_chart(fig_at, use_container_width=True)

        with col2:
            st.markdown('<div class="section-title">Számlánkénti Egyenlegek</div>', unsafe_allow_html=True)
            fig_ab = px.bar(df_at, x='BalanceHUF', y='Account', orientation='h', color='BalanceHUF', color_continuous_scale='Blues')
            fig_ab.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='#0f172a', height=320)
            st.plotly_chart(fig_ab, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# 10. COMPARE MODE
# ═════════════════════════════════════════════════════════════════════════════
elif page == '10. Compare Mode ⭐':
    st.markdown('<h2 style="color:#0f172a">⚖️ Compare Mode (A/B Összehasonlítás)</h2>', unsafe_allow_html=True)
    mode = st.radio('Összehasonlítás Típusa', ['Év vs Év', 'Számla vs Számla'], horizontal=True)

    if mode == 'Év vs Év':
        years = sorted(df_tx['Year'].unique().tolist(), reverse=True)
        if len(years) >= 2:
            y1 = st.selectbox('A Időszak (Alap)', years, index=1)
            y2 = st.selectbox('B Időszak (Összehasonlított)', years, index=0)
            df_comp = compare_periods(df_tx, (df_tx['Year'] == y1), (df_tx['Year'] == y2), dimension='Category')
            st.markdown(f'<div class="section-title">{y1} vs {y2} Kategória Összehasonlítás</div>', unsafe_allow_html=True)
            st.dataframe(df_comp.style.format({'Period_A': '{:,.0f} Ft', 'Period_B': '{:,.0f} Ft', 'Difference': '{:,.0f} Ft', 'PctChange': '{:+.1f}%'}), use_container_width=True)

    elif mode == 'Számla vs Számla':
        accs = df_tx['Account'].unique().tolist()
        if len(accs) >= 2:
            a1 = st.selectbox('A Számla', accs, index=0)
            a2 = st.selectbox('B Számla', accs, index=1)
            df_comp = compare_periods(df_tx, (df_tx['Account'] == a1), (df_tx['Account'] == a2), dimension='Category')
            st.markdown(f'<div class="section-title">{a1} vs {a2} Kategória Összehasonlítás</div>', unsafe_allow_html=True)
            st.dataframe(df_comp.style.format({'Period_A': '{:,.0f} Ft', 'Period_B': '{:,.0f} Ft', 'Difference': '{:,.0f} Ft', 'PctChange': '{:+.1f}%'}), use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# 11. AUTOMATED INSIGHTS
# ═════════════════════════════════════════════════════════════════════════════
elif page == '11. Automated Insights':
    st.markdown('<h2 style="color:#0f172a">💡 Automated Financial Insights</h2>', unsafe_allow_html=True)
    insights = generate_insights(df_tx, poc_docs)
    for ins in insights:
        st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 12. TRANZAKCIÓK (CRUD) - TELJES SZERKESZTÉS & ÚJ TRÁNZAKCIÓ
# ═════════════════════════════════════════════════════════════════════════════
elif page == '📋 Tranzakciók (CRUD)':
    st.markdown('<h2 style="color:#0f172a">📋 Tranzakciók Kezelése</h2>', unsafe_allow_html=True)

    # Filters
    st.markdown('<div class="section-title">Szűrők</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([2, 2, 2, 2, 1.5, 1.5])
    f_search   = fc1.text_input('🔍 Keresés', placeholder='Megjegyzés...')
    f_type     = fc2.multiselect('Típus', TYPE_OPTIONS, format_func=lambda x: TYPE_LABELS[x])
    f_account  = fc3.multiselect('Számla', [d['name'] for d in acc_docs])
    f_category = fc4.multiselect('Kategória', [d['name'] for d in cat_docs])
    f_months   = fc5.slider('Elmúlt hónapok', 1, 36, 6)
    f_hide_internal = fc6.checkbox('🔄 Átcsoportosítások elrejtése', value=True)

    now = datetime.now()
    cutoff = datetime(now.year, now.month - f_months + 1 if now.month > f_months else 1, 1) if f_months < 36 else datetime(2000, 1, 1)

    # Filter transactions
    rows = []
    for tx in tx_docs:
        d = tx.get('date')
        if d and hasattr(d, 'year') and d < cutoff: continue
        if f_hide_internal and (tx.get('type') == 'transfer' or tx.get('isInternalAllocation')): continue

        d_str = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)[:10]
        c_name = cat_map.get(str(tx.get('categoryId', '')), '')
        a_name = acc_map.get(str(tx.get('accountId', '')), '')
        p_name = poc_map.get(str(tx.get('virtualPocketId', '')), '')
        note   = tx.get('note', '')

        if f_search and f_search.lower() not in note.lower(): continue
        if f_type and tx.get('type') not in f_type: continue
        if f_account and a_name not in f_account: continue
        if f_category and c_name not in f_category: continue

        rows.append({
            '_id': str(tx['_id']), 'Dátum': d_str, 'Típus': TYPE_LABELS.get(tx.get('type',''), tx.get('type','')),
            'Összeg': tx.get('amount', 0), 'Deviza': tx.get('currency', 'HUF'),
            'Számla': a_name, 'Kategória': c_name, 'Zseb': p_name, 'Megjegyzés': note, 'raw_tx': tx
        })

    df_tx_view = pd.DataFrame(rows)

    # Action bar & Add form at the top
    btn_add, btn_info = st.columns([2.5, 7.5])
    if btn_add.button('➕ Új Tranzakció Rögzítése', type='primary', use_container_width=True):
        st.session_state['show_add_form'] = not st.session_state.get('show_add_form', False)
        st.session_state['edit_tx_id'] = None

    # Add form (top position)
    if st.session_state.get('show_add_form'):
        st.markdown('<div class="section-title">➕ Új Tranzakció Rögzítése</div>', unsafe_allow_html=True)
        res = tx_form(user_id, acc_map, acc_docs, cat_map, cat_docs, poc_map, poc_docs, key_prefix='new')
        if res:
            res['createdAt'] = datetime.now()
            db.transactions.insert_one(res)
            st.session_state['show_add_form'] = False
            load_data.clear()
            st.success('Új tranzakció sikeresen rögzítve!')
            st.rerun()
        if st.button('❌ Mégse', key='cancel_add'):
            st.session_state['show_add_form'] = False
            st.rerun()

    # Edit form (top position)
    if st.session_state.get('edit_tx_id'):
        edit_id = st.session_state['edit_tx_id']
        existing_tx = db.transactions.find_one({'_id': ObjectId(edit_id)})
        if existing_tx:
            st.markdown('<div class="section-title">✏️ Tranzakció szerkesztése</div>', unsafe_allow_html=True)
            res = tx_form(user_id, acc_map, acc_docs, cat_map, cat_docs, poc_map, poc_docs, existing=existing_tx, key_prefix=f'edit_{edit_id}')
            if res:
                db.transactions.update_one({'_id': ObjectId(edit_id)}, {'$set': res})
                st.session_state['edit_tx_id'] = None
                load_data.clear()
                st.success('Tranzakció frissítve!')
                st.rerun()
            if st.button('❌ Mégse', key='cancel_edit'):
                st.session_state['edit_tx_id'] = None
                st.rerun()

    # Delete confirmation
    if st.session_state.get('confirm_delete_id'):
        del_id = st.session_state['confirm_delete_id']
        st.warning(f'⚠️ Biztosan törlöd ezt a tranzakciót?')
        cc1, cc2 = st.columns(2)
        if cc1.button('✅ Igen, törlöm', type='primary'):
            db.transactions.delete_one({'_id': ObjectId(del_id)})
            st.session_state['confirm_delete_id'] = None
            load_data.clear()
            st.success('Tranzakció törölve!')
            st.rerun()
        if cc2.button('❌ Mégsem'):
            st.session_state['confirm_delete_id'] = None
            st.rerun()

    if df_tx_view.empty:
        st.info('Nincs találat a beállított szűrőkre.')
    else:
        inc_shown = sum(r['Összeg'] for r in rows if 'Bevétel' in r['Típus'])
        exp_shown = sum(r['Összeg'] for r in rows if 'Kiadás' in r['Típus'])
        st.markdown(
            f'<p style="color:#64748b;font-size:0.85rem;margin-top:8px">'
            f'{len(rows)} tranzakció &nbsp;|&nbsp; Bevétel: <b style="color:#10b981">{fmt_huf(inc_shown)}</b> &nbsp;|&nbsp; Kiadás: <b style="color:#ef4444">{fmt_huf(exp_shown)}</b>'
            f'</p>', unsafe_allow_html=True
        )

        st.markdown('<div class="section-title">Tranzakciók Listája (Szerkesztés & Törlés)</div>', unsafe_allow_html=True)
        for i, row in df_tx_view.iterrows():
            c_date, c_type, c_amt, c_curr, c_acc, c_cat, c_poc, c_note, c_edit, c_del = st.columns([1.2,1.1,1,0.8,1.3,1.3,1,2.2,0.6,0.5])
            c_date.markdown(f'<small style="color:#64748b">{row["Dátum"]}</small>', unsafe_allow_html=True)
            t_col = '#10b981' if 'Bevétel' in row['Típus'] else ('#ef4444' if 'Kiadás' in row['Típus'] else '#64748b')
            c_type.markdown(f'<small style="color:{t_col};font-weight:600">{row["Típus"]}</small>', unsafe_allow_html=True)
            c_amt.markdown(f'<small style="color:#0f172a;font-weight:700">{row["Összeg"]:,.0f}</small>', unsafe_allow_html=True)
            c_curr.markdown(f'<small style="color:#64748b">{row["Deviza"]}</small>', unsafe_allow_html=True)
            c_acc.markdown(f'<small style="color:#475569">{row["Számla"]}</small>', unsafe_allow_html=True)
            c_cat.markdown(f'<small style="color:#475569">{row["Kategória"]}</small>', unsafe_allow_html=True)
            c_poc.markdown(f'<small style="color:#64748b">{row["Zseb"]}</small>', unsafe_allow_html=True)
            c_note.markdown(f'<small style="color:#64748b">{row["Megjegyzés"] or ""}</small>', unsafe_allow_html=True)

            if c_edit.button('✏️', key=f'edit_{row["_id"]}', help='Szerkesztés'):
                st.session_state['edit_tx_id'] = row['_id']
                st.session_state['show_add_form'] = False

            if c_del.button('🗑️', key=f'del_{row["_id"]}', help='Törlés'):
                st.session_state['confirm_delete_id'] = row['_id']

# ═════════════════════════════════════════════════════════════════════════════
# 13. BEÁLLÍTÁSOK
# ═════════════════════════════════════════════════════════════════════════════
elif page == '⚙️ Beállítások':
    st.markdown('<h2 style="color:#0f172a">⚙️ Beállítások</h2>', unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown('**Számlák**')
        for a in acc_docs: st.write(f"- {a['name']} ({a.get('currency','HUF')})")
    with sc2:
        st.markdown('**Kategóriák**')
        for c in cat_docs: st.write(f"- {c['name']}")
    with sc3:
        st.markdown('**Zsebek**')
        for p in poc_docs: st.write(f"- {p['name']}")

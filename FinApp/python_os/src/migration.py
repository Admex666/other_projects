import pandas as pd
from pymongo import MongoClient
from config import MONGODB_URI


def migrate_data():
    print("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    try:
        db = client.get_default_database()
    except Exception:
        db = client.get_database('test')

    # ── User ────────────────────────────────────────────────────────────────
    user = db.users.find_one({'username': 'adam'})
    if not user:
        raise Exception("User 'adam' not found in database!")
    user_id = user['_id']

    # ── Lookup maps ──────────────────────────────────────────────────────────
    print("Building lookup maps...")
    account_map  = {str(a['_id']): a['name']  for a in db.accounts.find({'userId': user_id})}
    category_map = {str(c['_id']): c['name']  for c in db.categories.find({'userId': user_id})}
    pocket_map   = {str(p['_id']): p['name']  for p in db.virtualpockets.find({'owners': user_id})}

    # ── 01_Transactions ──────────────────────────────────────────────────────
    print("Extracting Transactions...")
    tx_rows = []
    for idx, tx in enumerate(db.transactions.find({'userId': user_id})):
        date_str = ''
        if tx.get('date'):
            try:    date_str = tx['date'].strftime('%Y-%m-%d')
            except: date_str = str(tx['date'])

        created_str = ''
        if tx.get('createdAt'):
            try:    created_str = tx['createdAt'].strftime('%Y-%m-%d %H:%M:%S')
            except: created_str = str(tx['createdAt'])

        tx_rows.append({
            'Date':      date_str,
            'Type':      tx.get('type', 'expense').capitalize(),
            'Account':   account_map.get(str(tx.get('accountId',  '')), ''),
            'Amount':    tx.get('amount', 0),
            'Currency':  tx.get('currency', 'HUF'),
            'Category':  category_map.get(str(tx.get('categoryId', '')), ''),
            'Pocket':    pocket_map.get(str(tx.get('virtualPocketId', '')), ''),
            'Merchant':  '',
            'Owner':     'Adam',
            'Note':      tx.get('note', ''),
            'ID':        f'TX-{idx+1000}',           # auto
            'BaseAmount': tx.get('amountInBaseCurrency', tx.get('amount', 0)),  # formula later
            'CreatedAt': created_str,                 # auto
        })

    tx_df = pd.DataFrame(tx_rows)
    tx_df['Date'] = pd.to_datetime(tx_df['Date'], errors='coerce')
    tx_df = tx_df.sort_values('Date').reset_index(drop=True)
    tx_df['Date'] = tx_df['Date'].dt.strftime('%Y-%m-%d').fillna('')

    # ── 02_Accounts ──────────────────────────────────────────────────────────
    print("Extracting Accounts...")
    acc_rows = []
    for a in db.accounts.find({'userId': user_id}):
        acc_rows.append({
            'Name':           a['name'],
            'Type':           a.get('type', 'bank').capitalize(),
            'Currency':       a.get('currency', 'HUF'),
            'Owner':          'Adam',
            'OpeningBalance': a.get('initialBalance', 0),
            'IsArchived':     a.get('isArchived', False),
            '_MongoID':       str(a['_id']),
        })
    acc_df = pd.DataFrame(acc_rows)

    # ── 03_Budgets_Goals ─────────────────────────────────────────────────────
    budgets_df = pd.DataFrame([
        {'Name': 'Élelmiszer',  'Type': 'Budget', 'Owner': 'Adam', 'Target': 0, 'Period': 'Monthly', 'Note': ''},
        {'Name': 'Szórakozás',  'Type': 'Budget', 'Owner': 'Adam', 'Target': 0, 'Period': 'Monthly', 'Note': ''},
        {'Name': 'Vésztartalék','Type': 'Goal',   'Owner': 'Adam', 'Target': 0, 'Deadline': '',       'Note': ''},
    ])

    # ── 04_Pockets ───────────────────────────────────────────────────────────
    print("Extracting Pockets...")
    pocket_rows = []
    for p in db.virtualpockets.find({'owners': user_id}):
        pocket_rows.append({
            'Pocket':   p['name'],
            'Owner':    'Adam',
            'Currency': p.get('currency', 'HUF'),
            'Target':   p.get('targetAmount', 0),
            '_MongoID': str(p['_id']),
        })
    pockets_df = pd.DataFrame(pocket_rows) if pocket_rows else pd.DataFrame(
        columns=['Pocket', 'Owner', 'Currency', 'Target', '_MongoID'])

    # ── 90_Settings ──────────────────────────────────────────────────────────
    people    = [{'#People':    v} for v in ['Adam']]
    categories= [{'#Categories': c['name']} for c in db.categories.find({'userId': user_id})]
    merchants = [{'#Merchants':  m} for m in ['Lidl', 'Netflix', 'Spotify', 'Amazon']]
    tags      = [{'#Tags':       t} for t in ['Nyaralás', 'Munka', 'Ajándék']]

    settings_df = pd.DataFrame({
        'People':     pd.Series([r['#People']     for r in people]),
        'Categories': pd.Series([r['#Categories'] for r in categories]),
        'Merchants':  pd.Series([r['#Merchants']  for r in merchants]),
        'Tags':       pd.Series([r['#Tags']        for r in tags]),
    })

    # ── 22_ExchangeRates  (lives inside 91_Data) ─────────────────────────────
    print("Extracting Exchange Rates...")
    rate_rows = []
    for r in db.exchangerates.find({}):
        date_str  = str(r['date'])
        rates_d   = r.get('rates', {})
        huf_rate  = float(rates_d.get('HUF', 1))
        for curr, val in rates_d.items():
            if curr == 'HUF': continue
            fval = float(val) if val else 0
            rate_rows.append({
                'LookupKey':  f"{date_str}{curr}",
                'Date':       date_str,
                'Currency':   curr,
                'Rate_to_HUF': round(huf_rate / fval, 6) if fval else 0,
            })
    exchange_df = pd.DataFrame(rate_rows) if rate_rows else pd.DataFrame(
        columns=['LookupKey', 'Date', 'Currency', 'Rate_to_HUF'])

    # ── 91_Data  (mongo ID mapping) ──────────────────────────────────────────
    id_map_rows = [{'Sheet': '02_Accounts', 'Name': a['name'], 'MongoID': str(a['_id'])}
                   for a in db.accounts.find({'userId': user_id})]
    id_map_df = pd.DataFrame(id_map_rows)

    # ── Migration Report ─────────────────────────────────────────────────────
    report = (
        "Migration Report\n"
        "====================\n"
        f"User: Adam\n"
        f"Accounts migrated:      {len(acc_df)}\n"
        f"Pockets migrated:       {len(pockets_df)}\n"
        f"Transactions migrated:  {len(tx_df)}\n"
        f"Exchange rate rows:     {len(exchange_df)}\n"
    )
    with open('../Finance_OS_migration_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print(report)

    return {
        '01_Transactions':  tx_df,
        '02_Accounts':      acc_df,
        '03_BudgetsGoals':  budgets_df,
        '04_Pockets':       pockets_df,
        '90_Settings':      settings_df,
        '91_Data_ExRates':  exchange_df,
        '91_Data_IDMap':    id_map_df,
    }


if __name__ == '__main__':
    migrate_data()

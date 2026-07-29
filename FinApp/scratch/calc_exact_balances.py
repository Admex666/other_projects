from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('.env.local')
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.get_database('test')
user = db.users.find_one({'username': 'adam'})
uid = user['_id']
accs = list(db.accounts.find({'userId': uid}))
pockets = list(db.virtualpockets.find({'owners': uid}))

rates_doc = db.exchangerates.find_one(sort=[('date', -1)])
rates = rates_doc['rates'] if rates_doc else {'HUF': 390.0, 'USD': 1.1, 'BGN': 1.95}

def convert(amt, f, t):
    if f == t: return amt
    eur = amt / rates[f] if f != 'EUR' else amt
    return eur * rates[t] if t != 'EUR' else eur

pers_total = 0
bus_total = 0

print("--- ACCOUNT BALANCES ---")
for a in accs:
    if a.get('isArchived'): continue
    acc_id = a['_id']
    txs = list(db.transactions.find({
        'userId': str(uid),
        'isInternalAllocation': {'$ne': True},
        '$or': [{'accountId': acc_id}, {'toAccountId': acc_id}]
    }))
    if len(txs) == 0:
        txs = list(db.transactions.find({
            'userId': uid,
            'isInternalAllocation': {'$ne': True},
            '$or': [{'accountId': acc_id}, {'toAccountId': acc_id}]
        }))
        
    bal = a.get('initialBalance') or 0
    for tx in txs:
        tx_amt = tx.get('amount', 0)
        tx_curr = tx.get('currency', 'HUF')
        amt_in_acc = convert(tx_amt, tx_curr, a.get('currency', 'HUF'))
        
        acc_str = str(acc_id)
        tx_acc_str = str(tx.get('accountId', ''))
        tx_to_acc_str = str(tx.get('toAccountId', ''))
        
        if tx_acc_str == acc_str:
            if tx.get('type') == 'income': bal += amt_in_acc
            else: bal -= amt_in_acc
        elif tx_to_acc_str == acc_str and tx.get('type') == 'transfer':
            bal += amt_in_acc
            
    bal_huf = convert(bal, a.get('currency', 'HUF'), 'HUF')
    print(f"{a['name']} ({a.get('currency')}): {bal:.2f} => {bal_huf:,.0f} HUF | Business: {a.get('isBusinessAccount')}")
    if a.get('isBusinessAccount'):
        bus_total += bal_huf
    else:
        pers_total += bal_huf

print("\n--- POCKET BALANCES ---")
total_pocket_huf = 0
for p in pockets:
    txs = list(db.transactions.find({'virtualPocketId': p['_id']}))
    p_bal = 0
    for tx in txs:
        amt_in_poc = convert(tx.get('amount', 0), tx.get('currency', 'HUF'), p.get('currency', 'HUF'))
        if tx.get('type') in ['income', 'transfer']: p_bal += amt_in_poc
        else: p_bal -= amt_in_poc
    p_bal = max(0, p_bal)
    p_huf = convert(p_bal, p.get('currency', 'HUF'), 'HUF')
    print(f"Pocket {p['name']}: {p_bal:.2f} {p.get('currency')} => {p_huf:,.0f} HUF")
    total_pocket_huf += p_huf

print("\n--- SUMMARY ---")
print(f"Personal Portfolio: {pers_total:,.0f} HUF")
print(f"Business Portfolio: {bus_total:,.0f} HUF")
print(f"Total Portfolio: {pers_total + bus_total:,.0f} HUF")
print(f"Total Pockets: {total_pocket_huf:,.0f} HUF")
print(f"Personal Free Balance: {pers_total - total_pocket_huf:,.0f} HUF")

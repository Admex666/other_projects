"""
FinSpace Weekly Notification — Pushbullet
==========================================
Standalone script for GitHub Actions.
Connects to MongoDB, generates a weekly report, and sends a push notification.
"""
import os
import sys
import requests
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Add parent paths for imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bi_analytics import convert_val, prepare_tx_dataframe
from report_engine import generate_weekly_report, format_weekly_notification


def main():
    # ── Config from environment ──
    mongo_uri = os.environ.get('MONGODB_URI')
    pushbullet_token = os.environ.get('PUSHBULLET_ACCESS_TOKEN')

    if not mongo_uri:
        print("ERROR: MONGODB_URI not set")
        sys.exit(1)
    if not pushbullet_token:
        print("ERROR: PUSHBULLET_ACCESS_TOKEN not set")
        sys.exit(1)

    # ── MongoDB connection ──
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    try:
        db = client.get_default_database()
    except Exception:
        db = client.get_database('test')

    user = db.users.find_one({'username': 'adam'})
    if not user:
        print("ERROR: User 'adam' not found")
        sys.exit(1)

    uid = user['_id']

    # ── Load data ──
    acc_docs = list(db.accounts.find({'userId': uid}))
    cat_docs = list(db.categories.find({'userId': uid}))
    poc_docs = list(db.virtualpockets.find({'owners': uid}))
    tx_docs = list(db.transactions.find({'userId': uid}).sort('date', -1))

    rates_doc = db.exchangerates.find_one(sort=[('date', -1)])
    rates = rates_doc['rates'] if (rates_doc and 'rates' in rates_doc) else {
        'HUF': 390.0, 'USD': 1.1, 'EUR': 1.0, 'BGN': 1.95
    }

    acc_map = {str(a['_id']): a['name'] for a in acc_docs}
    cat_map = {str(c['_id']): c['name'] for c in cat_docs}
    poc_map = {str(p['_id']): p['name'] for p in poc_docs}

    # Compute account balances (same logic as finspace_app.py)
    for acc in acc_docs:
        acc_id = str(acc['_id'])
        acc_curr = acc.get('currency', 'HUF')
        bal = float(acc.get('initialBalance') or 0.0)
        for tx in tx_docs:
            if tx.get('isInternalAllocation'):
                continue
            tx_acc = str(tx.get('accountId', ''))
            tx_to_acc = str(tx.get('toAccountId', ''))
            tx_curr = tx.get('currency', 'HUF')
            tx_amt = float(tx.get('amount', 0.0))
            tx_type = tx.get('type', '')

            if tx_acc == acc_id:
                amt_in_acc = convert_val(tx_amt, tx_curr, acc_curr, rates)
                if tx_type == 'income':
                    bal += amt_in_acc
                elif tx_type in ['expense', 'transfer']:
                    bal -= amt_in_acc

            if tx_to_acc == acc_id and tx_type == 'transfer':
                amt_in_acc = convert_val(tx_amt, tx_curr, acc_curr, rates)
                bal += amt_in_acc

        acc['balance'] = bal
        acc['balanceInBase'] = convert_val(bal, acc_curr, 'HUF', rates)

    # Compute pocket balances
    for poc in poc_docs:
        poc_id = str(poc['_id'])
        poc_curr = poc.get('currency', 'HUF')
        p_bal = 0.0
        for tx in tx_docs:
            if str(tx.get('virtualPocketId', '')) == poc_id:
                tx_curr = tx.get('currency', 'HUF')
                tx_amt = float(tx.get('amount', 0.0))
                tx_type = tx.get('type', '')
                amt_in_poc = convert_val(tx_amt, tx_curr, poc_curr, rates)
                if tx_type in ['income', 'transfer']:
                    p_bal += amt_in_poc
                elif tx_type == 'expense':
                    p_bal -= amt_in_poc
        poc['currentAmount'] = max(0.0, p_bal)
        poc['currentAmountInBase'] = convert_val(max(0.0, p_bal), poc_curr, 'HUF', rates)

    # ── Generate report ──
    df_tx = prepare_tx_dataframe(tx_docs, acc_map, cat_map, poc_map, rates)
    report = generate_weekly_report(df_tx, acc_docs, poc_docs, rates)
    notification_text = format_weekly_notification(report)

    print("=== Notification Preview ===")
    print(notification_text)
    print("============================")

    # ── Send via Pushbullet ──
    resp = requests.post(
        'https://api.pushbullet.com/v2/pushes',
        headers={
            'Access-Token': pushbullet_token,
            'Content-Type': 'application/json',
        },
        json={
            'type': 'note',
            'title': f'📊 FinSpace Weekly — {report["period"]}',
            'body': notification_text,
        }
    )

    if resp.status_code == 200:
        print(f"✅ Notification sent successfully!")
    else:
        print(f"❌ Pushbullet error: {resp.status_code} — {resp.text}")
        sys.exit(1)


if __name__ == '__main__':
    main()

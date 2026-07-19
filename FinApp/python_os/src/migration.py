import pandas as pd
from pymongo import MongoClient
from config import MONGODB_URI
import os

def migrate_data():
    print("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    try:
        db = client.get_default_database()
    except Exception:
        db = client.get_database('test')
    
    # Get user 'adam'
    user = db.users.find_one({'username': 'adam'})
    if not user:
        raise Exception("User 'adam' not found in database!")
        
    user_id = user['_id']
    
    print("Extracting Accounts...")
    accounts_cursor = db.accounts.find({'userId': user_id})
    accounts_data = []
    account_map = {} # _id to name
    
    for acc in accounts_cursor:
        account_map[str(acc['_id'])] = acc['name']
        accounts_data.append({
            'AccountID': str(acc['_id']),
            'Name': acc['name'],
            'Institution': '',
            'Currency': acc.get('currency', 'HUF'),
            'Type': acc.get('type', 'bank').capitalize(),
            'Owner': 'Adam',
            'OpeningBalance': acc.get('initialBalance', 0),
            'CurrentBalance': 0, # Formula
            'IsArchived': acc.get('isArchived', False),
            'Color': acc.get('color', ''),
            'Icon': acc.get('icon', '')
        })
        
    accounts_df = pd.DataFrame(accounts_data)
    
    print("Extracting Categories...")
    categories_cursor = db.categories.find({'userId': user_id})
    category_map = {}
    categories_data = []
    
    for cat in categories_cursor:
        category_map[str(cat['_id'])] = cat['name']
        categories_data.append({
            'CategoryID': str(cat['_id']),
            'ParentCategory': '',
            'Name': cat['name'],
            'Type': cat.get('type', 'expense').capitalize(),
            'TotalSpent': 0, # Formula
            'Color': cat.get('color', ''),
            'Icon': cat.get('icon', ''),
            'Order': 0
        })
        
    categories_df = pd.DataFrame(categories_data)
    
    print("Extracting Pockets...")
    pockets_cursor = db.virtualpockets.find({'owners': user_id})
    pocket_map = {}
    pockets_data = []
    for p in pockets_cursor:
        pocket_map[str(p['_id'])] = p['name']
        pockets_data.append({
            'PocketID': str(p['_id']),
            'Name': p['name'],
            'Owner': 'Adam',
            'Currency': p.get('currency', 'HUF'),
            'GoalAmount': p.get('targetAmount', 0),
            'CurrentBalance': 0, # Formula
            'Type': 'Virtual',
            'Active': True
        })
    pockets_df = pd.DataFrame(pockets_data)
        
    print("Extracting Exchange Rates...")
    rates_cursor = db.exchangerates.find({})
    rates_data = []
    
    for r in rates_cursor:
        date_str = str(r['date'])
        rates_dict = r.get('rates', {})
        huf_rate = rates_dict.get('HUF', 1)
        
        for curr, val in rates_dict.items():
            if curr == 'HUF': continue
            multiplier = huf_rate / val if val else 0
            rates_data.append({
                'Date_Currency': f"{date_str}{curr}",
                'Date': date_str,
                'BaseCurrency': 'HUF',
                'Currency': curr,
                'Rate': multiplier
            })
            
        # Add EUR explicitly
        rates_data.append({
            'Date_Currency': f"{date_str}EUR",
            'Date': date_str,
            'BaseCurrency': 'HUF',
            'Currency': 'EUR',
            'Rate': huf_rate
        })
        
    exchange_rates_df = pd.DataFrame(rates_data)

    print("Extracting Transactions...")
    tx_cursor = db.transactions.find({'userId': user_id})
    tx_data = []
    
    for idx, tx in enumerate(tx_cursor):
        cat_id = str(tx.get('categoryId'))
        cat_name = category_map.get(cat_id, '')
        
        acc_id = str(tx.get('accountId'))
        acc_name = account_map.get(acc_id, '')
        
        to_acc_id = str(tx.get('toAccountId', ''))
        to_acc_name = account_map.get(to_acc_id, '')
        
        pocket_id = str(tx.get('virtualPocketId', ''))
        pocket_name = pocket_map.get(pocket_id, '')
        
        tx_type = tx.get('type', 'expense').capitalize()
            
        date_str = ''
        if 'date' in tx and tx['date']:
            try:
                date_str = tx['date'].strftime('%Y-%m-%d')
            except:
                date_str = str(tx['date'])
                
        created_at_str = ''
        if 'createdAt' in tx and tx['createdAt']:
            try:
                created_at_str = tx['createdAt'].strftime('%Y-%m-%d %H:%M:%S')
            except:
                created_at_str = str(tx['createdAt'])
                
        tx_data.append({
            'TransactionID': f"TX-{idx+1000}",
            'Date': date_str,
            'Type': tx_type,
            'Owner': 'Adam',
            'Account': acc_name,
            'ToAccount': to_acc_name,
            'Amount': tx.get('amount', 0),
            'Currency': tx.get('currency', 'HUF'),
            'BaseAmount': 0, # Placeholder, will be replaced with formula
            'ExchangeRate': tx.get('exchangeRate', 1), # Will be used as fallback
            'Category': cat_name,
            'Pocket': pocket_name,
            'Merchant': '',
            'Note': tx.get('note', ''),
            'Status': 'Completed',
            'RecurringID': '',
            'CreatedAt': created_at_str
        })
        
    tx_df = pd.DataFrame(tx_data)
    
    # Sort transactions by Date
    tx_df['Date'] = pd.to_datetime(tx_df['Date'], errors='coerce')
    tx_df = tx_df.sort_values('Date', ascending=True)
    tx_df['Date'] = tx_df['Date'].dt.strftime('%Y-%m-%d').fillna('')
    tx_df = tx_df.reset_index(drop=True)
    
    # Store fallback exchange rates in the dataframe so excel_builder can use them
    # Formulas will be written by excel_builder.py to ensure they work in Excel
    
    # Create empty dataframes for other sheets
    transaction_splits_df = pd.DataFrame(columns=['SplitID', 'TransactionID', 'Category', 'Amount', 'Pocket', 'OwnerShare', 'Note'])
    assets_df = pd.DataFrame(columns=['AssetID', 'Name', 'Ticker', 'Type', 'Currency', 'Quantity', 'Notes'])
    tags_df = pd.DataFrame(columns=['TagID', 'Name', 'Color'])
    goals_df = pd.DataFrame(columns=['GoalID', 'Name', 'TargetAmount', 'Deadline', 'Priority', 'PocketID', 'Status'])
    budgets_df = pd.DataFrame(columns=['BudgetID', 'Month', 'Category', 'Owner', 'Limit', 'WarningPercentage', 'CriticalPercentage'])
    people_df = pd.DataFrame([{'PersonID': 'P-1', 'Name': 'Adam', 'Type': 'Primary'}])
    recurring_df = pd.DataFrame(columns=['RecurringID', 'Name', 'Amount', 'Currency', 'Frequency', 'NextDate', 'Category', 'Pocket', 'Enabled'])
    debts_df = pd.DataFrame(columns=['DebtID', 'From', 'To', 'Amount', 'Currency', 'TransactionID', 'Settled', 'SettledDate'])
    
    if exchange_rates_df.empty:
        exchange_rates_df = pd.DataFrame(columns=['Date_Currency', 'Date', 'BaseCurrency', 'Currency', 'Rate'])
    settings_df = pd.DataFrame([
        {'Key': 'BaseCurrency', 'Value': 'HUF'},
        {'Key': 'Version', 'Value': '1.0'}
    ])
    
    # Save Migration Report
    report = f"""Migration Report
====================
User: Adam
Accounts migrated: {len(accounts_df)}
Categories migrated: {len(categories_df)}
Pockets migrated: {len(pockets_df)}
Transactions migrated: {len(tx_df)}
"""
    with open('Migration_Report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
        
    print("Migration extraction complete.")
    
    return {
        '01_Transactions': tx_df,
        '02_TransactionSplits': transaction_splits_df,
        '10_Accounts': accounts_df,
        '11_Assets': assets_df,
        '12_Categories': categories_df,
        '13_Tags': tags_df,
        '14_Pockets': pockets_df,
        '15_Goals': goals_df,
        '16_Budgets': budgets_df,
        '17_People': people_df,
        '20_Recurring': recurring_df,
        '21_Debts': debts_df,
        '22_ExchangeRates': exchange_rates_df,
        '99_Settings': settings_df
    }

if __name__ == "__main__":
    migrate_data()

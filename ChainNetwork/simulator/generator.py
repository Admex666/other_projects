import sqlite3
import random
import numpy as np
from datetime import datetime, timedelta

def get_db_connection():
    return sqlite3.connect('simulator/chainnetwork.db')

def seed_initial_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Reset DB
    tables = ["transaction_items", "transactions", "interventions", "users", "stores", "menu_items", "campaigns"]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    with open('simulator/schema.sql', 'r') as f:
        cursor.executescript(f.read())

    # Stores
    stores = [
        ('Bamba Marha Deák', 'City'),
        ('Bamba Marha Westend', 'Mall'),
        ('Bamba Marha Corvin', 'Mall'),
        ('Bamba Marha Bazilika', 'City')
    ]
    cursor.executemany("INSERT INTO stores (name, location_type) VALUES (?, ?)", stores)

    # Menu Items
    menu_items = [
        ('b_classic', 'Classic Burger', 'Burger', 3200, 1200),
        ('b_cheese', 'Cheese Burger', 'Burger', 3500, 1300),
        ('b_bacon', 'Bacon Burger', 'Burger', 3800, 1500),
        ('b_vegan', 'Beyond Vegan', 'Burger', 4200, 1800),
        ('s_fries', 'French Fries', 'Side', 900, 200),
        ('s_rings', 'Onion Rings', 'Side', 1100, 300),
        ('s_sweet', 'Sweet Potato', 'Side', 1400, 400),
        ('d_cola', 'Coca Cola', 'Drink', 800, 150),
        ('d_lemonade', 'Homemade Lemonade', 'Drink', 1200, 300),
        ('d_beer', 'Craft Beer', 'Drink', 1500, 600)
    ]
    cursor.executemany("INSERT INTO menu_items (sku, name, category, price, cost) VALUES (?, ?, ?, ?, ?)", menu_items)

    # Campaigns
    campaigns = [
        ('Churn Save', 'ChurnSave', 'Win back at-risk users with a 20% coupon.'),
        ('Upsell Hero', 'Upsell', 'Suggest a side/drink for high-margin burgers.'),
        ('Dead Zone Deal', 'DeadZone', 'Happy hour discounts for 15:00-17:00.')
    ]
    cursor.executemany("INSERT INTO campaigns (name, type, description) VALUES (?, ?, ?)", campaigns)

    conn.commit()
    conn.close()

def generate_reactive_history(days=180):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Setup
    cursor.execute("SELECT id FROM stores")
    store_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT id, sku, category, price FROM menu_items")
    menu_data = cursor.fetchall()
    items_by_cat = {'Burger': [], 'Side': [], 'Drink': []}
    prices = {}
    for iid, sku, cat, price in menu_data:
        items_by_cat[cat].append(iid)
        prices[iid] = price

    # Users
    users = []
    user_states = {} 
    for i in range(1000):
        test_group = 'A' if i < 500 else 'B'
        lifestyle = random.choices(['Student', 'Office', 'Family', 'Tourist'], weights=[25, 40, 25, 10])[0]
        age = random.choices(['18-24', '25-34', '35-44', '45+'], weights=[30, 40, 20, 10])[0]
        gender = random.choice(['Male', 'Female', 'Non-binary'])
        
        users.append((f"User_{i}", f"user_{i}@chain.com", test_group, age, gender, lifestyle, 1))
        user_states[i+1] = {
            'group': test_group, 
            'lifestyle': lifestyle,
            'age': age,
            'last_visit': None,
            'active_coupon': None,
            'home_store': random.choice(store_ids)
        }
    cursor.executemany("INSERT INTO users (name, email, test_group, age_group, gender, lifestyle_tag, consent_given) VALUES (?, ?, ?, ?, ?, ?, ?)", users)
    conn.commit()

    # Simulation loop
    start_date = datetime.now() - timedelta(days=days)
    
    for d in range(days):
        current_date = start_date + timedelta(days=d)
        is_weekend = current_date.weekday() >= 5
        
        for uid, state in user_states.items():
            # 1. Decision Engine Logic (B Group)
            if state['group'] == 'B':
                # Churn Save
                if state['last_visit'] and (current_date - state['last_visit']).days > 20 and not state['active_coupon']:
                    state['active_coupon'] = 1 
                    cursor.execute("INSERT INTO interventions (user_id, campaign_id, timestamp, discount_percent) VALUES (?, ?, ?, ?)",
                                 (uid, 1, current_date.strftime('%Y-%m-%d 09:00:00'), 20))

            # 2. Visit Probability
            base_prob = 0.02
            if state['lifestyle'] == 'Office' and not is_weekend: base_prob = 0.08
            if state['lifestyle'] == 'Student' and is_weekend: base_prob = 0.05
            
            if state['active_coupon']: base_prob *= 2.5
            
            if random.random() < base_prob:
                store_id = state['home_store']
                hour = random.randint(12, 21)
                
                # Lifestyle Hour Bias
                if state['lifestyle'] == 'Office': hour = random.choices([12, 13, 18], weights=[50, 30, 20])[0]
                if state['lifestyle'] == 'Student': hour = random.randint(14, 22)
                
                ts = current_date.replace(hour=hour, minute=random.randint(0,59)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Order Logic
                order = [random.choice(items_by_cat['Burger'])]
                
                # Family ordering
                multiplier = 3 if state['lifestyle'] == 'Family' else 1
                
                if random.random() < 0.6: order.append(random.choice(items_by_cat['Side']))
                if random.random() < 0.8: order.append(random.choice(items_by_cat['Drink']))

                discount = 0
                if state['active_coupon']:
                    discount = sum(prices[i] for i in order) * multiplier * 0.2
                    cursor.execute("UPDATE interventions SET is_converted = 1 WHERE user_id = ? AND campaign_id = ? AND is_converted = 0", (uid, state['active_coupon']))
                    state['active_coupon'] = None

                total = (sum(prices[i] for i in order) * multiplier) - discount
                cursor.execute("INSERT INTO transactions (user_id, store_id, timestamp, total_amount, discount_amount) VALUES (?, ?, ?, ?, ?)",
                             (uid, store_id, ts, total, discount))
                tid = cursor.lastrowid
                for iid in order:
                    cursor.execute("INSERT INTO transaction_items (transaction_id, menu_item_id, quantity, unit_price) VALUES (?, ?, ?, ?)", 
                                 (tid, iid, multiplier, prices[iid]))
                
                state['last_visit'] = current_date

        if d % 30 == 0: conn.commit() # Periodic commit

    conn.commit()
    conn.close()
    print("Reactive simulation completed.")

if __name__ == "__main__":
    seed_initial_data()
    generate_reactive_history()


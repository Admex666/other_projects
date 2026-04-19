import sqlite3
import random
import numpy as np
from datetime import datetime, timedelta

def get_db_connection():
    return sqlite3.connect('simulator/chainnetwork.db')

def seed_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fully reset the DB
    cursor.execute("DROP TABLE IF EXISTS transaction_items")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS interventions")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS stores")
    cursor.execute("DROP TABLE IF EXISTS menu_items")
    
    # Re-run schema (or just manually recreate, but let's re-read schema.sql)
    with open('simulator/schema.sql', 'r') as f:
        cursor.executescript(f.read())

    # Seed Stores (Uneven popularity - Deák is busiest)
    stores = [
        ('Bamba Marha Deák', 'City'),
        ('Bamba Marha Westend', 'Mall'),
        ('Bamba Marha Corvin', 'Mall'),
        ('Bamba Marha Bazilika', 'City')
    ]
    cursor.executemany("INSERT INTO stores (name, location_type) VALUES (?, ?)", stores)

    # Seed Menu Items (SKU, Name, Category, Price, Cost)
    menu_items = [
        ('b_classic', 'Classic Burger', 'Burger', 3200, 1200),
        ('b_cheese', 'Cheese Burger', 'Burger', 3500, 1300),
        ('b_bacon', 'Bacon Burger', 'Burger', 3800, 1500),
        ('s_fries', 'French Fries', 'Side', 900, 200),
        ('s_rings', 'Onion Rings', 'Side', 1100, 300),
        ('d_cola', 'Coca Cola', 'Drink', 800, 150),
        ('d_lemonade', 'Homemade Lemonade', 'Drink', 1200, 300)
    ]
    cursor.executemany("INSERT INTO menu_items (sku, name, category, price, cost) VALUES (?, ?, ?, ?, ?)", menu_items)

    conn.commit()
    conn.close()
    print("Database reset and seeded.")

def get_weighted_hour():
    hours = list(range(11, 23))
    weights = [5, 20, 15, 5, 2, 3, 8, 15, 20, 12, 5, 2]
    return random.choices(hours, weights=weights)[0]

def generate_history(days=180):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get dynamic IDs
    cursor.execute("SELECT id FROM stores")
    store_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id, category, price FROM menu_items")
    items = cursor.fetchall()
    burgers = [row[0] for row in items if row[1] == 'Burger']
    sides = [row[0] for row in items if row[1] == 'Side']
    drinks = [row[0] for row in items if row[1] == 'Drink']
    items_prices = {row[0]: row[2] for row in items}

    # Create 1000 users with Store Affinity and specialized profiles
    users = []
    user_metadata = {} 
    for i in range(1000):
        name = f"User_{i}"
        test_group = 'A' if i < 500 else 'B'
        joined_days_ago = random.randint(30, 270)
        joined_at = (datetime.now() - timedelta(days=joined_days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        home_store = random.choices(store_ids, weights=[40, 25, 20, 15])[0]
        profile = random.choices(
            ['Loyalist', 'Casual', 'OfficeWorker', 'DealSeeker'],
            weights=[20, 45, 25, 10]
        )[0]
        
        users.append((name, f"user_{i}@example.com", joined_at, test_group))
        user_metadata[i+1] = {'home_store': home_store, 'profile': profile}
    
    cursor.executemany("INSERT INTO users (name, email, joined_at, test_group) VALUES (?, ?, ?, ?)", users)
    conn.commit()

    profiles = {
        'Loyalist': {'prob': 0.12, 'side_prob': 0.85, 'drink_prob': 0.9},
        'Casual': {'prob': 0.03, 'side_prob': 0.4, 'drink_prob': 0.5},
        'OfficeWorker': {'prob': 0.10, 'side_prob': 0.6, 'drink_prob': 0.7},
        'DealSeeker': {'prob': 0.04, 'side_prob': 0.2, 'drink_prob': 0.4}
    }

    start_date = datetime.now() - timedelta(days=days)
    transactions = []

    for d in range(days):
        current_date = start_date + timedelta(days=d)
        is_weekend = current_date.weekday() >= 5
        daily_noise = np.random.normal(1.0, 0.15)

        for uid, meta in user_metadata.items():
            prof = profiles[meta['profile']]
            v_prob = prof['prob'] * daily_noise
            if is_weekend: v_prob *= 1.4
            
            if random.random() < v_prob:
                store_id = meta['home_store'] if random.random() < 0.8 else random.choice(store_ids)
                hour = get_weighted_hour()
                if meta['profile'] == 'OfficeWorker':
                    hour = random.choices([12, 13, 17, 18], weights=[40, 30, 15, 15])[0]
                
                timestamp = current_date.replace(hour=hour, minute=random.randint(0, 59)).strftime('%Y-%m-%d %H:%M:%S')
                
                # Dynamic order logic
                order_items_ids = [random.choice(burgers)]
                if random.random() < prof['side_prob']: order_items_ids.append(random.choice(sides))
                if random.random() < prof['drink_prob']: order_items_ids.append(random.choice(drinks))

                base_total = sum(items_prices[iid] for iid in order_items_ids)
                total_amount = round(base_total * np.random.normal(1.0, 0.05), 0)
                
                transactions.append((uid, store_id, timestamp, total_amount, 'Card', 0, order_items_ids))

    # Insert transactions and transaction_items
    for t_data in transactions:
        uid, sid, ts, amt, pay, disc, items_ids = t_data
        cursor.execute("INSERT INTO transactions (user_id, store_id, timestamp, total_amount, payment_method, discount_amount) VALUES (?, ?, ?, ?, ?, ?)", (uid, sid, ts, amt, pay, disc))
        tid = cursor.lastrowid
        for iid in items_ids:
            cursor.execute("INSERT INTO transaction_items (transaction_id, menu_item_id, quantity, unit_price) VALUES (?, ?, ?, ?)", (tid, iid, 1, items_prices[iid]))

    conn.commit()
    print(f"Realistic noisy history generated. Total transactions: {len(transactions)}")
    conn.close()

if __name__ == "__main__":
    seed_data()
    generate_history()

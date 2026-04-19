-- ChainNetwork Simulator Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_group TEXT DEFAULT 'A' -- 'A' for Control, 'B' for Treatment
);

-- Stores table
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location_type TEXT -- 'City', 'Mall', 'Office'
);

-- Menu Items table
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT, -- 'Burger', 'Side', 'Drink', 'Dessert'
    price REAL NOT NULL,
    cost REAL NOT NULL -- To calculate margin
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    store_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL NOT NULL,
    payment_method TEXT, -- 'Card', 'Cash'
    discount_amount REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (store_id) REFERENCES stores(id)
);

-- Transaction Items (Linking transactions to menu items)
CREATE TABLE IF NOT EXISTS transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER,
    menu_item_id INTEGER,
    quantity INTEGER DEFAULT 1,
    unit_price REAL NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
);

-- Campaigns table (Defining our automated actions)
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT, -- 'ChurnSave', 'Upsell', 'DeadZone'
    description TEXT
);

-- Interventions table (Logging actions taken)
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    campaign_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    offered_item_id INTEGER,
    discount_percent REAL,
    is_converted BOOLEAN DEFAULT 0, -- Whether the user acted on it
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (offered_item_id) REFERENCES menu_items(id)
);

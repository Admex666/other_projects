import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def init_db(db_path="gym_data.db"):
    """Initializes the SQLite database with the required schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Membership Plans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MembershipPlans (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            duration_days INTEGER,
            entries_allowed INTEGER,
            price INTEGER NOT NULL
        )
    ''')

    # Members
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            registration_date DATE NOT NULL,
            age INTEGER,
            gender TEXT
        )
    ''')

    # Subscriptions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            plan_id INTEGER,
            purchase_date DATE NOT NULL,
            expiry_date DATE,
            entries_used INTEGER DEFAULT 0,
            FOREIGN KEY (member_id) REFERENCES Members (member_id),
            FOREIGN KEY (plan_id) REFERENCES MembershipPlans (plan_id)
        )
    ''')

    # Visits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Visits (
            visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            subscription_id INTEGER,
            check_in_time DATETIME NOT NULL,
            duration_minutes INTEGER,
            FOREIGN KEY (member_id) REFERENCES Members (member_id),
            FOREIGN KEY (subscription_id) REFERENCES Subscriptions (subscription_id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")

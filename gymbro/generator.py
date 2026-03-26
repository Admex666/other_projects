import sqlite3
import random
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def generate_mock_data(db_path="gym_data.db", num_members=200, avg_churn=0.15):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

def generate_mock_data(db_path="gym_data.db", num_members=200, avg_churn=0.15):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure schema is up to date (add name column if old DB exists)
    try:
        cursor.execute("ALTER TABLE Members ADD COLUMN name TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # 1. Clear existing data and RESET IDs
    cursor.execute("DELETE FROM Visits")
    cursor.execute("DELETE FROM Subscriptions")
    cursor.execute("DELETE FROM Members")
    # Reset SQLite Auto-increment sequences
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('Visits', 'Subscriptions', 'Members')")

    # 2. Generate Membership Plans (Only if table is empty)
    cursor.execute("SELECT COUNT(*) FROM MembershipPlans")
    if cursor.fetchone()[0] == 0:
        plans = [
            ("Napijegy", "Occasional", 1, 1, 3000),
            ("5 alkalmas bérlet", "Occasional", 30, 5, 13000),
            ("10 alkalmas bérlet", "Occasional", 45, 10, 24000),
            ("Havi korlátlan", "Monthly", 30, None, 19000),
            ("Éves bérlet", "Monthly", 365, None, 180000)
        ]
        cursor.executemany("INSERT INTO MembershipPlans (name, type, duration_days, entries_allowed, price) VALUES (?, ?, ?, ?, ?)", plans)
    
    # Get current plans
    cursor.execute("SELECT plan_id, name, type, duration_days, entries_allowed, price FROM MembershipPlans")
    db_plans = cursor.fetchall()
    monthly_plans = [row[0] for row in db_plans if row[2] == 'Monthly']
    occasional_plans = [row[0] for row in db_plans if row[2] == 'Occasional']
    all_plan_ids = [row[0] for row in db_plans]

    if not all_plan_ids:
        print("No plans available. Generation aborted.")
        return

    # 3. Generate Members
    start_date = datetime.now() - timedelta(days=365)
    names_m = ["Bence", "Máté", "Levente", "Dávid", "Ádám", "Dániel", "Milán", "Zoltán", "Gergő", "László"]
    names_f = ["Hanna", "Anna", "Luca", "Lili", "Zoé", "Emma", "Léna", "Zorka", "Bogárka", "Eszter"]
    lastnames = ["Kovács", "Nagy", "Kiss", "Szabó", "Tóth", "Farkas", "Varga", "Horváth", "Molnár", "Papp"]

    members = []
    for i in range(num_members):
        reg_date = start_date + timedelta(days=random.randint(0, 300))
        age = int(np.random.gamma(shape=2, scale=5) + 18) 
        age = min(age, 80)
        gender = random.choices(['M', 'F', 'O'], weights=[0.55, 0.40, 0.05])[0]
        
        # Name generation
        first = random.choice(names_m if gender == 'M' else names_f if gender == 'F' else names_m + names_f)
        full_name = f"{random.choice(lastnames)} {first}"
        
        members.append((full_name, reg_date.strftime("%Y-%m-%d"), age, gender))
    
    cursor.executemany("INSERT INTO Members (name, registration_date, age, gender) VALUES (?, ?, ?, ?)", members)
    member_ids = [row[0] for row in cursor.execute("SELECT member_id FROM Members").fetchall()]

    # 4. Generate Subscriptions & Visits (Persona based)
    # The avg_churn parameter influences the ratio of Resolution/Churner personas
    # Personas: 0: Fanatic, 1: Casual, 2: Resolution (Churner)
    res_weight = avg_churn * 1.5 # Higher target churn = more short-lived personas
    fan_weight = 1.0 - res_weight
    persona_weights = [max(0.1, fan_weight * 0.5), 0.4, res_weight]
    
    for i, m_id in enumerate(member_ids):
        persona = random.choices([0, 1, 2], weights=persona_weights)[0]
        reg_date_str = members[i][1]
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
        
        current_date = reg_date
        while current_date < datetime.now():
            # Select plan based on persona
            if persona == 0: # Fanatic
                p_id = random.choice(monthly_plans) if monthly_plans else random.choice(all_plan_ids)
                freq = random.randint(3, 6) # visits per week
            elif persona == 1: # Casual
                p_id = random.choice(all_plan_ids)
                freq = random.randint(1, 4)
            else: # Resolution / Churner
                p_id = random.choice(monthly_plans) if monthly_plans else random.choice(all_plan_ids)
                # Decay frequency
                months_since_reg = (current_date - reg_date).days // 30
                freq = max(0, 4 - months_since_reg) 
                
            cursor.execute("SELECT duration_days, entries_allowed FROM MembershipPlans WHERE plan_id = ?", (p_id,))
            dur, ent = cursor.fetchone()
            
            expiry = current_date + timedelta(days=dur)
            cursor.execute("INSERT INTO Subscriptions (member_id, plan_id, purchase_date, expiry_date) VALUES (?, ?, ?, ?)",
                           (m_id, p_id, current_date.date(), expiry.date()))
            sub_id = cursor.lastrowid
            
            # Generate Visits for this subscription
            used = 0
            temp_date = current_date
            while temp_date < expiry and temp_date < datetime.now():
                if freq > 0:
                    # Distribute visits in the week
                    days_step = 7 / freq
                    temp_date += timedelta(days=random.uniform(days_step*0.5, days_step*1.5))
                    
                    if temp_date < expiry and temp_date < datetime.now():
                        if ent is None or used < ent:
                            visit_time = temp_date.replace(hour=random.randint(6, 20), minute=random.randint(0, 59))
                            cursor.execute("INSERT INTO Visits (member_id, subscription_id, check_in_time, duration_minutes) VALUES (?, ?, ?, ?)",
                                           (m_id, sub_id, visit_time, random.randint(45, 120)))
                            used += 1
                else:
                    break
            
            cursor.execute("UPDATE Subscriptions SET entries_used = ? WHERE subscription_id = ?", (used, sub_id))
            
            # Decide if they renew
            if freq == 0 or (persona == 2 and random.random() < 0.7) or (persona == 1 and random.random() < 0.3):
                break # Churned
            
            current_date = expiry + timedelta(days=random.randint(0, 3)) # Short gap before renewal

    conn.commit()
    conn.close()

if __name__ == "__main__":
    from db_utils import init_db
    init_db()
    generate_mock_data()
    print("Mock data generated.")

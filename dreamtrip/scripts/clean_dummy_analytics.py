"""
Clean dummy users and dummy test events from data/analytics.db
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "analytics.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Töröljük a dummy teszt felhasználókat
c.execute("DELETE FROM beta_users WHERE username IN ('demo', 'utazasmagus', 'wayzio') OR username LIKE 'test_advisor_%'")

# 2. Biztosítsuk hogy 'admin' és 'bean' létezik
c.execute("""
INSERT OR REPLACE INTO beta_users (username, password_hash, full_name, company_name, email, role, is_active, last_active_at)
VALUES 
('admin', 'optivoya2024', 'Adminisztrátor', 'Optivoya HQ', 'admin@optivoya.com', 'admin', 1, CURRENT_TIMESTAMP),
('bean', 'bean', 'Bean (Founder)', 'Optivoya HQ', 'adam@optivoya.com', 'advisor', 1, CURRENT_TIMESTAMP)
""")

# 3. Töröljük a dummy teszteseményeket (csak a valós bean és releváns események maradnak)
c.execute("DELETE FROM telemetry_events WHERE user_id LIKE 'test_advisor_%' OR user_id IN ('demo', 'utazasmagus', 'anonymous_guest')")
c.execute("DELETE FROM user_sessions WHERE user_id LIKE 'test_advisor_%' OR user_id IN ('demo', 'utazasmagus', 'anonymous_guest')")

conn.commit()

print("--- TISZTÍTÁS UTÁNI FELHASZNÁLÓK ---")
for r in c.execute("SELECT id, username, full_name, company_name, role FROM beta_users").fetchall():
    print(r)

print("\n--- TISZTÍTÁS UTÁNI ESEMÉNYEK ---")
for r in c.execute("SELECT id, user_id, event_type, module, created_at FROM telemetry_events").fetchall():
    print(r)

conn.close()
print("\n[OK] Dummy adatok sikeresen törölve!")

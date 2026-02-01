import sqlite3
import os

DB_PATH = "backend/data/users.db"

def fix_sets():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Checking for set_id prefixes...")
    c.execute("SELECT id, set_id FROM items WHERE set_id LIKE 'set_%'")
    rows = c.fetchall()
    
    if not rows:
        print("No items with 'set_' prefix found. Checking if any set_ids exist...")
        c.execute("SELECT id, set_id FROM items WHERE set_id IS NOT NULL")
        all_rows = c.fetchall()
        print(f"Found {len(all_rows)} items with set_id.")
        for r in all_rows:
            print(f" - {r[0]}: {r[1]}")
    else:
        print(f"Found {len(rows)} items with 'set_' prefix. Fixing...")
        c.execute("UPDATE items SET set_id = REPLACE(set_id, 'set_', '') WHERE set_id LIKE 'set_%'")
        conn.commit()
        print("Fixed set_ids.")
        
    conn.close()

if __name__ == "__main__":
    fix_sets()

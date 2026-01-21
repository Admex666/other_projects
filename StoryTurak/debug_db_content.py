import sqlite3
import os

# Pointing to the same location we setup
DB_PATH = os.path.join("backend", "data", "users.db")

print(f"Checking DB at: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print("❌ DB FILE NOT FOUND!")
    exit()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("\n--- TABLES ---")
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(c.fetchall())

print("\n--- CHARACTERS TABLE SCHEMA ---")
c.execute("PRAGMA table_info(characters)")
cols = c.fetchall()
for col in cols:
    print(col)

print("\n--- USERS ---")
c.execute("SELECT id, username FROM users")
users = c.fetchall()
print(users)

print("\n--- CHARACTERS ---")
c.execute("SELECT id, user_id, name, inventory FROM characters")
chars = c.fetchall()
for char in chars:
    print(char)
    # Check normalized items
    print(f"   -> Items for {char[0]}:")
    try:
        c.execute("SELECT * FROM character_items WHERE character_id=?", (char[0],))
        items = c.fetchall()
        print(items)
    except Exception as e:
        print(f"   ❌ Query failed: {e}")

conn.close()

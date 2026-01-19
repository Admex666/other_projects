import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", "data", "users.db")
# Adjusting path to be relative to the root if needed, but let's try to find it correctly.
# The previous DB_PATH was os.path.join(os.path.dirname(__file__), "data", "users.db") where __file__ was backend/db.py.
# Now it's backend/app/db/database.py. 

def get_connection():
    # Make sure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, steps INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Progress table
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                 (user_id TEXT, story_id TEXT, node_id TEXT, variables TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (user_id, story_id))''')
                  
    # Sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id TEXT PRIMARY KEY, host_id TEXT, story_id TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                 
    # Session players table
    c.execute('''CREATE TABLE IF NOT EXISTS session_players
                 (session_id TEXT, user_id TEXT, PRIMARY KEY (session_id, user_id))''')

    # Characters table
    c.execute('''CREATE TABLE IF NOT EXISTS characters
                 (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, character_class TEXT, level INTEGER DEFAULT 1, steps INTEGER DEFAULT 0, weekly_steps INTEGER DEFAULT 0,
                  max_hp INTEGER DEFAULT 10, current_hp INTEGER DEFAULT 10, stats TEXT, inventory TEXT, visited_zones TEXT, completed_quests TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Quests table
    c.execute('''CREATE TABLE IF NOT EXISTS quests
                 (id TEXT PRIMARY KEY, title TEXT, description TEXT, flavor_text TEXT, image_url TEXT, start_location TEXT, stages TEXT,
                  estimated_distance_km REAL, min_level INTEGER, objectives TEXT, rewards_steps INTEGER, rewards_items TEXT, starter_zone_id TEXT)''')

    # User Quests table
    c.execute('''CREATE TABLE IF NOT EXISTS user_quests
                 (id TEXT PRIMARY KEY, user_id TEXT, quest_id TEXT, status TEXT, current_stage_index INTEGER DEFAULT 0,
                  current_objective_index INTEGER DEFAULT 0, current_count INTEGER DEFAULT 0, started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Items table
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id TEXT PRIMARY KEY, name TEXT, description TEXT, type TEXT, value INTEGER, icon_code TEXT, stats TEXT)''')
                 
    # Loot Tables table
    c.execute('''CREATE TABLE IF NOT EXISTS loot_tables
                 (id TEXT PRIMARY KEY, entries TEXT)''')

    # Analytics table
    c.execute('''CREATE TABLE IF NOT EXISTS analytics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, event_type TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    try:
        _migrate_xp_to_steps(c)
    except Exception as e:
        print(f"Migration warning: {e}")

    conn.commit()
    conn.close()

def _migrate_xp_to_steps(cursor):
    # Try to rename columns if they exist in old format
    # SQLite 3.25+ supports RENAME COLUMN
    try:
        cursor.execute("ALTER TABLE users RENAME COLUMN xp TO steps")
    except Exception:
        pass # Already done or table doesn't exist

    try:
        cursor.execute("ALTER TABLE characters RENAME COLUMN xp TO steps")
    except Exception:
        pass

    try:
        # Add weekly_steps if missing
        cursor.execute("ALTER TABLE characters ADD COLUMN weekly_steps INTEGER DEFAULT 0")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE quests RENAME COLUMN rewards_xp TO rewards_steps")
    except Exception:
        pass

def execute_query(query, params=()):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        return c.fetchall()
    finally:
        conn.close()

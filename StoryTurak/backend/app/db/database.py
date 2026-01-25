import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "users.db")
# Path: backend/app/db/database.py -> backend/app/db -> backend/app -> backend -> backend/data/users.db
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
                 (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, character_class TEXT, faction TEXT DEFAULT 'none', currency INTEGER DEFAULT 0,
                  weekly_streak_count INTEGER DEFAULT 0, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, steps INTEGER DEFAULT 0, weekly_steps INTEGER DEFAULT 0,
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
                 (id TEXT PRIMARY KEY, name TEXT, description TEXT, type TEXT, rarity TEXT DEFAULT 'common', value INTEGER, icon_code TEXT, stats TEXT,
                  effects TEXT, set_id TEXT)''')
                 
    # Loot Tables table
    c.execute('''CREATE TABLE IF NOT EXISTS loot_tables
                 (id TEXT PRIMARY KEY, entries TEXT)''')

    # Analytics table
    c.execute('''CREATE TABLE IF NOT EXISTS analytics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, event_type TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, transaction_type TEXT, item_id TEXT, quantity INTEGER, 
                  currency_change INTEGER, balance_after INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # --- NORMALIZED TABLES (v2) ---
    
    # Character Items (Inventory joined)
    c.execute('''CREATE TABLE IF NOT EXISTS character_items
                 (character_id TEXT, item_id TEXT, quantity INTEGER DEFAULT 1, is_equipped BOOLEAN DEFAULT 0,
                  PRIMARY KEY (character_id, item_id),
                  FOREIGN KEY(character_id) REFERENCES characters(id))''')

    # Character Zones (Visited Zones joined)
    c.execute('''CREATE TABLE IF NOT EXISTS character_zones
                 (character_id TEXT, zone_id TEXT, visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (character_id, zone_id),
                  FOREIGN KEY(character_id) REFERENCES characters(id))''')

    # --- STAR SCHEMA / CONTENT TABLES ---

    # Zones (Dimension)
    c.execute('''CREATE TABLE IF NOT EXISTS zones
                 (id TEXT PRIMARY KEY, name TEXT, description TEXT, boundary_points TEXT, difficulty_level INTEGER, min_level INTEGER DEFAULT 1)''')

    # Encounters (Dimension)
    c.execute('''CREATE TABLE IF NOT EXISTS encounters
                 (id TEXT PRIMARY KEY, zone_id TEXT, title TEXT, description TEXT, type TEXT, location_lat REAL, location_lon REAL, 
                  trigger_radius REAL DEFAULT 20.0, definition TEXT,
                  FOREIGN KEY(zone_id) REFERENCES zones(id))''')

    # Quest Stages (Normalized Stages)
    c.execute('''CREATE TABLE IF NOT EXISTS quest_stages
                 (quest_id TEXT, stage_index INTEGER, description TEXT, target_encounter_id TEXT, target_zone_id TEXT,
                  PRIMARY KEY (quest_id, stage_index),
                  FOREIGN KEY(quest_id) REFERENCES quests(id),
                  FOREIGN KEY(target_encounter_id) REFERENCES encounters(id))''')

    # Loot Entries (Normalized Loot)
    c.execute('''CREATE TABLE IF NOT EXISTS loot_table_entries
                 (loot_table_id TEXT, item_id TEXT, chance REAL, min_qty INTEGER, max_qty INTEGER,
                  PRIMARY KEY (loot_table_id, item_id),
                  FOREIGN KEY(item_id) REFERENCES items(id))''')

    # Character Collections (Zeigarnik Effect)
    c.execute('''CREATE TABLE IF NOT EXISTS character_collections
                 (character_id TEXT, collection_id TEXT, item_id TEXT, found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (character_id, collection_id, item_id),
                  FOREIGN KEY(character_id) REFERENCES characters(id),
                  FOREIGN KEY(item_id) REFERENCES items(id))''')

    # Zone Control table (Faction System)
    c.execute('''CREATE TABLE IF NOT EXISTS zone_control
                 (zone_id TEXT PRIMARY KEY, controlling_faction TEXT DEFAULT 'none',
                  faction_points_transformer INTEGER DEFAULT 0,
                  faction_points_chronicler INTEGER DEFAULT 0,
                  faction_points_forgotten INTEGER DEFAULT 0,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    try:
        _migrate_xp_to_steps(c)
        _migrate_gamification_columns(c)
        _migrate_json_to_relational(c)
        # Seed Content from Code to DB (One-Way Sync for now)
        from app.services.content_service import seed_world_content
        # We need to commit first because seed_world_content uses execute_query which opens its own connection
        conn.commit() 
        seed_world_content()
    except Exception as e:
        print(f"Migration warning: {e}")

    conn.commit()
    conn.close()

def _migrate_json_to_relational(cursor):
    import json
    # Check if we have data in the old JSON columns and if new tables are empty
    cursor.execute("SELECT count(*) FROM character_items")
    if cursor.fetchone()[0] > 0:
        return # Already migrated

    print("🔄 Migrating JSON Blobs to Relational Tables...")
    
    cursor.execute("SELECT id, inventory, visited_zones FROM characters")
    chars = cursor.fetchall()
    
    for char in chars:
        char_id = char['id']
        inv_json = char['inventory']
        zones_json = char['visited_zones']
        
        # Migrate Inventory
        if inv_json:
            try:
                inventory = json.loads(inv_json)
                for slot in inventory:
                    # slot is likely a dict from the Pydantic model dump
                    # {'item_id': '...', 'quantity': 1, 'equipped': False}
                    if isinstance(slot, dict):
                         item_id = slot.get('item_id')
                         qty = slot.get('quantity', 1)
                         equipped = 1 if slot.get('equipped', False) else 0
                         
                         if item_id:
                             cursor.execute("INSERT OR REPLACE INTO character_items (character_id, item_id, quantity, is_equipped) VALUES (?, ?, ?, ?)",
                                            (char_id, item_id, qty, equipped))
            except Exception as e:
                print(f"Failed to migrate inventory for {char_id}: {e}")

        # Migrate Zones
        if zones_json:
            try:
                zones = json.loads(zones_json)
                for z_id in zones:
                    if isinstance(z_id, str):
                        cursor.execute("INSERT OR IGNORE INTO character_zones (character_id, zone_id) VALUES (?, ?)", (char_id, z_id))
            except Exception as e:
                print(f"Failed to migrate zones for {char_id}: {e}")

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



def _migrate_gamification_columns(cursor):
    # Characters: Faction, Currency, Streak, XP
    try: cursor.execute("ALTER TABLE characters ADD COLUMN faction TEXT DEFAULT 'none'")
    except: pass
    try: cursor.execute("ALTER TABLE characters ADD COLUMN currency INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE characters ADD COLUMN weekly_streak_count INTEGER DEFAULT 0")
    except: pass
    try: cursor.execute("ALTER TABLE characters ADD COLUMN xp INTEGER DEFAULT 0")
    except: pass
    
    # Items: Rarity, SetID, Effects
    try: cursor.execute("ALTER TABLE items ADD COLUMN rarity TEXT DEFAULT 'common'")
    except: pass
    try: cursor.execute("ALTER TABLE items ADD COLUMN set_id TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE items ADD COLUMN effects TEXT")
    except: pass
    
    # Character Items: Rarity? No, comes from join. Effects? No.
    # But maybe distinct items (instances)? For now kept simple.

def execute_query(query, params=()):
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        return c.fetchall()
    finally:
        conn.close()

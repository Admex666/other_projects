import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "users.db")
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    is_postgres = DATABASE_URL is not None
    
    # User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Characters Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            class TEXT,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 10,
            stats TEXT, -- JSON
            inventory TEXT, -- JSON
            visited_zones TEXT, -- JSON
            completed_quests TEXT, -- JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Progress Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            user_id TEXT,
            story_id TEXT,
            current_node TEXT,
            variables TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, story_id)
        )
    ''')
    # Analytics Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS analytics (
            {"id SERIAL PRIMARY KEY" if is_postgres else "id INTEGER PRIMARY KEY AUTOINCREMENT"},
            user_id TEXT,
            event_type TEXT,
            data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Session Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            host_id TEXT,
            story_id TEXT,
            status TEXT DEFAULT 'waiting',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Session Players Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_players (
            session_id TEXT,
            user_id TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, user_id)
        )
    ''')
    
    # Quests Table (Static Quest Definitions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quests (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            min_level INTEGER,
            objectives TEXT, -- JSON
            rewards_xp INTEGER,
            rewards_items TEXT, -- JSON
            starter_zone_id TEXT
        )
    ''')

    # User Quests Table (Player Progress)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_quests (
            id TEXT PRIMARY KEY, -- Unique ID (e.g. uuid)
            user_id TEXT,
            quest_id TEXT,
            status TEXT, -- available, active, completed, failed
            current_objective_index INTEGER DEFAULT 0,
            current_count INTEGER DEFAULT 0,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(quest_id) REFERENCES quests(id)
        )
    ''')

    # Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            type TEXT,
            value INTEGER,
            icon_code TEXT,
            stats TEXT -- JSON
        )
    ''')

    # Loot Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loot_tables (
            id TEXT PRIMARY KEY,
            entries TEXT -- JSON List[LootEntry]
        )
    ''')
    
    conn.commit()
    conn.close()

def execute_query(query, params=()):
    # Replace ? with %s for Postgres compatibility if needed
    if DATABASE_URL:
        query = query.replace('?', '%s')
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            result = []
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()
    return result

# --- User Functions ---
def get_user_by_username(username):
    res = execute_query("SELECT id, username, password_hash, xp FROM users WHERE username = ?", (username,))
    if res:
        return {"id": res[0][0], "username": res[0][1], "password_hash": res[0][2], "xp": res[0][3]}
    return None

def update_user_xp(user_id, xp_gain):
    execute_query("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_gain, user_id))

def create_user(user_id, username, password_hash):
    execute_query("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", 
                  (user_id, username, password_hash))

# --- Character Functions ---
def create_character(char_data: dict):
    stats_json = json.dumps(char_data.get("stats", {}))
    inv_json = json.dumps(char_data.get("inventory", []))
    zones_json = json.dumps(char_data.get("visited_zones", []))
    quests_json = json.dumps(char_data.get("completed_quests", []))
    
    execute_query('''
        INSERT INTO characters (id, user_id, name, class, level, xp, hp, stats, inventory, visited_zones, completed_quests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        char_data["id"], char_data["user_id"], char_data["name"], char_data["character_class"],
        char_data.get("level", 1), char_data.get("xp", 0), char_data.get("max_hp", 10),
        stats_json, inv_json, zones_json, quests_json
    ))

def get_characters_by_user(user_id: str):
    res = execute_query("SELECT * FROM characters WHERE user_id = ?", (user_id,))
    chars = []
    for r in res:
        inventory = json.loads(r[8]) if r[8] else []
        
        # Enrich inventory with item metadata
        enriched_inventory = []
        for slot in inventory:
            item = get_item(slot["item_id"])
            if item:
                slot.update({
                    "name": item["name"],
                    "description": item["description"],
                    "icon_code": item["icon_code"],
                    "stats": item["stats"]
                })
            enriched_inventory.append(slot)

        # Schema: 0:id, 1:user, 2:name, 3:class, 4:lvl, 5:xp, 6:hp, 7:stats, 8:inv, 9:zones, 10:quests, 11:created
        chars.append({
            "id": r[0],
            "user_id": r[1],
            "name": r[2],
            "character_class": r[3],
            "level": r[4],
            "xp": r[5],
            "max_hp": r[6],
            "current_hp": r[6], # Simplify for now, load max as current on fresh load
            "stats": json.loads(r[7]) if r[7] else {},
            "inventory": enriched_inventory,
            "visited_zones": json.loads(r[9]) if r[9] else [],
            "completed_quests": json.loads(r[10]) if r[10] else [],
            "created_at": r[11]
        })
    return chars

def update_character_inventory(char_id: str, new_inventory: list):
    inv_json = json.dumps(new_inventory)
    execute_query("UPDATE characters SET inventory = ? WHERE id = ?", (inv_json, char_id))

# --- Progress Functions ---
def save_progress(user_id, story_id, node_id, variables_dict):
    vars_json = json.dumps(variables_dict)
    if DATABASE_URL:
        # Postgres UPSERT syntax
        execute_query('''
            INSERT INTO user_progress (user_id, story_id, current_node, variables, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (user_id, story_id) DO UPDATE SET
                current_node = EXCLUDED.current_node,
                variables = EXCLUDED.variables,
                last_updated = EXCLUDED.last_updated
        ''', (user_id, story_id, node_id, vars_json, datetime.now()))
    else:
        # SQLite UPSERT syntax
        execute_query('''
            INSERT INTO user_progress (user_id, story_id, current_node, variables, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, story_id) DO UPDATE SET
                current_node = excluded.current_node,
                variables = excluded.variables,
                last_updated = excluded.last_updated
        ''', (user_id, story_id, node_id, vars_json, datetime.now().isoformat()))

def get_progress(user_id, story_id):
    res = execute_query("SELECT current_node, variables FROM user_progress WHERE user_id = ? AND story_id = ?", 
                        (user_id, story_id))
    if res:
        return {"nodeId": res[0][0], "variables": json.loads(res[0][1])}
    return None

# --- Session Functions ---
def db_create_session(session_id, host_id, story_id):
    execute_query("INSERT INTO sessions (id, host_id, story_id, status) VALUES (?, ?, ?, 'waiting')", 
                  (session_id, host_id, story_id))
    db_join_session(session_id, host_id)

def db_join_session(session_id, user_id):
    if DATABASE_URL:
        execute_query("INSERT INTO session_players (session_id, user_id) VALUES (?, ?) ON CONFLICT DO NOTHING", 
                      (session_id, user_id))
    else:
        execute_query("INSERT OR IGNORE INTO session_players (session_id, user_id) VALUES (?, ?)", 
                      (session_id, user_id))

def db_update_session_status(session_id, status):
    execute_query("UPDATE sessions SET status = ? WHERE id = ?", (status, session_id))

def get_user_sessions(user_id):
    query = '''
        SELECT s.id, s.host_id, s.story_id, s.status, s.created_at
        FROM sessions s
        JOIN session_players sp ON s.id = sp.session_id
        WHERE sp.user_id = ?
        ORDER BY s.created_at DESC
    '''
    res = execute_query(query, (user_id,))
    output = []
    for r in res:
        # Get players for each session
        players_res = execute_query("SELECT u.id, u.username, u.xp FROM users u JOIN session_players sp ON u.id = sp.user_id WHERE sp.session_id = ?", (r[0],))
        players = [{"id": p[0], "username": p[1], "xp": p[2]} for p in players_res]
        output.append({
            "id": r[0],
            "hostId": r[1],
            "campaignId": r[2],
            "status": r[3],
            "createdAt": r[4],
            "players": players
        })
    return output

# --- Quest Functions ---
def create_quest(quest_data: dict):
    objectives_json = json.dumps(quest_data.get("objectives", []))
    items_json = json.dumps(quest_data.get("rewards_items", []))
    
    execute_query('''
        INSERT OR IGNORE INTO quests (id, title, description, min_level, objectives, rewards_xp, rewards_items, starter_zone_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        quest_data["id"], quest_data["title"], quest_data["description"],
        quest_data.get("min_level", 1), objectives_json,
        quest_data.get("rewards_xp", 100), items_json,
        quest_data.get("starter_zone_id")
    ))

def get_quest_by_id(quest_id):
    res = execute_query("SELECT * FROM quests WHERE id = ?", (quest_id,))
    if res:
        r = res[0]
        return {
            "id": r[0], "title": r[1], "description": r[2], "min_level": r[3],
            "objectives": json.loads(r[4]) if r[4] else [],
            "rewards_xp": r[5], "rewards_items": json.loads(r[6]) if r[6] else [],
            "starter_zone_id": r[7]
        }
    return None

def get_user_quests(user_id):
    query = '''
        SELECT uq.id, uq.user_id, uq.quest_id, uq.status, uq.current_objective_index, uq.current_count, uq.started_at,
               q.title, q.description
        FROM user_quests uq
        JOIN quests q ON uq.quest_id = q.id
        WHERE uq.user_id = ?
    '''
    res = execute_query(query, (user_id,))
    output = []
    for r in res:
        output.append({
            "id": r[0], "user_id": r[1], "quest_id": r[2], "status": r[3],
            "current_objective_index": r[4], "current_count": r[5], "started_at": r[6],
            "quest_title": r[7], "quest_description": r[8]
        })
    return output

def add_quest_to_user(user_quest_data: dict):
    execute_query('''
        INSERT INTO user_quests (id, user_id, quest_id, status, current_objective_index, current_count, started_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_quest_data["id"], user_quest_data["user_id"], user_quest_data["quest_id"],
        user_quest_data["status"], user_quest_data["current_objective_index"],
        user_quest_data["current_count"], datetime.now()
    ))

def update_user_quest_progress(uq_id, new_count, new_index=None, new_status=None):
    query = "UPDATE user_quests SET current_count = ?"
    params = [new_count]
    if new_index is not None:
        query += ", current_objective_index = ?"
        params.append(new_index)
    if new_status:
        query += ", status = ?"
        params.append(new_status)
    
    query += " WHERE id = ?"
    params.append(uq_id)
    execute_query(query, tuple(params))


# --- Item & Loot Functions ---
def create_item(item_data: dict):
    stats_json = json.dumps(item_data.get("stats", {}))
    execute_query('''
        INSERT OR IGNORE INTO items (id, name, description, type, value, icon_code, stats)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        item_data["id"], item_data["name"], item_data["description"],
        item_data["type"], item_data.get("value", 0), item_data["icon_code"],
        stats_json
    ))

def get_item(item_id):
    res = execute_query("SELECT * FROM items WHERE id = ?", (item_id,))
    if res:
        r = res[0]
        return {
            "id": r[0], "name": r[1], "description": r[2], "type": r[3],
            "value": r[4], "icon_code": r[5], "stats": json.loads(r[6]) if r[6] else {}
        }
    return None

def create_loot_table(lt_data: dict):
    entries_json = json.dumps(lt_data.get("entries", []))
    execute_query("INSERT OR IGNORE INTO loot_tables (id, entries) VALUES (?, ?)", 
                  (lt_data["id"], entries_json))

def get_loot_table(lt_id):
    res = execute_query("SELECT * FROM loot_tables WHERE id = ?", (lt_id,))
    if res:
        return {"id": res[0][0], "entries": json.loads(res[0][1])}
    return None

def update_character_xp_and_level(char_id: str, new_xp: int, new_level: int):
    execute_query(
        "UPDATE characters SET xp = ?, level = ? WHERE id = ?",
        (new_xp, new_level, char_id)
    )

def update_character_visited_zones(char_id: str, zone_id: str):
    res = execute_query("SELECT visited_zones FROM characters WHERE id = ?", (char_id,))
    if res:
        zones = json.loads(res[0][0]) if res[0][0] else []
        if zone_id not in zones:
            zones.append(zone_id)
            execute_query("UPDATE characters SET visited_zones = ? WHERE id = ?", (json.dumps(zones), char_id))

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()

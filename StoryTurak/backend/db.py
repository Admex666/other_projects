
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
    
    # In Postgres, use SERIAL for id. In SQLite, AUTOINCREMENT works on INTEGER PRIMARY KEY.
    # We'll use a generic approach.
    is_postgres = DATABASE_URL is not None
    
    # User Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()

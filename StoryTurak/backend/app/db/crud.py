import json
from .database import get_connection, execute_query

# --- User Functions ---
def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_steps(user_id, steps_gain):
    execute_query("UPDATE users SET steps = steps + ? WHERE id = ?", (steps_gain, user_id))

def create_user(user_id, username, password_hash):
    execute_query("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", (user_id, username, password_hash))

# --- Character Functions ---
def create_character(char_data: dict):
    execute_query(
        "INSERT INTO characters (id, user_id, name, character_class, level, steps, weekly_steps, max_hp, stats, inventory, visited_zones, completed_quests) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (char_data["id"], char_data["user_id"], char_data["name"], char_data["character_class"], char_data["level"], char_data["steps"], char_data.get("weekly_steps", 0), char_data["max_hp"], 
         json.dumps(char_data.get("stats", {})), json.dumps(char_data.get("inventory", [])), json.dumps(char_data.get("visited_zones", [])), json.dumps(char_data.get("completed_quests", [])))
    )

def get_characters_by_user(user_id: str):
    rows = execute_query("SELECT * FROM characters WHERE user_id = ?", (user_id,))
    chars = []
    chars = []
    
    # Pre-fetch all needed items to enrich inventory
    all_item_ids = set()
    temp_chars = []
    for r in rows:
        d = dict(r)
        d["stats"] = json.loads(d["stats"]) if d["stats"] else {}
        d["inventory"] = json.loads(d["inventory"]) if d["inventory"] else []
        d["visited_zones"] = json.loads(d["visited_zones"]) if d["visited_zones"] else []
        d["completed_quests"] = json.loads(d["completed_quests"]) if d["completed_quests"] else []
        
        for slot in d["inventory"]:
            all_item_ids.add(slot["item_id"])
        temp_chars.append(d)
        
    # Batch fetch items
    items_map = {}
    if all_item_ids:
        placeholders = ','.join(['?'] * len(all_item_ids))
        i_rows = execute_query(f"SELECT * FROM items WHERE id IN ({placeholders})", tuple(all_item_ids))
        for ir in i_rows:
            i_dict = dict(ir)
            # Parse stats for item
            i_dict["stats"] = json.loads(str(i_dict["stats"])) if i_dict["stats"] else {}
            items_map[i_dict["id"]] = i_dict

    # Enrich inventory
    for c in temp_chars:
        for slot in c["inventory"]:
            i_id = slot["item_id"]
            if i_id in items_map:
                item = items_map[i_id]
                slot["name"] = item["name"]
                slot["description"] = item["description"]
                slot["icon_code"] = item["icon_code"]
                slot["stats"] = item["stats"]
        chars.append(c)
        
    return chars

def update_character_inventory(char_id: str, new_inventory: list):
    execute_query("UPDATE characters SET inventory = ? WHERE id = ?", (json.dumps(new_inventory), char_id))

def update_character_steps_and_level(char_id: str, new_steps: int, new_level: int):
    execute_query("UPDATE characters SET steps = ?, level = ? WHERE id = ?", (new_steps, new_level, char_id))

def update_character_visited_zones(char_id: str, zone_id: str):
    chars = execute_query("SELECT visited_zones FROM characters WHERE id = ?", (char_id,))
    if chars:
        vz = json.loads(chars[0][0]) if chars[0][0] else []
        if zone_id not in vz:
            vz.append(zone_id)
            execute_query("UPDATE characters SET visited_zones = ? WHERE id = ?", (json.dumps(vz), char_id))

# --- Progress Functions ---
def save_progress(user_id, story_id, node_id, variables_dict):
    execute_query(
        "INSERT INTO progress (user_id, story_id, node_id, variables) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, story_id) DO UPDATE SET node_id=excluded.node_id, variables=excluded.variables, updated_at=CURRENT_TIMESTAMP",
        (user_id, story_id, node_id, json.dumps(variables_dict))
    )

def get_progress(user_id, story_id):
    rows = execute_query("SELECT node_id, variables FROM progress WHERE user_id = ? AND story_id = ?", (user_id, story_id))
    if rows:
        return {"nodeId": rows[0][0], "variables": json.loads(rows[0][1])}
    return None

# --- Session Functions ---
def db_create_session(session_id, host_id, story_id):
    execute_query("INSERT INTO sessions (id, host_id, story_id, status) VALUES (?, ?, ?, ?)", (session_id, host_id, story_id, "waiting"))

def db_join_session(session_id, user_id):
    execute_query("INSERT OR IGNORE INTO session_players (session_id, user_id) VALUES (?, ?)", (session_id, user_id))

def db_update_session_status(session_id, status):
    execute_query("UPDATE sessions SET status = ? WHERE id = ?", (status, session_id))

def get_user_sessions(user_id):
    rows = execute_query("SELECT s.* FROM sessions s JOIN session_players sp ON s.id = sp.session_id WHERE sp.user_id = ?", (user_id,))
    return [dict(r) for r in rows]

# --- Quest Functions ---
def create_quest(q: dict):
    execute_query(
        "INSERT INTO quests (id, title, description, flavor_text, image_url, start_location, stages, estimated_distance_km, min_level, objectives, rewards_steps, rewards_items, starter_zone_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description, stages=excluded.stages, start_location=excluded.start_location",
        (q["id"], q["title"], q["description"], q.get("flavor_text"), q.get("image_url"), json.dumps(q.get("start_location")), 
         json.dumps(q.get("stages", [])), q.get("estimated_distance_km", 0.0), q.get("min_level", 1), 
         json.dumps(q.get("objectives", [])), q.get("rewards_steps", 100), json.dumps(q.get("rewards_items", [])), q.get("starter_zone_id"))
    )

def get_all_quests():
    rows = execute_query("SELECT * FROM quests")
    quests = []
    for r in rows:
        d = dict(r)
        d["start_location"] = json.loads(d["start_location"]) if d["start_location"] else None
        d["stages"] = json.loads(d["stages"]) if d["stages"] else []
        d["objectives"] = json.loads(d["objectives"]) if d["objectives"] else []
        d["rewards_items"] = json.loads(d["rewards_items"]) if d["rewards_items"] else []
        quests.append(d)
    return quests

def get_quest_by_id(quest_id):
    rows = execute_query("SELECT * FROM quests WHERE id = ?", (quest_id,))
    if rows:
        d = dict(rows[0])
        d["start_location"] = json.loads(d["start_location"]) if d["start_location"] else None
        d["stages"] = json.loads(d["stages"]) if d["stages"] else []
        d["objectives"] = json.loads(d["objectives"]) if d["objectives"] else []
        d["rewards_items"] = json.loads(d["rewards_items"]) if d["rewards_items"] else []
        return d
    return None

def get_user_quests(user_id):
    rows = execute_query("""
        SELECT uq.*, q.title as quest_title, q.description as quest_description 
        FROM user_quests uq 
        JOIN quests q ON uq.quest_id = q.id 
        WHERE uq.user_id = ?
    """, (user_id,))
    return [dict(r) for r in rows]

def add_quest_to_user(uq: dict):
    execute_query(
        "INSERT INTO user_quests (id, user_id, quest_id, status, current_stage_index, current_objective_index, current_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (uq["id"], uq["user_id"], uq["quest_id"], uq["status"], uq.get("current_stage_index", 0), uq.get("current_objective_index", 0), uq.get("current_count", 0))
    )

def update_user_quest_progress(uq_id, new_count, new_index=None, new_status=None, new_stage_index=None):
    query = "UPDATE user_quests SET current_count = ?"
    params = [new_count]
    if new_index is not None:
        query += ", current_objective_index = ?"
        params.append(new_index)
    if new_stage_index is not None:
        query += ", current_stage_index = ?"
        params.append(new_stage_index)
    if new_status:
        query += ", status = ?"
        params.append(new_status)
    query += " WHERE id = ?"
    params.append(uq_id)
    execute_query(query, tuple(params))

# --- Item & Loot Functions ---
def create_item(item_data: dict):
    execute_query(
        "INSERT INTO items (id, name, description, type, value, icon_code, stats) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
        (item_data["id"], item_data["name"], item_data["description"], item_data["type"], item_data["value"], item_data["icon_code"], json.dumps(item_data.get("stats", {})))
    )

def get_item(item_id):
    rows = execute_query("SELECT * FROM items WHERE id = ?", (item_id,))
    if rows:
        d = dict(rows[0])
        d["stats"] = json.loads(d["stats"]) if d["stats"] else {}
        return d
    return None

def create_loot_table(lt_data: dict):
    execute_query("INSERT INTO loot_tables (id, entries) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET entries=excluded.entries", 
                  (lt_data["id"], json.dumps(lt_data["entries"])))

def get_loot_table(lt_id):
    rows = execute_query("SELECT * FROM loot_tables WHERE id = ?", (lt_id,))
    if rows:
        d = dict(rows[0])
        d["entries"] = json.loads(d["entries"]) if d["entries"] else []
        return d
    return None

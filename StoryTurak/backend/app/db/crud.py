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

# --- Character Functions (Refactored for Normalization) ---
def create_character(char_data: dict):
    # Insert basic data (Inventory/Zones/Quests columns ignored/deprecated)
    execute_query(
        "INSERT INTO characters (id, user_id, name, character_class, faction, currency, level, steps, weekly_steps, max_hp, stats) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (char_data["id"], char_data["user_id"], char_data["name"], char_data["character_class"], char_data.get("faction", "none"), char_data.get("currency", 0),
         char_data["level"], char_data["steps"], char_data.get("weekly_steps", 0), char_data["max_hp"], 
         json.dumps(char_data.get("stats", {})))
    )

def get_characters_by_user(user_id: str):
    rows = execute_query("SELECT * FROM characters WHERE user_id = ?", (user_id,))
    chars = []
    
    for r in rows:
        d = dict(r)
        
        # Legacy schema mapping: DB has 'class', Model expects 'character_class'
        if "class" in d and "character_class" not in d:
             d["character_class"] = d["class"]
             
        char_id = d["id"]
        d["stats"] = json.loads(d["stats"]) if d["stats"] else {}
        
        # 1. Fetch Inventory from character_items
        inv_rows = execute_query("""
            SELECT ci.item_id, ci.quantity, ci.is_equipped, i.name, i.description, i.icon_code, i.stats, i.type, i.value, i.rarity, i.effects 
            FROM character_items ci
            LEFT JOIN items i ON ci.item_id = i.id
            WHERE ci.character_id = ?
        """, (char_id,))
        
        d["inventory"] = []
        for ir in inv_rows:
            inv_item = dict(ir)
            # Normalize keys to match schema
            inv_item["equipped"] = bool(inv_item["is_equipped"])
            # Parse item stats if present
            if inv_item.get("stats"):
                 try:
                     inv_item["stats"] = json.loads(inv_item["stats"])
                 except:
                     inv_item["stats"] = {}
            else:
                 inv_item["stats"] = {}
            
            if inv_item.get("effects"):
                 try:
                     inv_item["effects"] = json.loads(inv_item["effects"])
                 except:
                     inv_item["effects"] = []
            else:
                 inv_item["effects"] = []
                 
            d["inventory"].append(inv_item)
            
        # 2. Fetch Visited Zones
        z_rows = execute_query("SELECT zone_id FROM character_zones WHERE character_id = ?", (char_id,))
        d["visited_zones"] = [z[0] for z in z_rows]
        
        # 3. Fetch Completed Quests
        q_rows = execute_query("SELECT quest_id FROM user_quests WHERE user_id = ? AND status = 'completed'", (user_id,))
        d["completed_quests"] = [q[0] for q in q_rows]
        
        chars.append(d)
        
    return chars

def get_character_with_details(char_id: str):
    rows = execute_query("SELECT * FROM characters WHERE id = ?", (char_id,))
    if not rows:
        return None
        
    d = dict(rows[0])
    
    # Legacy schema mapping
    if "class" in d and "character_class" not in d:
         d["character_class"] = d["class"]
         
    d["stats"] = json.loads(d["stats"]) if d["stats"] else {}
    
    # 1. Fetch Inventory from character_items
    inv_rows = execute_query("""
        SELECT ci.item_id, ci.quantity, ci.is_equipped, i.name, i.description, i.icon_code, i.stats, i.type, i.value, i.rarity, i.effects 
        FROM character_items ci
        LEFT JOIN items i ON ci.item_id = i.id
        WHERE ci.character_id = ?
    """, (char_id,))
    
    d["inventory"] = []
    for ir in inv_rows:
        inv_item = dict(ir)
        inv_item["equipped"] = bool(inv_item["is_equipped"])
        if inv_item.get("stats"):
             try:
                 inv_item["stats"] = json.loads(inv_item["stats"])
             except:
                 inv_item["stats"] = {}
        else:
             inv_item["stats"] = {}
        
        if inv_item.get("effects"):
             try:
                 inv_item["effects"] = json.loads(inv_item["effects"])
             except:
                 inv_item["effects"] = []
        else:
             inv_item["effects"] = []
             
        d["inventory"].append(inv_item)
        
    # 2. Fetch Visited Zones
    z_rows = execute_query("SELECT zone_id FROM character_zones WHERE character_id = ?", (char_id,))
    d["visited_zones"] = [z[0] for z in z_rows]
    
    # 3. Fetch Completed Quests
    # We need user_id for this, which is in d
    q_rows = execute_query("SELECT quest_id FROM user_quests WHERE user_id = ? AND status = 'completed'", (d["user_id"],))
    d["completed_quests"] = [q[0] for q in q_rows]
    
    return d

# Granular Inventory Management
def add_character_item(char_id: str, item_id: str, quantity: int = 1):
    # Check if exists
    row = execute_query("SELECT quantity FROM character_items WHERE character_id = ? AND item_id = ?", (char_id, item_id))
    if row:
        new_qty = row[0][0] + quantity
        execute_query("UPDATE character_items SET quantity = ? WHERE character_id = ? AND item_id = ?", (new_qty, char_id, item_id))
    else:
        execute_query("INSERT INTO character_items (character_id, item_id, quantity, is_equipped) VALUES (?, ?, ?, 0)", (char_id, item_id, quantity))

    # Trigger Collection Check
    try:
        from app.services.collection_service import check_and_update_collection
        check_and_update_collection(char_id, item_id)
    except ImportError:
        pass # Handle circular import if service not ready
    except Exception as e:
        print(f"Collection update failed: {e}")

def remove_character_item(char_id: str, item_id: str, quantity: int = 1):
    print(f"DEBUG DB: remove_character_item {char_id} {item_id} {quantity}")
    row = execute_query("SELECT quantity FROM character_items WHERE character_id = ? AND item_id = ?", (char_id, item_id))
    if not row:
        print("DEBUG DB: Item not found, cannot remove")
        return # Item not found
    
    current_qty = row[0][0]
    if current_qty > quantity:
         print(f"DEBUG DB: Decreasing qty from {current_qty} to {current_qty - quantity}")
         execute_query("UPDATE character_items SET quantity = ? WHERE character_id = ? AND item_id = ?", (current_qty - quantity, char_id, item_id))
    else:
         print("DEBUG DB: Removing item row completely")
         execute_query("DELETE FROM character_items WHERE character_id = ? AND item_id = ?", (char_id, item_id))

def update_character_currency(char_id: str, amount: int):
    # Amount can be positive (add) or negative (subtract)
    print(f"DEBUG DB: update_character_currency {char_id} add {amount}")
    execute_query("UPDATE characters SET currency = currency + ? WHERE id = ?", (amount, char_id))

def get_character_inventory(char_id: str):
    # Helper to return formatted inventory list
    inv_rows = execute_query("""
            SELECT ci.item_id, ci.quantity, ci.is_equipped as equipped, i.name, i.description, i.icon_code, i.stats, i.type, i.value 
            FROM character_items ci
            LEFT JOIN items i ON ci.item_id = i.id
            WHERE ci.character_id = ?
        """, (char_id,))
    res = []
    for r in inv_rows:
        d = dict(r)
        d["equipped"] = bool(d["equipped"])
        if d.get("stats") and isinstance(d["stats"], str):
             try: d["stats"] = json.loads(d["stats"]) 
             except: d["stats"] = {}
        res.append(d)
    return res

def set_item_equipped(char_id: str, item_id: str, is_equipped: bool):
    execute_query("UPDATE character_items SET is_equipped = ? WHERE character_id = ? AND item_id = ?", (1 if is_equipped else 0, char_id, item_id))

def update_character_loadout(char_id: str, item_ids: list[str]):
    # 1. Validation: Max 3 items
    if len(item_ids) > 3:
        raise ValueError("Maximum 3 items can be equipped.")

    # 2. Reset all equipped items for this character
    execute_query("UPDATE character_items SET is_equipped = 0 WHERE character_id = ?", (char_id,))

    # 3. Equip selected items
    # Verify ownership is implicit if we only update where char_id matches
    for i_id in item_ids:
        # We use AND character_id to ensure we only equip if they own it
        execute_query("UPDATE character_items SET is_equipped = 1 WHERE character_id = ? AND item_id = ?", (char_id, i_id))


def update_character_steps_and_level(char_id: str, new_steps: int, new_level: int):
    execute_query("UPDATE characters SET steps = ?, level = ? WHERE id = ?", (new_steps, new_level, char_id))

def update_character_visited_zones(char_id: str, zone_id: str):
    execute_query("INSERT OR IGNORE INTO character_zones (character_id, zone_id) VALUES (?, ?)", (char_id, zone_id))

def log_transaction(character_id: str, transaction_type: str, item_id: str, quantity: int, currency_change: int, balance_after: int):
    print(f"DEBUG DB: log_transaction {transaction_type} for {character_id} / item {item_id} / change {currency_change}")
    execute_query(
        "INSERT INTO transactions (character_id, transaction_type, item_id, quantity, currency_change, balance_after) VALUES (?, ?, ?, ?, ?, ?)",
        (character_id, transaction_type, item_id, quantity, currency_change, balance_after)
    )

def set_character_faction(character_id: str, faction: str):
    execute_query("UPDATE characters SET faction = ? WHERE id = ?", (faction, character_id))

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
        "INSERT INTO quests (id, title, description, flavor_text, image_url, start_location, stages, estimated_distance_km, min_level, objectives, rewards_steps, rewards_items, starter_zone_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description, flavor_text=excluded.flavor_text, image_url=excluded.image_url, start_location=excluded.start_location, stages=excluded.stages, estimated_distance_km=excluded.estimated_distance_km, min_level=excluded.min_level, objectives=excluded.objectives, rewards_steps=excluded.rewards_steps, rewards_items=excluded.rewards_items, starter_zone_id=excluded.starter_zone_id",
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

def get_quest_history(user_id):
    rows = execute_query("""
        SELECT uq.completed_at, q.title, q.rewards_steps 
        FROM user_quests uq 
        JOIN quests q ON uq.quest_id = q.id 
        WHERE uq.user_id = ? AND uq.status = 'completed'
        ORDER BY uq.completed_at DESC
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
        if new_status == 'completed':
            query += ", completed_at = CURRENT_TIMESTAMP"
    query += " WHERE id = ?"
    params.append(uq_id)
    execute_query(query, tuple(params))

# --- Item & Loot Functions ---
def create_item(item_data: dict):
    execute_query(
        "INSERT INTO items (id, name, description, type, rarity, value, icon_code, stats, effects, set_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET set_id=excluded.set_id, rarity=excluded.rarity, effects=excluded.effects, stats=excluded.stats, value=excluded.value, icon_code=excluded.icon_code, description=excluded.description, name=excluded.name, type=excluded.type",
        (item_data["id"], item_data["name"], item_data["description"], item_data["type"], item_data.get("rarity", "common"), 
         item_data["value"], item_data["icon_code"], json.dumps(item_data.get("stats", {})), json.dumps(item_data.get("effects", [])), item_data.get("set_id"))
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

# --- Zone Control Functions ---

def get_zone_control(zone_id):
    rows = execute_query("SELECT * FROM zone_control WHERE zone_id = ?", (zone_id,))
    if rows:
        return dict(rows[0])
    return None

def init_zone_control(zone_id):
    execute_query("INSERT OR IGNORE INTO zone_control (zone_id, controlling_faction) VALUES (?, 'none')", (zone_id,))

def update_zone_points(zone_id: str, faction: str, points: int):
    # Retrieve current state
    zc = get_zone_control(zone_id)
    if not zc:
        init_zone_control(zone_id)
        zc = get_zone_control(zone_id) # reload
    
    if not zc: 
        return # Should not happen

    # Map faction name to column
    # transformers -> faction_points_transformer
    # chroniclers -> faction_points_chronicler
    # forgotten -> faction_points_forgotten
    
    col_name = f"faction_points_{faction.lower()}"
    # Verify column exists (simple check)
    if col_name not in ["faction_points_transformer", "faction_points_chronicler", "faction_points_forgotten"]:
        print(f"Invalid faction for points update: {faction}")
        return

    execute_query(f"UPDATE zone_control SET {col_name} = {col_name} + ?, updated_at = CURRENT_TIMESTAMP WHERE zone_id = ?", (points, zone_id))
    
    # Check for Control Flip Logic
    # If a faction exceeds e.g. 1000 points and has > 10% more than others, they take control.
    # For MVP: whoever has max points > 500 takes control
    
    rows = execute_query("SELECT * FROM zone_control WHERE zone_id = ?", (zone_id,))
    if rows:
        new_zc = dict(rows[0])
        p_trans = new_zc["faction_points_transformer"]
        p_chron = new_zc["faction_points_chronicler"]
        p_forg = new_zc["faction_points_forgotten"]
        
        candidates = {
            "transformer": p_trans,
            "chronicler": p_chron,
            "forgotten": p_forg
        }
        
        # Find max
        best_faction = max(candidates, key=candidates.get)
        max_points = candidates[best_faction]
        
        # Threshold Logic
        THRESHOLD = 100 # Low for testing
        
        if max_points >= THRESHOLD:
            # Check if it's already the controller
            if new_zc["controlling_faction"] != best_faction:
                execute_query("UPDATE zone_control SET controlling_faction = ? WHERE zone_id = ?", (best_faction, zone_id))
                return {"flipped": True, "new_owner": best_faction}
    
    return {"flipped": False}

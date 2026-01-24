from app.db.crud import execute_query

# Hardcoded Definitions (for MVP)
# In future, these could be in a 'collections' table
COLLECTIONS_DEF = [
    {
        "id": "col_1848_weapons",
        "name": "1848-as Fegyvertár",
        "description": "A Szabadságharc elveszett fegyverei.",
        "items": ["item_fokos", "item_handzsar", "item_revolver_kossuth"] 
        # Note: item_handzsar might be Turkish but let's assume it fits the era or theme
    },
    {
        "id": "col_budapest_relics",
        "name": "Budapest Ereklyéi",
        "description": "A város rejtett kincsei.",
        "items": ["item_ancient_coin", "item_metro_ticket_1980"]
    }
]

def get_character_collections(char_id: str):
    # Fetch all found items for this char
    rows = execute_query("SELECT collection_id, item_id, found_at FROM character_collections WHERE character_id = ?", (char_id,))
    
    found_map = {} # {col_id: {item_id: timestamp}}
    for r in rows:
        cid = r['collection_id']
        iid = r['item_id']
        if cid not in found_map: found_map[cid] = {}
        found_map[cid][iid] = r['found_at']
        
    # Build Result
    result = []
    for col_def in COLLECTIONS_DEF:
        c_id = col_def["id"]
        found_items_in_col = found_map.get(c_id, {})
        
        items_status = []
        for iid in col_def["items"]:
            is_found = iid in found_items_in_col
            # We nominally need item details (name, icon) for the frontend
            # Ideally fetch from generic Items cache or DB
            from app.db.crud import get_item
            item_data = get_item(iid)
            
            items_status.append({
                "item_id": iid,
                "found": is_found,
                "found_at": found_items_in_col.get(iid),
                "name": item_data["name"] if item_data else "???",
                "icon_code": item_data.get("icon_code", "help_outline") if item_data else "help_outline",
                "description": item_data.get("description") if item_data else "???"
            })
            
        result.append({
            "id": c_id,
            "name": col_def["name"],
            "description": col_def["description"],
            "total_items": len(col_def["items"]),
            "found_items": len(found_items_in_col),
            "items": items_status
        })
        
    return result

def check_and_update_collection(char_id: str, item_id: str):
    """
    Called when user receives an item. Checks if it belongs to any collection
    and if it's new, adds it to character_collections.
    """
    for col_def in COLLECTIONS_DEF:
        if item_id in col_def["items"]:
            # Check if already added
            existing = execute_query("SELECT 1 FROM character_collections WHERE character_id=? AND collection_id=? AND item_id=?", 
                                     (char_id, col_def["id"], item_id))
            if not existing:
                execute_query("INSERT INTO character_collections (character_id, collection_id, item_id) VALUES (?, ?, ?)",
                              (char_id, col_def["id"], item_id))
                return True # New collection item found!
    return False

from app.db.crud import execute_query

# Hardcoded Set Metadata (until we have a 'sets' table)
SET_METADATA = {
    "betyar": {"name": "Betyár Felszerelés", "description": "A puszta rettegett betyárjainak tárgyai."},
    "ottoman": {"name": "Ottomán Hagyaték", "description": "A török hódoltság emlékei."},
    "kuruc": {"name": "Kuruc Ereklyék", "description": "Rákóczi szabadságharcának tárgyai."},
    "modern": {"name": "Modern Budapest", "description": "A közelmúlt emlékei a városból."}
}

def get_character_collections(char_id: str):
    # 1. Fetch all items that belong to a set
    items_rows = execute_query("SELECT id, set_id, name, icon_code, description, rarity FROM items WHERE set_id IS NOT NULL")
    
    # Group by set_id
    sets_map = {} # {set_id: [item_dict]}
    for r in items_rows:
        s_id = r["set_id"]
        if s_id not in sets_map: sets_map[s_id] = []
        sets_map[s_id].append(dict(r))
        
    # 2. Fetch user's found items
    # Note: collection_id in DB corresponds to set_id here
    found_rows = execute_query("SELECT collection_id, item_id, found_at FROM character_collections WHERE character_id = ?", (char_id,))
    found_map = {} # {set_id: {item_id: found_at}}
    for r in found_rows:
        cid = r['collection_id']
        iid = r['item_id']
        if cid not in found_map: found_map[cid] = {}
        found_map[cid][iid] = r['found_at']

    # 3. Build Result
    result = []
    # Iterate over defined sets in metadata to ensure order/visibility, 
    # or iterate sets_map to show everything available in DB.
    # Let's interact over sets_map but use metadata for display.
    
    for s_id, items in sets_map.items():
        meta = SET_METADATA.get(s_id, {"name": f"Set: {s_id}", "description": "Ismeretlen gyűjtemény."})
        
        found_items_in_set = found_map.get(s_id, {})
        
        items_status = []
        for item in items:
            iid = item["id"]
            is_found = iid in found_items_in_set
            
            items_status.append({
                "item_id": iid,
                "found": is_found,
                "found_at": found_items_in_set.get(iid),
                "name": item["name"],
                "icon_code": item["icon_code"] if item["icon_code"] else "help_outline",
                "description": item["description"],
                "rarity": item["rarity"] if item["rarity"] else "common"
            })
            
        result.append({
            "id": s_id,
            "name": meta["name"],
            "description": meta["description"],
            "total_items": len(items),
            "found_items": len(found_items_in_set),
            "items": items_status
        })
        
    return result

def check_and_update_collection(char_id: str, item_id: str):
    """
    Called when user receives an item. Checks if it belongs to any set (collection)
    and if it's new, adds it to character_collections.
    """
    # 1. Check if item has a set_id
    rows = execute_query("SELECT set_id FROM items WHERE id = ?", (item_id,))
    if not rows:
        return False
        
    set_id = rows[0]["set_id"]
    if not set_id:
        return False
        
    # 2. Check if already added to collection
    # collection_id column stores the set_id
    existing = execute_query("SELECT 1 FROM character_collections WHERE character_id=? AND collection_id=? AND item_id=?", 
                             (char_id, set_id, item_id))
    
    if not existing:
        execute_query("INSERT INTO character_collections (character_id, collection_id, item_id) VALUES (?, ?, ?)",
                      (char_id, set_id, item_id))
        return True # New collection item found!
        
    return False

import random
from app.db.crud import get_loot_table, get_item

def roll_loot(table_id: str):
    # Classic independent drop chance
    table = get_loot_table(table_id)
    drops = []
    if table:
        for entry in table["entries"]: # list of dicts from JSON
            if random.random() <= entry["chance"]:
                # Drop!
                item = get_item(entry["item_id"])
                if item:
                    drops.append(item)
    return drops

def roll_weighted_loot(table_id: str, count: int = 1):
    # Weighted random pick (Loot Box style)
    table = get_loot_table(table_id)
    drops = []
    if not table or not table["entries"]:
        return drops
        
    entries = table["entries"]
    # Calculate cumulative weights if "chance" is treated as weight
    # Or just use random.choices if available
    
    # We assume 'chance' is weight here.
    # Note: earlier logic treated chance as probability (0.0-1.0).
    # If using as weights, we can normalize.
    
    weights = [e["chance"] for e in entries]
    items_ids = [e["item_id"] for e in entries]
    
    picked_ids = random.choices(items_ids, weights=weights, k=count)
    
    for iid in picked_ids:
        item = get_item(iid)
        if item:
            drops.append(item)
            
    return drops

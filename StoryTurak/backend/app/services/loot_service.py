import random
from app.db.crud import get_loot_table, get_item

def roll_loot(table_id: str):
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

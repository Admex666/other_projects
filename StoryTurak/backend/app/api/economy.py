from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from app.db.crud import get_character_with_details, remove_character_item, add_character_item, update_character_currency, get_item

router = APIRouter()

class TradeRequest(BaseModel):
    character_id: str
    item_id: str
    quantity: int = 1

@router.post("/merchant/sell")
def sell_item(request: TradeRequest):
    """
    Sells an item from the character's inventory to the merchant.
    """
    char = get_character_with_details(request.character_id)
# ...

@router.get("/merchant/items")
def get_merchant_items():
    """
    Returns the list of items the merchant sells.
    In a real app, this could be dynamic or based on location.
    """
    # For now, return specific items
    from app.db.crud import execute_query
    
    # We want Potion, and maybe a Loot Box if we have one defined as an item
    # Let's fetch all items with a value > 0 and type != 'quest'
    rows = execute_query("SELECT * FROM items WHERE type != 'quest' AND value > 0")
    
    items = []
    for r in rows:
        item = dict(r)
        # Parse stats/effects if needed, though frontend mostly needs name/value/icon
        # But let's be safe
        import json
        try:
             item["stats"] = json.loads(item["stats"]) if item["stats"] else {}
        except:
             item["stats"] = {}
        items.append(item)
        
    return items

@router.post("/merchant/sell")
def sell_item(request: TradeRequest):
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
        
    # Check if user has the item
    item_in_inv = next((i for i in char["inventory"] if i["item_id"] == request.item_id), None)
    if not item_in_inv or item_in_inv["quantity"] < request.quantity:
        raise HTTPException(status_code=400, detail="Not enough items to sell")
        
    item_def = get_item(request.item_id)
    if not item_def:
        raise HTTPException(status_code=404, detail="Item definition not found")
        
    # Calculate Value (e.g. 50% of base value)
    base_value = item_def.get("value", 0)
    sell_price = int(base_value * 0.5) * request.quantity
    
    # 1. Remove Item
    remove_character_item(request.character_id, request.item_id, request.quantity)
    
    # 2. Add Currency
    update_character_currency(request.character_id, sell_price)
    
    return {
        "success": True,
        "sold_item": item_def["name"],
        "quantity": request.quantity,
        "earned": sell_price,
        "new_currency": char.get("currency", 0) + sell_price # Approximate, normally should refetch
    }

@router.post("/merchant/buy")
def buy_item(request: TradeRequest):
    """
    Buys an item from the merchant.
    """
    char = get_character_with_details(request.character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
        
    item_def = get_item(request.item_id)
    if not item_def:
        raise HTTPException(status_code=404, detail="Item definition not found")
        
    cost = item_def.get("value", 100) * request.quantity
    current_currency = char.get("currency", 0)
    
    if current_currency < cost:
        raise HTTPException(status_code=400, detail="Not enough currency")
        
    # 1. Deduct Currency
    update_character_currency(request.character_id, -cost)
    
    # 2. Add Item
    add_character_item(request.character_id, request.item_id, request.quantity)
    
    return {
        "success": True,
        "bought_item": item_def["name"],
        "quantity": request.quantity,
        "spent": cost,
        "new_currency": current_currency - cost
    }

from app.services.loot_service import roll_weighted_loot

@router.post("/character/use_item")
def use_item(request: TradeRequest):
    """
    Uses an item (Consumable or Loot Box).
    """
    char = get_character_with_details(request.character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
        
    # Check item
    item_in_inv = next((i for i in char["inventory"] if i["item_id"] == request.item_id), None)
    if not item_in_inv or item_in_inv["quantity"] < 1:
        raise HTTPException(status_code=400, detail="Item not in inventory")

    item_def = get_item(request.item_id)
    
    # 1. Handle Consumable (Healing)
    # Simple logic: if stats['hp_restore'] > 0
    stats = item_def.get("stats", {})
    if stats.get("hp_restore"):
        heal = stats["hp_restore"]
        new_hp = min(char["current_hp"] + heal, char["max_hp"])
        # Update HP
        # We need a crud update_character_hp or generic update
        from app.db.crud import execute_query
        execute_query("UPDATE characters SET current_hp = ? WHERE id = ?", (new_hp, request.character_id))
        
        remove_character_item(request.character_id, request.item_id, 1)
        return {"success": True, "message": f"Healed {heal} HP", "new_hp": new_hp}

    # 2. Handle Loot Box
    # Check if logic is in effects or stats
    # Convention: stats["loot_table_id"]
    loot_table_id = stats.get("loot_table_id")
    if loot_table_id:
        drops = roll_weighted_loot(loot_table_id)
        added_items = []
        for d in drops:
            add_character_item(request.character_id, d["id"], 1)
            added_items.append(d["name"])
            
        remove_character_item(request.character_id, request.item_id, 1)
        return {"success": True, "message": "Opened loot box!", "drops": added_items}

    return {"success": False, "message": "Item depends on context or has no effect."}

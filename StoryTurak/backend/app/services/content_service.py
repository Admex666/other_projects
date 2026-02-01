import json
from app.db.database import execute_query
from app.db.crud import create_item
import os

def seed_world_content():
    # 0. Seed Items
    seed_items()

    # 1. Seed Zones
    # From world.py hardcoded list
    zones = [
        {
            "id": "zone_belvaros",
            "name": "Belváros - A Ködös Utcák",
            "description": "A régi Pest szíve. Itt a legerősebb a Rend őreinek jelenléte.",
            "boundary_points": [[47.498, 19.040], [47.502, 19.050], [47.495, 19.060], [47.490, 19.045]],
            "difficulty_level": 1
        },
        {
            "id": "zone_nyolcker",
            "name": "VIII. Kerület - A Sötét Parkok",
            "description": "A senki földje. Kereskedők, csempészek és bukott költők tanyája.",
            "boundary_points": [[47.495, 19.065], [47.498, 19.080], [47.485, 19.085], [47.485, 19.070]],
            "difficulty_level": 3
        },
        {
            "id": "zone_gellert",
            "name": "Gellért-hegy - A Boszorkányok Sziklája",
            "description": "A város fölé magasodó szikla, ahol az ősi energiák összegyűlnek.",
            "boundary_points": [[47.490, 19.030], [47.485, 19.035], [47.482, 19.045], [47.488, 19.055], [47.492, 19.048]],
            "difficulty_level": 5
        }
    ]

    for z in zones:
        execute_query(
            "INSERT INTO zones (id, name, description, boundary_points, difficulty_level) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET name=excluded.name, description=excluded.description, boundary_points=excluded.boundary_points",
            (z["id"], z["name"], z["description"], json.dumps(z["boundary_points"]), z["difficulty_level"])
        )

    # 2. Seed Encounters
    encounters = [
        {
            "id": "enc_poet_ghost",
            "zone_id": "zone_belvaros",
            "title": "Az Elfeledett Költő Szelleme",
            "description": "Egy halvány alak szaval a lámpaoszlop alatt.",
            "type": "story",
            "location_lat": 47.498,
            "location_lon": 19.040,
            "definition": {
                "start_node_id": "start",
                "nodes": {
                    "start": { "id": "start", "type": "narrative", "text": "A szellem feléd fordul. 'Emlékszel még a régi szavakra?'", "next_node_id": "choice1" },
                    "choice1": { "id": "choice1", "type": "choice", "text": "Mit válaszolsz?", "choices": [
                         {"text": "Igen, emlékszem.", "next_node_id": "end_good"},
                         {"text": "Nem tudom miről beszélsz.", "next_node_id": "end_bad"}
                    ]},
                    "end_good": {"id": "end_good", "type": "narrative", "text": "A szellem elmosolyodik és köddé válik. (Kaptál egy ősi érmét!)"},
                    "end_bad": {"id": "end_bad", "type": "narrative", "text": "A szellem szomorúan rázza a fejét."}
                }
            }
        },
        {
            "id": "enc_citadella_shadows",
            "zone_id": "zone_gellert",
            "title": "A Citadella Árnyai",
            "description": "Sötét alakok gyülekeznek a régi erőd falainál.",
            "type": "fight",
            "location_lat": 47.487,
            "location_lon": 19.044,
            "definition": {
                "start_node_id": "start",
                "nodes": {
                    "start": { "id": "start", "type": "fight", "text": "Egy Árny-Őr állja utadat!", "enemy_id": "enemy_shadow_guard", "enemy_hp": 30, "success_node_id": "win", "failure_node_id": "lose" },
                    "win": {"id": "win", "type": "narrative", "text": "Legyőzted az árnyat! Az út szabad."},
                    "lose": {"id": "lose", "type": "narrative", "text": "Az árny túl erős volt... Visszavonulsz."}
                }
            }
        }
    ]

    for e in encounters:
        execute_query(
            "INSERT INTO encounters (id, zone_id, title, description, type, location_lat, location_lon, definition) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, definition=excluded.definition, location_lat=excluded.location_lat, location_lon=excluded.location_lon",
            (e["id"], e["zone_id"], e["title"], e["description"], e["type"], e["location_lat"], e["location_lon"], json.dumps(e["definition"]))
        )
    
    # 3. Seed Loot Tables (Example)
    # Common Table
    execute_query("INSERT OR IGNORE INTO loot_tables (id) VALUES (?)", ("loot_table_common",))
    
    entries = [
        {"item_id": "item_healing_potion_minor", "chance": 0.5, "min_qty": 1, "max_qty": 1},
        {"item_id": "item_ancient_coin", "chance": 0.3, "min_qty": 1, "max_qty": 2}
    ]
    
    for entry in entries:
        execute_query(
            "INSERT OR REPLACE INTO loot_table_entries (loot_table_id, item_id, chance, min_qty, max_qty) VALUES (?, ?, ?, ?, ?)",
            ("loot_table_common", entry["item_id"], entry["chance"], entry["min_qty"], entry["max_qty"])
        )

def get_all_zones():
    rows = execute_query("SELECT * FROM zones")
    res = []
    for r in rows:
        d = dict(r)
        d["boundary_points"] = json.loads(d["boundary_points"])
        res.append(d)
    return res

def get_zone_encounters(zone_id):
    rows = execute_query("SELECT * FROM encounters WHERE zone_id = ?", (zone_id,))
    res = []
    for r in rows:
        d = dict(r)
        try:
           definition = json.loads(d["definition"])
        except:
           definition = {}
           
        # Remap to Match Pydantic Model if needed (nodes, start_node_id)
        d["nodes"] = definition.get("nodes", {})
        d["start_node_id"] = definition.get("start_node_id", "")
        # Construct location list
        d["location"] = [d["location_lat"], d["location_lon"]]
        res.append(d)
    return res

def seed_items():
    try:
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app", "data", "historical_items.json")
        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)
            
        for item in items:
            create_item(item)
            
        # Hardcoded Collection Items (Ensuring they exist for Collection V1)
        collection_items = [
            {"id": "item_fokos", "name": "Betyár Fokos", "type": "weapon", "rarity": "rare", "value": 250, "icon_code": "architecture", "description": "Díszes nyelű fokos, a puszta emléke.", "set_id": "betyar"},
            {"id": "item_handzsar", "name": "Török Handzsár", "type": "weapon", "rarity": "common", "value": 120, "icon_code": "explore", "description": "Rozsdás, de éles penge az 1500-as évekből.", "set_id": "ottoman"},
            {"id": "item_revolver_kossuth", "name": "1848-as Pisztoly", "type": "weapon", "rarity": "legendary", "value": 1000, "icon_code": "offline_bolt", "description": "Egy tiszt oldalfegyvere a szabadságharcból."}, 
            {"id": "item_metro_ticket_1980", "name": "Régi Metró Jegy", "type": "relic", "rarity": "common", "value": 10, "icon_code": "confirmation_number", "description": "Egy lyukasztott jegy a 3-as metróról.", "set_id": "modern"},
            # item_ancient_coin is likely already in historical_items or loot table
            {"id": "item_ancient_coin", "name": "Római Érme", "type": "relic", "rarity": "uncommon", "value": 50, "icon_code": "monetization_on", "description": "Aquincumi ásatásokból származó érme."},
            {"id": "item_test_cookie", "name": "Teszt Süti", "type": "consumable", "rarity": "common", "value": 10, "icon_code": "cookie", "stats": {"hp_restore": 5}, "description": "Finom és olcsó. Tökéletes teszteléshez."},
            {"id": "item_kuruc_zaszlo", "name": "Kuruc Zászló", "type": "relic", "rarity": "rare", "value": 300, "icon_code": "outlined_flag", "description": "Szakadt zászlófoszlány Rákóczi seregéből.", "set_id": "kuruc"}
        ]
        for it in collection_items:
            create_item(it)

        print(f"✅ Seeded {len(items)} historical items + Collections.")
    except Exception as e:
        print(f"❌ Failed to seed items: {e}")

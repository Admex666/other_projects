import json
import re

with open("docs/card_spritesheet_map.json", "r", encoding="utf-8") as f:
    smap = json.load(f)
with open("docs/ocr_extracted_cards.json", "r", encoding="utf-8-sig") as f:
    ocr = {item["slot"]: item for item in json.load(f)}

game_cards = [s for s in smap["slots"] if s.get("slot_type") == "game_card"]

# Known accurate data from card_mechanics_spec.md & OCR analysis
known_cards = {
    1: {"name": "Baby Beaver", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "3 VP if adjacent to any parent (Beaver Dad or Beaver Mom)."},
    2: {"name": "Beaver Dad", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "Synergy animal card for Baby Beaver. 2 VP."},
    3: {"name": "Beaver Mom", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "Synergy animal card for Baby Beaver. 2 VP."},
    4: {"name": "Fish", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    5: {"name": "Fish", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    6: {"name": "Fish", "types": ["animal"], "beeHives": 1, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    7: {"name": "Fish", "types": ["animal"], "beeHives": 1, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    8: {"name": "Fish", "types": ["animal"], "beeHives": 1, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    9: {"name": "Fish", "types": ["animal"], "beeHives": 1, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    10: {"name": "Fish", "types": ["animal"], "beeHives": 1, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    11: {"name": "Fish", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Fish in your largest group of orthogonally adjacent Fish."},
    12: {"name": "Cabin", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "4 VP if adjacent to exactly 1 Mountain or Water."},
    13: {"name": "Harbor", "types": ["building"], "beeHives": 0, "hasGoal": True, "text": "Goal: 8 VP if adjacent to at least 2 Water cards; otherwise 2 VP."},
    14: {"name": "Lighthouse", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Water card in this row and column (counted once)."},
    15: {"name": "Binoculars", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "Activate a Building in your tableau."},
    16: {"name": "Collector", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "3 VP per Item in your tableau."},
    17: {"name": "Collector (Goal)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": True, "text": "Goal: 20 VP if you have at least 5 of the same color or type; otherwise 2 VP."},
    18: {"name": "Binoculars", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "Activate a Building in your tableau."},
    19: {"name": "Fisherbear", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "4 VP if adjacent to at least 1 Water."},
    20: {"name": "Spy (Water)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Water card in any one opponent's tableau."},
    21: {"name": "Reed", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "5 VP if adjacent to exactly 1 Water."},
    22: {"name": "Reed", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "5 VP if adjacent to exactly 1 Water."},
    23: {"name": "Water Lily", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "3 VP per adjacent Water."},
    24: {"name": "Coyote", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "2 VP per adjacent Desert or Animal."},
    25: {"name": "Queen Bee", "types": ["animal"], "beeHives": 1, "hasGoal": False, "text": "4 VP per adjacent Bee Hive symbol."},
    26: {"name": "Trading Post", "types": ["building"], "beeHives": 0, "hasGoal": True, "text": "Goal: 16 VP if adjacent to 4 different colors; otherwise 4 VP."},
    27: {"name": "CIA Headquarters", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "5 VP per Spy in your tableau."},
    28: {"name": "Rock Shelter", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "4 VP if adjacent to at least 1 Desert card."},
    29: {"name": "Small Trading Post", "types": ["building"], "beeHives": 0, "hasGoal": True, "text": "Goal: 8 VP if adjacent to exactly 2 different colors; otherwise 2 VP."},
    30: {"name": "Medium Trading Post", "types": ["building"], "beeHives": 0, "hasGoal": True, "text": "Goal: 12 VP if adjacent to exactly 3 different colors; otherwise 3 VP."},
    31: {"name": "Bearbecue", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "4 VP per adjacent Fish."},
    32: {"name": "Binoculars", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "Activate a Building in your tableau."},
    33: {"name": "Compass", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "2 VP per adjacent Mountain or Water card."},
    34: {"name": "Secret Honey Stash", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "Gain 2 bee tokens when placed; gain 1 bee token when activated by another card."},
    35: {"name": "Signpost", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "2 VP per adjacent Plant or Building."},
    36: {"name": "Water Canteen", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "4 VP per adjacent Water card."},
    37: {"name": "Explorer", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "3 VP per different type adjacent."},
    38: {"name": "Photographer", "types": ["bearfolk"], "beeHives": 0, "hasGoal": True, "text": "Goal: 8 VP if there is a matching card adjacent to its right; otherwise 2 VP."},
    39: {"name": "Spy (Dual)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "1 VP per City and 1 VP per Desert in any one opponent's tableau."},
    40: {"name": "Spy (Tokens)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "2 VP per token in any one opponent's tableau."},
    41: {"name": "Treasure Hunter", "types": ["bearfolk"], "beeHives": 0, "hasGoal": True, "text": "Goal: 8 VP if adjacent to at least 1 Goal card; otherwise 2 VP."},
    42: {"name": "Cactus", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "4 VP if not adjacent to Water."},
    43: {"name": "Sunflower", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "5 VP if adjacent to exactly 1 Desert."},
    44: {"name": "Yucca", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Plant in your tableau."},
    45: {"name": "Cat", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "4 VP per adjacent Bearfolk."},
    46: {"name": "City Pigeon", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "3 VP per adjacent Building."},
    47: {"name": "Pigeon", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "4 VP per Animal in all rows below this card."},
    48: {"name": "Cellar", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "4 VP per Item/Building in all rows above this card."},
    49: {"name": "Factory", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "4 VP if not adjacent to Plant or Animal."},
    50: {"name": "Suburban Apartments", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "2 VP per complete column in your tableau."},
    51: {"name": "Station", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "3 VP per complete row in your tableau."},
    52: {"name": "Tourist Office", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "1 VP per card in your tableau."},
    53: {"name": "Town Hall", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "2 VP per City/Building in this row and column (counted once)."},
    54: {"name": "Rubber Duck", "types": ["item"], "beeHives": 2, "hasGoal": False, "text": "Flat 2 VP. Provides 2 Bee Hive multiplier symbols for end-game."},
    55: {"name": "Binoculars", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "Activate a Building in your tableau."},
    56: {"name": "Streetlight", "types": ["item"], "beeHives": 0, "hasGoal": True, "text": "Goal: 10 VP if adjacent to at least 2 City cards; otherwise 2 VP."},
    57: {"name": "Statue", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "2 VP per adjacent card with at least 1 Bearfolk."},
    58: {"name": "Actor", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "2 VP per every other Bearfolk in your tableau."},
    59: {"name": "Architect", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "4 VP per Building in your tableau."},
    60: {"name": "Banker", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "5 VP per Goal card in your tableau."},
    61: {"name": "Football Player", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "5 VP if this card's row is complete."},
    62: {"name": "Bearlet", "types": ["bearfolk"], "beeHives": 0, "hasGoal": True, "text": "Goal: 10 VP if you have at least 6 bee tokens; otherwise 2 VP."},
    63: {"name": "Optician", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "4 VP per Bearfolk without glasses in your tableau."},
    64: {"name": "Sergeant", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "3 VP per Bearfolk in this row."},
    65: {"name": "Spy (City)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "2 VP per City card in any one opponent's tableau."},
    66: {"name": "Window Cleaner", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "5 VP if this card's column is complete."},
    67: {"name": "Planter Box", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "2 VP per adjacent card with at least 1 Plant."},
    68: {"name": "Rose", "types": ["plant"], "beeHives": 0, "hasGoal": True, "text": "Goal: 10 VP if adjacent to exactly 2 City cards; otherwise 2 VP."},
    69: {"name": "Eagle", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Animal in your tableau (including this Eagle)."},
    70: {"name": "Mountain Goat", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "4 VP per adjacent Mountain card."},
    71: {"name": "Snake", "types": ["animal"], "beeHives": 0, "hasGoal": False, "text": "2 VP per card in your tableau whose name starts with S."},
    72: {"name": "Lookout Tower", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "1 VP per card in your tableau NOT adjacent to this card."},
    73: {"name": "Research Lab", "types": ["building"], "beeHives": 0, "hasGoal": True, "text": "Goal: 10 VP if adjacent to at least 1 Building and 1 Item; otherwise 2 VP."},
    74: {"name": "Visitor Center", "types": ["building"], "beeHives": 0, "hasGoal": False, "text": "6 VP if all 4 colors are represented in your tableau."},
    75: {"name": "Backpack", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "3 VP if you have at least 3 Items in your tableau (including this)."},
    76: {"name": "Binoculars", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "Activate a Building in your tableau."},
    77: {"name": "Water Trough", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "4 VP per adjacent Animal card."},
    78: {"name": "Snack Bag", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "2 VP per bee token you currently have."},
    79: {"name": "Weather: City", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "7 VP if you have a City (Red) card in your reserve."},
    80: {"name": "Weather: Water", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "7 VP if you have a Water (Blue) card in your reserve."},
    81: {"name": "Weather: Mountain", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "7 VP if you have a Mountain (Green) card in your reserve."},
    82: {"name": "Weather: Desert", "types": ["item"], "beeHives": 0, "hasGoal": False, "text": "7 VP if you have a Desert (Yellow) card in your reserve."},
    83: {"name": "Botanist", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "3 VP per Plant in your tableau."},
    84: {"name": "Guide", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "Activate a Bearfolk in your tableau."},
    85: {"name": "Hiker", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "2 VP per Mountain card in your tableau."},
    86: {"name": "Spy (Dual Mtn)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "1 VP per Mountain and 1 VP per Water in any one opponent's tableau."},
    87: {"name": "Spy (Dual Desert)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "1 VP per Desert and 1 VP per Mountain in any one opponent's tableau."},
    88: {"name": "Spy (Bee Tokens)", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "2 VP per bee token any one opponent has."},
    89: {"name": "Wildlife Ranger", "types": ["bearfolk"], "beeHives": 0, "hasGoal": False, "text": "3 VP per Animal in your tableau."},
    90: {"name": "Berries", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "4 VP per Plant in this row."},
    91: {"name": "Dandelion", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "7 VP when placed; 1 VP when activated by another card."},
    92: {"name": "Wild Flowers", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "3 VP per adjacent Plant or Animal."},
    93: {"name": "Sequoia", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "Flat 3 VP."},
    94: {"name": "Wild Carrot", "types": ["plant"], "beeHives": 0, "hasGoal": False, "text": "5 VP if adjacent to at least 1 Animal."}
}

catalog = []
for c in game_cards:
    c_id = c["game_card_id"]
    s_idx = c["slot_index"]
    color = c["suit"].lower()
    info = known_cards.get(c_id, {
        "name": f"Card #{c_id}",
        "types": ["item"],
        "beeHives": 0,
        "hasGoal": False,
        "text": "Scores victory points when activated."
    })
    catalog.append({
        "id": c_id,
        "name": info["name"],
        "color": color,
        "types": info["types"],
        "beeHives": info["beeHives"],
        "hasGoal": info["hasGoal"],
        "text": info["text"],
        "spriteIndex": s_idx
    })

# Format as TypeScript
ts_content = '''import { CardDefinition } from '../types';

export const CARD_CATALOG: CardDefinition[] = ''' + json.dumps(catalog, indent=2) + ''';
'''

with open("src/game/cards/catalog.ts", "w", encoding="utf-8") as f:
    f.write(ts_content)

print(f"Generated catalog with {len(catalog)} cards.")

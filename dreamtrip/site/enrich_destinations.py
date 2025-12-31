import json
import os
import re

def enrich_destinations():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dest_path = os.path.join(base_dir, "data", "destinations.json")
    numbeo_path = os.path.join(base_dir, "data", "live_numbeo_indices.json")
    
    with open(dest_path, "r", encoding="utf-8") as f:
        destinations = json.load(f)
        
    with open(numbeo_path, "r", encoding="utf-8") as f:
        numbeo_data = json.load(f)
        
    # Manual mapping for Hungarian names to Numbeo keys (approximate)
    name_map = {
        "Barcelona": "Barcelona", "Róma": "Rome", "Bali": "Bali, Indonesia", "Reykjavík": "Reykjavik",
        "Tokió": "Tokyo", "Párizs": "Paris", "Lisszabon": "Lisbon", "Bangkok": "Bangkok",
        "Sydney": "Sydney", "Amszterdam": "Amsterdam", "Szantorini": "Athens", "Dubaj": "Dubai",
        "New York": "New York", "Berlin": "Berlin", "Bécs": "Vienna", "Bécs": "Vienna",
        "London": "London", "Zürich": "Zurich", "Brüsszel": "Brussels", "Prága": "Prague",
        "Varsó": "Warsaw", "Koppenhága": "Copenhagen", "Stockholm": "Stockholm", "Oslo": "Oslo",
        "Helsinki": "Helsinki", "Dublin": "Dublin", "Tallinn": "Tallinn", "Riga": "Riga",
        "Vilnius": "Vilnius", "Isztambul": "Istanbul", "Valletta": "Valletta", "Larnaca": "Larnaca",
        "Luxembourg": "Luxembourg", "Split": "Split", "Szófia": "Sofia", "Bukarest": "Bucharest",
        "Belgrád": "Belgrade", "Tirana": "Tirana", "Ljubljana": "Ljubljana", "Szarajevó": "Sarajevo"
    }
    
    def find_numbeo_entry(city_name):
        eng_name = name_map.get(city_name, city_name)
        for key, val in numbeo_data.items():
            if eng_name.lower() in key.lower():
                return val
        return None

    updated_count = 0
    for dest in destinations:
        numbeo = find_numbeo_entry(dest["name"])
        if numbeo:
            index = numbeo["cost_index"]
            safety = numbeo["safety_index"]
            
            # Special logic for Santorini (premium island)
            if dest["name"] == "Szantorini":
                if index: index *= 1.2 # 20% premium over Athens
                if safety: safety += 5 # Usually safer than capital
            
            if index:
                # Linear model with offset: max(65, round(Index * 4.7 - 115))
                # Derived from USD model: (Index * 5.13 - 125) converted to EUR
                new_cost = max(65, round(index * 4.7 - 115))
                dest["metrics"]["cost_index_daily_eur"] = new_cost
                
            if safety:
                dest["metrics"]["safety_index"] = min(100, round(safety))
            
            updated_count += 1
            print(f"Updated {dest['name']} -> Cost: {dest['metrics']['cost_index_daily_eur']} EUR, Safety: {dest['metrics']['safety_index']}")
        else:
            print(f"No Numbeo data for {dest['name']}")

    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(destinations, f, indent=2, ensure_ascii=False)
        
    print(f"Finished! Updated {updated_count}/{len(destinations)} destinations.")

if __name__ == "__main__":
    enrich_destinations()

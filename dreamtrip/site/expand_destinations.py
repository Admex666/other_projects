import json
import os

new_cities = [
    {"id": "berlin_de", "name": "Berlin", "country": "Németország", "region": "Europe", "lat": 52.5200, "lon": 13.4050, "vibe": {"urban": 1.0, "beach": 0.0, "nature": 0.4, "history": 0.9, "nightlife": 1.0, "luxury": 0.7}, "img": "https://images.unsplash.com/photo-1560969184-10fe8719e047?auto=format&fit=crop&w=800&q=80"},
    {"id": "london_uk", "name": "London", "country": "Egyesült Királyság", "region": "Europe", "lat": 51.5074, "lon": -0.1278, "vibe": {"urban": 1.0, "beach": 0.0, "nature": 0.5, "history": 1.0, "nightlife": 1.0, "luxury": 0.9}, "img": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=800&q=80"},
    {"id": "vienna_at", "name": "Bécs", "country": "Ausztria", "region": "Europe", "lat": 48.2082, "lon": 16.3738, "vibe": {"urban": 0.8, "beach": 0.0, "nature": 0.4, "history": 1.0, "nightlife": 0.6, "luxury": 0.8}, "img": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=800&q=80"},
    {"id": "zurich_ch", "name": "Zürich", "country": "Svájc", "region": "Europe", "lat": 47.3769, "lon": 8.5417, "vibe": {"urban": 0.7, "beach": 0.2, "nature": 0.8, "history": 0.7, "nightlife": 0.6, "luxury": 1.0}, "img": "https://images.unsplash.com/photo-1515488764276-beab7607c1e6?auto=format&fit=crop&w=800&q=80"},
    {"id": "brussels_be", "name": "Brüsszel", "country": "Belgium", "region": "Europe", "lat": 50.8503, "lon": 4.3517, "vibe": {"urban": 0.8, "beach": 0.0, "nature": 0.3, "history": 0.9, "nightlife": 0.7, "luxury": 0.6}, "img": "https://images.unsplash.com/photo-1549410141-65476a20d43f?auto=format&fit=crop&w=800&q=80"},
    {"id": "prague_cz", "name": "Prága", "country": "Csehország", "region": "Europe", "lat": 50.0755, "lon": 14.4378, "vibe": {"urban": 0.8, "beach": 0.0, "nature": 0.4, "history": 1.0, "nightlife": 0.9, "luxury": 0.5}, "img": "https://images.unsplash.com/photo-1541849546-216549ae216d?auto=format&fit=crop&w=800&q=80"},
    {"id": "warsaw_pl", "name": "Varsó", "country": "Lengyelország", "region": "Europe", "lat": 52.2297, "lon": 21.0122, "vibe": {"urban": 0.9, "beach": 0.0, "nature": 0.4, "history": 0.8, "nightlife": 0.8, "luxury": 0.5}, "img": "https://images.unsplash.com/photo-1519197924294-4ba991a11128?auto=format&fit=crop&w=800&q=80"},
    {"id": "copenhagen_dk", "name": "Koppenhága", "country": "Dánia", "region": "Europe", "lat": 55.6761, "lon": 12.5683, "vibe": {"urban": 0.8, "beach": 0.3, "nature": 0.6, "history": 0.7, "nightlife": 0.7, "luxury": 0.8}, "img": "https://images.unsplash.com/photo-1513622470522-26c3c8a854bc?auto=format&fit=crop&w=800&q=80"},
    {"id": "stockholm_se", "name": "Stockholm", "country": "Svédország", "region": "Europe", "lat": 59.3293, "lon": 18.0686, "vibe": {"urban": 0.8, "beach": 0.2, "nature": 0.7, "history": 0.8, "nightlife": 0.7, "luxury": 0.8}, "img": "https://images.unsplash.com/photo-150935684345d-85ca13fdd6a5?auto=format&fit=crop&w=800&q=80"},
    {"id": "oslo_no", "name": "Oslo", "country": "Norvégia", "region": "Europe", "lat": 59.9139, "lon": 10.7522, "vibe": {"urban": 0.7, "beach": 0.3, "nature": 0.9, "history": 0.6, "nightlife": 0.5, "luxury": 0.8}, "img": "https://images.unsplash.com/photo-1583275484611-53415b443748?auto=format&fit=crop&w=800&q=80"},
    {"id": "helsinki_fi", "name": "Helsinki", "country": "Finnország", "region": "Europe", "lat": 60.1699, "lon": 24.9384, "vibe": {"urban": 0.7, "beach": 0.3, "nature": 0.8, "history": 0.6, "nightlife": 0.5, "luxury": 0.7}, "img": "https://images.unsplash.com/photo-1513693215234-95c52c03882a?auto=format&fit=crop&w=800&q=80"},
    {"id": "dublin_ie", "name": "Dublin", "country": "Írország", "region": "Europe", "lat": 53.3498, "lon": -6.2603, "vibe": {"urban": 0.8, "beach": 0.2, "nature": 0.6, "history": 0.8, "nightlife": 1.0, "luxury": 0.6}, "img": "https://images.unsplash.com/photo-1549918838-0678095d985a?auto=format&fit=crop&w=800&q=80"},
    {"id": "tallinn_ee", "name": "Tallinn", "country": "Észtország", "region": "Europe", "lat": 59.4370, "lon": 24.7535, "vibe": {"urban": 0.6, "beach": 0.3, "nature": 0.6, "history": 1.0, "nightlife": 0.6, "luxury": 0.5}, "img": "https://images.unsplash.com/photo-1548810935-77983656913c?auto=format&fit=crop&w=800&q=80"},
    {"id": "riga_lv", "name": "Riga", "country": "Lettország", "region": "Europe", "lat": 56.9496, "lon": 24.1052, "vibe": {"urban": 0.6, "beach": 0.2, "nature": 0.5, "history": 0.9, "nightlife": 0.7, "luxury": 0.4}, "img": "https://images.unsplash.com/photo-1561058423-f308876ae90b?auto=format&fit=crop&w=800&q=80"},
    {"id": "vilnius_lt", "name": "Vilnius", "country": "Litvánia", "region": "Europe", "lat": 54.6872, "lon": 25.2797, "vibe": {"urban": 0.6, "beach": 0.0, "nature": 0.6, "history": 0.9, "nightlife": 0.6, "luxury": 0.4}, "img": "https://images.unsplash.com/photo-1528659556885-3e284a7e6d19?auto=format&fit=crop&w=800&q=80"},
    {"id": "istanbul_tr", "name": "Isztambul", "country": "Törökország", "region": "Europe", "lat": 41.0082, "lon": 28.9784, "vibe": {"urban": 1.0, "beach": 0.3, "nature": 0.3, "history": 1.0, "nightlife": 0.9, "luxury": 0.8}, "img": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=800&q=80"},
    {"id": "valletta_mt", "name": "Valletta", "country": "Málta", "region": "Europe", "lat": 35.8989, "lon": 14.5146, "vibe": {"urban": 0.5, "beach": 0.9, "nature": 0.2, "history": 1.0, "nightlife": 0.7, "luxury": 0.7}, "img": "https://images.unsplash.com/photo-1523437341230-da858a735c03?auto=format&fit=crop&w=800&q=80"},
    {"id": "larnaca_cy", "name": "Larnaca", "country": "Ciprus", "region": "Europe", "lat": 34.9240, "lon": 33.6232, "vibe": {"urban": 0.4, "beach": 1.0, "nature": 0.4, "history": 0.6, "nightlife": 0.7, "luxury": 0.6}, "img": "https://images.unsplash.com/photo-1589326887563-39d67568f237?auto=format&fit=crop&w=800&q=80"},
    {"id": "luxembourg_lu", "name": "Luxembourg", "country": "Luxemburg", "region": "Europe", "lat": 49.6116, "lon": 6.1319, "vibe": {"urban": 0.6, "beach": 0.0, "nature": 0.6, "history": 0.8, "nightlife": 0.4, "luxury": 0.9}, "img": "https://images.unsplash.com/photo-1563812859424-df3b3060f089?auto=format&fit=crop&w=800&q=80"},
    {"id": "split_hr", "name": "Split", "country": "Horvátország", "region": "Europe", "lat": 43.5081, "lon": 16.4402, "vibe": {"urban": 0.5, "beach": 1.0, "nature": 0.5, "history": 0.9, "nightlife": 0.8, "luxury": 0.6}, "img": "https://images.unsplash.com/photo-1555990538-40679822aef0?auto=format&fit=crop&w=800&q=80"},
    {"id": "sofia_bg", "name": "Szófia", "country": "Bulgária", "region": "Europe", "lat": 42.6977, "lon": 23.3219, "vibe": {"urban": 0.7, "beach": 0.0, "nature": 0.7, "history": 0.8, "nightlife": 0.7, "luxury": 0.4}, "img": "https://images.unsplash.com/photo-1549422915-d729e2fdeed2?auto=format&fit=crop&w=800&q=80"},
    {"id": "bucharest_ro", "name": "Bukarest", "country": "Románia", "region": "Europe", "lat": 44.4268, "lon": 26.1025, "vibe": {"urban": 0.8, "beach": 0.0, "nature": 0.4, "history": 0.7, "nightlife": 0.9, "luxury": 0.5}, "img": "https://images.unsplash.com/photo-1510520434124-5bc7e642b61d?auto=format&fit=crop&w=800&q=80"},
    {"id": "belgrade_rs", "name": "Belgrád", "country": "Szerbia", "region": "Europe", "lat": 44.7866, "lon": 20.4489, "vibe": {"urban": 0.8, "beach": 0.1, "nature": 0.4, "history": 0.7, "nightlife": 1.0, "luxury": 0.5}, "img": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=800&q=80"},
    {"id": "tirana_al", "name": "Tirana", "country": "Albánia", "region": "Europe", "lat": 41.3275, "lon": 19.8187, "vibe": {"urban": 0.7, "beach": 0.2, "nature": 0.6, "history": 0.5, "nightlife": 0.8, "luxury": 0.4}, "img": "https://images.unsplash.com/photo-1555590538-40679822aef0?auto=format&fit=crop&w=800&q=80"},
    {"id": "ljubljana_si", "name": "Ljubljana", "country": "Szlovénia", "region": "Europe", "lat": 46.0569, "lon": 14.5058, "vibe": {"urban": 0.5, "beach": 0.0, "nature": 1.0, "history": 0.8, "nightlife": 0.5, "luxury": 0.6}, "img": "https://images.unsplash.com/photo-150935684345d-85ca13fdd6a5?auto=format&fit=crop&w=800&q=80"},
    {"id": "sarajevo_ba", "name": "Szarajevó", "country": "Bosznia-Hercegovina", "region": "Europe", "lat": 43.8563, "lon": 18.4131, "vibe": {"urban": 0.6, "beach": 0.0, "nature": 0.7, "history": 1.0, "nightlife": 0.6, "luxury": 0.4}, "img": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=800&q=80"}
]

base_dir = os.path.dirname(os.path.abspath(__file__))
dest_path = os.path.join(base_dir, "data", "destinations.json")

with open(dest_path, "r", encoding="utf-8") as f:
    dests = json.load(f)

existing_names = [d["name"] for d in dests]

for c in new_cities:
    if c["name"] not in existing_names:
        dests.append({
            "id": c["id"],
            "name": c["name"],
            "country": c["country"],
            "region": c["region"],
            "lat": c["lat"],
            "lon": c["lon"],
            "vibe_metrics": {
                "urban_scale": c["vibe"]["urban"],
                "beach_scale": c["vibe"]["beach"],
                "nature_scale": c["vibe"]["nature"],
                "historical_scale": c["vibe"]["history"],
                "nightlife_scale": c["vibe"]["nightlife"],
                "luxury_scale": c["vibe"]["luxury"]
            },
            "metrics": {
                "safety_index": 50,
                "cost_index_daily_eur": 100,
                "happiness_score": 70
            },
            "image": c["img"]
        })

with open(dest_path, "w", encoding="utf-8") as f:
    json.dump(dests, f, indent=2, ensure_ascii=False)

print(f"Added {len(new_cities)} cities.")

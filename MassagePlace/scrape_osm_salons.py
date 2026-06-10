import json
import csv
import requests

def scrape_budapest_salons():
    print("Budapesti wellness és masszázs szalonok lekérdezése az OpenStreetMap Overpass API-ról...")
    
    # Overpass QL lekérdezés: Budapest területén lévő 'massage' és 'spa' helyek
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json][timeout:50];
    area["name"="Budapest"]->.searchArea;
    (
      node["amenity"="massage"](area.searchArea);
      way["amenity"="massage"](area.searchArea);
      node["leisure"="spa"](area.searchArea);
      way["leisure"="spa"](area.searchArea);
    );
    out body;
    """
    
    try:
        response = requests.post(overpass_url, data={'data': overpass_query}, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Hiba a lekérdezés során: {e}")
        return

    elements = data.get("elements", [])
    print(f"Sikeresen lekérve {len(elements)} OSM elem. Feldolgozás...")

    salons = []
    for elem in elements:
        tags = elem.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
            
        # Cím összeszerelése
        postcode = tags.get("addr:postcode", "")
        city = tags.get("addr:city", "Budapest")
        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")
        address = f"{postcode} {city}, {street} {housenumber}".strip().replace("  ", " ")
        
        # Elérhetőségek kinyerése
        website = tags.get("website") or tags.get("contact:website") or tags.get("facebook") or ""
        email = tags.get("email") or tags.get("contact:email") or ""
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        
        salons.append({
            "Név": name,
            "Cím": address,
            "Weboldal": website,
            "E-mail": email,
            "Telefon": phone
        })

    # Írás CSV fájlba
    output_file = "budapest_osm_salons.csv"
    try:
        with open(output_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Név", "Cím", "Weboldal", "E-mail", "Telefon"])
            writer.writeheader()
            for salon in salons:
                writer.writerow(salon)
        print(f"Sikeresen elmentve {len(salons)} szalon a(z) '{output_file}' fájlba!")
    except Exception as e:
        print(f"Hiba a fájl mentésekor: {e}")

if __name__ == "__main__":
    scrape_budapest_salons()

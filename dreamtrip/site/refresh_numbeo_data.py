import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_numbeo_rankings():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    cities_data = {}

    def normalize(name):
        # Remove parenthetical suffixes like "(China)" and lowercase
        import re
        name = re.sub(r"\s*\(.*?\)\s*", "", name)
        return name.strip()

    # 1. Cost of Living
    print("Scraping Cost of Living...")
    try:
        col_url = "https://www.numbeo.com/cost-of-living/rankings.jsp"
        r = requests.get(col_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", id="indices_comparison_table")
        if not table:
            # Fallback for dynamic IDs
            table = soup.find("table", class_="stripe")
            
        if table:
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    city_full = cells[1].text.strip()
                    index = float(cells[2].text.strip())
                    norm_city = normalize(city_full)
                    cities_data[city_full] = {
                        "norm_name": norm_city,
                        "cost_index": index,
                        "safety_index": None
                    }
    except Exception as e:
        print(f"COL Scrape error: {e}")

    # 2. Safety
    print("Scraping Safety...")
    try:
        safe_url = "https://www.numbeo.com/crime/rankings.jsp"
        r = requests.get(safe_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", id="indices_comparison_table")
        if not table:
            table = soup.find("table", class_="stripe")
            
        if table:
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    city_full = cells[1].text.strip()
                    safety = float(cells[3].text.strip())
                    norm_city = normalize(city_full)
                    
                    found = False
                    for key, val in cities_data.items():
                        if val["norm_name"] == norm_city:
                            val["safety_index"] = safety
                            found = True
                            break
                    
                    if not found:
                        cities_data[city_full] = {
                            "norm_name": norm_city,
                            "cost_index": None,
                            "safety_index": safety
                        }
    except Exception as e:
        print(f"Safety Scrape error: {e}")

    # Save to file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "data", "live_numbeo_indices.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cities_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved {len(cities_data)} cities to {output_path}")

if __name__ == "__main__":
    scrape_numbeo_rankings()

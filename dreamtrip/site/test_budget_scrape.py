import requests
from bs4 import BeautifulSoup
import re

def get_budget_your_trip_cost(city_name):
    try:
        # Search for city
        search_url = f"https://www.budgetyourtrip.com/search?q={city_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(search_url, headers=headers, allow_redirects=True, timeout=10)
        
        # If it redirected to a city page
        if "budgetyourtrip.com/" in r.url and r.url.count("/") >= 4:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Look for average daily cost
            # Example text: "The average daily cost (per person) in Paris is €220"
            content = soup.get_text()
            
            # Try to find currency + amount
            # Look for something like "average daily cost (per person) in ... is"
            match = re.search(r"average daily cost.*?is.*?([\€\$£]|[A-Z]{3})\s?([\d,]+)", content, re.IGNORECASE | re.DOTALL)
            if match:
                currency = match.group(1)
                amount = match.group(2).replace(",", "")
                print(f"City: {city_name} | URL: {r.url} | Cost: {currency}{amount}")
                return float(amount), currency
            
            # Backup: find specific price tags if they exist
            # Often there are spans with class 'price' or similar
            price_tag = soup.find("span", string=re.compile(r"Average Daily Cost", re.I))
            if price_tag:
                 # The amount is usually in the next sibling or parent
                 parent = price_tag.find_parent()
                 print(f"Found price tag parent: {parent.get_text()}")
                 
        else:
            print(f"Could not find specific city page for {city_name}. URL: {r.url}")
            
    except Exception as e:
        print(f"Error for {city_name}: {e}")
    return None

if __name__ == "__main__":
    get_budget_your_trip_cost("Paris")
    get_budget_your_trip_cost("Budapest")
    get_budget_your_trip_cost("Barcelona")

import requests
from bs4 import BeautifulSoup

def main():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})
    
    for url in ["https://schnopsn.com", "https://schnopsn.com/login", "https://schnopsn.com/game/schnopsn.htm"]:
        try:
            r = session.get(url, timeout=10)
            print(f"\n--- {url} (Status: {r.status_code}) ---")
            soup = BeautifulSoup(r.text, "html.parser")
            print("Title:", soup.title.string if soup.title else "No title")
            forms = soup.find_all("form")
            print("Forms:", len(forms))
            for f in forms:
                print("  Action:", f.get("action"), "Method:", f.get("method"))
                inputs = f.find_all("input")
                for inp in inputs:
                    print("    Input:", inp.get("name"), inp.get("type"), inp.get("id"))
            
            links = soup.find_all("a")
            interesting_links = [a.get("href") for a in links if a.get("href") and any(k in a.get("href").lower() for k in ["login", "anmeld", "user", "konto", "auth", "sign", "game"])]
            print("Interesting links:", set(interesting_links))
        except Exception as e:
            print(f"Error fetching {url}: {e}")

if __name__ == "__main__":
    main()

import json

def check_keys():
    with open("data/live_numbeo_indices.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        keys = list(data.keys())
        
        targets = ["denpasar", "bali", "santorini", "thira", "thera", "greece", "indonesia"]
        for k in keys:
            if any(t in k.lower() for t in targets):
                print(k)

if __name__ == "__main__":
    check_keys()

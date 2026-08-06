import os, sys, json, urllib.request
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv('landing_predikalo1/.env')
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def sb_get(endpoint):
    req = urllib.request.Request(f"{url}/rest/v1/{endpoint}", headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

# Get all runs in pilis campaign
pilis_runs = sb_get("runs?select=*,runners(email,name),shipments(*)&campaign=eq.pilis")

print(f"=== ALL {len(pilis_runs)} RUNS IN PILIS (Nagy-Kevély) CAMPAIGN ===")
for r in pilis_runs:
    email = (r.get('runners') or {}).get('email', '')
    name = r.get('name') or (r.get('runners') or {}).get('name', '')
    sn = r.get('serial_number', '')
    shipments_raw = r.get('shipments')
    shipment = shipments_raw[0] if isinstance(shipments_raw, list) and shipments_raw else (shipments_raw or {})
    print(f"Pilis Run {sn:<14} | {name:<22} | {email:<30} | run.shipped={r.get('shipped')} | ship.shipped={shipment.get('shipped')} | tracking={shipment.get('tracking_code')}")

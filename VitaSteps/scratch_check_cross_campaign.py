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

runs = sb_get("runs?select=id,serial_number,name,campaign,shipped,runners(email),shipments(*)&order=created_at.asc")

print(f"=== CHECKING ALL {len(runs)} RUNS AND THEIR SHIPMENTS ===")
for r in runs:
    email = (r.get('runners') or {}).get('email', '')
    sn = r.get('serial_number', '')
    camp = r.get('campaign', '')
    shipments_raw = r.get('shipments')
    
    if shipments_raw:
        if isinstance(shipments_raw, list):
            for s in shipments_raw:
                print(f"Run ID={r['id'][:8]} | {sn:<12} | camp={camp:<12} | email={email:<28} | ship_id={s.get('id')[:8]} | ship.run_id={s.get('run_id')[:8]} | tracking={s.get('tracking_code')} | shipped={s.get('shipped')}")
        else:
            s = shipments_raw
            print(f"Run ID={r['id'][:8]} | {sn:<12} | camp={camp:<12} | email={email:<28} | ship_id={s.get('id')[:8]} | ship.run_id={s.get('run_id')[:8]} | tracking={s.get('tracking_code')} | shipped={s.get('shipped')}")
    else:
        print(f"Run ID={r['id'][:8]} | {sn:<12} | camp={camp:<12} | email={email:<28} | NO SHIPMENT RECORD")

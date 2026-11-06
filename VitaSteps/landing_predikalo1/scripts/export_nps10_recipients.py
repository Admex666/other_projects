import os
import sys
import csv
import json
import urllib.request
import secrets
from dotenv import load_dotenv

# Windows console UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
CSV_FILE = os.path.join(DATA_DIR, "kitero_nps10_recipients.csv")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

def supabase_get(endpoint: str) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def guess_first_name(names_list: list) -> str:
    """Hungarian name heuristic: usually 'Vezetéknév Keresztnév' -> Keresztnév."""
    if not names_list:
        return ""
    # Filter out email-like names
    valid_names = [n for n in names_list if "@" not in n]
    name_to_use = valid_names[0] if valid_names else names_list[0]
    
    parts = name_to_use.strip().split()
    if len(parts) > 1:
        # Check if first part is a title like dr., Dr.
        if parts[0].lower().startswith("dr"):
            return parts[-1] if len(parts) > 2 else parts[1]
        return parts[-1]
    return parts[0]

def export_recipients():
    print("=== Exporting NPS=10 Feedback Recipients ===")
    
    # 1. Fetch feedbacks with nps_score = 10
    feedbacks = supabase_get("feedbacks?nps_score=eq.10&select=*")
    print(f"Total feedback rows with NPS=10: {len(feedbacks)}")

    # 2. Fetch runners and orders for name lookup
    runners = supabase_get("runners?select=id,email,name,billing_name")
    orders = supabase_get("orders?select=id,billing_email,billing_name")

    email_to_names = {}
    def register_name(email, name):
        if not email or not name:
            return
        e = email.lower().strip()
        n = name.strip()
        if not e or not n:
            return
        if e not in email_to_names:
            email_to_names[e] = set()
        email_to_names[e].add(n)

    for r in runners:
        register_name(r.get("email"), r.get("name"))
        register_name(r.get("email"), r.get("billing_name"))

    for o in orders:
        register_name(o.get("billing_email"), o.get("billing_name"))

    # Extract unique emails from feedbacks
    unique_emails = []
    seen = set()
    for f in feedbacks:
        raw_e = f.get("runner_email")
        if raw_e:
            e = raw_e.lower().strip()
            if e and e not in seen:
                seen.add(e)
                unique_emails.append(e)

    print(f"Unique NPS=10 recipient emails: {len(unique_emails)}")

    # 3. Check existing CSV to preserve manual edits and sent flags
    existing_data = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row["email"].lower().strip()] = row

    rows_to_write = []
    for idx, email in enumerate(unique_emails, 1):
        names_set = email_to_names.get(email, set())
        names_list = sorted(list(names_set))
        all_names_str = " / ".join(names_list) if names_list else ""
        
        if email in existing_data:
            # Preserve existing manual edits
            ex = existing_data[email]
            row = {
                "email": email,
                "first_name": ex.get("first_name") or guess_first_name(names_list),
                "all_names": all_names_str or ex.get("all_names", ""),
                "cid": ex.get("cid") or f"c_nps10_{idx:02d}_{secrets.token_hex(3)}",
                "sent": ex.get("sent", "0"),
                "sent_at": ex.get("sent_at", "")
            }
        else:
            first_name = guess_first_name(names_list)
            cid = f"c_nps10_{idx:02d}_{secrets.token_hex(3)}"
            row = {
                "email": email,
                "first_name": first_name,
                "all_names": all_names_str,
                "cid": cid,
                "sent": "0",
                "sent_at": ""
            }
        rows_to_write.append(row)

    # Write CSV
    fieldnames = ["email", "first_name", "all_names", "cid", "sent", "sent_at"]
    with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_write)

    print(f"\n✅ Successfully exported {len(rows_to_write)} recipients to:")
    print(f"   {CSV_FILE}\n")
    print("Minta sorok:")
    for r in rows_to_write[:5]:
        print(f"  - {r['email']}: first_name='{r['first_name']}', all_names='{r['all_names']}', cid='{r['cid']}', sent={r['sent']}")

if __name__ == "__main__":
    export_recipients()

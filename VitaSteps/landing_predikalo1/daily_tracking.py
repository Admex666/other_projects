import os
import json
import sys
import smtplib
import ssl
import datetime
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from requests.auth import HTTPBasicAuth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Ensure console logs are UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load local .env file (if it exists) for local execution
env_path = os.path.join(SCRIPT_DIR, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# ===== CONFIGURATION =====
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SHEET_NAME = "Nevezések"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Foxpost Credentials
FOXPOST_API_KEY = os.getenv("FOXPOST_API_KEY")
FOXPOST_USERNAME = os.getenv("FOXPOST_USERNAME")
FOXPOST_PASSWORD = os.getenv("FOXPOST_PASSWORD")
FOXPOST_BASE_URL = "https://webapi.foxpost.hu/api"

# SMTP Credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "vitasteps.team@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Tally Feedback Form
TALLY_FEEDBACK_FORM_ID = os.getenv("TALLY_FEEDBACK_FORM_ID", "NpRz5W_feedback")

DRY_RUN = os.getenv("DRY_RUN", "False").lower() in ("true", "1", "yes")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def update_supabase_runner(email, received_date):
    """Updates the received_date for the runner in Supabase."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("Supabase credentials missing. Skipping Supabase update.")
        return
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/runners?email=eq.{email.lower()}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "received_date": received_date
    }
    if DRY_RUN:
        print(f"[DRY RUN] Would update Supabase runner {email} with received_date={received_date}")
        return
    try:
        r = requests.patch(url, headers=headers, json=payload, timeout=10)
        print(f"Supabase update for {email}: status {r.status_code}")
    except Exception as e:
        print(f"Supabase update failed for {email}: {e}")

print(f"Daily Tracking started. Mode: {'DRY RUN (No write/send)' if DRY_RUN else 'PRODUCTION'}")


def get_sheets_service():
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set.")
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def fetch_sheet_data(service):
    # Fetch first 500 rows and columns up to Z (or beyond, let's fetch A1:AH500 to be safe)
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_NAME}!A1:AH500"
    ).execute()
    return result.get("values", [])

def ensure_column_exists(service, headers, col_name):
    """Checks if a column exists. If not, appends it to the header row in Google Sheet."""
    # Find case-insensitive
    for idx, h in enumerate(headers):
        if h.strip().lower() == col_name.strip().lower():
            return idx, headers
            
    # If not found, append to header
    new_col_idx = len(headers)
    col_letter = chr(ord('A') + new_col_idx) if new_col_idx < 26 else f"A{chr(ord('A') + (new_col_idx - 26))}"
    print(f"Column '{col_name}' not found. Dynamically appending it at index {new_col_idx} (Col {col_letter})...")
    
    if not DRY_RUN:
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"{SHEET_NAME}!{col_letter}1",
            valueInputOption="RAW",
            body={"values": [[col_name]]}
        ).execute()
    
    headers.append(col_name)
    return new_col_idx, headers

def write_cell(service, row_number, col_index, value):
    """Writes a value to a cell. row_number is 1-based sheet row."""
    col_letter = chr(ord('A') + col_index) if col_index < 26 else f"A{chr(ord('A') + (col_index - 26))}"
    cell_range = f"{SHEET_NAME}!{col_letter}{row_number}"
    print(f"Writing '{value}' to {cell_range}...")
    if not DRY_RUN:
        service.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=cell_range,
            valueInputOption="RAW",
            body={"values": [[value]]}
        ).execute()

def get_first_name(full_name: str) -> str:
    parts = full_name.strip().split()
    return parts[-1] if parts else full_name

def send_feedback_email(name, email):
    """Sends the follow-up feedback email via SMTP pointing to the portal."""
    first_name = get_first_name(name)
    portal_link = f"https://vitastepsss.vercel.app/portal.html?email={urllib.parse.quote(email)}"
    
    # Load template
    template_path = os.path.join(SCRIPT_DIR, "email_feedback_template.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        # Fallback basic template if file not found
        html = f"""
        <html>
        <body>
            <p>Szia {first_name}!</p>
            <p>Látjuk a Foxpost rendszerében, hogy az érmed sikeresen megérkezett! Reméljük, elégedett vagy vele.</p>
            <p>Kérjük, szánj rá 2 percet, és oszd meg velünk a véleményedet az alábbi linken:</p>
            <p><a href="{portal_link}">Vélemény megosztása</a></p>
            <p>Üdvözlettel,<br>A VitaSteps Csapata</p>
        </body>
        </html>
        """
        
    html = html.replace("{{FIRST_NAME}}", first_name)
    html = html.replace("{{TALLY_FEEDBACK_LINK}}", portal_link)

    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🏔️ Hogy tetszett a kihívás? – Küldd el a visszajelzésed!"
    msg["From"] = f"VitaSteps <{SENDER_EMAIL}>"
    msg["To"] = email
    
    msg.attach(MIMEText(html, "html"))
    
    if DRY_RUN:
        print(f"[DRY RUN] Would send feedback email to {name} ({email})")
        print(f"          Link: {feedback_link}")
        return True
        
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        print(f"📧 Feedback email successfully sent to {name} ({email})")
        return True
    except Exception as e:
        print(f"❌ Failed to send feedback email to {email}: {e}")
        return False

def main():
    service = get_sheets_service()
    rows = fetch_sheet_data(service)
    if not rows or len(rows) < 2:
        print("Empty sheet or unable to fetch rows.")
        return
        
    headers = rows[0]
    
    # Locate/create columns
    def find_col(name, default_val):
        for idx, h in enumerate(headers):
            if h.strip().lower() == name.lower().strip():
                return idx
        return default_val
        
    col_nev = find_col("név", 4)
    col_email = find_col("email", 3)
    col_barcode = find_col("foxpost barcode", 23)
    col_kikuldve = find_col("érem kiküldve?", 24)
    col_egyutt_kuldve = find_col("együtt küldve", 26)
    
    # Dynamically find or create columns
    col_atveve, headers = ensure_column_exists(service, headers, "érem átvéve")
    col_followup, headers = ensure_column_exists(service, headers, "follow-up email?")
    
    print(f"Column indices in Sheet:")
    print(f"  - Név: {col_nev} | Email: {col_email}")
    print(f"  - Barcode: {col_barcode} | Kiküldve: {col_kikuldve}")
    print(f"  - Együtt küldve: {col_egyutt_kuldve}")
    print(f"  - Érem átvéve (Target): {col_atveve}")
    print(f"  - Follow-up email (Target): {col_followup}")
    
    # Parse runners
    runners = []
    for idx, row in enumerate(rows[1:], start=2):
        row += [""] * (len(headers) - len(row))
        
        name = row[col_nev].strip()
        email = row[col_email].strip()
        barcode = row[col_barcode].strip()
        kikuldve = row[col_kikuldve].strip()
        atveve = row[col_atveve].strip()
        followup = row[col_followup].strip()
        egyutt_kuldve = row[col_egyutt_kuldve].strip()
        
        if not name or not email:
            continue
            
        runners.append({
            "row_index": idx,
            "name": name,
            "email": email,
            "barcode": barcode,
            "shipped": bool(kikuldve) and kikuldve.lower() not in ("", "#n/a", "#name?", "#value!", "nem", "no", "false", "0"),
            "received_date": atveve if atveve not in ("", "#n/a", "#name?", "#value!") else None,
            "followup_sent": followup.lower() in ("igen", "yes"),
            "egyutt_kuldve": egyutt_kuldve
        })
        
    print(f"Total parsed runners: {len(runners)}")
    
    # 2. Build shipment groups (exactly matching app.py logic)
    for r in runners:
        primary = None
        egyutt_val = r["egyutt_kuldve"].strip()
        primary_email = ""
        is_sub_order = False
        
        if egyutt_val:
            primary = next((x for x in runners if x["email"].lower() == egyutt_val.lower()), None)
            if not primary:
                primary = next((x for x in runners if x["name"].lower() == egyutt_val.lower()), None)
            if primary:
                primary_email = primary["email"]
                is_sub_order = True
        else:
            primary = next((x for x in runners if x["email"].lower() == r["email"].lower() and x["row_index"] != r["row_index"] and x["barcode"]), None)
            if primary:
                primary_email = primary["email"]
                is_sub_order = True
                
        r["primary_buyer"] = primary_email
        r["is_sub_order"] = is_sub_order
        r["group_key"] = primary_email if (is_sub_order and primary_email) else r["email"]

    # 3. Group runners
    groups = {}
    for r in runners:
        key = r["group_key"].lower()
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
        
    print(f"Total shipment groups: {len(groups)}")
    
    # Find groups where shipment is in transit (shipped=True, received_date=None)
    tracking_list = []
    for gkey, members in groups.items():
        # A group has a barcode if any member has one
        barcode = next((m["barcode"] for m in members if m["barcode"].upper().startswith("CLFOX")), None)
        shipped = any(m["shipped"] for m in members)
        already_received = any(m["received_date"] for m in members)
        
        if barcode and shipped and not already_received:
            tracking_list.append({
                "group_key": gkey,
                "barcode": barcode,
                "members": members
            })
            
    print(f"Groups to track (shipped, but not yet marked received): {len(tracking_list)}")
    
    # 4. Batch track statuses via Foxpost API
    if tracking_list:
        barcodes_to_query = [t["barcode"] for t in tracking_list]
        print(f"Querying Foxpost API for barcodes: {barcodes_to_query}")
        
        headers_api = {
            "Api-key": FOXPOST_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        auth = HTTPBasicAuth(FOXPOST_USERNAME, FOXPOST_PASSWORD)
        
        try:
            r_api = requests.post(f"{FOXPOST_BASE_URL}/tracking/tracks", headers=headers_api, auth=auth, json=barcodes_to_query, timeout=15)
            if r_api.status_code == 200:
                results = r_api.json()
                
                # Create a map for fast lookup
                barcode_results = {p.get("barcode"): p for p in results}
                
                for item in tracking_list:
                    bc = item["barcode"]
                    res = barcode_results.get(bc)
                    if not res:
                        print(f"No tracking results returned for {bc}")
                        continue
                        
                    # Extract latest status
                    statuses = res.get("statuses", [])
                    if not statuses:
                        continue
                        
                    # Sort statuses by date descending
                    sorted_statuses = sorted(statuses, key=lambda x: x.get("statusDate", ""), reverse=True)
                    latest = sorted_statuses[0]
                    status_code = latest.get("status")
                    status_date_str = latest.get("statusDate", "") # '2026-06-29T22:59:36'
                    
                    print(f"Tracking status of group {item['group_key']} ({bc}): {status_code} at {status_date_str}")
                    
                    if status_code in ("RECEIVE", "HDRECEIVE"):
                        # Parse receipt date (e.g. 2026.06.29)
                        try:
                            dt = datetime.datetime.fromisoformat(status_date_str)
                            received_date = dt.strftime("%Y.%m.%d")
                        except Exception:
                            received_date = datetime.datetime.now().strftime("%Y.%m.%d")
                            
                        print(f"🎉 Group {item['group_key']} has picked up the package on {received_date}!")
                        
                        # Update received date for all group members in Sheet & Supabase
                        for member in item["members"]:
                            write_cell(service, member["row_index"], col_atveve, received_date)
                            update_supabase_runner(member["email"], received_date)
                            member["received_date"] = received_date # Update local model as well
            else:
                print(f"Foxpost API returned code {r_api.status_code}: {r_api.text}")
        except Exception as e:
            print(f"Failed to query Foxpost API: {e}")
            
    # 5. Send follow-up emails for received packages
    # We send follow-up emails to any group member whose received_date is set (NOT NULL) and followup_sent is False (NULL)
    print("\nChecking for eligible follow-up email recipients...")
    followup_count = 0
    
    for r in runners:
        # Check if received but follow-up email not yet sent
        if r["received_date"] and not r["followup_sent"]:
            print(f"Runner {r['name']} ({r['email']}) is eligible (Received: {r['received_date']}, Email: Pending)")
            
            # Send the email
            success = send_feedback_email(r["name"], r["email"])
            if success:
                # Write "Igen" back to Sheet
                write_cell(service, r["row_index"], col_followup, "Igen")
                followup_count += 1
                
    print(f"Done. Sent {followup_count} follow-up emails in this run.")

if __name__ == "__main__":
    main()

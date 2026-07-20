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
from dotenv import load_dotenv

# Ensure console logs are UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load local .env file (if it exists) for local execution
env_path = os.path.join(SCRIPT_DIR, '..', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# ===== CONFIGURATION =====
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

# Dry Run flag
DRY_RUN = os.getenv("DRY_RUN", "False").lower() in ("true", "1", "yes")

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"Daily Tracking started. Mode: {'DRY RUN (No write/send)' if DRY_RUN else 'PRODUCTION'}")

def get_headers():
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }

def fetch_in_transit_shipments():
    """Fetches all shipments from Supabase where shipped=true and received=false."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("Error: Supabase credentials missing!")
        return []

    # Get shipments joined with runs and runners
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/shipments?shipped=eq.true&received=eq.false&select=*,runs(*,runners(*))"
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Failed to fetch shipments. Status: {r.status_code}, Response: {r.text}")
            return []
    except Exception as e:
        print(f"Exception while fetching shipments: {e}")
        return []

def update_received_status(shipment_id, run_id, received_date_iso, received_date_str):
    """Marks the shipment and run as received in Supabase."""
    if DRY_RUN:
        print(f"[DRY RUN] Would update Supabase shipment {shipment_id} and run {run_id} to received (date={received_date_str})")
        return True

    try:
        # 1. Update shipments table
        shipment_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/shipments?id=eq.{shipment_id}"
        r_ship = requests.patch(shipment_url, headers=get_headers(), json={
            "received": True,
            "received_at": received_date_iso
        }, timeout=10)

        # 2. Update runs table
        run_url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/runs?id=eq.{run_id}"
        r_run = requests.patch(run_url, headers=get_headers(), json={
            "received_date": received_date_str
        }, timeout=10)

        print(f"Updated status in Supabase. Shipment patch status: {r_ship.status_code}, Run patch status: {r_run.status_code}")
        return r_ship.status_code in (200, 204) and r_run.status_code in (200, 204)
    except Exception as e:
        print(f"Failed to update received status: {e}")
        return False

def get_first_name(full_name: str) -> str:
    parts = full_name.strip().split()
    return parts[-1] if parts else full_name

def send_feedback_email(name, email, campaign):
    """Sends the follow-up feedback email via SMTP with dynamic campaign mapping."""
    first_name = get_first_name(name)
    portal_link = f"https://vitastepsss.vercel.app/portal.html?email={urllib.parse.quote(email)}"
    
    # Map campaign to human readable name
    campaign_name = "VitaSteps"
    if campaign:
        campaign_lower = str(campaign).lower()
        if "pilis" in campaign_lower or "nagy" in campaign_lower:
            campaign_name = "Nagy-Kevély"
        elif "predikalo" in campaign_lower:
            campaign_name = "Prédikálószék"
        else:
            campaign_name = campaign

    # Load template
    template_path = os.path.join(SCRIPT_DIR, "..", "email_feedback_template.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        # Fallback basic template if file not found
        html = f"""
        <html>
        <body>
            <p>Szia {first_name}!</p>
            <p>Látjuk a Foxpost rendszerében, hogy a <strong>{campaign_name} érmed</strong> sikeresen megérkezett! Reméljük, elégedett vagy vele.</p>
            <p>Kérjük, szánj rá 2 percet, és oszd meg velünk a véleményedet az alábbi linken:</p>
            <p><a href="{portal_link}">Vélemény megosztása és Oklevél letöltése</a></p>
            <p>Üdvözlettel,<br>A VitaSteps Csapata</p>
        </body>
        </html>
        """
        
    html = html.replace("{{FIRST_NAME}}", first_name)
    html = html.replace("{{TALLY_FEEDBACK_LINK}}", portal_link)
    html = html.replace("{{CAMPAIGN_NAME}}", campaign_name)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏔️ Hogy tetszett a {campaign_name} kihívás? – Küldd el a visszajelzésed!"
    msg["From"] = f"VitaSteps <{SENDER_EMAIL}>"
    msg["To"] = email
    
    msg.attach(MIMEText(html, "html"))
    
    if DRY_RUN:
        print(f"[DRY RUN] Would send feedback email to {name} ({email}) for campaign {campaign_name}")
        print(f"          Link: {portal_link}")
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
    # 1. Fetch in-transit shipments from Supabase
    shipments = fetch_in_transit_shipments()
    if not shipments:
        print("No shipments currently in transit (shipped=true, received=false) in Supabase.")
        return

    print(f"Found {len(shipments)} shipments to track.")

    # 2. Group shipments by parcel barcode to batch query Foxpost
    # Only track shipments with valid Foxpost barcodes
    tracking_groups = {}
    for s in shipments:
        barcode = s.get("tracking_code")
        if not barcode or not barcode.upper().startswith("CLFOX"):
            continue
        
        barcode = barcode.strip()
        if barcode not in tracking_groups:
            tracking_groups[barcode] = []
        tracking_groups[barcode].append(s)

    if not tracking_groups:
        print("No shipments found with valid Foxpost barcodes (CLFOX...).")
        return

    barcodes_to_query = list(tracking_groups.keys())
    print(f"Querying Foxpost API for {len(barcodes_to_query)} barcodes: {barcodes_to_query}")

    # 3. Query Foxpost API for tracking statuses
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
            barcode_results = {p.get("barcode"): p for p in results}

            for barcode, group_shipments in tracking_groups.items():
                res = barcode_results.get(barcode)
                if not res:
                    print(f"No tracking results returned for barcode {barcode}")
                    continue

                statuses = res.get("statuses", [])
                if not statuses:
                    continue

                # Get latest status based on date
                sorted_statuses = sorted(statuses, key=lambda x: x.get("statusDate", ""), reverse=True)
                latest = sorted_statuses[0]
                status_code = latest.get("status")
                status_date_str = latest.get("statusDate", "")

                print(f"Barcode {barcode} latest status: {status_code} at {status_date_str}")

                # If package was successfully delivered/received
                if status_code in ("RECEIVE", "HDRECEIVE"):
                    # Parse received date
                    try:
                        # Parse ISO format e.g. 2026-06-29T22:59:36
                        dt = datetime.datetime.fromisoformat(status_date_str)
                        received_date_iso = dt.isoformat() + "+00:00"
                        received_date_str = dt.strftime("%Y.%m.%d")
                    except Exception:
                        received_date_iso = datetime.datetime.utcnow().isoformat() + "+00:00"
                        received_date_str = datetime.datetime.now().strftime("%Y.%m.%d")

                    print(f"🎉 Package {barcode} has been picked up on {received_date_str}!")

                    # Update database and send emails for each shipment in the group
                    for shipment in group_shipments:
                        run = shipment.get("runs") or {}
                        runner = run.get("runners") or {}
                        
                        shipment_id = shipment.get("id")
                        run_id = run.get("id")
                        name = run.get("name") or runner.get("name") or "Teljesítő"
                        email = runner.get("email")
                        campaign = run.get("campaign")

                        if not run_id or not shipment_id:
                            continue

                        # Mark as received in Supabase
                        success = update_received_status(shipment_id, run_id, received_date_iso, received_date_str)
                        
                        # Send follow-up feedback email on success
                        if success and email:
                            send_feedback_email(name, email, campaign)
        else:
            print(f"Foxpost API returned status code {r_api.status_code}: {r_api.text}")
    except Exception as e:
        print(f"Failed to query Foxpost API or process results: {e}")

if __name__ == "__main__":
    main()

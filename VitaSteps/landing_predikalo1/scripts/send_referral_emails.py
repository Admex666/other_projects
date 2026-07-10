import os
import json
import sys
import smtplib
import ssl
import time
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests

# Ensure console logs are UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# ===== CONFIGURATION =====
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SHEET_NAME = "Nevezések"
FEEDBACK_SHEET_NAME = "feedback_raw"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# SMTP Credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "vitasteps.team@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

DRY_RUN = os.getenv("DRY_RUN", "False").lower() in ("true", "1", "yes")

def get_sheets_service():
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set.")
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)

def fetch_sheet_data(service, sheet_name_target):
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{sheet_name_target}!A1:AH500"
    ).execute()
    return result.get("values", [])

def ensure_column_exists(service, headers, col_name):
    """Checks if a column exists. If not, appends it to the header row in Google Sheet."""
    for idx, h in enumerate(headers):
        if h.strip().lower() == col_name.strip().lower():
            return idx, headers
            
    new_col_idx = len(headers)
    col_letter = chr(ord('A') + new_col_idx) if new_col_idx < 26 else f"A{chr(ord('A') + (new_col_idx - 26))}"
    print(f"Column '{col_name}' not found. Appending it at index {new_col_idx} (Col {col_letter})...")
    
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

def send_referral_email(name, email, portal_link):
    first_name = get_first_name(name)
    
    # Load referral template
    template_path = os.path.join(SCRIPT_DIR, "email_referral_template.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        print("❌ Error: email_referral_template.html not found!")
        return False
        
    referral_link = f"https://vitastepsss.vercel.app/checkout-widget.html?ref={urllib.parse.quote(email)}"
    
    html = html.replace("{{FIRST_NAME}}", first_name)
    html = html.replace("{{PORTAL_LINK}}", portal_link)
    html = html.replace("{{REFERRAL_LINK}}", referral_link)
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🎁 Ajánld a VitaSteps-et, teljesíts legközelebb ingyen!"
    msg["From"] = f"VitaSteps <{SENDER_EMAIL}>"
    msg["To"] = email
    
    msg.attach(MIMEText(html, "html"))
    
    if DRY_RUN:
        print(f"[DRY RUN] Would send referral email to {name} ({email})")
        print(f"          Referral link: {referral_link}")
        return True
        
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        print(f"📧 Referral email successfully sent to {name} ({email})")
        return True
    except Exception as e:
        print(f"❌ Failed to send referral email to {email}: {e}")
        return False

def main():
    print(f"==================================================")
    print(f"VitaSteps – Referral Email Sender")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'PRODUCTION'}")
    print(f"==================================================")
    
    service = get_sheets_service()
    
    # 1. Fetch feedbacks from Supabase REST API
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("Error: Supabase environment variables not found in .env!")
        return

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/feedbacks?select=runner_email"
    http_headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.get(url, headers=http_headers, timeout=10)
        if r.status_code != 200:
            print(f"Error fetching feedbacks from Supabase: {r.status_code} - {r.text}")
            return
        feedbacks = r.json()
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return

    feedback_emails = set(fb.get("runner_email", "").strip().lower() for fb in feedbacks if fb.get("runner_email"))
    print(f"Found {len(feedback_emails)} unique users who submitted feedback in Supabase.")
    
    # 2. Fetch runners from Nevezések
    rows = fetch_sheet_data(service, SHEET_NAME)
    if not rows or len(rows) < 2:
        print("Empty sheet or unable to fetch rows.")
        return
        
    headers = rows[0]
    
    def find_col(name, default_val):
        for idx, h in enumerate(headers):
            if h.strip().lower() == name.lower().strip():
                return idx
        return default_val
        
    col_nev = find_col("név", 4)
    col_email = find_col("email", 3)
    col_ref_sent, headers = ensure_column_exists(service, headers, "referral email sent?")
    
    # 3. Process each row
    sent_count = 0
    for idx, row in enumerate(rows[1:], start=2):
        row += [""] * (len(headers) - len(row))
        
        email = row[col_email].strip().lower()
        name = row[col_nev].strip()
        ref_sent = row[col_ref_sent].strip().lower() if len(row) > col_ref_sent else ''
        
        if not email or not name:
            continue
            
        # Check if they have submitted feedback and haven't received referral email yet
        if email in feedback_emails and ref_sent != "igen":
            print(f"\nProcessing {name} ({email})...")
            
            portal_link = f"https://vitastepsss.vercel.app/portal.html?email={urllib.parse.quote(email)}"
            
            success = send_referral_email(name, email, portal_link)
            if success:
                write_cell(service, idx, col_ref_sent, "Igen")
                sent_count += 1
                time.sleep(2) # delay to avoid rate limiting
                
    print(f"\n==================================================")
    print(f"Finished. Sent {sent_count} referral emails in this run.")
    print(f"==================================================")

if __name__ == "__main__":
    main()

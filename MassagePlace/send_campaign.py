import os
import csv
import sys
import time
import datetime
import smtplib
import urllib.parse
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Környezeti változók betöltése
load_dotenv()

# --- KONFIGURÁCIÓ ---
# Ha a DRY_RUN True, a script nem küld tényleges e-maileket, csak kiírja a terminálra a küldendő levelek előnézetét.
# Állítsd False-ra, ha valóban küldeni szeretnéd a kampányt.
DRY_RUN = False

# SMTP Beállítások (.env fájlból, vagy alapértelmezett értékekkel)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")  # pl. zenslot.team@gmail.com
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Gmail App Jelszó!
SENDER_NAME = os.getenv("SENDER_NAME", "Ádám")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)

# Google Sheets URL (.env fájlból) - pl. https://docs.google.com/spreadsheets/d/.../edit#gid=0
GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL")

# A Vercel partner landing page alap címe (ide irányítjuk őket)
BASE_URL = os.getenv("BASE_URL", "https://zenslot.vercel.app/partner")

# Késleltetés az e-mailek küldése között (másodpercben), hogy elkerüljük a spam szűrőket
SEND_DELAY = 10

# CSV fájlok nevei (ha nem a Google Sheets-et használod)
CONTACTS_FILE = "contacts.csv"
LOG_FILE = "campaign_log.csv"
# --- SABLONOK BETÖLTÉSE ---
def load_templates(campaign_type):
    """Betölti a megadott kampánytípushoz tartozó HTML és TXT sablonokat."""
    if campaign_type == "initial":
        html_path = "templates/initial_email.html"
        txt_path = "templates/initial_email.txt"
        subject = "Üres időpontok a következő 24 órában / Unsold slots in the next 24 hours"
    elif campaign_type == "followup":
        html_path = "templates/followup_email.html"
        txt_path = "templates/followup_email.txt"
        subject = "Re: Üres órák a naptárban / Unsold slots in your calendar"
    else:
        raise ValueError("Ismeretlen kampánytípus")
        
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_template = f.read()
        with open(txt_path, "r", encoding="utf-8") as f:
            txt_template = f.read()
    except Exception as e:
        print(f"HIBA: Nem sikerült beolvasni a sablonokat a templates/ mappából: {e}")
        sys.exit(1)
        
    return html_template, txt_template, subject


def check_config():
    """Ellenőrzi a küldéshez szükséges alapfeltételeket."""
    if not DRY_RUN:
        if not SMTP_USER or not SMTP_PASSWORD:
            print("HIBA: Az SMTP_USER vagy SMTP_PASSWORD nincs beállítva a .env fájlban!")
            print("Valódi küldés előtt kérjük, konfiguráld az SMTP adatokat!")
            sys.exit(1)
    
    # Ha nincs megadva Google Sheets, ellenőrizzük a helyi fájlt
    if not GOOGLE_SHEETS_URL and not os.path.exists(CONTACTS_FILE):
        print(f"HIBA: Sem GOOGLE_SHEETS_URL nincs a .env-ben, sem a(z) '{CONTACTS_FILE}' nem létezik!")
        sys.exit(1)

def get_csv_export_url(sheet_url):
    """Google Sheets URL átalakítása CSV letöltési linkké."""
    if not sheet_url:
        return None
    if "/export?format=csv" in sheet_url:
        return sheet_url
    if "/d/" in sheet_url:
        parts = sheet_url.split("/d/")
        subparts = parts[1].split("/")
        spreadsheet_id = subparts[0]
        export_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
        
        # Gid kinyerése tabokhoz (#gid=123)
        if "#gid=" in sheet_url:
            gid = sheet_url.split("#gid=")[1].split("&")[0]
            export_url += f"&gid={gid}"
        elif "gid=" in sheet_url:
            url_parts = urllib.parse.urlparse(sheet_url)
            query = urllib.parse.parse_qs(url_parts.query)
            if "gid" in query:
                export_url += f"&gid={query['gid'][0]}"
        return export_url
    return sheet_url

def get_sheets_client():
    """Létrehozza a hitelesített gspread klienst a Service Account kulccsal."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    if not os.path.exists(credentials_file):
        return None
    try:
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Figyelmeztetés: Nem sikerült a Google Sheets API hitelesítés: {e}")
        return None

def get_spreadsheet_id(sheet_url):
    """Kinyeri a táblázat ID-t az URL-ből."""
    if not sheet_url:
        return None
    if "/d/" in sheet_url:
        return sheet_url.split("/d/")[1].split("/")[0]
    return sheet_url

def update_sheet_status(email, new_status, new_date=None):
    """Közvetlenül frissíti a státuszt és opcionálisan a dátumot a Google Sheets-ben az e-mail cím alapján."""
    client = get_sheets_client()
    if not client:
        return False
        
    try:
        sheet_id = get_spreadsheet_id(GOOGLE_SHEETS_URL)
        if not sheet_id:
            return False
            
        sh = client.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        
        # Oszlopfejlécek beolvasása az indexek kinyeréséhez
        headers = worksheet.row_values(1)
        cleaned_headers = [h.strip().lower() for h in headers]
        
        try:
            email_col_idx = cleaned_headers.index("email") + 1
        except ValueError:
            print("HIBA: Nem található 'Email' oszlop a Google Sheet-ben!")
            return False
            
        try:
            status_col_idx = cleaned_headers.index("státusz") + 1
        except ValueError:
            try:
                status_col_idx = cleaned_headers.index("status") + 1
            except ValueError:
                print("HIBA: Nem található 'Státusz' vagy 'Status' oszlop a Google Sheet-ben!")
                return False
                
        # Dátum oszlop indexe (H oszlop = 8. oszlop)
        date_col_idx = 8
        for idx, h in enumerate(cleaned_headers):
            if "dátum" in h or "date" in h:
                date_col_idx = idx + 1
                break
                
        # Megkeressük a sort az e-mail cím alapján
        email_list = worksheet.col_values(email_col_idx)
        
        target_row_idx = -1
        for idx, email_val in enumerate(email_list):
            cleaned_email_val = clean_email(email_val)
            if cleaned_email_val and cleaned_email_val.lower() == email.lower():
                target_row_idx = idx + 1
                break
                
        if target_row_idx != -1:
            worksheet.update_cell(target_row_idx, status_col_idx, new_status)
            print(f" -> Google Sheet státusz frissítve: {email} -> {new_status}")
            
            if new_date:
                # Biztosítjuk, hogy a fejléc létezzen a dátum oszlopban, ha a táblázat rövidebb volt
                if len(headers) < date_col_idx:
                    worksheet.update_cell(1, date_col_idx, "Kiküldés dátuma")
                worksheet.update_cell(target_row_idx, date_col_idx, new_date)
                print(f" -> Google Sheet dátum frissítve: {email} -> {new_date}")
                
            return True
        else:
            print(f" -> Figyelmeztetés: Nem található a(z) '{email}' e-mail cím a táblázatban a státusz frissítéséhez.")
            return False
    except Exception as e:
        print(f" -> HIBA a Google Sheet frissítése közben: {e}")
        return False

def get_campaign_status_logs():
    """Beolvassa a campaign_log.csv-t és visszaadja az e-mailek legutolsó státuszait."""
    status_map = {}
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "email" in reader.fieldnames and "status" in reader.fieldnames:
                    for row in reader:
                        email = row["email"].strip().lower()
                        status = row["status"].strip().upper()
                        status_map[email] = status
        except Exception as e:
            print(f"Figyelmeztetés: Nem sikerült beolvasni a korábbi logokat: {e}")
    return status_map

def generate_personalized_url(salon_name, email):
    """Létrehozza a személyre szabott, követhető URL-t."""
    encoded_salon = urllib.parse.quote_plus(salon_name)
    encoded_email = urllib.parse.quote_plus(email)
    return f"{BASE_URL}?s={encoded_salon}&email={encoded_email}"

def log_campaign_send(salon_name, email, status, details=""):
    """Naplózza az e-mail küldés eredményét egy CSV-be."""
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "salon_name", "email", "status", "details"])
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, salon_name, email, status, details])

def send_email(session, salon_name, recipient_email, personalized_url, html_template, txt_template, subject):
    """Elküldi a személyre szabott e-mailt HTML és Plain Text formában is."""
    msg = MIMEMultipart('alternative')
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Szövegek generálása
    plain_body = txt_template.format(
        salon_name=salon_name,
        sender_name=SENDER_NAME,
        personalized_url=personalized_url
    )
    
    html_body = html_template.format(
        salon_name=salon_name,
        sender_name=SENDER_NAME,
        personalized_url=personalized_url
    )
    
    # MIME részek csatolása (a plain text az első, a HTML a második a fallback miatt)
    msg.attach(MIMEText(plain_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        session.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        return True, "Success"
    except Exception as e:
        return False, str(e)

def clean_email(email_str):
    """Megtisztítja az e-mail címet és ellenőrzi a formátumot."""
    if not email_str:
        return None
    email_str = email_str.strip()
    # Ha tartalmaz szóközt (pl. "email1 VAGY email2"), vegyük az első szót
    if " " in email_str:
        email_str = email_str.split()[0]
    # Ha vesszővel van elválasztva, vegyük az első címet
    if "," in email_str:
        email_str = email_str.split(",")[0].strip()
    # Alapvető ellenőrzés
    if "@" not in email_str:
        return None
    return email_str

def load_contacts():
    """Betölti a kapcsolatokat Google Sheets-ről vagy a helyi CSV-ből."""
    contacts = []
    
    if GOOGLE_SHEETS_URL:
        # 1. Próbáljuk meg közvetlenül a Google Sheets API-n keresztül olvasni
        client = get_sheets_client()
        if client:
            print("Kapcsolatok betöltése közvetlenül a Google Sheets API-n keresztül...")
            try:
                sheet_id = get_spreadsheet_id(GOOGLE_SHEETS_URL)
                sh = client.open_by_key(sheet_id)
                worksheet = sh.get_worksheet(0)
                rows = worksheet.get_all_values()
                if rows:
                    headers = [h.strip().lower() for h in rows[0]]
                    
                    # Oszlop indexek megkeresése
                    try:
                        salon_idx = headers.index("szalon neve")
                    except ValueError:
                        try:
                            salon_idx = headers.index("salon_name")
                        except ValueError:
                            salon_idx = 0
                            
                    try:
                        email_idx = headers.index("email")
                    except ValueError:
                        email_idx = 2
                        
                    try:
                        contact_idx = headers.index("kapcsolattartó")
                    except ValueError:
                        contact_idx = 5
                        
                    try:
                        status_idx = headers.index("státusz")
                    except ValueError:
                        try:
                            status_idx = headers.index("status")
                        except ValueError:
                            status_idx = 6
                            
                    # Kiküldés dátuma (H oszlop alapértelmezetten a 8. oszlop, 0-alapú indexe: 7)
                    date_idx = 7
                    for idx, h in enumerate(headers):
                        if "dátum" in h or "date" in h:
                            date_idx = idx
                            break
                            
                    for row in rows[1:]:
                        if len(row) <= max(salon_idx, email_idx):
                            continue
                            
                        salon_name = row[salon_idx].strip()
                        raw_email = row[email_idx].strip()
                        email = clean_email(raw_email)
                        contact_name = row[contact_idx].strip() if contact_idx < len(row) else ""
                        sheet_status = row[status_idx].strip() if status_idx < len(row) else ""
                        send_date = row[date_idx].strip() if date_idx < len(row) else ""
                        
                        if email:
                            contacts.append({
                                "salon_name": salon_name or "Szalon",
                                "email": email,
                                "contact_name": contact_name or salon_name or "Szalon Vezető",
                                "status": sheet_status,
                                "send_date": send_date
                            })
                        elif raw_email and not raw_email.startswith("#"):
                            print(f"Figyelmeztetés: Hibás e-mail cím átugorva: '{raw_email}' ({salon_name})")
                    print(f"Sikeresen betöltve {len(contacts)} cím közvetlenül a Google Sheets-ből.")
            except Exception as e:
                print(f"Figyelmeztetés: Nem sikerült a Google Sheets API olvasás: {e}")
                print("Visszalépés a publikus CSV export alapú letöltésre...")
                contacts = []

        # 2. Fallback a publikus CSV exportos URL-re, ha a Sheets API nem sikerült
        if not contacts:
            csv_url = get_csv_export_url(GOOGLE_SHEETS_URL)
            print(f"Kapcsolatok letöltése Google Sheets-ről (CSV export): {csv_url} ...")
            try:
                res = requests.get(csv_url, timeout=15)
                res.raise_for_status()
                csv_content = res.content.decode('utf-8')
                reader = csv.DictReader(csv_content.splitlines())
                for row in reader:
                    cleaned_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    salon_name = (cleaned_row.get("salon_name") or 
                                  cleaned_row.get("szalon_neve") or 
                                  cleaned_row.get("szalon neve") or 
                                  cleaned_row.get("szalon"))
                    
                    raw_email = cleaned_row.get("email") or cleaned_row.get("e-mail")
                    email = clean_email(raw_email)
                    
                    contact_name = (cleaned_row.get("contact_name") or 
                                    cleaned_row.get("kapcsolattartó") or 
                                    cleaned_row.get("kapcsolattartó    "))
                    
                    sheet_status = (cleaned_row.get("státusz") or 
                                    cleaned_row.get("status") or "").strip()
                    
                    # Dátum kinyerése a CSV-ből
                    send_date = ""
                    for k, v in cleaned_row.items():
                        if "dátum" in k or "date" in k:
                            send_date = v.strip()
                            break
                    
                    if email:
                        contacts.append({
                            "salon_name": salon_name or "Szalon",
                            "email": email,
                            "contact_name": contact_name or salon_name or "Szalon Vezető",
                            "status": sheet_status,
                            "send_date": send_date
                        })
                    elif raw_email and not raw_email.startswith("#"):
                        print(f"Figyelmeztetés: Hibás e-mail cím átugorva: '{raw_email}' ({salon_name})")
                print(f"Sikeresen betöltve {len(contacts)} cím Google Sheets-ről (CSV export).")
            except Exception as e:
                print(f"HIBA a Google Sheets letöltése közben: {e}")
                print("Visszalépés a helyi contacts.csv fájlra...")
                contacts = []

    # Ha a Google Sheets sikertelen volt vagy nincs beállítva, a helyi CSV-t olvassuk
    if not contacts:
        print(f"Kapcsolatok betöltése a helyi '{CONTACTS_FILE}' fájlból...")
        with open(CONTACTS_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                salon_name = (cleaned_row.get("salon_name") or 
                              cleaned_row.get("szalon_neve") or 
                              cleaned_row.get("szalon neve") or 
                              cleaned_row.get("szalon"))
                
                raw_email = cleaned_row.get("email") or cleaned_row.get("e-mail")
                email = clean_email(raw_email)
                
                contact_name = cleaned_row.get("contact_name") or cleaned_row.get("kapcsolattartó")
                sheet_status = (cleaned_row.get("státusz") or 
                                cleaned_row.get("status") or "").strip()
                
                if email:
                    contacts.append({
                        "salon_name": salon_name or "Szalon",
                        "email": email,
                        "contact_name": contact_name or salon_name or "Szalon Vezető",
                        "status": sheet_status
                    })
        print(f"Betöltve {len(contacts)} cím a helyi fájlból.")
        
    return contacts

def run_campaign():
    global DRY_RUN
    check_config()

    print("=" * 60)
    print("               ZENSLOT B2B KAMPÁNY KEZELŐ")
    print("=" * 60)
    print("Melyik kampányt szeretnéd küldeni?")
    print("1. Első megkeresés (Initial Reachout)")
    print("2. Követő levél (Follow-up)")
    
    try:
        campaign_choice = input("Opció száma (1-2): ").strip()
    except KeyboardInterrupt:
        print("\nKilépés...")
        return
        
    if campaign_choice == "1":
        campaign_type = "initial"
    elif campaign_choice == "2":
        campaign_type = "followup"
    else:
        print("\nHibás választás. Kilépés...")
        return
        
    # Sablonok betöltése fájlból
    html_template, txt_template, email_subject = load_templates(campaign_type)

    # Korábbi küldések naplójának betöltése
    status_map = get_campaign_status_logs()

    # Címjegyzék betöltése
    contacts = load_contacts()
    
    # Kapcsolatok és státuszok osztályozása
    print("\n--- KAPCSOLATOK STÁTUSZA ---")
    active_contacts = []
    skipped_count = 0
    
    for i, contact in enumerate(contacts, 1):
        salon_name = contact["salon_name"]
        email = contact["email"]
        sheet_status = contact.get("status", "").strip()
        status_lower = sheet_status.lower()
        
        if campaign_type == "initial":
            # Első megkeresés: Csak a "0. gyűjtés" státuszúaknak küldjük
            if status_lower in ("0. gyűjtés", "0. gyujtes"):
                status = "Küldendő (Új megkeresés)"
                active_contacts.append(contact)
            elif "érdeklődik" in status_lower:
                status = f"Már érdeklődik: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            elif "kiküldve" in status_lower or "sent" in status_lower or "follow-up" in status_lower or "followup" in status_lower:
                status = f"Már kapott levelet: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            else:
                status = f"Egyedi státusz: '{sheet_status}' (Kihagyva - nem '0. gyűjtés')"
                skipped_count += 1
        else:
            # Követő levél (followup): Csak akkor küldjük, ha a státusz pontosan "1. kiküldve" ÉS eltelt 72 óra
            if status_lower == "1. kiküldve":
                send_date_str = contact.get("send_date", "").strip()
                if not send_date_str:
                    status = "Nincs kiküldési dátum (Kihagyva)"
                    skipped_count += 1
                else:
                    try:
                        # Dátum normalizálása és parse-olása
                        date_str_clean = send_date_str.replace(".", "-").replace("/", "-").strip()
                        if len(date_str_clean) >= 19:
                            send_dt = datetime.datetime.strptime(date_str_clean[:19], "%Y-%m-%d %H:%M:%S")
                        elif len(date_str_clean) >= 16:
                            send_dt = datetime.datetime.strptime(date_str_clean[:16], "%Y-%m-%d %H:%M")
                        else:
                            send_dt = datetime.datetime.strptime(date_str_clean[:10], "%Y-%m-%d")
                            
                        now_dt = datetime.datetime.now()
                        hours_elapsed = (now_dt - send_dt).total_seconds() / 3600.0
                        
                        if hours_elapsed >= 72.0:
                            status = f"Küldendő (Követő levél - {hours_elapsed:.1f} órája kiküldve)"
                            active_contacts.append(contact)
                        else:
                            status = f"Várólistás ({hours_elapsed:.1f}/72 óra telt el - Kihagyva)"
                            skipped_count += 1
                    except Exception:
                        status = f"Hibás dátum formátum: '{send_date_str}' (Kihagyva)"
                        skipped_count += 1
            elif "follow-up" in status_lower or "followup" in status_lower:
                status = f"Már kapott követőt: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            elif status_lower.startswith("2."):
                status = f"Már 2. fázisban van: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            else:
                status = f"Nem megfelelő státusz: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
                
        print(f"[{i:02d}] {salon_name:<35} | {email:<35} | {status}")
        
    print("-" * 75)
    print(f"Összesen: {len(contacts)} cím | Ebből kihagyva: {skipped_count} | Küldendő: {len(active_contacts)}")
    print("-" * 75)

    # Interaktív választási menü a küldés módjára
    print("\nHogyan szeretnél továbblépni? (Válassz egy számot):")
    print("1. Teszt e-mail küldése (Kizárólag admexgm@gmail.com-ra, valódi küldéssel)")
    print("2. Valódi kampány indítása (Csak a 'Küldendő' státuszú címekre)")
    print("3. Kilépés")
    
    try:
        choice = input("Opció száma (1-3): ").strip()
    except KeyboardInterrupt:
        print("\nKilépés...")
        return

    if choice == "1":
        print("\n--- TESZT MÓD ---")
        print("Egyetlen teszt e-mailt küldünk a következő címre: admexgm@gmail.com")
        active_contacts = [{
            "salon_name": "Test Thai Massage",
            "email": "admexgm@gmail.com",
            "contact_name": "Test Thai Massage Vezetője"
        }]
        # Kikényszerítjük a küldést teszt módban
        DRY_RUN = False
        skipped_count = 0  # tesztben nincs skippelt cím
    elif choice == "2":
        if not active_contacts:
            print("\nNincs küldendő e-mail cím a listában. A kampány leáll.")
            return
        
        print(f"\nBIZTONSÁGI MEGERŐSÍTÉS: Valóban el akarod küldeni a következőt: {campaign_type.upper()} kampány {len(active_contacts)} címzettnek?")
        print("A folytatáshoz írd be pontosan azt, hogy: Biztos!")
        try:
            confirm = input("Megerősítés: ").strip()
        except KeyboardInterrupt:
            print("\nKüldés megszakítva.")
            return
            
        if confirm != "Biztos!":
            print("\nKüldés megszakítva (rossz megerősítő szó).")
            return
        print("\nMegerősítve. Indul a küldés...")
    else:
        print("\nKilépés...")
        return

    smtp_session = None
    if not DRY_RUN:
        print("Csatlakozás az SMTP szerverhez...")
        try:
            if SMTP_PORT == 465:
                smtp_session = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            else:
                smtp_session = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                smtp_session.starttls()
            
            smtp_session.login(SMTP_USER, SMTP_PASSWORD)
            print("Sikeres SMTP bejelentkezés.")
        except Exception as e:
            print(f"HIBA az SMTP csatlakozás során: {e}")
            sys.exit(1)

    success_count = 0
    failed_count = 0

    for i, contact in enumerate(active_contacts, 1):
        salon_name = contact["salon_name"]
        email = contact["email"]
        
        personalized_url = generate_personalized_url(salon_name, email)
        
        if DRY_RUN:
            print(f"\n[{i}/{len(active_contacts)}] [DRY-RUN ELŐNÉZET] Címzett: {salon_name} <{email}>")
            print(f"Tárgy: {email_subject}")
            print(f"Személyre szabott gomb linkje: {personalized_url}")
            print("-" * 40)
            preview_body = txt_template.format(
                salon_name=salon_name,
                sender_name=SENDER_NAME,
                personalized_url=personalized_url
            )
            print(preview_body)
            print("=" * 40)
            log_campaign_send(salon_name, email, f"DRY_RUN_PREVIEW_{campaign_type.upper()}", personalized_url)
            success_count += 1
        else:
            print(f"[{i}/{len(active_contacts)}] Küldés: {salon_name} <{email}>...", end="", flush=True)
            success, message = send_email(smtp_session, salon_name, email, personalized_url, html_template, txt_template, email_subject)
            
            if success:
                print(" OK")
                log_status = "SENT" if campaign_type == "initial" else "FOLLOWUP_SENT"
                log_campaign_send(salon_name, email, log_status, message)
                
                # Google Sheet státusz frissítése
                if campaign_type == "initial":
                    sheet_status_val = "1. kiküldve"
                    send_date_val = time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    sheet_status_val = "1.2. follow-up"
                    send_date_val = None
                    
                update_sheet_status(email, sheet_status_val, send_date_val)
                
                success_count += 1
            else:
                print(f" HIBA ({message})")
                log_status = "FAILED" if campaign_type == "initial" else "FOLLOWUP_FAILED"
                log_campaign_send(salon_name, email, log_status, message)
                failed_count += 1

            # Késleltetés a levelek között (kivéve az utolsónál)
            if i < len(active_contacts):
                time.sleep(SEND_DELAY)

    if smtp_session:
        smtp_session.quit()

    print("\n" + "=" * 60)
    print("                      KAMPÁNY ÖSSZEGZÉS")
    print("=" * 60)
    print(f"Kihagyott címek (már elküldve/nem releváns): {skipped_count}")
    print(f"Feldolgozott új címek: {len(active_contacts)}")
    print(f"Sikeres: {success_count}")
    print(f"Sikertelen: {failed_count}")
    print(f"Küldési napló frissítve ide: {LOG_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    run_campaign()

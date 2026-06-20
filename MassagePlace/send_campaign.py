import os
import csv
import sys
import time
import smtplib
import urllib.parse
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

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
        csv_url = get_csv_export_url(GOOGLE_SHEETS_URL)
        print(f"Kapcsolatok letöltése Google Sheets-ről: {csv_url} ...")
        try:
            res = requests.get(csv_url, timeout=15)
            res.raise_for_status()
            # A letöltött adatot CSV-ként parse-oljuk
            csv_content = res.content.decode('utf-8')
            reader = csv.DictReader(csv_content.splitlines())
            for row in reader:
                # Oszlopnevek kis/nagybetű függetlenítése és tisztítása
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
                
                if email:
                    contacts.append({
                        "salon_name": salon_name or "Szalon",
                        "email": email,
                        "contact_name": contact_name or salon_name or "Szalon Vezető",
                        "status": sheet_status
                    })
                elif raw_email and not raw_email.startswith("#"):
                    print(f"Figyelmeztetés: Hibás e-mail cím átugorva: '{raw_email}' ({salon_name})")
            print(f"Sikeresen betöltve {len(contacts)} cím Google Sheets-ről.")
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
            # Első megkeresés: Csak akkor küldjük, ha még nincs semmilyen státusza (üres)
            if not status_lower:
                status = "Küldendő (Új megkeresés)"
                active_contacts.append(contact)
            elif "érdeklődik" in status_lower:
                status = f"Már érdeklődik: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            elif "küldött" in status_lower or "sent" in status_lower or "followup" in status_lower:
                status = f"Már kapott levelet: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            else:
                # Bármi egyéb nem-üres státusz esetén is inkább kihagyjuk biztonságból
                status = f"Egyedi státusz: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
        else:
            # Követő levél (followup): Csak akkor küldjük, ha a státusz pontosan "1. küldött"
            if status_lower == "1. küldött":
                status = "Küldendő (Követő levél)"
                active_contacts.append(contact)
            elif "érdeklődik" in status_lower:
                status = f"Már érdeklődik: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            elif "followup" in status_lower:
                status = f"Már kapott követőt: '{sheet_status}' (Kihagyva)"
                skipped_count += 1
            elif not status_lower:
                status = "Nincs elküldött első levél (Kihagyva)"
                skipped_count += 1
            else:
                status = f"Egyedi státusz: '{sheet_status}' (Kihagyva)"
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

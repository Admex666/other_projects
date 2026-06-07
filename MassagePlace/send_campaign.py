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

# --- EMAIL TEMPLATES ---
EMAIL_SUBJECT = "Üres időpontok a következő 24 órában"

# 1. Plain Text verzió
EMAIL_BODY_TEMPLATE = """Kedves {salon_name}!

Több szalon foglalási rendszerét áttekintve azt láttam, hogy időnként még az adott napon is maradnak szabad időpontok.

Egy olyan rendszeren dolgozunk, amely olyan szalonoknál mint az Önöké, ezeket az utolsó pillanatban is üresen maradó időpontokat tölti fel last-minute vendégekkel, kizárólag sikerdíjas alapon (nincs semmiféle fix díj vagy előfizetés).

Az eddigi beszélgetések alapján ez havi szinten átlagosan 10-30 üres órát jelenthet, ami részleges feltöltés esetén is már érezhető plusz bevételt adhat.

Ha érdekes lehet a lehetőség, az alábbi linken a kalkulátorunk segítségével megnézheti, mennyi plusz bevételt tudna a rendszerünkkel visszaszerezni, vagy egyszerűen válaszoljon erre az e-mailre.

Megtekintés: {personalized_url}

Ha Ön nem a megfelelő kapcsolattartó ebben a témában, megköszönöm, ha továbbítja ezt az e-mailt az illetékes döntéshozónak.

Amennyiben bármi felmerül, állok rendelkezésükre.

Üdvözlettel,
{sender_name}
ZenSlot Partner Program
"""

# 2. HTML verzió a kattintható gombbal
EMAIL_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #2c3e50;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #fcfcfc;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
            border: 1px solid #eeeeee;
            border-radius: 8px;
        }}
        .greeting {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .content-text {{
            font-size: 15px;
            margin-bottom: 20px;
        }}
        .btn-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .cta-button {{
            display: inline-block;
            background-color: #c3a479;
            color: #ffffff !important;
            text-decoration: none;
            padding: 12px 28px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .signature {{
            margin-top: 30px;
            font-size: 15px;
            border-top: 1px solid #eeeeee;
            padding-top: 15px;
        }}
        .company-name {{
            font-weight: bold;
            color: #c3a479;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <p class="greeting">Kedves {salon_name}!</p>
        
        <p class="content-text">Több szalon foglalási rendszerét áttekintve azt láttam, hogy időnként még az adott napon is maradnak szabad időpontok.</p>
        
        <p class="content-text">Egy olyan rendszeren dolgozunk, amely olyan szalonoknál mint az Önöké, ezeket az utolsó pillanatban is üresen maradó időpontokat tölti fel last-minute vendégekkel, kizárólag sikerdíjas alapon (nincs semmiféle fix díj vagy előfizetés).</p>
        
        <p class="content-text">Az eddigi beszélgetések alapján ez sok szalonnál havi szinten átlagosan 10-30 üres órát jelenthet, ami részleges feltöltés esetén is már érezhető plusz bevételt adhat.</p>
        
        <p class="content-text">Ha Önöket is érinti ez a probléma, az alábbi gombra kattintva a kalkulátorunk segítségével megnézheti, mennyi plusz bevételt tudna a rendszerünkkel visszaszerezni.</p>
        
        <div class="btn-container">
            <a href="{personalized_url}" class="cta-button" target="_blank">Bevételkalkuláció megtekintése</a>
        </div>
        
        <p class="content-text">Amennyiben szeretnének többet megtudni, vagy bármiféle kérdésük van, állok rendelkezésükre.</p>

        <p class="content-text" style="font-size: 13px; color: #7f8c8d; font-style: italic;">Ha Ön nem a megfelelő kapcsolattartó ebben a témában, megköszönöm, ha továbbítja ezt az e-mailt az illetékes döntéshozónak.</p>
        
        <div class="signature">
            Üdvözlettel,<br>
            <strong>{sender_name}</strong><br>
            <span class="company-name">ZenSlot</span>
        </div>
    </div>
</body>
</html>
"""

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

def get_already_sent_emails():
    """Beolvassa a campaign_log.csv-t és kigyűjti a már sikeresen elküldött címeket."""
    sent_emails = set()
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and "email" in reader.fieldnames and "status" in reader.fieldnames:
                    for row in reader:
                        email = row["email"].strip().lower()
                        status = row["status"].strip().upper()
                        # Ha a státusz SENT vagy SUCCESS, akkor elküldöttnek vesszük
                        if status in ("SENT", "SUCCESS", "OK"):
                            sent_emails.add(email)
        except Exception as e:
            print(f"Figyelmeztetés: Nem sikerült beolvasni a korábbi logokat: {e}")
    return sent_emails

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

def send_email(session, salon_name, recipient_email, personalized_url):
    """Elküldi a személyre szabott e-mailt HTML és Plain Text formában is."""
    msg = MIMEMultipart('alternative')
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = recipient_email
    msg['Subject'] = EMAIL_SUBJECT

    # Szövegek generálása
    plain_body = EMAIL_BODY_TEMPLATE.format(
        salon_name=salon_name,
        sender_name=SENDER_NAME,
        personalized_url=personalized_url
    )
    
    html_body = EMAIL_HTML_TEMPLATE.format(
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
                
                if email:
                    contacts.append({
                        "salon_name": salon_name or "Szalon",
                        "email": email,
                        "contact_name": contact_name or salon_name or "Szalon Vezető"
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
                
                if email:
                    contacts.append({
                        "salon_name": salon_name or "Szalon",
                        "email": email,
                        "contact_name": contact_name or salon_name or "Szalon Vezető"
                    })
        print(f"Betöltve {len(contacts)} cím a helyi fájlból.")
        
    return contacts

def run_campaign():
    global DRY_RUN
    check_config()

    # Már elküldött címek betöltése (Deduplikáció)
    already_sent = get_already_sent_emails()

    print("=" * 60)
    print("               ZENSLOT B2B HIDEG E-MAIL KAMPÁNY")
    print("=" * 60)
    print(f"Mód: {'[DRY RUN / TESZT - Nincs valódi küldés]' if DRY_RUN else '[VALÓDI KÜLDÉS]'}")
    print(f"SMTP Szerver: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"Küldő: {SENDER_NAME} <{SENDER_EMAIL}>")
    if GOOGLE_SHEETS_URL:
        print("Forrás: Google Sheets")
    else:
        print(f"Forrás: Helyi CSV ({CONTACTS_FILE})")
    print(f"Korábban már elküldött címek száma: {len(already_sent)}")
    print("-" * 60)

    # Címjegyzék betöltése
    contacts = load_contacts()
    
    # Kapcsolatok és státuszok listázása
    print("\n--- KAPCSOLATOK STÁTUSZA ---")
    active_contacts = []
    skipped_count = 0
    for i, contact in enumerate(contacts, 1):
        salon_name = contact["salon_name"]
        email = contact["email"]
        if email.lower() in already_sent:
            status = "Már elküldve (Kihagyva)"
            skipped_count += 1
        else:
            status = "Küldendő"
            active_contacts.append(contact)
        print(f"[{i:02d}] {salon_name:<35} | {email:<35} | {status}")
    print("-" * 75)
    print(f"Összesen: {len(contacts)} cím | Ebből kihagyva: {skipped_count} | Küldendő: {len(active_contacts)}")
    print("-" * 75)

    # Interaktív választási menü
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
        
        print(f"\nBIZTONSÁGI MEGERŐSÍTÉS: Valóban el akarod küldeni a levelet {len(active_contacts)} címzettnek?")
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
            print(f"Tárgy: {EMAIL_SUBJECT}")
            print(f"Személyre szabott gomb linkje: {personalized_url}")
            print("-" * 40)
            # Előnézet plain text
            preview_body = EMAIL_BODY_TEMPLATE.format(
                salon_name=salon_name,
                sender_name=SENDER_NAME,
                personalized_url=personalized_url
            )
            print(preview_body)
            print("=" * 40)
            log_campaign_send(salon_name, email, "DRY_RUN_PREVIEW", personalized_url)
            success_count += 1
        else:
            print(f"[{i}/{len(active_contacts)}] Küldés: {salon_name} <{email}>...", end="", flush=True)
            success, message = send_email(smtp_session, salon_name, email, personalized_url)
            
            if success:
                print(" OK")
                log_campaign_send(salon_name, email, "SENT", message)
                success_count += 1
            else:
                print(f" HIBA ({message})")
                log_campaign_send(salon_name, email, "FAILED", message)
                failed_count += 1

            # Késleltetés a levelek között (kivéve az utolsónál)
            if i < len(active_contacts):
                time.sleep(SEND_DELAY)

    if smtp_session:
        smtp_session.quit()

    print("\n" + "=" * 60)
    print("                      KAMPÁNY ÖSSZEGZÉS")
    print("=" * 60)
    print(f"Kihagyott címek (már elküldve): {skipped_count}")
    print(f"Feldolgozott új címek: {len(active_contacts)}")
    print(f"Sikeres: {success_count}")
    print(f"Sikertelen: {failed_count}")
    print(f"Küldési napló frissítve ide: {LOG_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    run_campaign()

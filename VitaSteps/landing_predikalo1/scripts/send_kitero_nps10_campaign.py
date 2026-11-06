import os
import sys
import csv
import smtplib
import ssl
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Windows console UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 465
SENDER_EMAIL  = "vitasteps.team@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

CSV_FILE = os.path.join(PROJECT_ROOT, "data", "kitero_nps10_recipients.csv")
HTML_TEMPLATE_FILE = os.path.join(PROJECT_ROOT, "kitero", "email_templates", "medal_buyers.html")
TXT_TEMPLATE_FILE = os.path.join(PROJECT_ROOT, "kitero", "email_templates", "medal_buyers.txt")

EMAIL_SUBJECT = "Emlékszel még a VitaStepsre? Van egy új ötletünk..."

def load_templates():
    if not os.path.exists(HTML_TEMPLATE_FILE):
        print(f"❌ HTML template not found: {HTML_TEMPLATE_FILE}")
        sys.exit(1)
    if not os.path.exists(TXT_TEMPLATE_FILE):
        print(f"❌ TXT template not found: {TXT_TEMPLATE_FILE}")
        sys.exit(1)

    with open(HTML_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    with open(TXT_TEMPLATE_FILE, "r", encoding="utf-8") as f:
        txt = f.read()
    return html, txt

def load_csv_rows():
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file not found: {CSV_FILE}")
        sys.exit(1)

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return rows, fieldnames

def save_csv_rows(rows, fieldnames):
    with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def build_message(to_email: str, first_name: str, cid: str, html_tpl: str, txt_tpl: str):
    name_val = first_name.strip() if first_name else "Kedves Túrázó"
    
    html_body = html_tpl.replace("{{first_name}}", name_val).replace("{{cid}}", cid)
    txt_body = txt_tpl.replace("{{first_name}}", name_val).replace("{{cid}}", cid)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = f"VitaSteps <{SENDER_EMAIL}>"
    msg["To"] = to_email

    msg.attach(MIMEText(txt_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg

def main():
    args = sys.argv[1:]
    is_live = "--live" in args
    is_dry_run = "--dry-run" in args or not is_live
    test_email_arg = None
    for i, a in enumerate(args):
        if a == "--test" and i + 1 < len(args):
            test_email_arg = args[i + 1]

    print("============================================================")
    print(" 🚀 VitaSteps Kitérő – NPS=10 Kampány Kiküldő Script")
    print("============================================================")

    if not SMTP_PASSWORD:
        print("❌ Error: SMTP_PASSWORD is not set in landing_predikalo1/.env")
        sys.exit(1)

    html_tpl, txt_tpl = load_templates()
    rows, fieldnames = load_csv_rows()

    print(f"📋 Betöltött címzettek száma: {len(rows)}")
    print(f"✉️  Feladó: VitaSteps <{SENDER_EMAIL}>")
    print(f"🎯 Tárgy: {EMAIL_SUBJECT}\n")

    # Mode: Single test send
    if test_email_arg:
        print(f"🧪 [TESZT MÓD] Egyetlen próba küldése ide: {test_email_arg}")
        sample = rows[0] if rows else {"first_name": "Teszt Elek", "cid": "c_test_001"}
        msg = build_message(test_email_arg, sample.get("first_name", "Teszt"), sample.get("cid", "test_cid"), html_tpl, txt_tpl)
        
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, test_email_arg, msg.as_string())
        print(f"✅ Teszt email sikeresen elküldve ide: {test_email_arg} (CSV NEM módosult).\n")
        return

    # Check un-sent
    unsent_rows = [r for r in rows if str(r.get("sent", "0")).strip() != "1"]
    already_sent = [r for r in rows if str(r.get("sent", "0")).strip() == "1"]

    print(f"📊 Státusz: {len(already_sent)} már elküldve, {len(unsent_rows)} küldésre vár.")

    if not unsent_rows:
        print("🎉 Minden címzettnek el lett már küldve az e-mail! Nincs teendő.")
        return

    if is_dry_run:
        print("\n🔍 [DRY-RUN MÓD] Csak előnézet, NEM küld e-maileket és NEM írja át a CSV-t.")
        print("   Az alábbi címzetteknek menne ki a levél:\n")
        for idx, r in enumerate(unsent_rows, 1):
            print(f"   {idx:02d}. {r['email']} -> Megszólítás: 'Szia {r['first_name']}!', CID: {r['cid']}")
        print("\n💡 Az éles küldéshez futtasd a scriptet a --live kapcsolóval:")
        print("   python landing_predikalo1/scripts/send_kitero_nps10_campaign.py --live\n")
        return

    # LIVE SENDING
    print("\n🚨 [ÉLES KÜLDÉS INDÍTÁSA] Figyelem! Valós e-mailek kiküldése folyamatban...\n")
    confirm = input("Biztosan elküldöd az e-maileket a fenti címzetteknek? (írj 'igen'-t a megerősítéshez): ")
    if confirm.strip().lower() != "igen":
        print("❌ Megszakítva. Nem történt küldés.")
        return

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        print("🔐 SMTP bejelentkezés sikeres!\n")

        sent_count = 0
        for i, row in enumerate(rows):
            if str(row.get("sent", "0")).strip() == "1":
                print(f"⏩ [SKIP] Már elküldve korábban: {row['email']}")
                continue

            email = row["email"].strip()
            first_name = row.get("first_name", "").strip()
            cid = row.get("cid", "").strip()

            print(f"📤 [{sent_count + 1}/{len(unsent_rows)}] Küldés: {email} ('Szia {first_name}!', CID: {cid})...", end=" ", flush=True)

            try:
                msg = build_message(email, first_name, cid, html_tpl, txt_tpl)
                server.sendmail(SENDER_EMAIL, email, msg.as_string())
                
                # Update row
                row["sent"] = "1"
                row["sent_at"] = datetime.now().isoformat()
                save_csv_rows(rows, fieldnames)
                
                print("✅ SIKERES")
                sent_count += 1
                
                # Respect SMTP rate limits
                time.sleep(1.8)

            except Exception as e:
                print(f"❌ HIBA: {e}")
                print("⚠️  A hiba miatt a script megállt, de az eddig elküldöttek rögzítésre kerültek a CSV-ben.")
                break

    print(f"\n🏁 Befejezve! Sikeresen elküldve: {sent_count} db e-mail.")
    print(f"📁 A frissített státuszok elmentve a CSV-ben: {CSV_FILE}")

if __name__ == "__main__":
    main()

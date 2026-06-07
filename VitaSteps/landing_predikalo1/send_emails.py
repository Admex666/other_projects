import csv
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json
import urllib.request
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Környezeti változók betöltése a script melletti .env fájlból
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# ===== BEÁLLÍTÁSOK =====
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "vitasteps.team@gmail.com"
DRY_RUN = True  # Ha True, nem küld e-mailt, csak lekérdezi és mutatja a listát!

# Az App Password most már a .env fájlból jön
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Új: Tally API beállítások
TALLY_API_KEY = os.getenv("TALLY_API_KEY")
TALLY_FORM_ID = os.getenv("TALLY_FORM_ID")

CSV_FILE_PATH = os.path.join(SCRIPT_DIR, "contacts.csv")

EMAIL_SUBJECT = "🏔️ VitaSteps Prédikálószék Vertical – Gratulálunk a teljesítéshez! (Szállítási adatok)"

def get_html_template(name, email):
    import urllib.parse
    encoded_name = urllib.parse.quote(name)
    encoded_email = urllib.parse.quote(email)
    link = f"https://vitasteps.vercel.app/szallitas.html?name={encoded_name}&email={encoded_email}"
    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VitaSteps Prédikálószék Vertical</title>
    <style>
        body {{ margin: 0; padding: 0; background-color: #0b0f19; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #ffffff; }}
        .wrapper {{ width: 100%; background-color: #0b0f19; padding-bottom: 40px; }}
        .main {{ background-color: #121824; margin: 0 auto; width: 100%; max-width: 600px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(196, 255, 0, 0.15); border-collapse: collapse; }}
        .header {{ padding: 40px 20px; text-align: center; background: linear-gradient(180deg, #161f33 0%, #121824 100%); border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}
        .logo {{ font-size: 24px; font-weight: 900; letter-spacing: 4px; color: #ffffff; margin: 0; }}
        .logo span {{ color: #c4ff00; }}
        .content {{ padding: 40px 30px; }}
        h1 {{ font-size: 22px; font-weight: 700; margin-top: 0; margin-bottom: 20px; color: #ffffff; }}
        h2 {{ font-size: 18px; font-weight: 700; color: #c4ff00; margin-top: 30px; margin-bottom: 10px; }}
        p {{ font-size: 15px; line-height: 1.6; color: #b0bcd0; margin-top: 0; margin-bottom: 15px; }}
        .highlight {{ color: #c4ff00; font-weight: bold; }}
        .info-card {{ background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 20px; margin-bottom: 25px; }}
        .cta-container {{ text-align: center; padding: 25px 0; }}
        .btn {{ background-color: #c4ff00; color: #000000 !important; font-size: 15px; font-weight: bold; text-decoration: none; padding: 14px 30px; border-radius: 8px; display: inline-block; box-shadow: 0 4px 15px rgba(196, 255, 0, 0.3); }}
        .footer {{ padding: 30px 20px; text-align: center; background-color: #0b0f19; }}
        .footer p {{ font-size: 11px; color: #5d6b82; }}
    </style>
</head>
<body>
    <center class="wrapper">
        <table class="main" width="100%">
            <tr>
                <td class="header">
                    <h1 class="logo">VITA<span>STEPS</span></h1>
                </td>
            </tr>
            <tr>
                <td class="content">
                    <h1>Kedves {name}!</h1>
                    
                    <p>Sikeresen feldolgoztuk az igazolásodat! Gratulálunk a <span class="highlight">Prédikálószék Vertical</span> kihívás teljesítéséhez! 🎉</p>
                    
                    <p>Óriási teljesítmény, és nagyon büszkék vagyunk rád, hogy a közösségünk része vagy.</p>
                    
                    <h2>1. 📦 Szállítási adatok megadása (Nagyon Fontos!)</h2>
                    <p>Az érmek kiküldése várhatóan <strong>június 30-tól indul el</strong>.</p>
                    <p>Kérjük, hogy az alábbi gombra kattintva látogass el a szállítási oldalunkra, ahol kiválaszthatod, hogy melyik Foxpost csomagpontra kéred a megérdemelt érmedet!</p>
                    
                    <div class="cta-container">
                        <a href="{link}" class="btn" target="_blank">📦 Szállítási adatok megadása</a>
                    </div>
                    
                    <h2>2. 🚀 Érkezik a saját Felhasználói fiókod és a Ranglista!</h2>
                    <p>Gőzerővel dolgozunk a weboldalunk bővítésén! Hamarosan elindul a saját <strong>Felhasználói fiókod</strong>, ahol nyomon követheted a megszerzett kilométereidet, láthatod a közös <strong>Ranglistát</strong>, és összekötheted a profilodat a túratársaiddal is. A digitális, sorszámozott okleveledet is ezen a felületen fogod tudni letölteni.</p>
                    
                    <div class="info-card" style="border-left: 4px solid #c4ff00;">
                        <p style="margin: 0; font-size: 14px; color: #ffffff;">
                            <strong>💡 Fontos:</strong> Ha egyetlen e-mail címmel több nevezést is vásároltál (tehát a családod vagy a barátaid is veled tartottak), kérjük, hogy a fenti szállítási űrlapon feltétlenül add meg az ő e-mail címeiket is! Így nekik is saját fiókot tudunk létrehozni, hogy jóváírhassuk a kilométereiket.
                        </p>
                    </div>
                    
                    <p>Még egyszer gratulálunk, várjuk a szállítási adataidat, és hamarosan jelentkezünk! Ha bármilyen kérdésed van, csak válaszolj erre az e-mailre.</p>
                    
                    <p style="margin-top: 30px; margin-bottom: 0;">Üdvözlettel,<br><strong>A VitaSteps Csapata</strong></p>
                </td>
            </tr>
            <tr>
                <td class="footer">
                    <p>© 2026 VitaSteps. Minden jog fenntartva.<br>Kérdés esetén írj nekünk: vitasteps.team@gmail.com</p>
                </td>
            </tr>
        </table>
    </center>
</body>
</html>
"""

def fetch_tally_submissions():
    if not TALLY_API_KEY or not TALLY_FORM_ID:
        print("ℹ️ Tally API Key vagy Form ID nincs megadva a .env fájlban. Manuális CSV módban futunk.")
        return []

    print("🔄 Adatok lekérése a Tally rendszeréből...")
    url = f"https://api.tally.so/forms/{TALLY_FORM_ID}/submissions"
    req = urllib.request.Request(
        url, 
        headers={
            "Authorization": f"Bearer {TALLY_API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    
    extracted = []
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        submissions = data.get("submissions", [])
        for sub in submissions:
            responses = sub.get("responses", [])
            name = "Teljesítő"
            email = ""
            for resp in responses:
                q_id = resp.get("questionId")
                ans = resp.get("answer")
                
                if not isinstance(ans, str):
                    continue
                    
                # Q0ar1X = Név, 9lg1B5 = E-mail (ebben a Tally űrlapban)
                if q_id == "9lg1B5":
                    email = ans
                elif q_id == "Q0ar1X":
                    name = ans
                # Fallback az emailre, ha változna az űrlap
                elif "@" in ans and "." in ans and " " not in ans and not email:
                    email = ans
            
            if email:
                extracted.append({"Name": name, "Email": email})
        
        print(f"✅ Sikeresen letöltve {len(extracted)} beküldés a Tally-ből.")
        return extracted
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Hiba a Tally API lekérdezésekor: {e.code} - Ellenőrizd az API kulcsot!")
        return []
    except Exception as e:
        print(f"❌ Hiba a Tally API lekérdezésekor: {e}")
        return []

def send_emails():
    # Biztonságos SSL kapcsolat létrehozása
    context = ssl.create_default_context()
    
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        print("✅ Sikeres SMTP csatlakozás a Gmail-hez!")
    except Exception as e:
        print(f"❌ Hiba az SMTP csatlakozáskor: {e}")
        print("Tipp: Ellenőrizd, hogy az App Password helyes-e és be van-e kapcsolva a kétlépcsős azonosítás!")
        return

    # Tally adatok lekérése
    tally_data = fetch_tally_submissions()

    rows = []
    headers = ["Name", "Email", "Sent"]

    # Fájl beolvasása, ha létezik
    if os.path.exists(CSV_FILE_PATH):
        try:
            with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                file_headers = reader.fieldnames
                if file_headers:
                    headers = file_headers
                    
                if "Sent" not in headers:
                    headers.append("Sent")
                
                for row in reader:
                    if "Sent" not in row:
                        row["Sent"] = ""
                    rows.append(row)
        except Exception as e:
            print(f"❌ Hiba a CSV beolvasásakor: {e}")
    else:
        print("ℹ️ Nem található contacts.csv, létrehozunk egy újat a Tally adatokból.")

    # Csatoljuk a Tally adatokat a létezőkhöz (duplikáció szűréssel)
    existing_emails = [r.get("Email", "").strip().lower() for r in rows]
    
    for new_row in tally_data:
        email_lower = new_row["Email"].strip().lower()
        if email_lower not in existing_emails:
            rows.append({"Name": new_row["Name"], "Email": new_row["Email"], "Sent": ""})
            existing_emails.append(email_lower)

    if not rows:
        print("❌ Hiba: Nincs egyetlen elküldendő adat sem (se Tallyben, se a CSV-ben).")
        server.quit()
        return

    success_count = 0
    skipped_count = 0

    print("-" * 30)
    for row in rows:
        recipient_email = (row.get("Email") or "").strip()
        recipient_name = (row.get("Name") or "").strip()
        sent_status = (row.get("Sent") or "").strip().lower()
        
        if not recipient_email:
            continue
        
        if sent_status == "yes" or sent_status == "igen":
            skipped_count += 1
            continue
        
        print(f"Küldés folyamatban: {recipient_name} ({recipient_email})...")
        
        # Levél összeállítása
        message = MIMEMultipart("alternative")
        message["Subject"] = EMAIL_SUBJECT
        message["From"] = SENDER_EMAIL
        message["To"] = recipient_email
        
        # HTML tartalom generálása
        html_content = get_html_template(recipient_name, recipient_email)
        part = MIMEText(html_content, "html")
        message.attach(part)
        
        # Küldés
        try:
            if DRY_RUN:
                print("➡️ [TESZT MÓD] Szimulált küldés (valós levél nem ment ki).")
            else:
                server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
                print("➡️ Elküldve!")
            row["Sent"] = "Yes"
            success_count += 1
        except Exception as e:
            print(f"❌ Hiba {recipient_email} küldésekor: {e}")

    # Visszaírás a CSV-be (frissített adatok)
    with open(CSV_FILE_PATH, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n🎉 Kész! {success_count} db új e-mail kiküldve. ({skipped_count} db már korábban el lett küldve, kihagyva).")
    server.quit()

if __name__ == "__main__":
    send_emails()

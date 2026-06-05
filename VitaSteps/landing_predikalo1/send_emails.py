import csv
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Környezeti változók betöltése a script melletti .env fájlból
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# ===== BEÁLLÍTÁSOK =====
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "vitasteps.team@gmail.com"

# Az App Password most már a .env fájlból jön (SMTP_PASSWORD=...)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

CSV_FILE_PATH = os.path.join(SCRIPT_DIR, "contacts.csv")  # A Stripe-ból vagy kézzel készített CSV fájl helye

EMAIL_SUBJECT = "🏔️ VitaSteps Prédikálószék Vertical – Gratulálunk a teljesítéshez! (Szállítási adatok)"

def get_html_template(name):
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
                    <p>Kérjük, hogy az alábbi gombra kattintva látogass el a szállítási oldalunkra, ahol kiválaszthatod, hogy melyik Foxpost, Packeta vagy MPL csomagpontra kéred a megérdemelt érmedet!</p>
                    
                    <div class="cta-container">
                        <a href="https://vitasteps.vercel.app/szallitas.html" class="btn" target="_blank">📦 Szállítási adatok megadása</a>
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

    # CSV beolvasása és e-mailek küldése
    try:
        with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            
            # Ellenőrizzük a fejléceket
            headers = reader.fieldnames
            print(f"Beolvasott oszlopok: {headers}")
            
            email_col = None
            name_col = None
            
            # Próbáljuk megtalálni az e-mail és név oszlopokat (Stripe export vagy egyedi)
            for h in headers:
                if "email" in h.lower():
                    email_col = h
                if "name" in h.lower() or "név" in h.lower():
                    name_col = h
            
            if not email_col or not name_col:
                print("❌ Hiba: Nem található 'email' vagy 'name' (név) oszlop a CSV-ben!")
                return
            
            success_count = 0
            for row in reader:
                recipient_email = row[email_col].strip()
                recipient_name = row[name_col].strip()
                
                if not recipient_email:
                    continue
                
                print(f"Küldés folyamatban: {recipient_name} ({recipient_email})...")
                
                # Levél összeállítása
                message = MIMEMultipart("alternative")
                message["Subject"] = EMAIL_SUBJECT
                message["From"] = SENDER_EMAIL
                message["To"] = recipient_email
                
                # HTML tartalom generálása
                html_content = get_html_template(recipient_name)
                part = MIMEText(html_content, "html")
                message.attach(part)
                
                # Küldés
                server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
                print(f"➡️ Elküldve!")
                success_count += 1
                
            print(f"\n🎉 Sikeresen kiküldve {success_count} db e-mail!")
            
    except FileNotFoundError:
        print(f"❌ Hiba: A '{CSV_FILE_PATH}' fájl nem található! Kérlek hozz létre egy '{CSV_FILE_PATH}' fájlt.")
    except Exception as e:
        print(f"❌ Hiba történt a küldés során: {e}")
    finally:
        server.quit()

if __name__ == "__main__":
    send_emails()

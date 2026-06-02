import csv
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# ===== BEÁLLÍTÁSOK =====
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "vitasteps.team@gmail.com"
# Cseréld ki az alábbi App Password-re (Google App-jelszóra):
# Útmutató az App Password megszerzéséhez: https://support.google.com/accounts/answer/185833
# A kétlépcsős azonosításnak bekapcsolva kell lennie a Gmail fiókodon!
SMTP_PASSWORD = "IDE_ILLESZD_AZ_APP_JELSZAVAT" 

CSV_FILE_PATH = "contacts.csv"  # A Stripe-ból vagy kézzel készített CSV fájl helye

EMAIL_SUBJECT = "🏔️ VitaSteps Prédikálószék Vertical – Fontos információk a teljesítésről és szállításról!"

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
                    
                    <p>Hivatalosan is üdvözlünk a <span class="highlight">Prédikálószék Vertical</span> kihívás első szériájában! 🎉</p>
                    
                    <p>A teljesítési időszak már javában tart (egészen <strong>június 30-ig</strong>), és örömmel látjuk, hogy a közösségünk napról napra bővül.</p>
                    
                    <h2>1. 🏅 Az igazolás és az érmek postázása</h2>
                    <p>A túrát bármikor teljesítheted június 30-ig. Az érmek fizikai gyártása és a csomagok kiküldése várhatóan <strong>június 30-tól indul el folyamatosan</strong>.</p>
                    
                    <h2>2. 📦 Szállítási adatok megadása (Nagyon Fontos!)</h2>
                    <p>Kérjük, hogy az alábbi gombra kattintva töltsd ki a hivatalos szállítási űrlapunkat! Itt tudod megadni, hogy melyik Foxpost vagy MPL automatába kéred az érmedet, illetve biztonsági ellenőrzésként (double-check) jelezheted, hány darab érmet vásároltál.</p>
                    
                    <div class="cta-container">
                        <a href="https://vitasteps.vercel.app/teljesites.html" class="btn" target="_blank">🏆 Szállítási adatok és Igazolás megadása</a>
                    </div>
                    
                    <h2>3. 🚀 Érkezik a saját VitaSteps profilod és a Leaderboard!</h2>
                    <p>Gőzerővel dolgozunk a weboldalunk bővítésén! Hamarosan elindul a saját <strong>felhasználói oldalad</strong>, ahol láthatod a megszerzett kilométereidet, lesz egy közös <strong>Leaderboard (ranglista)</strong>, és összekötheted a profilodat a barátaiddal/túratársaiddal is. A digitális, sorszámozott okleveledet is ezen a felületen fogod tudni elérni és letölteni.</p>
                    
                    <div class="info-card" style="border-left: 4px solid #c4ff00;">
                        <p style="margin: 0; font-size: 14px; color: #ffffff;">
                            <strong>💡 Fontos:</strong> Ha egyetlen e-mail címmel több nevezést is vásároltál (pl. a barátaidnak is te fizettél), kérjük, hogy a fenti szállítási űrlapon add meg az ő e-mail címeiket is! Így nekik is saját profilt tudunk létrehozni, és nekik is jóvá tudjuk majd írni a kilométereket.
                        </p>
                    </div>
                    
                    <p>Nagyon jó felkészülést és fantasztikus élményeket kívánunk a hegyen! Ha bármilyen kérdésed vagy észrevételed van, csak válaszolj erre az e-mailre.</p>
                    
                    <p style="margin-top: 30px; margin-bottom: 0;">Baráti üdvözlettel,<br><strong>A VitaSteps Csapata</strong></p>
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

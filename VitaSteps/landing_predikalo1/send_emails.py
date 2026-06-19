import smtplib
import ssl
import os
import json
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import urllib.parse

# Windows konzolon UTF-8 kimenet
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# ===== BEÁLLÍTÁSOK =====
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 465
SENDER_EMAIL  = "vitasteps.team@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
DRY_RUN       = True   # Ha True → csak kilistázza, NEM küld és NEM ír vissza a Sheetbe

# ===== GOOGLE SHEETS BEÁLLÍTÁSOK =====
SHEET_ID        = os.getenv("GOOGLE_SHEET_ID")
SHEET_NAME      = "Nevezések"
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",   # olvasás + írás (visszajelöléshez)
]

# Oszlopindexek (0-alapú) – egyeznek a Nevezések fül fejlécével
COL_NUM           = 0   # #
COL_EMAIL         = 3   # email
COL_NEV           = 4   # név
COL_TELJESITVE    = 11  # teljesítve dátum
COL_HANY_KM       = 12  # hány km?
COL_EMAIL_KULDVE  = 13  # teljesítés email?

# ===== TALLY FORM =====
# A visszajelzős Tally form ID-ja (ahol a Foxpost + kérdések vannak)
TALLY_FORM_ID = "XXXXXXXX"   # ← cseréld ki a valódi ID-ra

EMAIL_SUBJECT = "🏔️ Gratulálunk a teljesítésedhez! + Szállítási adatok"


def get_sheets_service():
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def fetch_rows(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_NAME}!A1:S500"
    ).execute()
    return result.get("values", [])


def write_back(service, row_index, value="Igen"):
    """Visszaírja a 'teljesítés email kiküldve?' cellát (S oszlop, 1-alapú sor)."""
    # row_index: 0-alapú adatsor index (fejléc után), tehát sheet sor = row_index + 2
    sheet_row = row_index + 2
    col_letter = chr(ord('A') + COL_EMAIL_KULDVE)  # S
    cell_range = f"{SHEET_NAME}!{col_letter}{sheet_row}"
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=cell_range,
        valueInputOption="RAW",
        body={"values": [[value]]}
    ).execute()


def get_first_name(full_name: str) -> str:
    """Utolsó szó a névből – magyarnál ez a keresztnév."""
    parts = full_name.strip().split()
    return parts[-1] if parts else full_name


def make_tally_link(name: str, email: str) -> str:
    """Tally form link prefill-el (név + email)."""
    base = f"https://tally.so/r/{TALLY_FORM_ID}"
    params = urllib.parse.urlencode({
        "name": name,
        "email": email,
    })
    return f"{base}?{params}"


def get_html_email(first_name: str, full_name: str, email: str, km: str, date: str) -> str:
    tally_link = make_tally_link(full_name, email)
    km_display = f"{km} km" if km and not km.endswith("km") else km or "?"
    return f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VitaSteps – Teljesítés visszaigazolás</title>
  <style>
    body {{ margin:0; padding:0; background:#0b0f19; font-family:'Helvetica Neue',Arial,sans-serif; color:#fff; }}
    .wrapper {{ width:100%; background:#0b0f19; padding-bottom:40px; }}
    .main {{ background:#121824; margin:0 auto; max-width:600px; border-radius:12px; border:1px solid rgba(196,255,0,0.15); }}
    .header {{ padding:40px 20px; text-align:center; background:linear-gradient(180deg,#161f33 0%,#121824 100%); border-bottom:1px solid rgba(255,255,255,0.05); }}
    .logo {{ font-size:24px; font-weight:900; letter-spacing:4px; margin:0; }}
    .logo span {{ color:#c4ff00; }}
    .content {{ padding:40px 30px; }}
    h1 {{ font-size:22px; margin-top:0; margin-bottom:20px; }}
    h2 {{ font-size:18px; color:#c4ff00; margin-top:30px; margin-bottom:10px; }}
    p {{ font-size:15px; line-height:1.6; color:#b0bcd0; margin:0 0 15px; }}
    .highlight {{ color:#c4ff00; font-weight:bold; }}
    .stat-box {{ background:rgba(196,255,0,0.06); border:1px solid rgba(196,255,0,0.2); border-radius:8px; padding:20px; margin:20px 0; text-align:center; }}
    .stat-km {{ font-size:3rem; font-weight:900; color:#c4ff00; line-height:1; }}
    .stat-label {{ font-size:0.85rem; color:#7a8aa0; text-transform:uppercase; letter-spacing:0.1em; margin-top:4px; }}
    .cta-container {{ text-align:center; padding:25px 0; }}
    .btn {{ background:#c4ff00; color:#000 !important; font-size:15px; font-weight:bold; text-decoration:none; padding:14px 30px; border-radius:8px; display:inline-block; }}
    .divider {{ border:none; border-top:1px solid rgba(255,255,255,0.06); margin:30px 0; }}
    .footer {{ padding:30px 20px; text-align:center; }}
    .footer p {{ font-size:11px; color:#5d6b82; margin:0; }}
  </style>
</head>
<body>
  <center class="wrapper">
    <table class="main" width="100%">
      <tr><td class="header">
        <h1 class="logo">VITA<span>STEPS</span></h1>
      </td></tr>
      <tr><td class="content">
        <h1>Gratulálunk, {first_name}! 🎉</h1>
        <p>Sikeresen teljesítetted a <span class="highlight">Prédikálószék Vertical Kihívást</span> {date}-án/{date}-én!</p>

        <div class="stat-box">
          <div class="stat-km">{km_display}</div>
          <div class="stat-label">Teljesített távolság</div>
        </div>

        <p>Büszkék vagyunk rád, hogy a közösségünk részévé váltál – és a közösségi ranglistánkon is ott vagy! 🏆</p>

        <hr class="divider">

        <h2>📦 1. lépés – Szállítási adatok és visszajelzés</h2>
        <p>Kattints az alábbi gombra, ahol kiválaszthatod a <strong>Foxpost automatádat</strong>, és válaszolhatsz néhány rövid kérdésre a tapasztalataidról. Az egész <strong>kb. 2 percet</strong> vesz igénybe.</p>

        <div class="cta-container">
          <a href="{tally_link}" class="btn" target="_blank">📦 Foxpost kiválasztása + Visszajelzés →</a>
        </div>

        <p style="text-align:center; font-size:0.82rem; color:#5d6b82;">A Foxpost automata és a visszajelzés egyazon felületen érhető el.</p>

        <hr class="divider">

        <h2>📬 2. lépés – Az érem útban van hozzád</h2>
        <p>Amint megkaptuk a szállítási adataidat, elküldjük a <strong>kézzel festett Prédikálószék érmedet</strong> a megadott automatába. A kiszállítás várható ideje: <strong>2026. június 30-tól</strong>.</p>

        <p>Ha bármilyen kérdésed van, csak válaszolj erre az emailre.</p>
        <p style="margin-top:30px;">Üdvözlettel,<br><strong>A VitaSteps Csapata</strong></p>
      </td></tr>
      <tr><td class="footer">
        <p>© 2026 VitaSteps. Minden jog fenntartva.<br>vitasteps.team@gmail.com</p>
      </td></tr>
    </table>
  </center>
</body>
</html>"""


def send_emails():
    print("=" * 50)
    print(f"VitaSteps – Teljesítési email küldő {'[DRY RUN]' if DRY_RUN else '[ÉLES MÓD]'}")
    print("=" * 50)

    service = get_sheets_service()
    rows = fetch_rows(service)

    if not rows or len(rows) < 2:
        print("❌ Üres sheet vagy nem sikerült beolvasni.")
        return

    header = rows[0]
    data_rows = rows[1:]
    print(f"✅ {len(data_rows)} sor beolvasva a Sheetből.")

    # SMTP kapcsolat
    server = None
    # SMTP kapcsolat megnyitása éles módban, vagy DRY_RUN esetén a teszt emailhez (ha van SMTP_PASSWORD)
    if not DRY_RUN or (DRY_RUN and SMTP_PASSWORD):
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            print("✅ SMTP kapcsolat OK.")
        except Exception as e:
            print(f"⚠️ Nem sikerült az SMTP kapcsolat: {e}")
            if not DRY_RUN:
                return

    sent_count = 0
    skipped_count = 0
    eligible_count = 0
    preview_sent = False

    for i, row in enumerate(data_rows):
        # Biztonságos oszlop-kiolvasás
        def col(idx):
            return row[idx].strip() if idx < len(row) else ""

        teljesitve   = col(COL_TELJESITVE)
        email_kuldve = col(COL_EMAIL_KULDVE)
        email        = col(COL_EMAIL)
        nev          = col(COL_NEV)
        hany_km      = col(COL_HANY_KM)

        # Szűrés: teljesítve kell, email még nem ment ki, email cím kell
        if not teljesitve:
            continue   # még nem teljesített
        if email_kuldve.lower() in ("igen", "yes"):
            skipped_count += 1
            continue   # már ki lett küldve

        if not email:
            print(f"  ⚠️  [{i+2}. sor] Nincs email cím – kihagyva.")
            continue

        eligible_count += 1
        first_name = get_first_name(nev) if nev else "Teljesítő"
        print(f"\n  → [{i+2}. sor] {nev} ({email}) | {hany_km} km | teljesítve: {teljesitve}")

        if DRY_RUN:
            if not preview_sent and server:
                test_recipient = "admexgm@gmail.com"
                print(f"     [DRY RUN] Példa email küldése ide: {test_recipient} (adatok: {nev} ({email}))")
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"[TESZT - DRY RUN] {EMAIL_SUBJECT}"
                msg["From"]    = SENDER_EMAIL
                msg["To"]      = test_recipient
                html_body = get_html_email(first_name, nev, email, hany_km, teljesitve)
                msg.attach(MIMEText(html_body, "html"))
                try:
                    server.sendmail(SENDER_EMAIL, test_recipient, msg.as_string())
                    print(f"     ✅ Példa email sikeresen kiküldve a teszt címre!")
                    preview_sent = True
                except Exception as e:
                    print(f"     ❌ Hiba a példa email küldésekor: {e}")
            else:
                print(f"     [DRY RUN] Email NEM kerül kiküldésre (már ment példa vagy nincs kapcsolat).")
            continue

        # Email összeállítása (ÉLES MÓD)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = EMAIL_SUBJECT
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = email
        html_body = get_html_email(first_name, nev, email, hany_km, teljesitve)
        msg.attach(MIMEText(html_body, "html"))

        try:
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
            print(f"     ✅ Elküldve!")
            # Visszaírás a Sheetbe
            write_back(service, i, value="Igen")
            sent_count += 1
        except Exception as e:
            print(f"     ❌ Hiba küldéskor: {e}")

    if server:
        server.quit()

    print("\n" + "=" * 50)
    print(f"Összesítő:")
    print(f"  Teljesítők (emailre vár): {eligible_count}")
    print(f"  Kiküldve:                 {sent_count if not DRY_RUN else 'N/A (DRY RUN)'}")
    print(f"  Kihagyva (már kapott):    {skipped_count}")
    print(f"  Teszt email kiküldve:     {'Igen' if (DRY_RUN and preview_sent) else 'Nem'}")
    print("=" * 50)


if __name__ == "__main__":
    send_emails()

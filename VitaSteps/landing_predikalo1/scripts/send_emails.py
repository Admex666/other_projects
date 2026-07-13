import smtplib
import ssl
import os
import json
import sys
import time
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
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

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

# ===== TALLY FORM =====
# A visszajelzős Tally form ID-ja (ahol a Foxpost + kérdések vannak)
TALLY_FORM_ID = "NpRz5W"   # A .env-ből olvasott alapértelmezett érték

EMAIL_SUBJECT = "🏔️ Gratulálunk a teljesítésedhez! + Szállítási adatok"


def get_sheets_service():
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def fetch_rows(service):
    # Lekérünk elegendő oszlopot (pl. A-tól Z-ig)
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"{SHEET_NAME}!A1:Z500"
    ).execute()
    return result.get("values", [])


def write_back(service, row_index, col_index, value="Igen"):
    """Visszaírja a megadott cellát (1-alapú sor)."""
    # row_index: 0-alapú adatsor index (fejléc után), tehát sheet sor = row_index + 2
    sheet_row = row_index + 2
    col_letter = chr(ord('A') + col_index)
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


def _swap_block(html: str, start_tag: str, end_tag: str, keep: bool) -> str:
    """Ha keep=True: megtartja a blokk tartalmát (kommentek nélkül).
       Ha keep=False: teljesen eltávolítja a blokkot."""
    if start_tag not in html or end_tag not in html:
        return html
    parts = html.split(start_tag)
    before = parts[0]
    inner_and_after = parts[1].split(end_tag)
    inner = inner_and_after[0]
    after = inner_and_after[1]
    return before + (inner if keep else "") + after


def make_shipping_link(name: str, email: str) -> str:
    """Szállítási oldal linkje prefill-el (név + email)."""
    base = "https://vitastepsss.vercel.app/predikalo/szallitas.html"
    params = urllib.parse.urlencode({
        "name": name,
        "email": email,
    })
    return f"{base}?{params}"


def make_completion_link(name: str, email: str) -> str:
    """Teljesítés igazolása Tally form linkje (NpRz5W), prefill-el."""
    base = "https://tally.so/r/NpRz5W"
    params = urllib.parse.urlencode({
        "name": name,
        "email": email,
    })
    return f"{base}?{params}"


def get_html_email(first_name: str, full_name: str, email: str, km: str, date: str, mode: str = "teljesites", has_address: bool = False, address_val: str = "") -> str:
    shipping_link = make_shipping_link(full_name, email)
    completion_link = make_completion_link(full_name, email)
    km_display = f"{km} km" if km and not km.endswith("km") else km or "?"
    
    template_filename = "email_template.html" if mode == "teljesites" else "email_ping_template.html"
    template_path = os.path.join(PROJECT_ROOT, template_filename)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"❌ Nem sikerült betölteni a sablon fájlt ({template_path}): {e}")
        raise e

    # Ha már megadta a szállítási címet, lecseréljük a szállítási blokkot a "nincs teendő" szövegre
    if has_address:
        no_action_html = f"""
          <h2 style="margin-top: 30px;">2️⃣ Szállítási adatok – már rögzítve ✅</h2>
          <p>A szállítási adataidat korábban már megadtad (<strong>{address_val}</strong>), ezzel a lépéssel nincs semmi teendőd.</p>
        """
        # Megkeressük a kommentek közötti részt és lecseréljük
        start_tag = "<!-- STEP_SHIPPING_START -->"
        end_tag = "<!-- STEP_SHIPPING_END -->"
        if start_tag in html and end_tag in html:
            parts = html.split(start_tag)
            before = parts[0]
            after = parts[1].split(end_tag)[1]
            html = before + no_action_html + after

        # 2. lépés szöveg: "már megkaptuk" verzió megtartása, "amint megkapjuk" eltávolítása
        html = _swap_block(html, "<!-- STEP_DELIVERY_HAS_ADDRESS_START -->", "<!-- STEP_DELIVERY_HAS_ADDRESS_END -->", keep=True)
        html = _swap_block(html, "<!-- STEP_DELIVERY_NO_ADDRESS_START -->", "<!-- STEP_DELIVERY_NO_ADDRESS_END -->", keep=False)
    else:
        # Nincs cím: a "már megkaptuk" blokkot eltávolítjuk, az "amint megkapjuk" marad
        html = _swap_block(html, "<!-- STEP_DELIVERY_HAS_ADDRESS_START -->", "<!-- STEP_DELIVERY_HAS_ADDRESS_END -->", keep=False)
        html = _swap_block(html, "<!-- STEP_DELIVERY_NO_ADDRESS_START -->", "<!-- STEP_DELIVERY_NO_ADDRESS_END -->", keep=True)

    html = html.replace("{{FIRST_NAME}}", first_name)
    html = html.replace("{{KM_DISPLAY}}", km_display)
    html = html.replace("{{TALLY_LINK}}", shipping_link)
    html = html.replace("{{COMPLETION_LINK}}", completion_link)
    
    # Ha ping módban vagyunk, és már teljesítette a túrát (van dátum)
    if mode == "ping" and date:
        html = html.replace("A csúcs hódítása folyamatban van ⛰️", "Sikeresen teljesítetted a kihívást! 🎉")
        html = html.replace("Teljesítés vége: 2026. június 30.", f"Teljesítve: {date}")
        html = html.replace(
            "Rendszerünkben jelenleg <strong>nem szerepel sem igazolás a teljesítésedről, sem szállítási cím</strong> a részedről – ezért keresünk meg ezzel a rövid üzenettel.",
            "Rendszerünkben azonban <strong>még nem szerepel szállítási cím</strong> a részedről, ezért nem tudtuk elküldeni az érmedet.",
        )
        html = html.replace(
            "Kérünk, jelezd nekünk, hogy mi a helyzet:",
            "Kérünk, add meg a szállítási adataidat, hogy azonnal postázhassuk az érmedet:",
        )
        
    return html


def send_emails(mode="teljesites"):
    print("=" * 50)
    print(f"VitaSteps – Email küldő ({'Teljesítés visszaigazolás' if mode == 'teljesites' else 'Szállítási adatok bekérése'})")
    print(f"Mód: {'[DRY RUN]' if DRY_RUN else '[ÉLES MÓD]'}")
    print("=" * 50)

    service = get_sheets_service()
    rows = fetch_rows(service)

    if not rows or len(rows) < 2:
        print("❌ Üres sheet vagy nem sikerült beolvasni.")
        return

    # Fejlécek beolvasása és kisbetűs keresés
    raw_header = rows[0]
    header = [h.strip().lower() for h in raw_header]
    data_rows = rows[1:]
    print(f"✅ {len(data_rows)} sor beolvasva a Sheetből.")

    # Dinamikus oszlop indexek (alapértelmezett értékekkel, ha nincs a fejlécben)
    def find_col(name, default):
        for idx, h in enumerate(header):
            if h == name.lower().strip():
                return idx
        return default

    col_email         = find_col("email", 3)
    col_nev           = find_col("név", 4)
    col_megnevezes    = find_col("megnevezés", 5)
    col_teljesitve    = find_col("teljesítve dátum", 12)
    col_hany_km       = find_col("tény táv?", 13)
    col_email_kuldve  = find_col("teljesítés email?", 17)
    col_szallitas_tip = find_col("szállítás típus", 18)
    col_szallitasi_cim = find_col("szállítási cím", 19)
    # Ha a 'ping0713' oszlop nem létezik a sheetben, 99-et adunk vissza
    # col(99) mindig "" lesz (a sor rövidebb), tehát mindenki küldeni kell
    col_ping          = find_col("ping0713", 99)
    col_szeria        = find_col("széria", 1)

    print("🔍 Dinamikus oszlopindexek detektálva:")
    print(f"  - széria:              {col_szeria}")
    print(f"  - email:               {col_email}")
    print(f"  - név:                 {col_nev}")
    print(f"  - megnevezés:          {col_megnevezes}")
    print(f"  - teljesítve dátum:    {col_teljesitve}")
    print(f"  - tény táv?:           {col_hany_km}")
    print(f"  - teljesítés email?:   {col_email_kuldve}")
    print(f"  - szállítás típus:     {col_szallitas_tip}")
    print(f"  - szállítási cím:      {col_szallitasi_cim}")
    print(f"  - ping0713 (visszaír): {col_ping}")

    # SMTP kapcsolat
    server = None
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

    subject_default = EMAIL_SUBJECT if mode == "teljesites" else "🏔️ VitaSteps Prédikálószék – Szállítási adatok megadása"

    for i, row in enumerate(data_rows):
        # Biztonságos oszlop-kiolvasás
        def col(idx):
            return row[idx].strip() if idx < len(row) else ""

        teljesitve      = col(col_teljesitve)
        email_kuldve    = col(col_email_kuldve)
        szallitas_tipus = col(col_szallitas_tip)
        szallitasi_cim  = col(col_szallitasi_cim)
        email           = col(col_email)
        nev             = col(col_nev)
        megnevezes      = col(col_megnevezes)
        hany_km         = col(col_hany_km)
        ping_status     = col(col_ping)
        szeria          = col(col_szeria)

        if not email or not nev:
            continue

        # Kizárólag a Prédikálószék széria indulóit pingeljük meg
        if "prédikálószék" not in szeria.lower() and "predikalo" not in szeria.lower():
            continue

        if mode == "teljesites":
            if not teljesitve:
                continue
            if email_kuldve.lower() in ("igen", "yes"):
                skipped_count += 1
                continue
            subject = subject_default
        else:
            # PING MÓD: csak azokat, akiknél ÜRES a teljesítve dátum ÉS ÜRES a ping0713
            if teljesitve:
                skipped_count += 1
                continue
            if ping_status.lower() in ("igen", "yes"):
                skipped_count += 1
                continue
            subject = "🏔️ VitaSteps Prédikálószék – Kérdés a teljesítésedről"

        eligible_count += 1
        
        # Megnevezés (F oszlop) használata, ha meg van adva, különben keresztnév generálása
        first_name = megnevezes if megnevezes else get_first_name(nev)
        
        print(f"\n  → [{i+2}. sor] {nev} (megszólítás: {first_name}) ({email}) | mód: {mode}")

        has_addr = bool(szallitasi_cim and szallitasi_cim.lower() not in ("", "#n/a", "#name?", "#value!"))

        if DRY_RUN:
            if not preview_sent and server:
                test_recipient = "admexgm@gmail.com"
                print(f"     [DRY RUN] Példa email küldése ide: {test_recipient} (eredeti címzett: {email})")
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"[TESZT - DRY RUN] {subject}"
                msg["From"]    = SENDER_EMAIL
                msg["To"]      = test_recipient
                html_body = get_html_email(first_name, nev, email, hany_km, teljesitve, mode, has_address=has_addr, address_val=szallitasi_cim)
                msg.attach(MIMEText(html_body, "html"))
                try:
                    server.sendmail(SENDER_EMAIL, test_recipient, msg.as_string())
                    print(f"     ✅ Példa email sikeresen kiküldve a teszt címre!")
                    preview_sent = True
                except Exception as e:
                    print(f"     ❌ Hiba a példa email küldésekor: {e}")
            else:
                print(f"     [DRY RUN] Email NEM kerül kiküldésre.")
            continue

        # Email összeállítása (ÉLES MÓD)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = email
        html_body = get_html_email(first_name, nev, email, hany_km, teljesitve, mode, has_address=has_addr, address_val=szallitasi_cim)
        msg.attach(MIMEText(html_body, "html"))

        try:
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
            print(f"     ✅ Elküldve!")
            
            # Visszaírás a Sheetbe a dinamikusan megtalált oszlop indexek alapján
            if mode == "teljesites":
                write_back(service, i, col_email_kuldve, value="Igen")
            else:
                write_back(service, i, col_ping, value="Igen")
                
            sent_count += 1
            
            # Gmail SMTP rate limit (tiltás/spam szűrő) elkerülése miatt várunk egy kicsit
            time.sleep(1.5)
        except Exception as e:
            print(f"     ❌ Hiba küldéskor: {e}")
            time.sleep(1.5)

    if server:
        server.quit()

    print("\n" + "=" * 50)
    print(f"Összesítő ({mode} mód):")
    print(f"  Célcsoport (küldésre vár): {eligible_count}")
    print(f"  Kiküldve:                 {sent_count if not DRY_RUN else 'N/A (DRY RUN)'}")
    print(f"  Kihagyva (már megkapta/nem érintett): {skipped_count}")
    print(f"  Teszt email kiküldve:     {'Igen' if (DRY_RUN and preview_sent) else 'Nem'}")
    print("=" * 50)


if __name__ == "__main__":
    # Használat: python send_emails.py [ping|teljesites]
    # Alapértelmezett: ping (szállítási adatok bekérése a nem teljesítőktől)
    mode = "ping"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("teljesites", "teljesítés"):
            mode = "teljesites"
    send_emails(mode)

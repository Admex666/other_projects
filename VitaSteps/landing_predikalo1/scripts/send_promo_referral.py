import smtplib
import ssl
import os
import sys
import time
import urllib.parse
import urllib.request
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

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
DRY_RUN       = False   # Ha True → csak kilistázza, NEM küld emailt

SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_KEY      = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

CHECKOUT_BASE  = "https://vitastepsss.vercel.app/checkout.html?c=pilis"
PORTAL_BASE    = "https://vitastepsss.vercel.app/portal.html"

EMAIL_SUBJECT = "⛰️ Indul a Nagy-Kevély csillagai – szerezz érmet INGYEN!"

# ===== EMAIL SABLON =====
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "email_promo_referral_template.html")
with open(TEMPLATE_PATH, encoding="utf-8") as f:
    TEMPLATE_HTML = f.read()


# ===== SUPABASE LEKÉRDEZÉS =====

def supabase_get(path: str) -> list:
    """Egyszerű Supabase REST GET hívás."""
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_recipients() -> list[dict]:
    """
    Visszaadja azokat az egyedi (email, name) párokat, ahol
    a Prédikálószék futó csomagja már átvett (shipments.received = true).
    """
    # Supabase PostgREST nested select:
    # shipments?received=eq.true&runs.campaign=eq.predikaloszek&select=runs(name,runners(email,name))
    path = (
        "shipments"
        "?received=eq.true"
        "&select=runs!inner(name,campaign,runners!inner(email,name))"
        "&runs.campaign=eq.predikaloszek"
    )
    rows = supabase_get(path)

    seen = set()
    recipients = []
    for row in rows:
        run = row.get("runs") or {}
        if isinstance(run, list):
            run = run[0] if run else {}
        campaign = run.get("campaign", "")
        if campaign != "predikaloszek":
            continue
        runner = run.get("runners") or {}
        if isinstance(runner, list):
            runner = runner[0] if runner else {}
        email = (runner.get("email") or "").strip().lower()
        name  = run.get("name") or runner.get("name") or "Kalandor"
        if not email or email in seen:
            continue
        seen.add(email)
        recipients.append({"email": email, "name": name})

    return recipients


# ===== EMAIL KÜLDÉS =====

def get_first_name(full_name: str) -> str:
    """Utolsó szó a névből – magyarnál ez a keresztnév."""
    parts = full_name.strip().split()
    return parts[-1] if parts else full_name


def build_html(name: str, email: str) -> str:
    referral_link = f"{CHECKOUT_BASE}&ref={urllib.parse.quote(email)}"
    return (
        TEMPLATE_HTML
        .replace("{{NAME}}", get_first_name(name))
        .replace("{{REFERRAL_LINK}}", referral_link)
        .replace("{{PORTAL_LINK}}", PORTAL_BASE)
    )


def send_email_to(to_email: str, template_name: str, template_email: str) -> bool:
    """Emailt küld to_email-re, de a sablonban template_name/template_email adatai jelennek meg."""
    html_body = build_html(template_name, template_email)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"]    = f"VitaSteps <{SENDER_EMAIL}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"  ❌ Hiba ({to_email}): {e}")
        return False



# ===== MAIN =====

def main():
    print(f"\n=== VitaSteps – Promo Referral Email Script ===")
    print(f"Mode: {'🔍 DRY RUN (nem küld emailt)' if DRY_RUN else '🚀 ÉLES KÜLDÉS'}\n")

    recipients = fetch_recipients()

    print(f"👤 Egyedi emailcímek (received=TRUE, predikaloszek): {len(recipients)}\n")
    print("--- Első 5 címzett (preview) ---")
    for i, r in enumerate(recipients[:5]):
        print(f"  {i+1}. {r['name']} <{r['email']}>")
    print("--------------------------------\n")

    if DRY_RUN:
        TEST_EMAIL = "admexgm@gmail.com"
        sample = recipients[0] if recipients else {"name": "Teszt Elek", "email": TEST_EMAIL}
        print(f"🔍 DRY RUN – teszt email küldése ide: {TEST_EMAIL}")
        print(f"   (sablon adatai: {sample['name']} / {sample['email']})\n")
        ok = send_email_to(TEST_EMAIL, sample["name"], sample["email"])
        print("✅ Teszt email elküldve!" if ok else "❌ Teszt email küldés sikertelen.")
        print("\n    Állítsd át a DRY_RUN = False értékre az éles küldéshez.")
        return


    sent = 0
    failed = 0
    for r in recipients:
        print(f"  Küldés: {r['name']} <{r['email']}>", end=" ... ", flush=True)
        ok = send_email_to(r["email"], r["name"], r["email"])
        if ok:
            print("✅")
            sent += 1
        else:
            failed += 1
        time.sleep(0.4)  # SMTP rate limit elkerülése

    print(f"\n=== Kész ===")
    print(f"✅ Sikeresen elküldve: {sent}")
    if failed:
        print(f"❌ Sikertelen: {failed}")


if __name__ == "__main__":
    main()

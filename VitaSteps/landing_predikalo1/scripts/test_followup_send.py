import os
import urllib.parse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ENV_PATH = r"e:\Data\other_projects\VitaSteps\landing_predikalo1\.env"
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "vitasteps.team@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

recipient = "admexgm@gmail.com"
name = "Adam Dev"
first_name = "Adam"
portal_link = f"https://vitastepsss.vercel.app/portal.html?email={urllib.parse.quote(recipient)}"

print("Preparing to send test follow-up email...")
print(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Sender: {SENDER_EMAIL}")
print(f"Recipient: {recipient}")
print(f"Portal Link: {portal_link}")

# Load template
template_path = "email_feedback_template.html"
if os.path.exists(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
else:
    print(f"Error: {template_path} not found!")
    exit(1)

html = html.replace("{{FIRST_NAME}}", first_name)
html = html.replace("{{TALLY_FEEDBACK_LINK}}", portal_link)

msg = MIMEMultipart("alternative")
msg["Subject"] = "🏔️ Hogy tetszett a kihívás? – Küldd el a visszajelzésed!"
msg["From"] = f"VitaSteps <{SENDER_EMAIL}>"
msg["To"] = recipient

msg.attach(MIMEText(html, "html"))

try:
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, [recipient], msg.as_string())
    print("\n[SUCCESS] Test follow-up email successfully sent to admexgm@gmail.com!")
except Exception as e:
    print(f"\n[ERROR] Failed to send email: {e}")

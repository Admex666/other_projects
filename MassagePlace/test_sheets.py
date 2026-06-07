import os
from dotenv import load_dotenv
from send_campaign import load_contacts, get_csv_export_url

load_dotenv()

GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL")

def test_final_data():
    if not GOOGLE_SHEETS_URL:
        print("HIBA: A GOOGLE_SHEETS_URL nincs beállítva a .env fájlban!")
        return

    csv_url = get_csv_export_url(GOOGLE_SHEETS_URL)
    print(f"Megosztott Google Sheets URL: {GOOGLE_SHEETS_URL}")
    print(f"Export URL: {csv_url}\n")
    
    print("Feldolgozás elindítása a send_campaign.py logikájával...\n")
    contacts = load_contacts()
    
    print("\n--- FELDOLGOZOTT ADATOK ELŐNÉZETE ---")
    print(f"Sikeresen beolvasott címek száma: {len(contacts)}")
    print("-" * 65)
    
    for i, contact in enumerate(contacts, 1):
        print(f"[{i:02d}] Szalon: {contact['salon_name']:<30} | E-mail: {contact['email']:<30} | Kapcsolattartó: {contact['contact_name']}")
        
    print("-" * 65)
    print("Teszt lefutott.")

if __name__ == "__main__":
    test_final_data()

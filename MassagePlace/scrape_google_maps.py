import os
import re
import csv
import sys
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Környezeti változók betöltése a szülő könyvtárból is (mivel ott van a .env)
load_dotenv()
load_dotenv("../.env")

# --- KONFIGURÁCIÓ ---
# Ha a TEST_MODE True, a script csak 1 kerületet néz meg, 2 görgetést végez, és maximum 3 szalont scrape-el le,
# hogy teszteljük az end-to-end működést gyorsan. Állítsd False-ra az éles futtatáshoz!
TEST_MODE = False

# Playwright böngésző beállítások
HEADLESS = True
BROWSER_TIMEOUT = 30000  # 30 mp

# Google Sheets beállítások (a send_campaign.py-ból átvéve)
GOOGLE_SHEETS_URL = os.getenv("GOOGLE_SHEETS_URL")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

# Keresési lekérdezések (Kerületek listája Budapesten)
# Azért bontjuk kerületekre, mert a Google Maps max 120 találatot mutat egyszerre.
DISTRICTS = ["V.", "VI.", "VII.", "VIII.", "IX.", "XIII.", "II.", "XI.", "XII.", "XIV.", "I.", "III.", "IV.", "X.", "XV.", "XVI.", "XVII.", "XVIII.", "XIX.", "XX.", "XXI.", "XXII.", "XXIII."]
DEFAULT_QUERIES = [f"massage Budapest {d} kerület" for d in DISTRICTS]

# Ha teszt mód van, csak 1 lekérdezést használunk
if TEST_MODE:
    ACTIVE_QUERIES = ["massage Budapest VII. kerület"]
    MAX_SCROLLS = 2
    MAX_DETAILS_TO_SCRAPE = 3
else:
    ACTIVE_QUERIES = DEFAULT_QUERIES
    MAX_SCROLLS = 15  # Görgetések száma lekérdezésenként
    MAX_DETAILS_TO_SCRAPE = 999  # Nincs limit élesben

# E-mail Regex
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# --- UTILS & HELPERS ---
def clean_str(s):
    """Megtisztítja a szöveget a konzol kimenet hibáinak elkerülésére."""
    if not s:
        return ""
    # Eltávolítjuk a gyanús Unicode ikonokat, amik a Windows terminált lefagyaszthatják
    return "".join(c for c in s if ord(c) < 65533 and ord(c) not in [0xe5d4, 0xe878])

def is_valid_email(email):
    """Kiszűri a hamis e-mail címeket (pl. képnevek, bootstrap sémák)."""
    email = email.lower().strip()
    bad_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.css', '.js', '.woff', '.ttf']
    if any(email.endswith(ext) for ext in bad_extensions):
        return False
    if '@example.com' in email or '@domain.com' in email or 'yourname@' in email or 'email@' in email:
        return False
    return True

def extract_coords(url):
    """Kinyeri a koordinátákat a Google Maps linkből (szélességi és hosszúsági fok)."""
    lat, lng = "", ""
    if not url:
        return lat, lng
    # Minta: !3d47.354662!4d19.030617
    match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match:
        lat = match.group(1)
        lng = match.group(2)
    else:
        # Alternatív Google Maps URL formátum: @latitude,longitude
        match_alt = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match_alt:
            lat = match_alt.group(1)
            lng = match_alt.group(2)
    return lat, lng

def write_single_to_csv(filepath, s):
    """Azonnal hozzáfűz egy szalont a CSV fájlhoz koordinátákkal együtt."""
    file_exists = os.path.exists(filepath)
    lat, lng = extract_coords(s.get("google_maps_url"))
    with open(filepath, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Név", "Google Maps Link", "Szélességi fok", "Hosszúsági fok", "Weboldal", "Telefon", "Cím", "E-mail", "Összes E-mail"])
        writer.writerow([
            s["name"], 
            s["google_maps_url"], 
            lat, 
            lng, 
            s["website"], 
            s["phone"], 
            s["address"], 
            s["email"], 
            s["emails_all"]
        ])

# --- EMAIL CRAWLER ---
def crawl_emails_from_website(website_url):
    """Megpróbálja letölteni a weboldalt és kiszedni az e-mail címeket."""
    if not website_url or not website_url.startswith("http"):
        return []
        
    print(f"  [*] E-mail keresése a weboldalon: {website_url}...", flush=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Főoldal lekérése
        response = requests.get(website_url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        print(f"  [-] Hiba a főoldal lekérésekor ({website_url}): {e}", flush=True)
        return []
        
    # E-mailek keresése a főoldalon
    found_emails = set(re.findall(EMAIL_REGEX, html))
    valid_emails = {email for email in found_emails if is_valid_email(email)}
    
    if valid_emails:
        print(f"  [+] E-mailek a főoldalon: {valid_emails}", flush=True)
        return list(valid_emails)
        
    # Ha nincs meg az e-mail a főoldalon, keressünk kapcsolat oldalakat
    print("  [*] Nem találtunk e-mailt a főoldalon. Kapcsolat aloldalak keresése...", flush=True)
    try:
        soup = BeautifulSoup(html, 'html.parser')
        contact_links = []
        
        # Kapcsolódó kulcsszavak magyarul és angolul
        keywords = ["kapcsolat", "contact", "impresszum", "about", "rolunk", "contact-us", "info", "bemutatkozas"]
        
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            text = a.get_text().lower().strip()
            
            # Ellenőrizzük, hogy a link szövege vagy az URL tartalmaz-e kapcsolati kulcsszót
            if any(kw in href.lower() or kw in text for kw in keywords):
                # Abszolút URL előállítása
                full_url = urllib.parse.urljoin(website_url, href)
                # Csak azonos domainen belüli linkeket nézünk meg
                if urllib.parse.urlparse(full_url).netloc == urllib.parse.urlparse(website_url).netloc:
                    contact_links.append(full_url)
                    
        contact_links = list(set(contact_links))
        
        if contact_links:
            print(f"  [*] Talált aloldalak: {contact_links[:3]}", flush=True)
            for link in contact_links[:3]:  # max 3 aloldalt vizsgálunk meg
                try:
                    print(f"  [*] Aloldal lekérése: {link}...", flush=True)
                    sub_res = requests.get(link, headers=headers, verify=False, timeout=8)
                    sub_emails = set(re.findall(EMAIL_REGEX, sub_res.text))
                    sub_valid = {email for email in sub_emails if is_valid_email(email)}
                    if sub_valid:
                        print(f"  [+] E-mailek az aloldalon ({link}): {sub_valid}", flush=True)
                        return list(sub_valid)
                except Exception as e:
                    print(f"  [-] Hiba az aloldal lekérésekor ({link}): {e}", flush=True)
    except Exception as e:
        print(f"  [-] Hiba a linkek elemzése közben: {e}", flush=True)
        
    return []

# --- GOOGLE SHEETS APPENDER ---
def get_sheets_client():
    """Létrehozza a hitelesített gspread klienst a Service Account kulccsal."""
    import gspread
    from google.oauth2.service_account import Credentials
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Keresünk service_account.json-t a jelenlegi és szülő mappában is
    creds_file = SERVICE_ACCOUNT_FILE
    if not os.path.exists(creds_file) and os.path.exists(f"../{creds_file}"):
        creds_file = f"../{creds_file}"
        
    if not os.path.exists(creds_file):
        print(f"[-] Google Sheets hitelesítési fájl ('{SERVICE_ACCOUNT_FILE}') nem található. Csak CSV mentés lesz.", flush=True)
        return None
        
    try:
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"[-] Google Sheets hitelesítési hiba: {e}", flush=True)
        return None

def append_to_google_sheet(salons):
    """Hozzáadja a kinyert szalonokat a Google Táblázathoz."""
    if not GOOGLE_SHEETS_URL:
        print("[-] GOOGLE_SHEETS_URL nincs beállítva a .env fájlban. Csak CSV mentés lesz.", flush=True)
        return False
        
    client = get_sheets_client()
    if not client:
        return False
        
    try:
        # Kinyerjük a Spreadsheet ID-t
        sheet_id = None
        if "/d/" in GOOGLE_SHEETS_URL:
            sheet_id = GOOGLE_SHEETS_URL.split("/d/")[1].split("/")[0]
        else:
            sheet_id = GOOGLE_SHEETS_URL
            
        print(f"[+] Google Táblázat megnyitása: {sheet_id}...", flush=True)
        sh = client.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        
        # Oszlopfejlécek beolvasása a helyes pozíciókhoz
        headers = worksheet.row_values(1)
        cleaned_headers = [h.strip().lower() for h in headers]
        print(f"[+] Fejlécek a táblázatban: {headers}", flush=True)
        
        # Oszlop indexek meghatározása (1-alapúak)
        try:
            salon_idx = cleaned_headers.index("szalon neve")
        except ValueError:
            try:
                salon_idx = cleaned_headers.index("salon_name")
            except ValueError:
                salon_idx = 0
                
        try:
            email_idx = cleaned_headers.index("email")
        except ValueError:
            email_idx = 2
            
        try:
            contact_idx = cleaned_headers.index("kapcsolattartó")
        except ValueError:
            contact_idx = 5
            
        try:
            status_idx = cleaned_headers.index("státusz")
        except ValueError:
            try:
                status_idx = cleaned_headers.index("status")
            except ValueError:
                status_idx = 6
                
        try:
            phone_idx = cleaned_headers.index("telefon")
        except ValueError:
            phone_idx = 4
            
        try:
            website_idx = cleaned_headers.index("weboldal")
        except ValueError:
            website_idx = 3
            
        # Már meglévő e-mailek lekérése a duplikáció elkerülésére
        existing_emails = set()
        email_list = worksheet.col_values(email_idx + 1)
        for e in email_list[1:]:
            if e:
                existing_emails.add(e.strip().lower())
                
        print(f"[+] Talált {len(existing_emails)} meglévő e-mail címet a táblázatban.", flush=True)
        
        rows_to_append = []
        for s in salons:
            email = s.get("email", "").strip()
            if not email:
                continue
            if email.lower() in existing_emails:
                print(f"[!] '{s['name']}' ({email}) már szerepel a Google Sheet-ben. Átugrás.", flush=True)
                continue
                
            # Sor létrehozása dinamikusan az indexek alapján
            row_len = max(salon_idx, email_idx, contact_idx, status_idx, phone_idx, website_idx) + 1
            row_data = [""] * row_len
            
            row_data[salon_idx] = s.get("name", "")
            row_data[email_idx] = email
            row_data[contact_idx] = s.get("name", "") + " Vezetője"
            row_data[status_idx] = "0. gyűjtés"
            row_data[phone_idx] = s.get("phone", "")
            row_data[website_idx] = s.get("website", "")
            
            rows_to_append.append(row_data)
            existing_emails.add(email.lower())
            
        if rows_to_append:
            print(f"[+] {len(rows_to_append)} új sor hozzáadása a táblázathoz...", flush=True)
            worksheet.append_rows(rows_to_append)
            print("[+] Google Sheet sikeresen frissítve!", flush=True)
            return True
        else:
            print("[*] Nem volt új egyedi szalon, amit fel lehetne venni a Google Sheet-be.", flush=True)
            return True
            
    except Exception as e:
        print(f"[-] Hiba a Google Sheet írása közben: {e}", flush=True)
        return False

# --- MAIN SCRAPER FLOW ---
def run_scraper():
    print("=" * 70, flush=True)
    print("               ZENSLOT GOOGLE MAPS & EMAIL SCRAPER", flush=True)
    print("=" * 70, flush=True)
    print(f"Mód: {'TESZT (Gyors ellenőrzés)' if TEST_MODE else 'ÉLES KAMPÁNY (Teljes futás)'}", flush=True)
    print(f"Lekérdezések száma: {len(ACTIVE_QUERIES)}", flush=True)
    print(f"Görgetések száma lekérdezésenként: {MAX_SCROLLS}", flush=True)
    print(f"Részletes adatgyűjtési limit: {MAX_DETAILS_TO_SCRAPE}", flush=True)
    print("-" * 70, flush=True)
    
    scraped_salons = []
    csv_file = "scraped_salons.csv"
    
    # Korábbi adatok beolvasása a duplikáció elkerülésére és az átugráshoz
    existing_places = set()
    if os.path.exists(csv_file):
        try:
            with open(csv_file, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    name_idx = 0
                    link_idx = 1
                    addr_idx = 4
                    for idx, h in enumerate(headers):
                        if h == "Név": name_idx = idx
                        elif h == "Google Maps Link": link_idx = idx
                        elif h == "Cím": addr_idx = idx
                    
                    for row in reader:
                        if len(row) > max(name_idx, link_idx, addr_idx):
                            g_link = row[link_idx].strip()
                            name = row[name_idx].strip()
                            addr = row[addr_idx].strip()
                            if g_link:
                                existing_places.add(g_link)
                            if name and addr:
                                existing_places.add(f"{name}||{addr}")
            print(f"[+] Betöltve {len(existing_places)} korábban lementett hely/kulcs a duplikáció kiszűréséhez.", flush=True)
        except Exception as e:
            print(f"[*] Figyelmeztetés: Nem sikerült beolvasni a korábbi CSV-t: {e}. Folytatás tiszta lappal.", flush=True)
            
    with sync_playwright() as p:
        print("[+] Böngésző indítása...", flush=True)
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        try:
            for q_idx, query in enumerate(ACTIVE_QUERIES, 1):
                print(f"\n[{q_idx}/{len(ACTIVE_QUERIES)}] Keresés és görgetés: '{query}'...", flush=True)
                page = context.new_page()
                
                # Keresési link közvetlenül
                search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}/"
                try:
                    page.goto(search_url, timeout=BROWSER_TIMEOUT)
                except Exception as e:
                    print(f"  [-] Nem sikerült betölteni a keresést: {e}", flush=True)
                    page.close()
                    continue
                    
                # Cookie Consent kezelése
                page.wait_for_timeout(2000)
                if "consent.google" in page.url:
                    print("  [*] Süti elfogadási oldal észlelve. Elfogadás gomb keresése...", flush=True)
                    consent_clicked = False
                    for term in ["Az összes elfogadása", "Accept all", "Elfogadom", "Mindent elfogadok"]:
                        try:
                            btn = page.get_by_role("button", name=term, exact=False)
                            if btn.count() > 0:
                                btn.first.click()
                                page.wait_for_timeout(3000)
                                print(f"  [+] Süti elfogadva ({term} gombbal). Új URL: {page.url}", flush=True)
                                consent_clicked = True
                                break
                        except Exception as e:
                            pass
                    
                    if not consent_clicked:
                        try:
                            buttons = page.locator("button").all()
                            for btn in buttons:
                                text = btn.inner_text().strip()
                                if any(t in text.lower() for t in ["elfogad", "accept", "összes"]):
                                    btn.click()
                                    page.wait_for_timeout(3000)
                                    print(f"  [+] Süti elfogadva gomb szövege alapján: '{text}'", flush=True)
                                    consent_clicked = True
                                    break
                        except Exception as e:
                            print(f"  [-] Nem sikerült a süti elfogadás: {e}", flush=True)
                
                # Görgetés és helyek betöltése
                print("  [*] Helyek listájának görgetése...", flush=True)
                feed_locator = page.locator("div[role='feed']")
                
                if feed_locator.count() > 0:
                    feed = feed_locator.first
                    last_count = 0
                    no_change_rounds = 0
                    
                    for scroll in range(MAX_SCROLLS):
                        feed.evaluate("node => node.scrollBy(0, 20000)")
                        page.wait_for_timeout(2000)
                        
                        curr_links = page.locator("a").all()
                        place_count = sum(1 for l in curr_links if l.get_attribute("href") and "/maps/place/" in l.get_attribute("href"))
                        print(f"    Görgetés {scroll+1}/{MAX_SCROLLS}: {place_count} hely észlelve.", flush=True)
                        
                        if place_count == last_count:
                            no_change_rounds += 1
                        else:
                            no_change_rounds = 0
                            
                        last_count = place_count
                        if no_change_rounds >= 3:
                            print("    [!] Elértük a lista végét (nincs új találat).", flush=True)
                            break
                else:
                    print("  [-] Nem található görgethető lista (div[role='feed']). Lehet, hogy kevés a találat.", flush=True)
                    page.wait_for_timeout(3000)
                    
                # Helyek URL-jeinek kinyerése erről a lapról
                all_links = page.locator("a").all()
                query_urls = []
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and "/maps/place/" in href:
                        query_urls.append(href)
                
                print(f"  [+] Keresés befejezve: {len(query_urls)} linket találtunk ezen a lapon.", flush=True)
                page.close()
                
                # AZONNAL feldolgozzuk a találatokat ebből a keresésből/kerületből!
                if query_urls:
                    print(f"  [*] {len(query_urls)} hely részletes feldolgozása ebben a kerületben...", flush=True)
                    
                    # Szűrjük ki azokat az URL-eket, amik már benne vannak a CSV-ben, hogy ne is logoljunk róluk feleslegesen
                    new_urls = [u for u in query_urls if u not in existing_places]
                    skipped_count = len(query_urls) - len(new_urls)
                    if skipped_count > 0:
                        print(f"    [*] Átugrunk {skipped_count} már korábban lementett linket ebben a kerületben.", flush=True)
                        
                    for u_idx, url in enumerate(new_urls, 1):
                        if TEST_MODE and len(scraped_salons) >= MAX_DETAILS_TO_SCRAPE:
                            break
                            
                        print(f"    [{u_idx}/{len(new_urls)}] Részletek letöltése: {url[:60]}...", flush=True)
                        detail_page = context.new_page()
                        
                        try:
                            detail_page.goto(url, timeout=BROWSER_TIMEOUT)
                            detail_page.wait_for_timeout(3500)
                            
                            h1_locator = detail_page.locator("h1")
                            name = ""
                            if h1_locator.count() > 0:
                                name = clean_str(h1_locator.first.inner_text().strip())
                            
                            if not name:
                                print("      [-] Nem sikerült kinyerni a szalon nevét. Átugrás.", flush=True)
                                detail_page.close()
                                continue
                                
                            address = ""
                            addr_btn = detail_page.locator("button[data-item-id='address']")
                            if addr_btn.count() > 0:
                                address = clean_str(addr_btn.first.inner_text().strip()).replace("", "").strip()
                            
                            if not address:
                                addr_els = detail_page.locator("[data-item-id*='address']").all()
                                if addr_els:
                                    address = clean_str(addr_els[0].inner_text().strip()).replace("", "").strip()
                                    
                            # Ellenőrzés: Név + Cím alapján
                            place_key = f"{name}||{address}"
                            if place_key in existing_places:
                                print(f"      [*] '{name}' ezen a címen ('{address}') már szerepel a CSV-ben. Átugrás.", flush=True)
                                detail_page.close()
                                continue
                                
                            print(f"      [+] Név: {name}", flush=True)
                            if address:
                                print(f"      [+] Cím: {address}", flush=True)
                            
                            website = ""
                            auth_link = detail_page.locator("a[data-item-id='authority']")
                            if auth_link.count() > 0:
                                website = auth_link.first.get_attribute("href")
                            
                            if not website:
                                links = detail_page.locator("a").all()
                                for l in links:
                                    href = l.get_attribute("href") or ""
                                    if href and "http" in href and "google.com" not in href and "google.hu" not in href:
                                        website = href
                                        break
                                        
                            if website:
                                print(f"      [+] Weboldal: {website}", flush=True)
                                
                            phone = ""
                            phone_btn = detail_page.locator("button[data-item-id^='phone:tel:']")
                            if phone_btn.count() > 0:
                                item_id = phone_btn.first.get_attribute("data-item-id")
                                phone = item_id.replace("phone:tel:", "").strip()
                            
                            if not phone:
                                tel_links = detail_page.locator("a[href^='tel:']").all()
                                if tel_links:
                                    phone = tel_links[0].get_attribute("href").replace("tel:", "").strip()
                                    
                            if not phone:
                                buttons = detail_page.locator("button").all()
                                for btn in buttons:
                                    aria = btn.get_attribute("aria-label") or ""
                                    text = btn.inner_text().strip()
                                    if "telefonszám" in aria.lower() or "telefon" in aria.lower() or "phone" in aria.lower():
                                        clean_text = clean_str(text)
                                        if re.search(r'\d', clean_text):
                                            phone = clean_text.replace("", "").strip()
                                            break
                                            
                            if phone:
                                print(f"      [+] Telefon: {phone}", flush=True)
                                
                            emails_found = []
                            if website:
                                emails_found = crawl_emails_from_website(website)
                                
                            email = emails_found[0] if emails_found else ""
                            
                            salon_data = {
                                "name": name,
                                "google_maps_url": url,
                                "website": website,
                                "phone": phone,
                                "address": address,
                                "email": email,
                                "emails_all": ", ".join(emails_found)
                            }
                            
                            scraped_salons.append(salon_data)
                            write_single_to_csv(csv_file, salon_data)
                            print(f"      [+] Sikeresen mentve a CSV fájlba.", flush=True)
                            
                            existing_places.add(url)
                            if name and address:
                                existing_places.add(place_key)
                                
                        except Exception as e:
                            print(f"    [-] Hiba történt a(z) '{url[:50]}' hely feldolgozása közben: {e}", flush=True)
                        finally:
                            detail_page.close()
                            
                if TEST_MODE and len(scraped_salons) >= MAX_DETAILS_TO_SCRAPE:
                    print("[*] Teszt mód limit elérve, leállítás.", flush=True)
                    break
                    
        except KeyboardInterrupt:
            print("\n[!] A futás felhasználói megszakítással (Ctrl+C) leállt. Szinkronizálás a mentett adatokkal...", flush=True)
            
        browser.close()
        
    print(f"\n[+] Sikeresen feldolgozva {len(scraped_salons)} új szalon ebben a menetben.", flush=True)
    
    # --- EREDMÉNYEK IRÁSA GOOGLE SHEET-BE ---
    if scraped_salons:
        print("\n[+] Google Sheet frissítése a most gyűjtött adatokkal...", flush=True)
        sheet_success = append_to_google_sheet(scraped_salons)
        if not sheet_success:
            print("[!] Figyelmeztetés: A Google Sheet-be írás sikertelen volt vagy nincs konfigurálva.", flush=True)
            print("    A szalonok adatai viszont biztonságosan elmentésre kerültek a 'scraped_salons.csv' fájlba!", flush=True)
            print("    Ha szinkronizálni szeretnéd a Google Sheet-tel, másold át a 'service_account.json' fájlt a projekt gyökerébe,", flush=True)
            print("    és ellenőrizd a GOOGLE_SHEETS_URL beállítást a .env fájlban!", flush=True)

if __name__ == "__main__":
    run_scraper()

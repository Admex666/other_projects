# 📬 LLM_email

> **Több email fiók napi szintű automatikus figyelése és AI-alapú összefoglalása sürgősség, teendők és határidők szerint.**

A rendszer összegyűjti az új leveleket személyes, munkahelyi, egyetemi és egyéb fiókokból, a **Groq API** segítségével elemzi és strukturálja őket, majd **Pushbullet** értesítésben elküldi az aggregált napi jelentést (kiemelve a határidőket, teendőket és sürgős leveleket).

---

## 🚀 Főbb funkciók

* **Több fiók párhuzamos kezelése:** Tetszőleges számú IMAP fiók konfigurálása (Gmail, Outlook, egyetemi/céges szerverek).
* **AI-alapú intelligens elemzés (Groq API):**
  * Kategóriák: `személyes`, `munka`, `egyetem`, `projekt`, `egyéb`
  * Sürgősség: `kritikus`, `magas`, `közepes`, `alacsony`
  * Teendők (`action items`) felismerése
  * Határidők (`deadlines`) kinyerése
  * Tömör 1-2 mondatos magyar összefoglalók
* **Pushbullet értesítés:** Kompakt napi riport közvetlenül a telefonodra vagy számítógépedre.
* **Idempotencia (SQLite adatbázis):** Nem dolgoz fel és nem foglal össze kétszer egyetlen korábban már látott emailt sem.
* **Biztonság:** A fiókadatok és API tokenek lokálisan maradnak (`.env` és `accounts.yaml` fájlokban).

---

## 🛠️ Telepítés és beállítás

### 1. Virtuális környezet és függőségek
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Környezeti változók (.env)
A `.env` fájlban már be vannak állítva az API kulcsok:
```env
GROQ_API_KEY=gsk_...
PUSHBULLET_ACCESS_TOKEN=o....
```

### 3. Fiókok beállítása (accounts.yaml)
Hozd létre a konfigurációs fájlt a sablonból:
```powershell
python main.py --init-accounts
```
Ezután nyisd meg az `accounts.yaml` fájlt, és töltsd ki a fiókjaid adatait.
Példa Gmail beállításra:
```yaml
accounts:
  # Gmail fiók (IMAP)
  - id: "my_gmail"
    name: "Személyes Gmail"
    category: "személyes"
    provider: "imap"
    imap_server: "imap.gmail.com"
    imap_port: 993
    use_ssl: true
    username: "te.cimed@gmail.com"
    password: "xxxx xxxx xxxx xxxx" # 16 karakteres Google Alkalmazásjelszó
    folder: "INBOX"
    fetch_hours: 24
    enabled: true

  # Munkahelyi / Egyetemi fiók (Microsoft Graph API / Modern Auth)
  - id: "mlsz"
    name: "Munkahelyi Outlook"
    category: "munka"
    provider: "graph"
    username: "te.neved@munkahely.hu"
    fetch_hours: 24
    enabled: true
```

### 4. Egyszeri Microsoft bejelentkezés (ha van Graph fiókod)
A Microsoft 365 / Outlook fiókokhoz nincs szükség jelszó megadására a YAML-ban! Futtasd le ezt a parancsot egyszer:
```powershell
python main.py --login-microsoft mlsz
```
A terminál kiír egy linket (`microsoft.com/devicelogin`) és egy kódot. Nyisd meg a böngészőt, jelentkezz be, és a token automatikusan elmentődik a háttérben. Ezután többet nem kell bejelentkezned!

---

## 🖥️ Használat

### Kapcsolatok és API keretek ellenőrzése
```powershell
python main.py --test-connections
python main.py --check-limits
```
A `--check-limits` valós időben kiírja a Groq API-tól kapott kérés- és token-keretedet, valamint a visszaállási időket (rate limits).

### Push értesítés tesztelése
```powershell
python main.py --send-test-push
```
Kiküld egy teszt üzenetet a Pushbullet eszközödre.

### Száraz futtatás (Dry Run)
```powershell
python main.py --run-daily --dry-run
```
Lekéri az emaileket, lefuttatja az AI elemzést és kiírja a terminálba az összefoglalót anélkül, hogy push üzenetet küldene vagy adatbázisba mentene.

### Éles napi futtatás
```powershell
python main.py --run-daily
```

---

## ⏰ Napi automatizálás (Windows Feladatütemező)

A program napi egyszeri automatikus futtatásához hozhatsz létre egy Windows ütemezett feladatot:
1. Nyisd meg a **Feladatütemezőt** (`Task Scheduler`).
2. Kattints: **Alapfeladat létrehozása** (`Create Basic Task...`).
3. Indítás: **Naponta** (pl. reggel 07:00-kor).
4. Művelet: **Program indítása**.
   * Program: `E:\Data\other_projects\LLM_email\.venv\Scripts\python.exe`
   * Argumentumok: `main.py --run-daily`
   * Indítás helye: `E:\Data\other_projects\LLM_email`

---

## 🧪 Tesztek futtatása
```powershell
pytest -v
```

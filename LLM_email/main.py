import argparse
import sys
from pathlib import Path
import shutil

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.config import get_settings, load_accounts, ACCOUNTS_YAML_PATH, BASE_DIR
from src.analyzer.gemini_analyzer import GeminiEmailAnalyzer
from src.fetchers.imap_fetcher import ImapEmailFetcher
from src.fetchers.graph_fetcher import GraphEmailFetcher
from src.notifier.pushbullet import PushbulletNotifier
from src.orchestrator import EmailOrchestrator


def test_connections() -> None:
    """Kapcsolódási tesztek futtatása a konfigurált szolgáltatásokhoz."""
    settings = get_settings()
    print("=== KAPCSOLÓDÁSI TESZTEK ===")

    # 1. Google Gemini API
    print("\n1. Google Gemini API (AI Studio) ellenőrzése...")
    analyzer = GeminiEmailAnalyzer(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if analyzer.test_connection():
        print(f"   [OK] Gemini API kapcsolat sikeres ({settings.gemini_model})!")
    else:
        print("   [FAIL] Nem sikerült elérni a Gemini API-t. Ellenőrizd a GEMINI_API_KEY változót.")

    # 2. Pushbullet API
    print("\n2. Pushbullet ellenőrzése...")
    notifier = PushbulletNotifier(access_token=settings.pushbullet_access_token)
    if notifier.test_connection():
        print("   [OK] Pushbullet kapcsolat és token sikeres!")
    else:
        print("   [FAIL] Nem sikerült elérni a Pushbulletet. Ellenőrizd a PUSHBULLET_ACCESS_TOKEN változót.")

    # 3. Email fiókok (ha létezik accounts.yaml)
    accounts = load_accounts()
    print(f"\n3. Konfigurált fiókok ellenőrzése ({len(accounts)} aktív fiók található)...")
    if not accounts:
        print("   [INFO] Nincs aktív fiók beállítva az accounts.yaml fájlban (vagy a fájl még nem létezik).")
    else:
        for acc in accounts:
            print(f"   - Fiók tesztelése: {acc.name} ({acc.username})...")
            if acc.provider == "imap":
                fetcher = ImapEmailFetcher(acc)
                if fetcher.test_connection():
                    print(f"     [OK] Sikeres IMAP bejelentkezés: {acc.name}")
                else:
                    print(f"     [FAIL] Sikertelen bejelentkezés: {acc.name}")
            elif acc.provider in ["graph", "microsoft"]:
                fetcher = GraphEmailFetcher(acc)
                if fetcher.test_connection():
                    print(f"     [OK] Sikeres Microsoft Graph bejelentkezés: {acc.name}")
                else:
                    print(f"     [FAIL] Sikertelen Graph bejelentkezés: {acc.name}")
            else:
                print(f"     [WARN] Nem támogatott provider: {acc.provider}")


def login_microsoft(account_id: str) -> None:
    """Interaktív Microsoft Graph bejelentkezés indítása egy fiókhoz."""
    accounts = load_accounts(only_enabled=False)
    matching = [a for a in accounts if a.id == account_id]
    if not matching:
        print(f"[ERROR] Nem található '{account_id}' azonosítójú fiók az accounts.yaml fájlban!")
        return

    account = matching[0]
    if account.provider not in ["graph", "microsoft"]:
        print(f"[WARN] A(z) '{account.name}' fiók provider-e '{account.provider}', nem 'graph'.")

    fetcher = GraphEmailFetcher(account)
    token = fetcher.acquire_token(interactive_fallback=True)
    if token:
        print(f"[OK] A(z) '{account.name}' fiók bejelentkezése és tokenje sikeresen elmentve!")
        fetcher.test_connection()
    else:
        print(f"[FAIL] Nem sikerült a bejelentkezés a(z) '{account.name}' fiókhoz.")


def check_limits() -> None:
    """Lekéri és kiírja az AI konfigurációt és kapcsolatot."""
    settings = get_settings()
    print("=== AI API STÁTUSZ ===")
    print(f"Szolgáltató: Google AI Studio (Gemini)")
    print(f"Modell: {settings.gemini_model}")
    analyzer = GeminiEmailAnalyzer(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if analyzer.test_connection():
        print("Állapot: [OK] Kapcsolat aktív, hívásra kész.")
    else:
        print("Állapot: [FAIL] Nem sikerült kapcsolatot létesíteni.")


def send_test_push() -> None:
    """Teszt push értesítés küldése."""
    settings = get_settings()
    notifier = PushbulletNotifier(access_token=settings.pushbullet_access_token)
    print("Teszt Pushbullet értesítés küldése...")
    success = notifier.send_push(
        title="📬 LLM_email Teszt Értesítés",
        body="A Pushbullet sikeresen be van állítva az LLM_email rendszerhez! 🚀",
    )
    if success:
        print("[OK] A teszt értesítés sikeresen kiküldve az eszközeidre!")
    else:
        print("[FAIL] Nem sikerült elküldeni a teszt üzenetet.")


def init_accounts() -> None:
    """Létrehozza az accounts.yaml konfigurációs fájlt a sablon alapján."""
    example_path = BASE_DIR / "accounts.example.yaml"
    target_path = ACCOUNTS_YAML_PATH

    if target_path.exists():
        print(f"[INFO] A(z) {target_path} fájl már létezik.")
        return

    if not example_path.exists():
        print(f"[ERROR] Nem található a sablon: {example_path}")
        return

    shutil.copyfile(example_path, target_path)
    print(f"[OK] {target_path} sikeresen létrehozva az accounts.example.yaml alapján!")
    print("Nyisd meg és add meg az email fiókjaid elérési adatait!")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM_email - Napi AI email figyelő és összesítő")
    parser.add_argument("--run-daily", action="store_true", help="Napi email figyelési és összefoglalási folyamat futtatása")
    parser.add_argument("--dry-run", action="store_true", help="Teszt futtatás: nem ment az adatbázisba és nem küld push értesítést")
    parser.add_argument("--test-connections", action="store_true", help="Gemini, Pushbullet és fiók kapcsolatok tesztelése")
    parser.add_argument("--check-limits", action="store_true", help="AI modell státusz ellenőrzése")
    parser.add_argument("--send-test-push", action="store_true", help="Teszt értesítés küldése a Pushbullet fiókra")
    parser.add_argument("--init-accounts", action="store_true", help="accounts.yaml létrehozása sablonból")
    parser.add_argument("--login-microsoft", type=str, metavar="ACCOUNT_ID", help="Egyszeri bejelentkezés Microsoft Graph fiókhoz (pl. mlsz vagy corvinus)")

    args = parser.parse_args()

    if args.check_limits:
        check_limits()
        return

    if args.login_microsoft:
        login_microsoft(args.login_microsoft)
        return

    if args.test_connections:
        test_connections()
        return

    if args.send_test_push:
        send_test_push()
        return

    if args.init_accounts:
        init_accounts()
        return

    if args.run_daily:
        settings = get_settings()
        orchestrator = EmailOrchestrator(settings)
        orchestrator.run_daily_workflow(dry_run=args.dry_run)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

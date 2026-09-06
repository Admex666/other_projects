from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup
import msal
import requests

from src.config import DATA_DIR
from src.fetchers.base import BaseEmailFetcher
from src.models import RawEmail, AccountConfig

TOKENS_DIR = DATA_DIR / "tokens"
TOKENS_DIR.mkdir(parents=True, exist_ok=True)

# Default public client ID for Microsoft Graph (Office CLI / Public App)
DEFAULT_CLIENT_ID = "d3590ed6-52b3-4102-aeff-aad2292ab01c"
GRAPH_SCOPES = ["Mail.Read", "User.Read"]


class GraphEmailFetcher(BaseEmailFetcher):
    """Microsoft Graph API (OAuth 2.0 / Modern Auth) alapú email begyűjtő."""

    def __init__(self, account: AccountConfig):
        super().__init__(account)
        self.client_id = account.client_id or DEFAULT_CLIENT_ID
        self.tenant_id = account.tenant_id or "organizations"
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.cache_file = TOKENS_DIR / f"{self.account.id}_token_cache.bin"
        self.cache = msal.SerializableTokenCache()
        self._load_cache()
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache,
        )

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                self.cache.deserialize(self.cache_file.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[WARN] Nem sikerült betölteni a token cache-t ({self.account.name}): {e}")

    def _save_cache(self) -> None:
        if self.cache.has_state_changed:
            try:
                self.cache_file.write_text(self.cache.serialize(), encoding="utf-8")
            except Exception as e:
                print(f"[WARN] Nem sikerült menteni a token cache-t ({self.account.name}): {e}")

    def acquire_token(self, interactive_fallback: bool = True) -> Optional[str]:
        """Megszerzi a Graph API access tokent cache-ből, vagy Device Flow-val bejelentkeztet."""
        accounts = self.app.get_accounts(username=self.account.username)
        account = accounts[0] if accounts else None

        # 1. Csendes (silent) lekérés meglévő refresh tokenből
        result = self.app.acquire_token_silent(GRAPH_SCOPES, account=account)
        if result and "access_token" in result:
            self._save_cache()
            return result["access_token"]

        if not interactive_fallback:
            return None

        # 2. Ha nincs érvényes token, Device Code Flow indítása
        print(f"\n[MS LOGIN] Microsoft bejelentkezés szükséges a(z) '{self.account.name}' fiókhoz...")
        flow = self.app.initiate_device_flow(scopes=GRAPH_SCOPES)
        if "user_code" not in flow:
            print(f"[ERROR] Nem sikerült elindítani a Device Flow-t: {flow.get('error_description')}")
            return None

        print("=" * 60)
        print(f"👉 Nyisd meg a böngészőt: {flow['verification_uri']}")
        print(f"👉 Add meg ezt a kódot:   {flow['user_code']}")
        print(f"👉 Jelentkezz be ezzel a címmel: {self.account.username}")
        print("=" * 60)
        print("Várakozás a bejelentkezésre a böngészőben...\n")

        result = self.app.acquire_token_by_device_flow(flow)
        if result and "access_token" in result:
            self._save_cache()
            print(f"[OK] Sikeres Microsoft bejelentkezés ({self.account.name})! Token mentve.")
            return result["access_token"]
        else:
            error_desc = result.get("error_description", result.get("error", "Ismeretlen hiba"))
            print(f"[ERROR] Sikertelen Microsoft bejelentkezés: {error_desc}")
            return None

    def test_connection(self) -> bool:
        """Ellenőrzi a Microsoft Graph API kapcsolatot és tokent."""
        token = self.acquire_token(interactive_fallback=False)
        if not token:
            print(f"     [INFO] Még nincs érvényes token. Futtasd: python main.py --login-microsoft {self.account.id}")
            return False

        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers, timeout=10)
            if resp.status_code == 200:
                user_data = resp.json()
                display_name = user_data.get("displayName") or user_data.get("mail")
                print(f"     [OK] Graph API azonosítva: {display_name} ({self.account.username})")
                return True
            else:
                print(f"     [FAIL] Graph API válasz hiba: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"     [ERROR] Graph API hiba ({self.account.name}): {e}")
            return False

    def fetch_recent_emails(self, hours: Optional[int] = None) -> List[RawEmail]:
        """Lekéri az elmúlt X órában érkezett leveleket a Microsoft Graph API-n keresztül."""
        token = self.acquire_token(interactive_fallback=False)
        if not token:
            print(f"[ERROR] Nincs érvényes token a(z) '{self.account.name}' fiókhoz. Futtasd: python main.py --login-microsoft {self.account.id}")
            return []

        fetch_hours = hours or self.account.fetch_hours or 24
        since_date = datetime.now(timezone.utc) - timedelta(hours=fetch_hours)
        since_iso = since_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
        params = {
            "$filter": f"receivedDateTime ge {since_iso}",
            "$select": "id,internetMessageId,subject,from,toRecipients,receivedDateTime,body",
            "$top": "50",
            "$orderby": "receivedDateTime desc",
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Prefer": 'outlook.body-content-type="text"',
        }

        emails: List[RawEmail] = []
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code != 200:
                print(f"[ERROR] Hiba a levelek lekérésekor a Graph API-ból: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            messages = data.get("value", [])

            for msg in messages:
                subject = msg.get("subject") or "(Nincs tárgy)"
                from_data = msg.get("from", {}).get("emailAddress", {})
                sender = f"{from_data.get('name', '')} <{from_data.get('address', '')}>".strip()
                to_list = [r.get("emailAddress", {}).get("address", "") for r in msg.get("toRecipients", [])]
                recipient = ", ".join(filter(None, to_list))

                recv_str = msg.get("receivedDateTime")
                try:
                    msg_date = datetime.fromisoformat(recv_str.replace("Z", "+00:00"))
                except Exception:
                    msg_date = datetime.now(timezone.utc)

                # Message-ID
                msg_id = msg.get("internetMessageId")
                if not msg_id:
                    hash_src = f"{self.account.id}_{sender}_{subject}_{msg_date.isoformat()}"
                    msg_id = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()

                raw_body = msg.get("body", {}).get("content", "")
                if msg.get("body", {}).get("contentType") == "html" or "<html" in raw_body.lower():
                    soup = BeautifulSoup(raw_body, "html.parser")
                    for s in soup(["script", "style"]):
                        s.decompose()
                    clean_text = soup.get_text(separator="\n")
                else:
                    clean_text = raw_body

                lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
                body_text = "\n".join(lines)[:5000]

                emails.append(
                    RawEmail(
                        message_id=msg_id.strip(),
                        account_id=self.account.id,
                        account_name=self.account.name,
                        default_category=self.account.category,
                        sender=sender,
                        recipient=recipient,
                        subject=subject,
                        date=msg_date,
                        body_text=body_text,
                    )
                )
        except Exception as e:
            print(f"[ERROR] Graph API lekérési hiba ({self.account.name}): {e}")

        return emails

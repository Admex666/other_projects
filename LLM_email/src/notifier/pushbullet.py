import requests
from typing import Optional


class PushbulletNotifier:
    """Pushbullet API értesítésküldő."""

    API_BASE = "https://api.pushbullet.com/v2"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def _headers(self) -> dict:
        return {
            "Access-Token": self.access_token,
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        """Ellenőrzi a Pushbullet tokent a felhasználói profil lekérdezésével."""
        if not self.access_token:
            print("[ERROR] Nincs megadva PUSHBULLET_ACCESS_TOKEN.")
            return False

        try:
            resp = requests.get(f"{self.API_BASE}/users/me", headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                user_info = resp.json()
                name = user_info.get("name") or user_info.get("email") or "Felhasználó"
                print(f"[INFO] Pushbullet sikeres kapcsolódás: {name}")
                return True
            else:
                print(f"[ERROR] Pushbullet auth hiba: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"[ERROR] Pushbullet kapcsolódási hiba: {e}")
            return False

    def send_push(self, title: str, body: str) -> bool:
        """Push értesítést (note) küld a konfigurált eszközökre."""
        if not self.access_token:
            print("[WARN] Nincs Pushbullet token beállítva, az értesítés elmarad.")
            return False

        payload = {
            "type": "note",
            "title": title,
            "body": body,
        }

        try:
            resp = requests.post(
                f"{self.API_BASE}/pushes",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if resp.status_code in [200, 201]:
                print("[INFO] Pushbullet értesítés sikeresen elküldve.")
                return True
            else:
                print(f"[ERROR] Pushbullet küldési hiba: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"[ERROR] Nem sikerült elküldeni a Pushbullet üzenetet: {e}")
            return False

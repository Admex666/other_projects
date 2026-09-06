import os
from pathlib import Path
from typing import List, Optional
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.models import AccountConfig

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "emails.db"
ACCOUNTS_YAML_PATH = BASE_DIR / "accounts.yaml"


class AppSettings(BaseModel):
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_model: str = Field(default_factory=lambda: os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"))
    pushbullet_access_token: str = Field(default_factory=lambda: os.getenv("PUSHBULLET_ACCESS_TOKEN", ""))
    db_path: Path = DEFAULT_DB_PATH
    accounts_file: Path = ACCOUNTS_YAML_PATH


def load_accounts(accounts_file: Optional[Path] = None, only_enabled: bool = True) -> List[AccountConfig]:
    """Betölti a fiókbeállításokat a megadott vagy alapértelmezett YAML fájlból."""
    filepath = accounts_file or ACCOUNTS_YAML_PATH
    if not filepath.exists():
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            raw_accounts = data.get("accounts", [])
            return [
                AccountConfig(**acc)
                for acc in raw_accounts
                if not only_enabled or acc.get("enabled", True)
            ]
    except Exception as e:
        print(f"[WARN] Nem sikerült betölteni a(z) {filepath} fájlt: {e}")
        return []


def get_settings() -> AppSettings:
    """Visszaadja az alkalmazás beállításait a környezeti változók alapján."""
    return AppSettings()

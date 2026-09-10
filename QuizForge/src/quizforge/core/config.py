"""Globális konfiguráció a QuizForge rendszerhez."""

import os
from pathlib import Path
from pydantic import BaseModel, Field

# Gyökérkönyvtár meghatározása
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# .env betöltése egyszerű, függőségmentes parserrel vagy python-dotenv-vel
def _load_env_file():
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()


class Settings(BaseModel):
    """QuizForge beállítások és elérési utak."""
    PROJECT_ROOT: Path = Field(default=PROJECT_ROOT)
    
    # Adatkönyvtárak
    @property
    def DATA_DIR(self) -> Path:
        d = self.PROJECT_ROOT / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def RAW_DATA_DIR(self) -> Path:
        d = self.DATA_DIR / "raw"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def PARQUET_DATA_DIR(self) -> Path:
        d = self.DATA_DIR / "parquet"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def CACHE_DIR(self) -> Path:
        d = self.DATA_DIR / "cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # DuckDB fájl
    @property
    def DUCKDB_PATH(self) -> Path:
        return self.DATA_DIR / "quizforge.duckdb"

    # Külső API kulcsok
    GROQ_API_KEY: str = Field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    GROQ_MODEL: str = Field(default_factory=lambda: os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b"))
    
    # Hálózati beállítások
    USER_AGENT: str = "QuizForge/0.1.0 (Educational Quiz Intelligence; mailto:info@quizforge.local)"
    REQUEST_TIMEOUT_SECONDS: float = 15.0


settings = Settings()

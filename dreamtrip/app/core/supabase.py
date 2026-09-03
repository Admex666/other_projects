"""
Optivoya — Supabase Client & Connection Manager
Provides unified access to Supabase PostgreSQL & PostgREST API.
"""
import os
from typing import Optional
from dotenv import load_dotenv

from app.core.config import ENV_PATH

load_dotenv(dotenv_path=ENV_PATH, override=True)

_supabase_client = None

def get_supabase_config():
    url = (os.getenv("SUPABASE_URL") or "").strip().strip('"').strip("'")
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip().strip('"').strip("'")
    return url, key

def is_supabase_configured() -> bool:
    url, key = get_supabase_config()
    return bool(url and key and url.startswith("http"))

def get_supabase():
    """Returns a singleton Supabase client instance if configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not is_supabase_configured():
        return None

    try:
        from supabase import create_client, Client
        url, key = get_supabase_config()
        _supabase_client = create_client(url, key)
        print(f"[SUPABASE] Connected successfully to {url}")
        return _supabase_client
    except Exception as e:
        print(f"[SUPABASE ERROR] Failed to initialize Supabase client: {e}")
        return None

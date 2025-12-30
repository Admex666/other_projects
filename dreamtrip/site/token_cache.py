"""
Token kezelő modul környezeti változókkal.
Ez a verzió környezeti változókból tölti be a tokeneket,
így nem kell Chrome-ot indítani production-ben.
"""
import os
from typing import Dict, Optional
from scraper import get_kiwi_tokens


def get_tokens_from_env() -> Optional[Dict[str, str]]:
    """
    Tokenek betöltése környezeti változókból.
    
    Returns:
        Dictionary a tokenekkel, vagy None ha nincsenek beállítva
    """
    umbrella_token = os.getenv('KIWI_UMBRELLA_TOKEN')
    visitor_id = os.getenv('KIWI_VISITOR_ID')
    rand_id = os.getenv('KIWI_RAND_ID')
    
    if all([umbrella_token, visitor_id, rand_id]):
        print("✅ Tokenek betöltve környezeti változókból")
        return {
            'umbrella_token': umbrella_token,
            'visitor_id': visitor_id,
            'rand_id': rand_id
        }
    
    return None


def get_tokens_with_fallback() -> Dict[str, str]:
    """
    Token megszerzése környezeti változókból vagy Selenium-mal.
    
    Először megpróbálja betölteni a környezeti változókból,
    ha nincs, akkor Selenium-mal szerzi be őket.
    
    Returns:
        Dictionary a tokenekkel
    """
    # 1. Próbáljuk meg környezeti változókból
    env_tokens = get_tokens_from_env()
    if env_tokens:
        return env_tokens
    
    # 2. Ha nincs környezeti változó, használjunk Selenium-ot
    print("⚠️ Nincs token környezeti változó, Selenium használata...")
    print("💡 Tipp: Állítsd be a KIWI_* környezeti változókat Railway-en!")
    print()
    
    tokens = get_kiwi_tokens(headless=True)
    
    # ✅ RAILWAY HELPER: Írjuk ki a tokeneket a logokba
    print()
    print("=" * 80)
    print("🔑 TOKENEK MEGSZERZVE - MÁSOLD KI EZEKET A RAILWAY VARIABLES-BE!")
    print("=" * 80)
    print()
    print(f"KIWI_UMBRELLA_TOKEN={tokens.get('umbrella_token', 'NONE')}")
    print(f"KIWI_VISITOR_ID={tokens.get('visitor_id', 'NONE')}")
    print(f"KIWI_RAND_ID={tokens.get('rand_id', 'NONE')}")
    print()
    print("=" * 80)
    print("📋 KÖVETKEZŐ LÉPÉSEK:")
    print("1. Másold ki a fenti 3 sort")
    print("2. Railway Dashboard > Variables > New Variable")
    print("3. Illeszd be őket")
    print("4. A következő deploy-nál már NEM fog Chrome-ot indítani!")
    print("=" * 80)
    print()
    
    return tokens


if __name__ == "__main__":
    print("=== Token Teszt ===\n")
    
    tokens = get_tokens_with_fallback()
    
    print("\nTokenek:")
    for key, value in tokens.items():
        if value:
            print(f"  {key}: {value[:20]}...")
        else:
            print(f"  {key}: None")

#!/usr/bin/env python3
"""
Manuális token kinyerő script - NEM headless módban
Ez megnyitja a böngészőt, hogy lásd mi történik
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import get_kiwi_tokens
import json

if __name__ == "__main__":
    print("=" * 70)
    print("MANUÁLIS TOKEN KINYERÉS - BÖNGÉSZŐ LÁTHATÓ")
    print("=" * 70)
    print()
    print("A böngésző meg fog nyílni. Figyeld meg, mi történik.")
    print("A script 12 másodpercet vár, majd megpróbálja kinyerni a tokeneket.")
    print()
    input("Nyomj ENTER-t a folytatáshoz...")
    print()
    
    try:
        # NEM headless mód - látod a böngészőt
        tokens = get_kiwi_tokens(headless=False)
        
        print()
        print("=" * 70)
        print("EREDMÉNY")
        print("=" * 70)
        print()
        print(json.dumps(tokens, indent=2, ensure_ascii=False))
        print()
        
        if all(tokens.get(key) for key in ['umbrella_token', 'visitor_id', 'rand_id']):
            print("✅ SIKERES!")
            print()
            print("Railway környezeti változók:")
            print("-" * 70)
            print(f"KIWI_UMBRELLA_TOKEN={tokens['umbrella_token']}")
            print(f"KIWI_VISITOR_ID={tokens['visitor_id']}")
            print(f"KIWI_RAND_ID={tokens['rand_id']}")
            print("-" * 70)
        else:
            print("❌ Néhány token hiányzik!")
            print()
            print("🔍 DEBUG INFO:")
            print("A böngésző megnyílt?")
            print("Az oldal betöltődött?")
            print("Láttál GraphQL hívásokat a Network fülön?")
            print()
            print("💡 ALTERNATÍV MEGOLDÁS:")
            print("Nyisd meg manuálisan a Chrome DevTools-t:")
            print("1. Menj: https://www.kiwi.com/hu/search/results/budapest-magyarorszag/barcelona-spanyolorszag/anytime/no-return/")
            print("2. Nyisd meg: F12 > Network fül")
            print("3. Szűrj: 'graphql'")
            print("4. Kattints egy GraphQL kérésre")
            print("5. Request Headers fül")
            print("6. Másold ki:")
            print("   - kw-umbrella-token")
            print("   - kw-skypicker-visitor-uniqid")
            print("   - kw-x-rand-id")
            
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ HIBA")
        print("=" * 70)
        print()
        print(f"Hiba: {e}")
        print()
        import traceback
        traceback.print_exc()

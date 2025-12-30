#!/usr/bin/env python3
"""
Token helper script - Tokenek megszerzése és Railway környezeti változók generálása
"""

import sys
import os

# Biztosítsuk, hogy a script könyvtára az importálási útvonalon legyen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import get_kiwi_tokens

if __name__ == "__main__":
    print("=" * 70)
    print("KIWI.COM TOKEN HELPER - RAILWAY DEPLOYMENT")
    print("=" * 70)
    print()
    print("Ez a script segít a tokenek megszerzésében Railway deployment-hez.")
    print()
    
    try:
        print("🔄 Tokenek megszerzése Selenium-mal...")
        print("⏳ Ez 10-15 másodpercig tarthat...")
        print()
        
        tokens = get_kiwi_tokens(headless=True)
        
        print()
        print("=" * 70)
        print("✅ TOKENEK SIKERESEN MEGSZERZVE")
        print("=" * 70)
        print()
        
        # Ellenőrizzük a tokeneket
        if all(tokens.get(key) for key in ['umbrella_token', 'visitor_id', 'rand_id']):
            print("📋 RAILWAY KÖRNYEZETI VÁLTOZÓK:")
            print("-" * 70)
            print()
            print(f"KIWI_UMBRELLA_TOKEN={tokens['umbrella_token']}")
            print(f"KIWI_VISITOR_ID={tokens['visitor_id']}")
            print(f"KIWI_RAND_ID={tokens['rand_id']}")
            print()
            print("-" * 70)
            print()
            print("📝 KÖVETKEZŐ LÉPÉSEK:")
            print()
            print("1. Másold ki a fenti 3 sort")
            print("2. Menj a Railway Dashboard-ra:")
            print("   https://railway.app/dashboard")
            print("3. Válaszd ki a projektedet")
            print("4. Kattints a 'Variables' fülre")
            print("5. Kattints 'New Variable'-re")
            print("6. Illeszd be a változókat (egy sorban egy változó)")
            print("7. Kattints 'Deploy'-ra")
            print()
            print("✅ Ezután a Railway-en NEM fog Chrome-ot indítani!")
            print("   Memóriahasználat: ~450MB → ~100MB")
            print()
            sys.exit(0)
        else:
            print("⚠️ FIGYELEM: Néhány token hiányzik!")
            print()
            for key in ['umbrella_token', 'visitor_id', 'rand_id']:
                if tokens.get(key):
                    print(f"   ✅ {key}: {tokens[key][:30]}...")
                else:
                    print(f"   ❌ HIÁNYZIK: {key}")
            print()
            print("💡 Lehetséges okok:")
            print("   - A Kiwi.com megváltoztatta az API-t")
            print("   - Hálózati probléma")
            print("   - Chrome verzió inkompatibilitás")
            print()
            print("🔧 Próbáld meg:")
            print("   1. Frissítsd a Chrome-ot")
            print("   2. Futtasd újra a scriptet")
            print("   3. Ha továbbra sem működik, használd a Railway-t")
            print("      headless=False módban és másold ki manuálisan")
            print()
            sys.exit(1)
            
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ HIBA A TOKEN MEGSZERZÉS SORÁN")
        print("=" * 70)
        print()
        print(f"Hiba: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Ellenőrizd, hogy a Chrome telepítve van-e")
        print("   2. Ellenőrizd az internet kapcsolatot")
        print("   3. Próbáld meg headless=False módban:")
        print()
        print("      from scraper import get_kiwi_tokens")
        print("      tokens = get_kiwi_tokens(headless=False)")
        print()
        print("   4. Másold ki manuálisan a tokeneket a böngésző")
        print("      Developer Tools > Network fülről")
        print()
        sys.exit(1)

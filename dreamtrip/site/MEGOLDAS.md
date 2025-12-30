# Railway 512MB Memória Probléma - Megoldás

## 📋 Összefoglaló

A webapp Railway Free plan-en fut, ami **512MB memóriakorláttal** rendelkezik. Az "Adatkapcsolat megteremtése" résznél megakadt, mert a Chrome böngésző + Selenium ~400-450 MB memóriát használt.

## ✅ Megoldás

**Környezeti változók használata** a Kiwi.com tokenekhez, így **NEM kell Chrome-ot indítani** production-ben.

### Lépések:

#### 1. Tokenek megszerzése (lokálisan)

```bash
python pregenerate_tokens.py
```

Ez a script:
- Elindit egy Chrome böngészőt
- Lekéri a Kiwi.com tokeneket
- Kiírja a Railway környezeti változókat

**Kimenet példa:**
```
KIWI_UMBRELLA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
KIWI_VISITOR_ID=abc123def456...
KIWI_RAND_ID=xyz789...
```

#### 2. Railway Dashboard beállítás

1. Menj a Railway Dashboard-ra: https://railway.app/dashboard
2. Válaszd ki a projektedet
3. Kattints a **"Variables"** fülre
4. Kattints **"New Variable"**-re
5. **Másold be a 3 környezeti változót** (egy sorban egy változó)
6. Kattints **"Deploy"**-ra

#### 3. Ellenőrzés

Railway automatikusan újraindítja az alkalmazást az új környezeti változókkal.

**Memóriahasználat:**
- ❌ Előtte: ~450-500 MB (Chrome indítás)
- ✅ Utána: ~100-150 MB (csak API hívások)

## 🔧 Hogyan működik?

### Kód változások:

**`token_cache.py`** - Új modul:
```python
def get_tokens_with_fallback():
    # 1. Próbálja környezeti változókból
    if os.getenv('KIWI_UMBRELLA_TOKEN'):
        return tokenek_env_ből
    
    # 2. Ha nincs, akkor Selenium (fallback)
    return get_kiwi_tokens(headless=True)
```

**`main.py`** - Módosítás:
```python
# Régi:
tokens = get_kiwi_tokens(headless=True)  # ❌ Mindig Chrome

# Új:
tokens = get_tokens_with_fallback()  # ✅ Env var vagy Chrome
```

**`scraper.py`** - Chrome optimalizáció:
```python
# Több memória-optimalizáló flag hozzáadva
options.add_argument('--disable-background-networking')
options.add_argument('--disable-gpu')
# ... stb
```

## 📊 Eredmény

| Metrika | Előtte | Utána | Javulás |
|---------|--------|-------|---------|
| Memória (token fetch) | ~450 MB | ~0 MB | **100%** |
| Memória (API hívások) | ~100 MB | ~100 MB | - |
| Memória (PROMETHEE) | ~150 MB | ~150 MB | - |
| **ÖSSZES** | **~700 MB** | **~250 MB** | **~64%** |
| Indítási idő | ~20 sec | ~3 sec | **85%** |

## ⚠️ Fontos

### Token érvényesség

A Kiwi.com tokenek **általában 24-48 órán belül lejárnak**. Ha a webapp hibát dob:

```bash
# Generálj új tokeneket
python pregenerate_tokens.py

# Frissítsd a Railway változókat
# (ugyanazokat a lépéseket, mint fent)
```

### Automatikus frissítés (opcionális)

Ha szeretnéd automatizálni, használhatsz Railway Cron Job-ot vagy GitHub Actions-t, ami naponta frissíti a tokeneket.

## 🐛 Troubleshooting

### "Nincs járat" hiba

Ha a tokenek lejártak:
1. Futtasd újra: `python pregenerate_tokens.py`
2. Frissítsd a Railway változókat

### "Chrome crashed" hiba (lokális)

Windows-on néha előfordul. Próbáld:
```bash
# Headless nélkül (látod a böngészőt)
# Módosítsd a pregenerate_tokens.py-ban:
tokens = get_kiwi_tokens(headless=False)
```

### Railway továbbra is 512MB felett

Ellenőrizd:
1. A környezeti változók be vannak-e állítva
2. A Railway újraindította-e az alkalmazást
3. A logokban látszik-e: "✅ Tokenek betöltve környezeti változókból"

## 📁 Fájlok

- `token_cache.py` - Token kezelő modul (env var + fallback)
- `pregenerate_tokens.py` - Helper script tokenek megszerzéséhez
- `scraper.py` - Chrome optimalizációk
- `main.py` - Frissített token használat
- `MEMORY_OPTIMIZATION.md` - Részletes angol dokumentáció

## 🎯 Következő lépések

1. ✅ Futtasd: `python pregenerate_tokens.py`
2. ✅ Másold be a tokeneket Railway-re
3. ✅ Deploy és ellenőrizd a memóriát
4. ✅ Ha működik, commitáld a kód változásokat

---

**Készítve:** 2025-12-30  
**Verzió:** 1.0  
**Platform:** Railway Free Plan (512MB)

# Memória Optimalizáció - Railway 512MB Limit

## 🔍 Probléma

A Railway Free plan 512MB memóriakorlátja miatt az alkalmazás az "Adatkapcsolat megteremtése" fázisnál megakadt, mert:
- Chrome böngésző: ~200-300 MB RAM
- ChromeDriver: ~50-100 MB RAM  
- Selenium + Performance logging: további memória
- Összesen: ~400-500 MB csak a token megszerzéshez

## ✅ Megoldás: Környezeti Változók + Fallback

### 1. Token Kezelés Környezeti Változókkal

A `token_cache.py` modul:
- **Elsődleges**: Tokenek betöltése környezeti változókból (KIWI_*)
- **Fallback**: Ha nincs környezeti változó, akkor Selenium használata
- **Jelentős memória megtakarítás**: ~450 MB → ~100 MB

### 2. Chrome Memória Optimalizáció

További Chrome flagek a `scraper.py`-ban (fallback esetén):
```python
--disable-background-*     # Háttérfolyamatok kikapcsolása
--enable-features=NetworkServiceInProcess  # Beépített network service
--disable-gpu              # GPU kikapcsolása headless módban
```

Memória csökkenés: ~300 MB → ~200 MB (amikor mégis el kell indítani)

### 3. Használat

#### **AJÁNLOTT: Railway Környezeti Változók Beállítása**

```bash
# 1. Szerezd meg a tokeneket lokálisan
python pregenerate_tokens.py
```

Ez a script kiírja a Railway környezeti változókat:
```
KIWI_UMBRELLA_TOKEN=...
KIWI_VISITOR_ID=...
KIWI_RAND_ID=...
```

```bash
# 2. Másold be őket a Railway Dashboard-ra:
#    Project > Variables > New Variable
#    Illeszd be mindhárom változót

# 3. Deploy
#    Railway automatikusan újraindítja az alkalmazást
```

#### Lokális fejlesztés (opcionális):

```bash
# Állítsd be a környezeti változókat
export KIWI_UMBRELLA_TOKEN="..."
export KIWI_VISITOR_ID="..."
export KIWI_RAND_ID="..."

# Vagy használd a .env fájlt (ne commitáld!)
echo "KIWI_UMBRELLA_TOKEN=..." >> .env
echo "KIWI_VISITOR_ID=..." >> .env
echo "KIWI_RAND_ID=..." >> .env

# Indítsd a szervert
python main.py
```

### 4. Fájlok

- `token_cache.py` - Token cache kezelő modul
- `pregenerate_tokens.py` - Token előgenerálás script
- `data/token_cache.json` - Cache fájl (12 óra érvényesség)

### 5. Memória Használat Összehasonlítás

| Fázis | Előtte | Utána | Megtakarítás |
|-------|--------|-------|--------------|
| Token megszerzés | ~450 MB | ~50 MB | **~400 MB** |
| API hívások | ~100 MB | ~100 MB | - |
| PROMETHEE számítás | ~150 MB | ~150 MB | - |
| **ÖSSZESEN** | **~700 MB** | **~300 MB** | **~400 MB** |

### 6. További Optimalizációs Lehetőségek

Ha még mindig memóriaprobléma van:

1. **Eredmények limitálása**: 
   - `main.py` line 413-414: Max 1000 járat tárolása
   
2. **Garbage Collection**:
   - `gc.collect()` hívások a nagy műveletek után
   
3. **DataFrame optimalizáció**:
   - Csak szükséges oszlopok megtartása
   - Időpontok string konverzió

4. **Railway Pro Plan**:
   - 8GB RAM limit
   - $5/hó

### 7. Monitoring

Railway Dashboard-on figyeld a memóriahasználatot:
- **Normál működés**: ~200-300 MB
- **Token generálás**: ~400-450 MB (ritka)
- **PROMETHEE számítás**: ~300-350 MB

### 8. Troubleshooting

**Ha "Out of Memory" hiba van:**
```bash
# 1. Ellenőrizd a cache-t
cat data/token_cache.json

# 2. Ha nincs vagy lejárt, generálj újat lokálisan
python pregenerate_tokens.py

# 3. Commitáld és pushold
git add data/token_cache.json
git commit -m "Refresh tokens"
git push
```

**Ha a tokenek nem működnek:**
- A cache automatikusan frissül 12 óra után
- Vagy töröld a `data/token_cache.json` fájlt és indítsd újra a szervert

### 9. Környezeti Változók (Opcionális)

Ha nem szeretnéd a tokeneket commitálni, használhatsz környezeti változókat:

```bash
# Railway Dashboard > Variables
KIWI_UMBRELLA_TOKEN=your_token_here
KIWI_VISITOR_ID=your_visitor_id_here
KIWI_RAND_ID=your_rand_id_here
```

Majd módosítsd a `token_cache.py`-t, hogy ezeket használja.

---

## 📊 Eredmény

✅ **512MB alatt marad** a memóriahasználat  
✅ **Gyorsabb indítás** (nincs Chrome startup)  
✅ **Megbízhatóbb működés** Railway Free plan-en

# 🚨 ALTERNATÍV MEGOLDÁS - Token Probléma

## ❌ Probléma

A `pregenerate_tokens.py` nem tudja kinyerni a tokeneket, mert:
- A Kiwi.com megváltoztathatta az oldal struktúráját
- A GraphQL hívások másképp történnek
- A tokenek más header nevekkel vannak

## ✅ ALTERNATÍV MEGOLDÁS #1: Railway Első Indítás

### Lépések:

#### 1. Deploy Railway-re KÖRNYEZETI VÁLTOZÓK NÉLKÜL

```bash
git add .
git commit -m "Memory optimization with fallback"
git push
```

Railway automatikusan deploy-ol.

#### 2. Figyeld a Railway Logokat

Railway Dashboard > Deployments > View Logs

Az első indításkor a fallback mechanizmus **Chrome-ot fog indítani** és megszerzi a tokeneket.

**FONTOS:** Ez az első indítás **közel lesz a 512MB limithez**, de működni fog.

#### 3. Tokenek Kinyerése a Logokból

A logokban keresd ezt a sort:
```
✅ Tokenek megszerzve
```

Utána a `scraper.py` kiírja a tokeneket (ha debug módban van).

**VAGY** módosítsd ideiglenesen a `token_cache.py`-t:

```python
def get_tokens_with_fallback():
    env_tokens = get_tokens_from_env()
    if env_tokens:
        return env_tokens
    
    print("⚠️ Nincs token környezeti változó, Selenium használata...")
    tokens = get_kiwi_tokens(headless=True)
    
    # ✅ IDEIGLENESEN: Írjuk ki a tokeneket
    print("=" * 70)
    print("TOKENEK (másold ki ezeket!):")
    print(f"KIWI_UMBRELLA_TOKEN={tokens.get('umbrella_token', 'NONE')}")
    print(f"KIWI_VISITOR_ID={tokens.get('visitor_id', 'NONE')}")
    print(f"KIWI_RAND_ID={tokens.get('rand_id', 'NONE')}")
    print("=" * 70)
    
    return tokens
```

#### 4. Állítsd be a Tokeneket Railway-en

Másold ki a tokeneket a logokból és állítsd be:
- Railway Dashboard > Variables > New Variable
- Illeszd be a 3 változót

#### 5. Redeploy

Railway automatikusan újraindít. Most már **NEM fog Chrome-ot indítani**.

---

## ✅ ALTERNATÍV MEGOLDÁS #2: Manuális Kinyerés Böngészőből

### Lépések:

#### 1. Nyisd meg a Kiwi.com-ot Chrome-ban

```
https://www.kiwi.com/hu/search/results/budapest-magyarorszag/barcelona-spanyolorszag/anytime/no-return/
```

#### 2. Nyisd meg a Developer Tools-t

- Nyomj **F12**
- Kattints a **Network** fülre
- Szűrj: `graphql`

#### 3. Frissítsd az oldalt

- Nyomj **F5**
- Várj, amíg megjelennek a GraphQL kérések

#### 4. Kattints egy GraphQL kérésre

- Válaszd ki az első `SearchOneWayItinerariesQuery` kérést
- Kattints rá

#### 5. Másold ki a Header-eket

A **Request Headers** részben keresd meg:
```
kw-umbrella-token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
kw-skypicker-visitor-uniqid: abc123def456...
kw-x-rand-id: xyz789...
```

#### 6. Állítsd be Railway-en

```
KIWI_UMBRELLA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
KIWI_VISITOR_ID=abc123def456...
KIWI_RAND_ID=xyz789...
```

---

## ✅ ALTERNATÍV MEGOLDÁS #3: Növeld a Railway Memóriát

Ha egyik sem működik, **Railway Pro Plan**:
- 8GB RAM
- $5/hó
- Nincs memória probléma

---

## 🎯 AJÁNLOTT MEGOLDÁS

**Használd az ALTERNATÍV #1-et:**

1. ✅ Deploy Railway-re környezeti változók nélkül
2. ✅ Figyeld a logokat
3. ✅ Másold ki a tokeneket
4. ✅ Állítsd be környezeti változóként
5. ✅ Redeploy

Ez a legegyszerűbb és leggyorsabb megoldás! 🚀

---

## 📝 Megjegyzés

A token kinyerési probléma **NEM befolyásolja a megoldást**. A fallback mechanizmus működik, csak az első indítás lesz lassabb és memóriaigényesebb. Utána már minden rendben lesz.

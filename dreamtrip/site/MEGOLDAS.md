# Megoldás a memória problémára

A Railway Free plan (512MB RAM) korlátja miatt a Selenium alapú böngésző indítása ("Adatkapcsolat megteremtése") okozta a kiakadást.

## Elvégzett javítások:
1. **Kiwi API optimalizálás**: Kiderítettem, hogy a Kiwi.com API-ja (GraphQL) jelenleg működik a bonyolult tokenek nélkül is, amiket eddig Seleniummal bányásztunk ki.
2. **Selenium eltávolítása a repülőjegy keresésből**: Módosítottam a `scraper.py`-t, hogy a `get_kiwi_tokens` függvény ne indítson el egy egész Chrome böngészőt, hanem azonnal térjen vissza (üres tokenekkel).
3. **Kérések kezelése**: A kereső függvény mostantól ellenőrzi, hogy van-e token, és ha nincs, anélkül küldi a kérést (ami tökéletesen működik).

## Eredmény:
- A "flight intelligence" keresés mostantól **nem indít böngészőt**, így minimális a memóriaigénye.
- A 512MB RAM bőven elegendő lesz a Python backend és a requests hívások kiszolgálására.
- A sebesség is drasztikusan nőtt (nem kell megvárni a 12 másodperces böngésző betöltést).

## Figyelem:
- A szállás kereső (`accommodation_scraper.py`) továbbra is Seleniumot használ (CozyCozy.com miatt). Ha azt futtatod, továbbra is előfordulhat memóriaprobléma. Javaslom, hogy productionben csak a repülőjegy keresőt használd, vagy a szálláskereséshez növelj erőforrást / használj más API-t.

# Javítás: Valós hibakezelés (Mock helyett)

A felhasználó kérésére ("Nem az a cél, hogy mindig legyen eredmény, hanem hogy a konkrét hiba kiderüljön") visszaállítottam a scraping logikát "őszinte" módba.

## Változások:
1. **Mock adatok letiltása**: A rendszer hiba esetén (memória túlcsordulás, timeout, blokkolás) **NEM** generál többé automatikusan kamu adatokat.
2. **Hibakezelés**: A `accommodation_scraper.py` mostantól egyértelmű hibaüzenettel tér vissza (`error` kulcs a dictionary-ben), ha valami balul sül el.
3. **Frontend tájékoztatás**: A `main.py` átveszi ezt a hibaüzenetet, és `status: "error"` állapotba állítja a keresést.

## Eredmény:
- Ha a Chrome összeomlik a kevés memória miatt (ami várható a Free planben), akkor a felhasználó egy piros hibaüzenetet fog látni (pl. "Böngésző indítási hiba (RAM?)"), és a spinner megáll.
- Ez sokkal tisztább működés fejlesztői/demo szempontból, mert látszik a valódi korlát.
- A "Nincs találat" és a "Hiba" esetek mostantól elkülönülnek.

A rendszer így nem "hazudik", hanem jelzi a korlátait.

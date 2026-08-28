---
id: op-export-proposal
type: operation
name: Export B2B Client Proposal
status: active

description: Nyomtatható és PDF-be menthető B2B ügyfélajánlat generálása az összeállított utazási tervből.

requires:
  - "[[trip-cart-engine]]"
  - "[[proposal-generation]]"

code:
  - static/js/trip_cart.js

related:
  - "[[numbeo-cost-model]]"
---

# Operation: Export B2B Client Proposal

## Lépések

1. Nyisd meg a lebegő Utazási Terv fiókot a képernyő alján lévő **„Terv megnyitása”** gombbal (vagy a lebegő ikonra kattintva).
2. Ellenőrizd a kiválasztott elemeket: Célállomás, Járat, Szállás és a tételes Numbeo költségtáblázatot.
3. Kattints a **„📄 Ügyfélajánlat készítése (Nyomtatás / PDF)”** gombra.
4. Az újonnan megnyíló lapon a böngésző natív nyomtatási párbeszédablaka jelenik meg, ahol a **„Mentés PDF-ként”** opcióval azonnal letölthető az ügyfélkész ajánlat.

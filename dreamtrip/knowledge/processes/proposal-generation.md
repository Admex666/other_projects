---
id: proposal-generation
type: process
name: B2B Client Proposal Generation
status: active

description: A teljes összeállított utazási tervből hivatalos, nyomtatható és PDF-be menthető B2B ügyfélajánlat készítése tételes matematikai költségbontással.

source:
  type: code
  ref: static.js.trip_cart.TripEngine.exportProposal

code:
  - static/js/trip_cart.js

related:
  - "[[trip]]"
  - "[[numbeo-cost-model]]"
  - "[[trip-cart-engine]]"

used_by:
  - "[[unified-trip-model]]"
---

# Process: B2B Client Proposal Generation

A B2B tanácsadó vagy felhasználó a lebegő fiókban található „Ügyfélajánlat készítése (Nyomtatás / PDF)” gombra kattintva egy önálló, professzionális ajánlati dokumentumot kap:

```text
1. Összesített fejléc (Optivoya logó, egyedi trip_id, dátum)
2. Célállomás kártya (város, ország, éghajlat, indoklás)
3. Repülőjegy kártya (légitársaság, oda- és visszaindulás, retúr összeg)
4. Szállás kártya (hotel neve, csillagok, értékelés, éjszakák száma)
5. Tételes Matematikai Költségkalkuláció táblázat (Numbeo képletekkel)
6. Végösszeg kiemelés (Teljes becsült összeg és Egy főre jutó költség)
```

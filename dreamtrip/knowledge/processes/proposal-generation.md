---
id: proposal-generation
type: process
name: B2B Client Proposal Generation
status: active

description: A teljes összeállított utazási tervből hivatalos, nyomtatható és PDF-be menthető B2B ügyfélajánlat készítése Unified TripScore-ral, élményilleszkedéssel, napi útitervvel és tételes költségbontással.

source:
  type: code
  ref: static.js.trip.trip_report.TripReport.exportProposal

code:
  - static/js/trip/trip_report.js
  - static/js/trip_cart.js

related:
  - "[[trip]]"
  - "[[numbeo-cost-model]]"
  - "[[trip-cart-engine]]"
  - "[[experience-graph-modeling]]"

used_by:
  - "[[unified-trip-model]]"
---

# Process: B2B Client Proposal Generation

A B2B tanácsadó vagy felhasználó a lebegő fiókban vagy az összegző nézetben található „Ügyfélajánlat készítése (Nyomtatás / PDF)” gombra kattintva egy önálló, professzionális ajánlati dokumentumot kap:

```text
1. Összesített fejléc (Optivoya logó, egyedi trip_id, dátum, utazók száma)
2. Unified TripScore & Értékajánlat banner (összhang pontszám 0-100, hasznos nyaralási idő, 4 pillér bontás)
3. Élményfókusz & Logisztikai profil (kiválasztott vibek, idősávok, maximális sétaidő)
4. Főbb adatok kártyák (célállomás, repülőjárat menetrenddel és hasznos idővel, szálláshely)
5. Napi Élmény Útiterv & Menetrend (napokra bontott idősávok, sétaidők és tranzit javaslatok)
6. Kiválasztott Fő Élmények portfóliója (kategóriák, egyezési pontszám és ajánlási indoklás)
7. Tételes Matematikai Költségkalkuláció táblázat (Numbeo képletekkel)
8. Végösszeg kiemelés (Teljes becsült összeg és Egy főre jutó költség)
```

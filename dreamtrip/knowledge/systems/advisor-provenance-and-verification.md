---
id: advisor-provenance-and-verification
type: system
name: Advisor Provenance & Data Freshness Engine
status: active

description: Az Optivoya B2B Advisor Workspace adat-eredet (Provenance) nyilvántartási, mélylinkelési (Deep Links), frissességi időkorlát (TTL) és verifikációs státusz modellje.

source:
  type: code
  ref: app.services.verification_service

code:
  - app/models/advisor_models.py
  - app/services/verification_service.py
  - app/services/trip_risk_service.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[honest-scraping-policy]]"
  - "[[kiwi-scraper]]"
  - "[[cozycozy-scraper]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 🏷️ Advisor Provenance & Data Freshness Engine

Ez a dokumentum specifikálja az **Optivoya Advisor Workspace** adat-eredet (Provenance) modelljét, amely biztosítja, hogy minden árajánlat, járat és szállás közvetlenül visszavezethető és ellenőrizhető legyen a forrásoldalakon.

---

## 1. Provenance Adatmodell (`ProviderProvenance`)

Minden generált elem (város, repülőjegy, hotel, program) kötelezően tartalmazza a `ProviderProvenance` struktúrát:

```yaml
ProviderProvenance:
  provider: "Kiwi.com" | "Cozycozy" | "Open-Meteo" | "Numbeo" | "OSM" | "Manual"
  source_type: "api" | "aggregator" | "website" | "manual" | "cache" | "estimate"
  source_url: "https://kiwi.com"
  deep_link: "https://kiwi.com/deep/bud-bcn-2026-06-12"
  booking_url: "https://booking.com/hotel/es/arts-barcelona"
  checked_at: "2026-09-24T14:15:00Z"
  expires_at: "2026-09-24T14:45:00Z"
  freshness_ttl_seconds: 1800 # 30 perc
  verification_status: "VERIFIED" | "ESTIMATED" | "STALE" | "NEEDS_REVIEW" | "UNAVAILABLE"
  raw_reference: "booking_token_xyz987"
  is_estimated: false
  price_currency: "HUF"
  original_price: 245.0
  original_currency: "EUR"
```

---

## 2. Verifikációs Státuszok (`VerificationStatus`)

- **`VERIFIED` (Élőben igazolt)**: Az adat közvetlenül a szolgáltatói API-ból vagy aggregátorból származik, és a frissességi időkorláton (TTL, pl. 30 perc) belül van.
- **`ESTIMATED` (Becsült)**: Statisztikai átlag, Numbeo megélhetési index vagy benchmark alapján kalkulált érték.
- **`STALE` (Elavult)**: Korábban lekért adat, amelynek érvényessége meghaladta a TTL-t; újrakutatás javasolt.
- **`NEEDS_REVIEW` (Ellenőrzést igényel)**: Tanácsadói manuális jóváhagyást igénylő elem (pl. speciális poggyászszabály vagy helyi idegenforgalmi adó).
- **`UNAVAILABLE` (Nem elérhető)**: A járat megtelt vagy a hotel nem fogad vendégeket a megadott napokon.

---

## 3. Tanácsadói UX Garanciák

A munkaterületen minden elem mellett megjelenik:
- **Forrás jelvény**: *Kiwi.com / Cozycozy*
- **Időbélyeg**: *Ellenőrizve: 8 perce*
- **Mélyhivatkozás (Deep Link)**: Közvetlen `Megnyitás forrásoldalon ↗` gomb, amellyel a tanácsadó 1 kattintással ellenőrizheti a valós jegyárat vagy lefoglalhatja a szobát.

---
id: project-context
type: concept
name: Optivoya Project Overview
status: active
---

# Optivoya (DreamTrip) — Project Context

## Project Overview

**Optivoya** (korábban DreamTrip) egy AI- és döntéselmélet-alapú **Travel Intelligence Platform** és **B2B Utazási Tanácsadói Rendszer**.

A rendszer célja, hogy a hagyományos utazási portálok manuális, több tucat böngészőfüllel végzett keresése helyett egyetlen integrált, adatvezérelt döntéstámogató folyamatot nyújtson mind utazóknak, mind B2B utazásszervezőknek.

## Core Capabilities

1. **Destination Matcher**:
   * Globális célállomások többkritériumos keresése és rangsorolása.
   * Valós éghajlati adatok (hőmérséklet, csapadék, napsütés), valós repülőjegy árak (Kiwi), biztonsági és megélhetési költségindexek (Numbeo).
   * Determinisztikus AHP (Analytic Hierarchy Process) döntési pontozás.

2. **Flight Intelligence**:
   * Élő Kiwi.com GraphQL adataggregáció Budapestről és regionális repülőterekről (Bécs, Debrecen, Pozsony).
   * Multi-kritériumos AHP páros mátrixos preferenciamodellezés és PROMETHEE II rangsorolás.
   * Ár, utazási idő, átszállások száma és menetrendi minőség optimalizálása.

3. **Accommodation Intelligence**:
   * Szállásaggregáció Cozycozy integrációval.
   * PROMETHEE II alapú ár-érték és vendégértékelés rangsorolás.
   * Automatikus dátum- és éjszakaszám-zárolás a kiválasztott repülőjárat menetrendjéből.

4. **Unified Trip Workspace & B2B Proposal**:
   * Egyetlen közös `[[Unified Trip Model]]` gerinc.
   * Tételes, hivatalos Numbeo Cost of Living alapú matematikai költségkalkuláció (repülőjegy + szállás + napi étkezés + helyi közlekedés).
   * 1-kattintásos nyomtatható / PDF B2B ügyfélajánlat generálás.

## Tech Stack

* **Backend**: Python 3.13, FastAPI, Pydantic v2, Uvicorn, Pandas, NumPy.
* **Frontend**: Vanilla JS (`TripEngine`), Jinja2 sablonok, modern responsive CSS (Dark/Light mode tokenek, glassmorphism, mobile-friendly kártyanézetek).
* **Adatforrások & API-k**: Kiwi GraphQL / REST API, Cozycozy, Open-Meteo Historical Climate API, Numbeo Cost of Living & Crime/Safety Index, Google Places API (opcionális).

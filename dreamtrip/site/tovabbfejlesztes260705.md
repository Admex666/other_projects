# 🌍 DREAMTRIP v2 — FEJLESZTÉSI SPEC

## 1. Egy mondatos definíció

> A DreamTrip egy intelligens utazástervező rendszer, amely több forrásból (Google Maps, flight data, cost indexek) származó adatokat kombinálva automatikusan rangsorolja az úti célokat, és constraint-alapú napi útitervet generál, amely valós időben újraoptimalizálható.

---

# 2. RENDSZER ÁTTEKINTÉS (MODULOK)

A rendszer 4 fő rétegből áll:

## 2.1 Destination Intelligence Layer

* városok értékelése (scoring + ranking)
* flight + cost + weather + POI density

## 2.2 POI Intelligence Layer (Google Maps alapú)

* Places API / Maps data
* rating, opening hours, type, price level
* kategorizálás (food, culture, nature, nightlife)

## 2.3 Trip Planning Engine

* constraint-alapú napi terv generálás
* meal slot rendszer
* travel time graph

## 2.4 Optimization + Replanning Engine

* itinerary módosítás → lokális újraszámolás
* schedule repair mode

---

# 3. USER FLOW (END-TO-END)

## 3.1 Trip discovery (város választás)

1. user megad:

   * indulási város
   * dátum intervallum
   * budget
   * utazási preferenciák

2. rendszer:

   * lekéri flight opciókat (Kiwi API)
   * lekéri város adatokat (Numbeo + weather + Google Places sample)
   * kiszámolja city score-t

3. output:

   * ranked city list
   * “why this city” explanation
   * scenario alapú ajánlás (pl. “relax / food / culture heavy”)

---

## 3.2 Trip build (útiterv generálás)

1. user kiválaszt várost

2. rendszer:

   * lekéri top POI-kat Google Places API-ból
   * kategorizálja őket:

     * attractions
     * restaurants
     * cafes
     * viewpoints

3. constraint engine:

   * napi időablakok
   * travel time graph
   * opening hours check

4. output:

   * napi itinerary (auto-generated)
   * meal slots automatikusan kitöltve

---

## 3.3 Editing + Re-optimization

* drag & drop módosítás
* rendszer:

  * csak affected day-et újraszámol
  * travel times újragenerálódnak
  * étkezési slotok újratöltődnek
  * nyitvatartás validálás

---

# 4. ADATMODELL (CORE ENTITIES)

## 4.1 City

```ts
City {
  id: string
  name: string
  country: string

  cost_index: number
  safety_index: number
  weather_score: number

  attraction_density: number
  nightlife_score: number
  walkability_score: number

  flight_score: number

  computed_score: number
}
```

---

## 4.2 POI (Google Maps based)

```ts
POI {
  id: string
  city_id: string

  name: string
  type: "restaurant" | "attraction" | "cafe" | "viewpoint"

  rating: number
  user_ratings_total: number

  price_level: number
  opening_hours: object

  location: lat/lng
}
```

---

## 4.3 Trip

```ts
Trip {
  id: string
  user_id: string

  city_id: string
  start_date: date
  end_date: date

  budget: number

  preferences: TravelPreferences
}
```

---

## 4.4 Itinerary

```ts
ItineraryDay {
  date: date
  items: ItineraryItem[]
}

ItineraryItem {
  poi_id: string
  start_time: datetime
  end_time: datetime

  type: "activity" | "meal" | "travel"

  locked: boolean
}
```

---

# 5. BUSINESS LOGIC RULES

## 5.1 Scheduling rules

* napi max 12 aktív POI
* 1 reggeli + 1 ebéd + 1 vacsora slot
* POI csak ha:

  * open
  * travel time belefér
  * nincs ütközés

---

## 5.2 Replanning rules

* user módosítás → local recalculation
* nem global rewrite
* locked items nem módosulnak

---

## 5.3 Ranking rules

City score = weighted sum:

* flight cost (0.3)
* cost of living (0.2)
* attraction density (0.2)
* weather (0.1)
* safety (0.1)
* walkability (0.1)

---

# 6. GOOGLE MAPS INTEGRATION (KÖTELEZŐ)

## Használt API-k:

* Google Places API
* Google Place Details API

## Data usage:

* POI fetch per city bounding box
* text search + category search:

  * restaurants
  * attractions
  * museums
  * parks

## Caching:

* city POI cache 7 nap
* deduplication by place_id

---

# 7. SYSTEM FEATURE SET (V1)

## BENNE VAN:

* city ranking engine
* Google Maps POI extraction
* itinerary generator
* meal slot system
* travel time estimation
* drag & drop itinerary editor
* local re-optimization
* explainable ranking

---

## NINCS BENNE:

* social features
* realtime multi-user editing
* push notifications
* gamification
* mobile app
* AI chat assistant UI (backend logic lehet, UI nem)

---

# 8. FAILURE SCENARIOS

* Google Maps API timeout → fallback cached POI
* missing opening hours → assume open default
* no flight data → reduce flight weight in scoring
* itinerary conflict → auto resolve greedy fallback
* user offline → read-only mode

---

# 9. ARCHITECTURE

## Backend:

* FastAPI
* modular services:

  * flight_service
  * maps_service
  * scoring_service
  * itinerary_service

## Pipeline:

```
APIs → Data Layer → Feature Builder → Scoring Engine → Planner Engine → UI
```

---

# 10. KEY DESIGN PRINCIPLE

> Az app nem “tervez”, hanem **optimalizál és újraoptimalizál constraint-ek alapján**.

---

# 🚀 EXTRA (KRITIKUS DESIGN INSIGHT)

A rendszer 3 dologra épül:

### 1. GRAPH MODEL

* POI = node
* travel time = edge

### 2. SCORING MODEL

* city + POI ranking

### 3. CONSTRAINT ENGINE

* idő
* nyitvatartás
* étkezés
* sétatávolság

---

# Ha ezt megcsinálod, akkor a DreamTrip nem:

* planner app lesz

hanem:

> **decision + optimization engine for travel planning**
# DreamTrip — Projekt Áttekintés

## Projekt Célja
A **DreamTrip** egy intelligens utazástervező és optimalizáló rendszer (*decision & optimization engine for travel planning*), amely több adatforrást (repjegyárak, időjárás, megélhetési indexek, Google Places látnivalók) kombinálva automatikusan rangsorolja az úti célokat, és constraint-alapú, valós időben újraoptimalizálható napi útitervet generál.

A rendszer **nem generatív AI mellébeszéléssel**, hanem valós matematikai, geográfiai és logikai modellek segítségével építi fel és igazítja ki az utazási tervet.

---

## Főbb Technológiai Stukk

* **Backend Framework**: Python 3.11+, FastAPI, Pydantic, Uvicorn
* **Adatmodell & Pontozás**: NumPy, Pandas, Haversine távolságmérés
* **API Integrációk**:
  * **Kiwi.com GraphQL / REST API** (valós idejű repjegyárak)
  * **Google Places & Place Details API** (látnivalók, nyitvatartások, értékelések)
  * **Open-Meteo API** (havi átlaghőmérsékletek és klímaadatok)
  * **Numbeo Indexek** (megélhetési költségek és közbiztonsági index)
* **Frontend**: HTML5, Vanilla CSS, JavaScript (ES6+), Leaflet.js (interaktív térkép), HTML5 Drag & Drop API, Jinja2 Templates
* **Csomagstruktúra**: Szabványos Python csomag elrendezés (`app/`, `data/`, `notebooks/`, `scripts/`, `docs/`, `memory/`)

---

## Projekt Terjedelem (Scope)

### Benne van
* Városrangsoroló és pontozó motor (6-tényezős súlyozott modell)
* Google Places POI lekérdezés 7 napos automatikus gyorsítótárazással (cache)
* Constraint-alapú napi útiterv-generálás (idősávok, étkezési slotok, utazási idők)
* Interaktív útiterv-szerkesztés drag & drop funkcióval és lokális újraoptimalizálással
* Nyitvatartási idő ellenőrzés és ütközésjelzés
* Lelakatolható (locked) programok kezelése

### Nincs benne (Out of scope)
* Közösségi hálózati funkciók és megosztás
* Valós idejű több-felhasználós közös szerkesztés (Multi-user co-editing)
* Mobil natív alkalmazás (kizárólag responsive web UI)

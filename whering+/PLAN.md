# PLAN.md
---

## 1️⃣ PROBLÉMA DEFINÍCIÓ

* **Ki használja?**

  * Karrier-orientált férfiak és nők, irodai/hibrid munkakörnyezetben.
  * Neurodivergens felhasználók (ADHD, AuDHD), akiknek döntési fáradtság és szenzoros érzékenység miatt nehéz napi outfiteket választani.
  * Átmeneti élethelyzetek: post-baby, súlyingadozás, új munkahely, fontos események.
  * Divat- és önkifejezés-orientált felhasználók, akik szeretnék tudatosan használni a ruhatárukat.

* **Milyen konkrét problémát old meg?**

  * Bizonytalanság a napi outfit választásában → stressz és döntési fáradtság csökkentése.
  * Nem használt ruhadarabok láthatóvá tétele → “cognitive clutter” csökkentése.
  * Önkifejezés + praktikum → konzisztens, mégis változatos outfit választás.
  * Viselt ruhák rögzítése → tudatosabb gardróbhasználat és történet alapú ajánlások.

* **Miért jobb, mint létező alternatívák?**

  * Nem csak outfit ötleteket ad, hanem **megmagyarázza, validálja és rögzíti** a választást.
  * Figyelembe veszi a kontextust: meeting, időjárás, dress code, események.
  * Gardróbkezelés és history tracking → a felhasználó tudja, mit hordott, mi működött.
  * Personalizált AI javaslatok a confidence növelésére.
  * Reális, könnyen használható: nem kell teljes gardróbot katalogizálni, de lehet.

---

## 2️⃣ SCOPE LOCK

**Mit NEM csinál az app?**

* Nem helyettesíti teljesen a személyes stylistot minden alkalommal.
* Nem tervez teljes közösségi hálót (share, like, comment)
* Nem integrál közvetlenül webshopokkal / vásárlással
* Nem AI generál teljesen új ruhadarabokat / trendeket

**Mit hagyunk ki szándékosan?**

* 3D body scanning vagy AR próbafülke
* Teljes offline-first működés (online-first, de cache-eli a wardrobe-t)

---

## 3️⃣ DOMAIN MODELL

**Fő entitások:**

1. **User**

   * Attributes: id, email, name, style profile, preferences, history, wardrobe
   * Lifecycle: regisztráció → wardrobe feltöltés → outfit validation → personalization

2. **Wardrobe Item**

   * Attributes: id, type (shirt, pants…), color, fabric, size, photo, tags, purchase date
   * Lifecycle: added → worn → archived / retired

3. **Outfit**

   * Attributes: id, items (WardrobeItem list), context, confidence score, rationale, date worn
   * Lifecycle: suggested → validated → archived

4. **Context**

   * Attributes: date, weather, event type, dress code, mood
   * Lifecycle: daily → associated with outfit

5. **Validation Feedback**

   * Attributes: user id, outfit id, score, comments
   * Lifecycle: user submission → stored → contributes to personalization

**Aggregátum gyökér:**

* **User** (minden wardrobe item, outfit és feedback hozzá kapcsolódik)

**Kapcsolatok:**

* User → WardrobeItem (0..n)
* User → Outfit (0..n)
* Outfit → ValidationFeedback (0..n)
* Outfit → Context (1..n)

---

## 4️⃣ USE CASE → FLOW DESIGN

### 1. Wardrobe Management

* **Indító esemény:** User hozzáad új ruhadarabot / szerkeszt meglévőt
* **Mi történik:**

  * Rögzítés, kategorizálás (típus, szín, anyag, méret)
  * Fotók feltöltése
  * Tags (pl. “business”, “casual”, “summer”)
* **Hiba lehetőség:** nem megfelelő fotó / hiányos adatok
* **Eredmény:** felhasználó gardróbja digitálisan kezelhető, alap a javaslatokhoz

### 2. Napi Outfit Validáció

* **Indító esemény:** User kiválasztja vagy javasolt outfitet
* **Mi történik:**

  1. Kontextus összegyűjtése (weather, event)
  2. Outfit scoring (confidence + rationale)
  3. Megjelenítés a felhasználónak
* **Hiba lehetőség:** hiányos context
* **Eredmény:** confidence score, megerősítés + tipp

### 3. Break the Loop / Suggestion

* **Indító esemény:** repetitív outfit mintázat
* **Mi történik:**

  * AI javasol apró változtatást a meglévő outfithez
* **Eredmény:** variáció, de biztonságos

### 4. History & Analytics

* **Indító esemény:** User megnézi múltbeli outfitjeit
* **Mi történik:**

  * Confidence trendek, viselt ruhák statisztikái
* **Eredmény:** tudatosabb gardróbhasználat, personalizált javaslatok

### 5. Outfit Validation + Rationale

* **Indító esemény:** outfit kiválasztása
* **Mi történik:**

  * Scoring
  * Miért működik? (context, múlt, feedback)
* **Eredmény:** megerősítés, confidence növelés

---

## 5️⃣ ARCHITEKTÚRA DÖNTÉSEK

* **State management:** React + Zustand / Redux
* **Dependency injection:** context + service layer
* **Storage:**

  * Local: gyors cache
  * Remote: Supabase / Firebase (User, WardrobeItem, Outfit, Feedback)
* **Offline-first:** wardrobe cache, napi outfit offline működés
* **Structure:** feature-based (wardrobe, outfit validation, history, suggestions, personalization)

---

## 6️⃣ UI STRUKTÚRA

**Fő képernyők:**

1. **Home / Daily Outfit Feed**

   * States: empty, loading, error
2. **Wardrobe Management**

   * Hozzáadás / szerkesztés / archiválás
   * Fotók, tags, type, fabric
3. **Outfit Validation Screen**

   * Score + rationale + minor suggestions
   * Actions: Accept / Modify
4. **Break the Loop Suggestions**

   * Repetitive outfits → “small upgrade” tip
5. **History / Analytics**

   * Confidence trend, outfit statistics, gyakran hordott ruhák
6. **Profile / Settings**

   * Style profile, preferences, context settings

**Navigáció:**

* Tab-based: Home | Wardrobe | Suggestions | History | Profile

---

## 7️⃣ ITERÁCIÓS STRATÉGIA

1. **Domain** – User, WardrobeItem, Outfit, Context, Feedback entitások definiálása
2. **Feature vertical slice:**

   * Wardrobe + Daily Outfit Validation + History
3. **Refactor:**

   * State, storage és aggregátum lifecycle
4. **Következő feature:**

   * Break the Loop, Suggestions, Analytics

**Megjegyzés:**

* Full product esetén minden vertical slice-t végig kell gondolni UI + logic + storage együtt
* MVP-ben csak Daily Outfit Validation + basic Wardrobe, full verzióban teljes confidence engine + wardrobe analytics + personalization
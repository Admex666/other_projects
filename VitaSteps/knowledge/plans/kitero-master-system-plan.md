---
id: kitero-master-system-plan
type: plan
name: VitaSteps Kitérő Master Rendszerterv & Architektúra
status: draft
version: 1.0.0
date: 2026-11-12
authors:
  - Lead Orchestrator (CEO Persona)
related:
  - "[[kitero|VitaSteps Kitérő]]"
  - "[[ADR-010-kitero-validation-architecture|ADR-010]]"
  - "[[ADR-009-strategic-ecosystem-pivot|ADR-009]]"
  - "[[checkout-pipeline|Checkout Pipeline]]"
  - "[[customer-funnel|Customer Funnel]]"
  - "[[supabase|Supabase Architecture]]"
---

# 🧭 VitaSteps Kitérő: Master Rendszerterv & Architektúra

Ez a dokumentum a **VitaSteps Kitérő** önvezetett, digitális városi élményséták end-to-end specifikációja. Integrálja a korábbi kutatási és kísérleti alapokat (az `E:\Data\hosszulepes` AI prompt és PWA tapasztalatait, valamint a `kitero_launch_handover.md` stratégiai döntéseit) a meglévő VitaSteps infrastruktúrába (`vitastepsss.vercel.app` / Supabase / Stripe / Számlázz.hu).

---

## 1. Vezetői Összefoglaló és Célkitűzés

A **VitaSteps Kitérő** a márka magas árrésű, zéró fizikai készletezési költségű digitális terméke.
* **Első éles pilot séta:** *A Kisföldalatti Nyomában* (Budapest VI. és XIV. kerület, Mexikói úti járműteleptől a Vörösmarty térig, 9 megálló, ~3.4 km, 1.5–2 óra).
* **Fő technológiai modell:** Mobil-optimalizált **PWA (Progressive Web App)**, amely asztali és mobil böngészőből azonnal elérhető telepítés nélkül, de "Kezdőképernyőhöz adható", Service Workerrel gyorsítótárazza a térképet és az audió anyagokat.
* **UI/UX & Design Rendszer:** **Tactical Carto** elrendezés egységes **Outfit** tipográfiával (nem-AI, tiszta architektúra):
  * **Nappali (Light) mód:** *Editorial Forest Light* (Meleg krém `#F8F7F2`, fehér kártyák, mély erdőzöld `#365A45` akcentus – közvetlen összhangban a meglévő marketing landinggel).
  * **Éjszakai (Dark) mód:** *Dark Olive Forest* (Mély olíva-fekete háttér `#141815`, erdőzöld kártyák `#1D231F`, smaragdzöld navigációs akcentus `#529B72`).
* **Tartalmi struktúra az állomásokon:** Strukturált 4 részes **Adatmátrix (Data Matrix)** (Építés éve, Stílus, Funkcióváltás, Történelmi súly) + lényegretörő háttértörténet + **Podcast stílusú TTS audiolejátszó**. Felesleges sallangok és AI-slop (pl. headline takeaway és emoji-túltengés) nélkül.
* **Üzleti modell:** Egyedi séta vásárlás (3 490 Ft – 3 990 Ft) Stripe fizetéssel, automata számlázással és azonnali hozzáféréssel (Magic Link / Access Token).
* **Vercel Free Limit Védelem:** Nem hozunk létre új serverless function-öket, a meglévő `api/kitero.js` végponton keresztül fut a checkout, process, auth és event routing.

---

## 2. Rendszerarchitektúra (Architecture Overview)

A meglévő VitaSteps architektúrába illeszkedve a Kitérő nem igényel új tárhelyet vagy teljesen különálló infrastruktúrát. A Vercel szerveroldali monorepo és a közös Supabase adatbázis szolgálja ki.

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Kliens & Felhasználói Réteg (Mobile/Desktop)"]
        LP["Landing Page (Marketing)<br>/kitero/index.html<br>• Értékajánlat, előnézet, árak<br>• Lead capture"]
        PWA["Kitérő Webapp (PWA)<br>/kitero/app/<br>• Leaflet térkép + GPS nyomkövetés<br>• Audio lejátszó + Szövegek<br>• Haladás és állapotkezelés"]
        AdminUI["VitaSteps Admin Panel<br>/admin.html & admin-kitero.js<br>• Séta tesztelő mód<br>• Funnel & vásárlási statisztikák"]
    end

    subgraph EdgeBackend ["2. Vercel Serverless Backend (/api)"]
        ApiCheckout["/api/kitero-checkout.js<br>Stripe Session létrehozás"]
        ApiProcess["/api/kitero-process-payment.js<br>Fizetés ellenőrzés & Token generálás"]
        ApiAccess["/api/kitero-auth.js<br>Token hitelesítés & Séta feloldás"]
        ApiTours["/api/kitero-tours.js<br>Séta metaadatok & POI-k kiszolgálása"]
        ApiEvents["/api/kitero-events.js<br>Részletes eseménymérés"]
    end

    subgraph DataIntegrations ["3. Adatbázis & Külső Integrációk"]
        Supa[(Supabase PostgreSQL)]
        SupaStorage[(Supabase Storage<br>/audio/ & /assets/)]
        StripeApi[Stripe API<br>Checkout & Apple/Google Pay]
        SzamlazzApi[Számlázz.hu API<br>E-számla generálás]
        Mailer[Gmail SMTP / Resend<br>Belépő link & számla kiküldés]
    end

    %% Kapcsolatok
    LP -->|1. Vásárlás indítása| ApiCheckout
    ApiCheckout --> StripeApi
    StripeApi -->|2. Sikeres fizetés átirányítás| ApiProcess
    ApiProcess -->|3. Upsert vásárló & Jogosultság| Supa
    ApiProcess -->|4. E-számla kiállítás| SzamlazzApi
    ApiProcess -->|5. Hozzáférési link email| Mailer
    Mailer -.->|6. Kattintás az email linkre| PWA

    PWA -->|Token ellenőrzés| ApiAccess
    ApiAccess --> Supa
    PWA -->|Séta & POI adatok lekérése| ApiTours
    PWA -->|Hangfájlok letöltése| SupaStorage
    PWA -->|GPS & Telemetria események| ApiEvents
    ApiEvents --> Supa

    AdminUI -->|Belső API hívások| Supa
```

---

## 3. End-to-End User Flow (Felhasználói Útvonal)

A felhasználó a hirdetéstől a városi séta fizikai befejezéséig terjedő teljes útja:

```mermaid
sequenceDiagram
    autonumber
    actor U as 📱 Felhasználó (Sétáló)
    participant LP as 🌐 Landing Page
    participant Stripe as 💳 Stripe Checkout
    participant Backend as ⚙️ Vercel API
    participant DB as 🗄️ Supabase
    participant Mail as ✉️ Email Rendszer
    participant PWA as 🗺️ Kitérő PWA Webapp

    Note over U,LP: 1. Felfedezés & Vásárlás
    U->>LP: Megérkezik (Meta hirdetés / Organikus)
    LP->>U: Bemutatja a Palotanegyed sétát + Hangminta előnézet
    U->>LP: Kattint a "Séta megvásárlása" gombra (Név, Email megadása)
    LP->>Backend: POST /api/kitero-checkout
    Backend->>Stripe: Stripe Checkout Session létrehozása
    Stripe-->>U: Megjelenik a bankkártyás / Apple Pay fizetőfelület
    U->>Stripe: Kifizeti a séta díját (pl. 3 490 Ft)

    Note over Stripe,PWA: 2. Azonnali Jogosultság & Átirányítás
    Stripe-->>U: Visszairányítás: /kitero/siker.html?session_id=cs_...
    U->>Backend: POST /api/kitero-process-payment
    Backend->>DB: Tranzakció mentése, 'kitero_purchases' rekord + Egyedi Token generálás
    Backend->>Mail: Hozzáférési link ("Magic Link") + Számla kiküldése
    Backend-->>U: Válasz: Token + Közvetlen sétaindító URL (/kitero/app/?token=XYZ)

    Note over U,PWA: 3. Városi Séta Élményszakasz (Terepen)
    U->>PWA: Megnyitja a webappot (vagy a böngészőből, vagy az email linkről)
    PWA->>Backend: Validálja a tokent & betölti a séta adatait
    PWA->>U: Kéri a GPS engedélyezést (Wake Lock bekapcsolása: képernyő ébrentartása)
    
    loop 8 Állomás bejárása (Palotanegyed)
        U->>PWA: Sétál a térképen jelölt következő POI felé
        PWA->>PWA: Ha távolság < 35m: "Megérkeztél!" esemény aktiválódik
        PWA->>U: Lejátssza az Audio Hook-ot & megnyitja a Történetkártyát
        U->>PWA: Meghallgatja a 2-3 perces audió narrációt / elolvassa a sztorit
        PWA->>DB: POI teljesítve esemény mentése (telemetria)
    end

    Note over U,PWA: 4. Teljesítés & Retenció
    PWA->>U: Gratuláló képernyő + Digitális Emléklap
    PWA->>DB: Séta státusz = 'completed'
    PWA->>U: NPS értékelő kérdőív & "Következő séta előjegyzése" ajánlat
```

---

## 4. UI/UX és Webapp Funkcionális Specifikáció

A korábbi `E:\Data\hosszulepes\webapp` prototípus és a Stitch dizájn tanulságai alapján a PWA az alábbi képernyőkből és modulokból épül fel:

```mermaid
stateDiagram-v2
    [*] --> SplashAuth : Megnyitás URL-ből (?token=XYZ)
    SplashAuth --> TourOverview : Érvényes token
    SplashAuth --> PaywallPrompt : Hiányzó / érvénytelen token

    state TourOverview {
        [*] --> SetaAdatlap : Táv, Időtartam, Megállók listája
        SetaAdatlap --> TerepStart : "Séta Indítása" gomb
    }

    state ActiveWalk {
        TerepStart --> MapView : GPS pozíció követés (Leaflet)
        MapView --> PoiDrawer : POI-ra kattintás (Lista)
        MapView --> ArrivedModal : Geofence beérés (<35m)
        
        state ArrivedModal {
            [*] --> AudioHookPlay : Rövid figyelemfelkeltő hang
            AudioHookPlay --> StoryCard : Teljes narráció & Archív fotó
            StoryCard --> MarkCompleted : "Megálló meghallgatva"
        }
        MarkCompleted --> MapView : Következő megálló kijelölése
    }

    ActiveWalk --> FinishedScreen : 8/8 megálló teljesítve
    FinishedScreen --> [*] : Értékelés & Megosztás
```

### Kulcsfontosságú UX megoldások:
1. **Screen Wake Lock API:** Megakadályozza, hogy séta közben a telefon képernyője lezárjon.
2. **Kétlépcsős Hangélmény:**
   * **Audio Hook:** 15–20 másodperces, azonnal induló felcsigázó felütés a helyszínhez éréskor.
   * **Full Story:** 2–3 perces mély, emberközpontú történet zenei aláfestéssel.
3. **Manuális felülbírálás (Fail-safe):** Ha a városi házak árnyékolása miatt a GPS pontatlan, a sétáló egyetlen gombnyomással manuálisan is bejelentkezhet az adott állomásra ("Itt vagyok" gomb).
4. **Offline ellenállóképesség:** A Service Worker előre cache-eli a hangfájlokat és a térképcsempéket induláskor, így a térerő-ingadozás sem akasztja meg az élményt.

---

## 5. Adatbázis Modell (Supabase Adatbázis Kiterjesztés)

Nem szükséges külön Supabase projektet indítani. A meglévő VitaSteps adatbázisban a Kitérő entitások dedikált táblákba kerülnek, közvetlenül összekapcsolva a meglévő `runners` és `analytics_sessions` rekordokkal.

```mermaid
erDiagram
    RUNNERS ||--o{ KITERO_PURCHASES : owns
    KITERO_TOURS ||--|{ KITERO_POIS : contains
    KITERO_TOURS ||--o{ KITERO_PURCHASES : target
    KITERO_PURCHASES ||--o{ KITERO_SESSIONS : authorises
    KITERO_SESSIONS ||--o{ KITERO_PROGRESS : tracks

    RUNNERS {
        uuid id PK
        text email UK
        text name
    }

    KITERO_TOURS {
        text id PK "palotanegyed"
        text title
        text district "VIII. kerület"
        numeric distance_km
        integer estimated_minutes
        integer stops_count
        boolean is_active
        jsonb metadata
    }

    KITERO_POIS {
        integer id PK
        text tour_id FK
        integer sequence_order
        text name
        numeric lat
        numeric lng
        text category "epiteszet, tortenelem, gasztro"
        text audio_hook_url
        text audio_story_url
        text story_text
        text[] photo_urls
    }

    KITERO_PURCHASES {
        uuid id PK
        uuid runner_id FK
        text tour_id FK
        text stripe_session_id UK
        text access_token UK "biztonságos URL token"
        integer amount_paid
        text status "paid, refunded, test"
        timestamp expires_at "örökös vagy 1 év"
        timestamp created_at
    }

    KITERO_SESSIONS {
        uuid id PK
        uuid purchase_id FK
        timestamp started_at
        timestamp finished_at
        text user_agent
        integer completed_pois_count
        boolean is_test_run "Admin teszt jelölő"
    }

    KITERO_PROGRESS {
        bigint id PK
        uuid session_id FK
        integer poi_id FK
        timestamp arrived_at
        boolean audio_listened
        boolean completed
    }
```

---

## 6. Sétagyártási & Tartalom Workflow (AI-Ember Kollaboráció)

A séták előállítása az `E:\Data\hosszulepes` mappában kidolgozott, bevált 5-fázisú receptúrára épül:

```mermaid
flowchart LR
    A["1. Téma & Kerület<br>ötletelés"] --> B["2. Deep Research<br>30 POI + 4 Történelmi szál"]
    B --> C["3. Emberi Kurálás<br>8-10 POI + TSP útvonalterv"]
    C --> D["4. Történetírás<br>Story & Hook AI promptolás"]
    D --> E["5. Audio Generálás<br>ElevenLabs AI szinkron"]
    E --> F["6. Terepi Teszt<br>Admin Mode-ban végigjárás"]
    F --> G["7. Éles Publikálás<br>Adatbázisba importálás"]
```

1. **Ötlet & Narratíva:** Claude / Gemini kutatás (érdekességek, legendák, botrányok).
2. **TSP Útvonal-optimalizálás:** Python szkript (`optimizer.py`) rendezi a megállókat a legkevesebb felesleges gyaloglást eredményező sorrendbe.
3. **Szövegezés:** A `03.2_webapp_prompt.txt` alapján készült formázás-mentes, folyó szövegek (Hook + 300–400 szavas Story).
4. **Hanganyag (AI Voice):** ElevenLabs / Google Cloud TTS élethű, atmoszférikus felolvasással, MP3 tömörítéssel a Supabase Storage-ba töltve.
5. **Terepi Teszt:** Az admin felületen dedikált tesztüzemmódban történő végigjárás.

---

## 7. Események Időbelisége és Felelősségi Mátrix (RACI)

| Időablak / Fázis | Feladat / Esemény | Felelős (R) | Támogató (A/C) | Output / Eredmény |
| :--- | :--- | :--- | :--- | :--- |
| **T0: Alapozás (1-2. nap)** | Supabase séma migráció (`kitero_*` táblák) | Lead Developer | CEO | Létrejött adatbázistáblák, RLS szabályok |
| **T0: Alapozás (2-3. nap)** | Backend API végpontok (`checkout`, `process`, `auth`) | Fullstack Eng. | Lead Developer | Működő Stripe fizetési & jogosultsági flow |
| **T1: Webapp & PWA (3-5. nap)** | `/kitero/app/` PWA felépítése a korábbi kódokból | Fullstack Eng. | Lead Developer | Leaflet GPS térkép, audio lejátszó, offline SW |
| **T1: Tartalom (3-4. nap)** | Palotanegyed POI adatok, szövegek & audió generálás | Research Scout | CEO | 8 megálló végleges hanganyaga és képei |
| **T2: Terepteszt (5-6. nap)** | **Élő budapesti séta végigjárása mobiltelefonnal** | **CEO (Adam)** | QA-Validator | GPS pontosság, hangerő és felhasználói élmény teszt |
| **T2: Landing frissítés (6. nap)** | Landing page átkötése a fizetési pipeline-ra | Fullstack Eng. | Lead Developer | Éles checkout CTA gombok, A/B tesztelt árak |
| **T3: Piacra lépés (7. nap)** | Meta kampány indítás & Email bejelentés | CEO | Data Analyst | Első éles vásárlók, analitikai figyelés |

---

## 8. Adminisztráció, Tesztelési Mód & Mérés (Analytics)

1. **Admin / Tesztelői Mód (`is_test=true`):**
   * Az admin felületről vagy egy speciális URL-lel (`/kitero/app/?test_mode=1`) a rendszer fizetés nélkül is megnyitható.
   * GPS szimulátor és megálló-léptető gombok segítik az asztali tesztelést.
   * A tesztelés során generált adatok nem torzítják az üzleti statisztikákat.
2. **Analitikai Mérőrendszer:**
   * A meglévő `analytics.js` bővítése Kitérő specifikus eseményekkel:
     * `kitero_landing_view` $\rightarrow$ `kitero_preview_play` $\rightarrow$ `kitero_checkout_init` $\rightarrow$ `kitero_purchase_success`
     * `kitero_walk_start` $\rightarrow$ `kitero_poi_reach` $\rightarrow$ `kitero_audio_finish` $\rightarrow$ `kitero_walk_complete`
   * Napi Pushbullet vezetői jelentés a Kitérő látogatókról, vásárlásokról és teljesítésekről.

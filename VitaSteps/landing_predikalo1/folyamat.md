# 🏔️ VitaSteps Logisztikai és Időbeli Folyamatábra (Sequence Diagram)

A diagram az idő múlását felülről lefelé ábrázolja, és pontosan mutatja az interakciókat a szereplők (Vásárló, Weboldal/Stripe, Google Sheet, Te/Admin, és a Foxpost) között.

```mermaid
sequenceDiagram
    autonumber
    actor V as 🏃 Vásárló
    participant R as 🌐 Rendszer (Stripe/Tally)
    participant S as 📝 Google Sheet
    actor A as 👑 Te (Admin)
    participant F as 🦊 Foxpost
    
    %% 1. Fázis
    Note over V, R: 1. Regisztráció & Vásárlás
    V->>R: Kiválasztja a Foxpost pontot a Checkout Widgetben
    V->>R: Sikeres fizetés (Stripe Checkout)
    R-->>S: webhook: Új sor létrehozása (Adatok + Szállítási cím)
    R-->>A: Stripe értesítés új vásárlásról
    Note over A, V: Onboarding (Manuális teendő)
    A->>V: Kézi számla kiállítása & Üdvözlő email küldése
    
    %% 2. Fázis
    Note over V: 2. Teljesítés szakasz (Napok/hetek telnek el)
    V->>V: Leküzdi a távot a Prédikálószéken
    V->>R: Teljesítés igazolása (GPX feltöltés / szelfi a Tally-n)
    R-->>A: Értesítés a teljesítés beküldéséről
    
    %% 3. Fázis
    Note over A, S: 3. Jóváhagyás & Értesítés
    A->>A: GPX fájl / kép manuális ellenőrzése
    A->>S: Beírja a teljesítési dátumot és a távot a Sheetbe
    A->>S: Futtatja a send_emails.py scriptet
    S-->>A: Lekérdezi a még emailre váró teljesítőket
    A->>V: Gratulációs email ("Nincs további teendőd, a címed rögzítve van")
    
    %% 4. Fázis
    Note over A, F: 4. Logisztika & Kézbesítés
    A->>A: Érem becsomagolása
    A->>F: Csomag feladása a rögzített automata címre
    Note over F, V: Szállítási idő (2-3 munkanap)
    F-->>V: SMS/Email értesítés: Megérkezett a csomag
    V->>F: Átveszi az érmet az automatából
    
    %% 5. Fázis
    Note over A, V: 5. Visszajelzés (Érem megérkezése után 3-5 nappal)
    A->>V: Feedback kérdőív kiküldése
    V->>R: Kitölti a Tally kérdőívet (Érem minősége, NPS skála stb.)
    R-->>S: Mentődik a visszajelzés a Sheetbe
```

### 🕒 Időbeli eloszlás és felelősségi körök:
*   **Vásárlási szakasz (1-3. lépések):** Valós idejű, másodpercek alatt lefutó automatizmusok.
*   **Onboarding szakasz (4-5. lépések):** 24 órán belül elvégzendő manuális teendőid (Számlázás + Üdvözlő levél).
*   **Kihívás teljesítése (6. lépés):** A legváltozóbb időtartam (akár 1-4 hét is lehet a túrázó tempójától függően).
*   **Jóváhagyási szakasz (7-11. lépések):** Általában heti 1-2 alkalommal végzett kötegelt feldolgozás (GPX ellenőrzés + Python script futtatás).
*   **Kézbesítési szakasz (12-15. lépések):** 2-3 napos logisztikai tranzitidő a Foxpost hálózatában.

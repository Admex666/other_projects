---
id: virtual-challenge
type: entity
name: Virtual Challenge
status: proposed
description: Location-independent distance challenge model allowing participants to log cumulative kilometers toward digital badges and optional medals.
related:
  - "[[strategic-positioning|Strategic Positioning]]"
  - "[[verified-challenge|Verified Challenge]]"
  - "[[ADR-009-strategic-ecosystem-pivot|ADR-009 Strategic Ecosystem Pivot]]"
---

# Entity: Virtual Challenge (Virtuális Kihívás)

## 1. Concept & Ecosystem Role

A Virtuális Kihívások a VitaSteps azon belépési pillérét képezik, amelyek nincsenek egyetlen konkrét földrajzi hegycsúcshoz vagy lokációhoz kötve.

### Célja:
* Megszólítani azokat, akik nem tudnak elutazni a Pilisbe vagy a Dunakanyarba.
* Lehetőséget biztosítani a mindennapos mozgásra (futás, kutyasétáltatás, napi séta, túrázás bárhol az országban).
* Alacsony vagy ingyenes belépési küszöböt nyújtani a VitaSteps világába.

---

## 2. MVP Specifikáció (Prioritás 2)

Az elv: **Validate first $\rightarrow$ integrate later.** Nem fejlesztünk hónapokig tartó automatikus API integrációkat addig, amíg a manuális verzió népszerűsége nincs igazolva.

```mermaid
flowchart LR
    REG["1. Regisztráció<br>(Kihívás választás pl. 100 km)"] --> LOG["2. Manuális Kilométer Napló<br>(Futó rögzíti a távokat)"]
    LOG --> PROG["3. Haladás & Progress Bar<br>(Virtuális térképes útvonal)"]
    PROG --> MILE["4. Digitális Jelvények<br>(25%, 50%, 75%, 100%)"]
    MILE --> FIN["5. Teljesítés & Opcionális Érem<br>(Prémium fizikai emlék rendelése)"]
```

### MVP Funkciók:
1. **Felhasználói fiók:** A futó/túrázó kiválasztja a célt (pl. *„Járd végig virtuálisan a Balaton-felvidéket – 100 km”*).
2. **Egyszerű manuális távbevitel:** Dátum + megtett kilométer rögzítése.
3. **Vizuális visszajelzés:** Dinamikus folyamatsáv (progress bar) és virtuális mérföldkövek.
4. **Digitális elismerés:** Megosztható jelvények (badges) és digitális oklevél.
5. **Opcionális fizikai érem:** A teljesítéskor vagy előzetesen megvásárolható prémium fémérem.

---

## 3. Későbbi Fázis (Prioritás 3 – Csak sikeres validáció után)
* Automatikus Garmin Connect és Strava webhook integráció.
* Valós idejű GPS aktivitás szinkronizáció.
* Részletes csapat- és ranglista versenyek.

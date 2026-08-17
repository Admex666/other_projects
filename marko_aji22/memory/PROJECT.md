# Marko 22nd Birthday Quest

## Overview
Mobil-first, gamifikált születésnapi küldetés webapp (PWA) Marko 22. születésnapjára. Az alkalmazás interaktív feladványokkal és navigációs mechanikákkal (GPS hideg-meleg, iránytű) vezeti végig a címzettet a közös ünnepi estéjén.

## Goals
- Egyedi, emlékezetes és játékos élmény nyújtása a hagyományos születésnapi meghívás helyett.
- Egyszerűen testreszabható konfiguráció (PLACEHOLDER helyszínek, opciók, jelszó könnyen cserélhető).
- Kiváló mobil élmény, offline-képes PWA működés, modern és prémium vizuális megjelenés.

## Core Flow
1. Teaser / Locked állapot (ajándékozáskor)
2. Quest feloldása (jelszóval)
3. Quest indítás
4. 1. Állomás: Bowling (fix program, kihívással)
5. 2. Állomás: Étkezés (választási lehetőséggel és navigációval)
6. 3. Állomás: Kocsmázás (hideg-meleg / iránytű lokációs kereséssel)
7. Lezárás / Completion screen (gratuláció, összefoglaló, ünneplés)

## Key Technologies
- React (Vite)
- Tailwind CSS / Vanilla CSS mikroanimációk & glassmorphism
- Lucide React ikonok & Canvas-Confetti
- Web Geolocation & DeviceOrientation API-k
- LocalStorage állapotmentés + Fejlesztői/tesztelő vezérlőpult

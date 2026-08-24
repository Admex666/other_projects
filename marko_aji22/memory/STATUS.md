# Current Status

## Status
- **Current Phase:** Updates & Persistence Complete
- **What is working:**
  - 1. Bowling állomás: Térkép link és "itt találkozunk" szövegek eltávolítva.
  - Állapotmentés: Teljes `localStorage` perzisztencia (beleértve a feloldott arcfelismerést és a kiválasztott állomásokat oldalfrissítés után is).
  - Visszalépés (Back navigation): Balra mutató nyílgomb a fejlécben, amivel bármikor vissza lehet lépni az előző állomásra.
  - Hangerő némítás: Eltávolítva a jobb felső némító gomb (a hangok mindig aktívak).
  - 3. Kocsma állomás: 5 rejtélyes jelige választó lista dummy koordinátákkal a `questConfig.ts`-ben, tiszta Hideg-Meleg vezérléssel:
    1. "az xG mindig nyüzsgő otthona" (A Grund)
    2. "Choose your character" (BarCraft Corvin)
    3. "nyugalom a káoszban" (7ker pub)
    4. "irány a romok közé" (Füge Udvar)
    5. "bort iszik és vizet prédikál" (Humbák Borkápolna)
  - Vercel-ready `vercel.json` SPA útválasztás.
- **Current focus:** Kész az élesítésre / koordináták manuális beírására.
- **Known blockers:** None.

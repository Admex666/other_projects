# 🎂 Markó 22nd Birthday Quest (PWA)

Mobil-first, gamifikált születésnapi küldetés webalkalmazás és PWA Markó 22. születésnapjára.

## 🚀 Főbb Jellemzők

- **Zárolt Teaser Képernyő:** Az ajándékozáskor a quest zárolva van, a projektgazda által átadott titkos jelszóval oldható fel.
- **Interaktív Keypad:** Érintőképernyő-barát numerikus és szöveges kódbevitel tactile hang- és rezgés-visszajelzéssel.
- **Többlépcsős Quest Folyamat:**
  1. 📋 **Misszió Briefing:** Szabályzat és party felszerelés lista.
  2. 🎳 **1. Állomás: Bowling Showdown:** Fix program találkozóhelyszín és interaktív strike-számláló kihívás.
  3. 🍔 **2. Állomás: Születésnapi Vacsora:** Kártyás étteremválasztó, azonnali leleplezéssel és térképes útvonaltervezéssel.
  4. 🍻 **3. Állomás: Titkos Kocsma Radar:** Valós idejű GPS hideg-meleg távolságmérő és iránytű-navigáció, feloldható nyomokkal.
  5. ⭐ **5. Állomás: Grand Finale:** Konfettieső, megszerzett kitüntetések és összefoglaló, megosztható eredménnyel.
- **🛠️ Fejlesztői / Tesztelő Panel (DevDrawer):** Bármikor tesztelhető asztali gépről is: azonnali ugrás bármelyik állomásra, GPS távolság és iránytű csúszka szimuláció, quest újraindítás.
- **Offline & PWA:** Telepíthető okostelefonra (Add to Home Screen), gyors betöltődés.

---

## ⚙️ Testreszabás & Helyszínek beállítása (`PLACEHOLDER`-ek)

A feladványok, a jelszó, az éttermi opciók és a GPS koordináták egyetlen fájlban találhatók és szerkeszthetők:
👉 [`src/config/questConfig.ts`](./src/config/questConfig.ts)

### Példa beállítások a `questConfig.ts`-ben:
- **Jelszó:** `unlockCode: '2208'`
- **Bowling helyszín:** `venueName`, `venueAddress`, `meetingTime`, `mapsUrl`
- **Étterem opciók:** `options: [{ title, category, description, venueName, venueAddress, mapsUrl }]`
- **Kocsma koordináták:** `targetLocation: { lat: 47.4984, lng: 19.0583 }`

---

## 💻 Fejlesztés és Futtatás

```bash
# Függőségek telepítése
npm install

# Helyi fejlesztői szerver indítása
npm run dev

# Production build készítése
npm run build
```

# 💡 Tanulság: Kétfázisú Letéti Zárolás (Immediate Escrow) és Kérdőív Skálák Szinkronizációja

> **Dátum:** 2026-11-12  
> **Kontextus:** V2 Specifikáció QA Validáció  
> **Érintett Rendszerek:** P2P Kereskedelmi Motor, Pre/Post-Game Felmérések, Központi Bank Átvétel  

---

## 1. Azonnali Letéti Modell (Immediate Escrow) vs. Kliensoldali Feltételezések

A P2P cseremotorok tervezésekor gyakori hiba a "pesszimista vagy optimista ellenőrzés csak az elfogadáskor":
- Ha egy felhasználó elküld egy ajánlatot, de az javakat nem vonja le azonnal a rendszer virtuális zárolásként (`escrowedItems`), akkor kettős költés (double-spending) vagy versengés alakulhat ki, amennyiben több partnernek küld párhuzamos ajánlatot ugyanarra az erőforrásra.
- **Megoldás:** A `sendTradeOffer` azonnal levonja a tételeket a szabad egyenlegből a tranzakció `escrowedItems` mezőjébe.
- **UI Következmény:** A felületen nem fordulhat elő az a hibaüzenet, hogy *"a feladó időközben elköltötte a fedezetet"*. Kizárólag a fogadó fél fedezethiánya hiúsíthatja meg az elfogadást.
- **Visszatérítés (Refund):** Ha a csere elutasításra (`REJECTED`), visszavonásra (`CANCELLED`), vagy a fázis lejártával kényszerített lezárásra (`EXPIRED`) kerül, a letét azonnal visszakerül a feladóhoz.

---

## 2. Kérdőív Metrikák Skálakonzisztenciája

A szociometriai és élménymérési adatok gyűjtésekor elengedhetetlen, hogy a mobil felület beviteli skálája (pl. 1–10 slider) és a backend adatbázis séma (pl. 1–5 Likert vs. 1–10 pont) megegyezzen:
- Ha a Debrief és Vezetői riportok 1–10 skálát és pont-deltát (`+2.2 pont`) jelenítenek meg, a kérdőív beviteli mezőinek is ezen a skálán kell rögzülniük.
- A nominációs mátrixoknál a felhasználói felület kártyalépéseit (Broker = más csapatok tagjai; Internal Enabler = saját csapat tagjai) 1:1-ben kell leképezni a JSON payload mezőneveire, megelőzve a felesleges vagy hiányzó űrlapmezőkből adódó validációs hibákat.

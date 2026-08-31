---
id: current-constraints
aliases:
  - CONSTRAINTS
type: strategic_concept
name: Constraints
status: active

description: A projekt aktuális technikai és üzleti korlátai.

related:
  - "[[CURRENT_STATE]]"
  - "[[PRIORITIES]]"
  - "[[honest-scraping-policy]]"
---

# 🛑 Constraints & Non-Goals

1. **Nem generálunk mesterséges / dummy járat- vagy szállásadatokat:** Ha a Kiwi vagy Cozycozy nem ad találatot, a felület nem találhat ki fiktív árakat (Honest Scraping Policy).
2. **Külső API Rate Limitek:** A Kiwi és egyéb aggregátorok felé a lekérdezéseket kíméletesen, párhuzamosítva és optimalizált sávokban végezzük.
3. **B2C fizetési átjáró (Stripe checkout) most nem cél:** A jelenlegi fázisban az utazási ajánlat előállítása és a partner linkek biztosítása a cél, közvetlen kártyás fizetési tranzakció lebonyolítása nélkül.
4. **Böngészőfüggetlen kliensoldali perzisztencia:** A kosárnak működnie kell session cookie-k és LocalStorage segítségével is.

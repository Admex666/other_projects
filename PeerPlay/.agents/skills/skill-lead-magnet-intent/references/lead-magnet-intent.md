---
id: lead-magnet-intent
type: learning
name: Lead Magnet Intent
status: active
description: Insights from the September 2026 lead magnet launch revealing that free resources filter high-intent prospects rather than merely converting cold leads.
code:
  - landing_predikalo1/api/capture-lead.js
  - landing_predikalo1/email_templates/lead_routes_kalandkonyv.html
related:
  - "[[growth-loop|Growth Loop]]"
  - "[[lead-nurturing-sequence|Lead Nurturing Sequence]]"
  - "[[customer-funnel|Customer Funnel]]"
---

# Learning: Lead Magnet Intent (Lead Mágnes Vásárlási Szándék Felismerés)

## 1. Context & Empirical Findings (2026. Szeptember)

2026 szeptemberében bevezettük a **Nagy-Kevély ingyenes túraútvonalak és digitális Kalandfüzet** lead mágnest (`api/capture-lead.js`).

### Eredmények:
* **Összes feliratkozás:** 20 rekord
* **Egyedi érdeklődők:** 17 fő
* **Közvetlen vásárlóvá vált (konvertált):** 5 fő
* **Lead $\rightarrow$ Purchase arány:** **~29.4%**

---

## 2. A Kulcs Stratégiai Felismerés

Első pillantásra a közel 30%-os lead-vásárlás konverzió kiemelkedőnek tűnik. Az alaposabb vizsgálat azonban egy mélyebb összefüggést tárt fel:

> **A lead mágnes nem feltétlenül a teljesen hideg, érdektelen embereket „győzi meg”. Sokkal inkább egy hatékony szűrő: azokat vonzza be és lépteti át az első küszöbön, akik már eleve érdeklődnek a VitaSteps élmény iránt, és a Kalandfüzet/GPX feloldásakor megerősítést kapnak.**

### Következtetés:
1. **Nem a puszta feliratkozó-szám a cél:** A hideg, irreleváns tömeggyűjtés helyett a **magas vásárlási szándékú érdeklődők** elérése az igazi érték.
2. **Életciklus-követés szükségessége:** A feliratkozókat nem szabad elengedni; a downstream viselkedésüket (letöltés, e-mail megnyitás, kattintás, checkout látogatás) mérni és automatizált szekvenciával ([[lead-nurturing-sequence|Lead Nurturing Sequence]]) kell támogatni.

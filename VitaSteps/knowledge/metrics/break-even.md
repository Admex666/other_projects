---
id: break-even
type: metric
name: Break-Even Tracking
status: active
description: A fix költségek (163k gyártás + könyvelés) megtérülésének számítása a termékenkénti fedezetekből.
source:
  type: code
  ref: landing_predikalo1/admin.html
depends_on:
  - "[[fixed-costs|Fixed Costs]]"
  - "[[unit-economics|Unit Economics]]"
  - "[[variable-costs|Variable Costs]]"
---

# Metric: Break-Even (Fedezeti Pont és Megtérülés)

A pénzügyi modell lényege, hogy minden kampánynál a termékenként megtermelt **nettó egységfedezet (Contribution Margin)** fokozatosan törleszti az induló **fix költségeket (Capex + Opex)**, amíg el nem érjük a nullszaldós (Break-Even) pontot:

$$\mathbf{\text{Break-Even Darabszám}} = \frac{\text{Összes Fix Költség (Gyártás + Könyvelés)}}{\text{Egységnyi Fedezet (Bevétel} - \text{Változó Költségek)}}$$

---

## 1. Számítási Példa egy 100 Érmes Kampányra

* **Fix Költségek ($\text{FC}$):**
  - Éremgyártás (100 db készlet előre kifizetve): **163 000 Ft**
  - 2 havi könyvelés (2 $\times$ 15 000 Ft): **30 000 Ft**
  - **Összes Fix Költség:** $\mathbf{193\,000 \text{ Ft}}$
* **Változó Költségek ($\text{VC}$ / db):**
  - Foxpost (1 250 Ft) + Stripe (170 Ft) + Számlázz.hu (35 Ft) + Csomagolás (120 Ft) + Átl. CAC (2 000 Ft) = **3 575 Ft / db**
* **Egységnyi Fedezet ($\text{CM}$ / db):**
  - $7\,990 \text{ Ft} - 3\,575 \text{ Ft} = \mathbf{4\,415 \text{ Ft / db}}$

$$\text{Break-Even Értékesítés} = \frac{193\,000 \text{ Ft}}{4\,415 \text{ Ft}} \approx \mathbf{44 \text{ db eladott érem}}$$

---

## 2. A Kampány Zónái (100 db-os limitnél)

```text
  0 db                  44 db (Break-Even)                  100 db (Sold Out)
   |───────────────────────▲───────────────────────────────────────|
     VISSZATERMELÉSI ZÓNA  │          TISZTA PROFIT ZÓNA
   (Fix költségek fedezése)│  (Minden további eladás tiszta haszon:
                           │   56 db × 4 415 Ft ≈ +247 000 Ft)
```

1. **1 – 44. eladott érem:** Visszahozza az előre befektetett 163 000 Ft-os gyártást és a havi könyvelési díjakat.
2. **45 – 100. eladott érem:** **Tiszta operating profit**, ami felhalmozható a következő érem gyártására vagy kivétre (~247 000 Ft nettó profit / 100 db-os sorozat).

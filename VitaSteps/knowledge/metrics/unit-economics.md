---
id: unit-economics
type: metric
name: Unit Economics
status: active
description: Termékenkénti bruttó bevétel, levonódó változó költségek és az így képződő nettó egységfedezet (Contribution Margin).
source:
  type: code
  ref: landing_predikalo1/admin.html
depends_on:
  - "[[dynamic-pricing|Dynamic Pricing]]"
  - "[[variable-costs|Variable Costs]]"
  - "[[stripe|Stripe]]"
  - "[[foxpost|Foxpost]]"
  - "[[szamlazz-hu|Számlázz.hu]]"
  - "[[cac|CAC]]"
used_by:
  - "[[break-even|Break-Even]]"
  - "[[fixed-costs|Fixed Costs]]"
---

# Metric: Unit Economics (Termékenkénti Fedezet)

A projekt pénzügyi alapelve, hogy minden egyes értékesített érem után egy **egységnyi fedezet (Contribution Margin)** keletkezik, amelyből a fix költségeket (pl. 163k gyártás, könyvelés) térítjük meg:

$$\mathbf{\text{Egységnyi Fedezet}} = \text{Bruttó Eladási Ár} - \sum \text{Változó Költségek}$$

---

## 1. Tételes Lebontás (1 db 7 990 Ft-os éremnél)

| Tétel | Típus | Összeg (Ft) | % | Megjegyzés |
| :--- | :--- | :--- | :--- | :--- |
| **Bruttó Bevétel** | **Bevétel** | **+7 990 Ft** | 100.0% | [[dynamic-pricing|Nevezési díj]] |
| **Foxpost automata szállítás** | Változó ktg | **-1 250 Ft** | 15.6% | [[foxpost|Foxpost API]] (1 141 Ft + ÁFA) |
| **Stripe kártyás tranzakció** | Változó ktg | **-170 Ft** | 2.1% | [[stripe|Stripe]] (1,5% + 50 Ft) |
| **Számlázz.hu autószámla** | Változó ktg | **-35 Ft** | 0.4% | [[szamlazz-hu|E-számla agent]] |
| **Csomagolás & kísérőkártya** | Változó ktg | **-120 Ft** | 1.5% | Párnázott boríték + nyomat |
| **Átlagos Meta CAC / CPA** | Változó ktg | **-2 000 Ft** | 25.0% | [[cac|Meta hirdetési költség]] |
| **Összes Változó Költség** | **Változó** | **-3 575 Ft** | 44.7% | [[variable-costs|Változó költségek]] |
| **Nettó Egységfedezet (Margin)** | **FEDEZET** | **+4 415 Ft** | **55.3%** | **Fix költségek törlesztésére és tiszta profitra** |

---

## 2. Több érmes / Visszatérő Vásárlói Bónusz
* **Összevont szállítás:** Ha egy vásárló 2 érmet vesz, vagy visszatérőként együtt kéri a korábbi érmével, a szállítási díj (1 250 Ft) csak egyszer merül fel $\rightarrow$ az egységfedezet **> 5 000 Ft / éremre** nő!
* **Organikus / Visszatérő vásárló (0 Ft CAC):** Hírlevélből vagy ajánlásból érkező vásárlónál az egységfedezet **> 6 400 Ft / érem**!

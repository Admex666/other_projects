---
id: fixed-costs
type: metric
name: Fixed Costs
status: active
description: Kampányonkénti és havi fix költségek (Capex & Opex), amelyeket a termékenkénti fedezetnek kell kitermelnie.
related:
  - "[[break-even|Break-Even]]"
  - "[[unit-economics|Unit Economics]]"
---

# Metric: Fixed Costs (Fix Költségek)

A fix költségek olyan tételek, amelyek **függetlenek az eladott darabszámtól** (a kampány indításához szükséges egyszeri beruházások és havi fenntartási díjak). A projekt pénzügyi modelljében ezeket a fix költségeket kell a termékenkénti **fedezeti összegből (Contribution Margin)** visszatermelni a break-even (nullszaldó) eléréséhez.

## 1. Kampány-szintű induló Capex (Egyszeri fix beruházás)
* **Éremgyártási és szerszámköltség (100 db):** **163 000 Ft** *(előre kifizetett fizikai készlet)*.
* **Grafikai tervezés & 3D mintaöntés:** Egyszeri indítási költség.

## 2. Havi szintű működési Opex (Fix fenntartási díjak)
* **Könyvelési díj:** **15 000 Ft / hó** *(pl. egy 2 hónapos futamidő alatt: $2 \times 15\,000 = 30\,000 \text{ Ft}$)*.
* **Infrastruktúra & Domén:** ~5 000 Ft / hó.

$$\text{Összes Fix Költség egy kampányra} \approx 163\,000 \text{ Ft (Gyártás)} + 30\,000 \text{ Ft (2 havi könyvelés)} = \mathbf{193\,000 \text{ Ft}}$$

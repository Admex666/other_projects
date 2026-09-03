---
id: design-system
aliases:
  - DESIGN_SYSTEM
type: governance
name: Design System & Tokens
status: active

description: Az Optivoya kanonikus dizájnrendszere, 3-as tipográfiai hierarchiája (Plus Jakarta Sans + Inter + JetBrains Mono), Material Symbols ikonográfiája és felületi tokenjei.

source:
  type: code
  ref: static/css/theme.css

related:
  - "[[DESIGN_PRINCIPLES]]"
  - "[[ANTI_AI_SLOP_POLICY]]"
  - "[[UX_PATTERNS]]"
  - "[[LEARNING-003-stitch-ui-design-principles]]"
---

# 📐 Design Governance: Design System & Tokens

A dizájnrendszer kanonikus forrása: [`static/css/theme.css`](file:///e:/Data/other_projects/dreamtrip/static/css/theme.css) és [`static/css/components.css`](file:///e:/Data/other_projects/dreamtrip/static/css/components.css).

---

## 🔤 1. Háromszintű Tipográfiai Rendszer (3-Tier Font Stack)

Minden felületen szigorúan el kell különíteni a három betűtípus szerepét:

1. **`--font-display` / `--font-headline`:** `'Plus Jakarta Sans', sans-serif`
   * **Szerep:** Főcímek, kártyacímek, szekciófejlécek (`font-weight: 600` vagy `700`).
   * **Stílus:** Feszes, negatív betűköz (`letter-spacing: -0.015em` vagy `-0.02em`), kompakt sormagasság.
2. **`--font-body` / `--font-label`:** `'Inter', -apple-system, sans-serif`
   * **Szerep:** Folyószöveg, magyarázatok, űrlapmezők címkéi, gombok, badge-ek (`font-weight: 400` vagy `500`).
   * **Stílus:** Kiváló olvashatóság kis méretben is, tiszta, nem lekerekített karakterforma.
3. **`--font-mono` / `--font-data`:** `'JetBrains Mono', monospace`
   * **Szerep:** Árak (HUF, EUR, USD), időpontok (`08:25`), időtartamok (`7h 50m`), PROMETHEE pontszámok, koordináták és kódok (`BUD`, `VIE`).
   * **Stílus:** Tabular számok, mérnöki pontosságú pénzügyi és analitikai megjelenés.

---

## 🎨 2. Kanonikus Szín- és Felületi Tokenek (Material Surface Hierarchy)

```css
:root {
  /* Brand: Mély fenyőzöld & Friss Chartreuse Akcentus */
  --primary: #003710;
  --primary-container: #1c4e24;
  --on-primary: #ffffff;
  --on-primary-container: #89bf89;
  
  --secondary: #406900;
  --secondary-container: #a7f540;
  --on-secondary-container: #436e00;

  /* Felületi Rétegződés (Material 3 Surfaces) */
  --bg-base: #f8faf8;
  --surface: #ffffff;
  --surface-container-low: #f2f4f2;
  --surface-container: #eceeec;
  --surface-container-high: #e6e9e7;
  
  /* Szövegek */
  --text-main: #191c1b;
  --text-secondary: #414940;
  --text-muted: #71796f;

  /* Vonalak & Szegélyek */
  --border-subtle: #e2e5e2;
  --border-strong: #c1c9bd;

  /* Tipográfia */
  --font-display: 'Plus Jakarta Sans', sans-serif;
  --font-body: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Rádiuszok */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
}
```

---

## 💎 3. Ikonográfiai Invariánsok
* **0% Emoji gombokon, badge-eken és tabokon.**
* Kizárólag **Material Symbols Outlined** vektoros ikonok vagy tiszta SVG-k használhatók.
* Ikonok skálája: `16px` (mikro-címkék), `18px` (gombok), `24px` (navigáció).

---

## 📱 4. Mobil Törésbiztossági Szabály (Mobile Wrap Invariant)
* Gombokon és füleken a mikro-szöveg hossza maximum 20 karakter lehet.
* Kétgombos vagy többgombos tab-választóknál mobilon tilos a merev `grid-template-columns: 1fr 1fr`, ha a szöveg nem fér el 1 sorban:
  * Használj `flex-wrap: wrap` elrendezést vagy tiszta, rövid szöveget (`Pontos dátum` vs. `Időablak`).

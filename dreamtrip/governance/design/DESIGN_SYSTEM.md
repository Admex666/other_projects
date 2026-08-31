---
id: design-system
aliases:
  - DESIGN_SYSTEM
type: governance
name: Design System & Tokens
status: active

description: A projekt kanonikus stílusrendszere, CSS változói és komponensosztályai.

source:
  type: code
  ref: static/css/theme.css

related:
  - "[[DESIGN_PRINCIPLES]]"
  - "[[UX_PATTERNS]]"
---

# 📐 Design Governance: Design System & Tokens

A dizájnrendszer kanonikus forrása: [`static/css/theme.css`](file:///e:/Data/other_projects/dreamtrip/static/css/theme.css) és [`static/css/components.css`](file:///e:/Data/other_projects/dreamtrip/static/css/components.css).

### 🎨 Kanonikus CSS Változók:
```css
:root {
  --primary: #0284c7;
  --primary-hover: #0369a1;
  --primary-light: #e0f2fe;
  
  --bg-app: #f8fafc;
  --bg-surface: #ffffff;
  --bg-surface-subtle: #f1f5f9;
  
  --text-main: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  
  --border-subtle: #e2e8f0;
  --border-strong: #cbd5e1;
  
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
}
```

### 🚫 Szabályok:
* Tilos egyedi, ad-hoc inline színeket (pl. `color: #432199`) használni a változók helyett.
* Minden új gomb és kártya a meglévő `.btn-primary`, `.btn-secondary`, `.advisor-main-card` vagy `.trip-pill-slot` osztályokat örökli.

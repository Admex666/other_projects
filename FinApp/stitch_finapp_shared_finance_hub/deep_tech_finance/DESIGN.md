---
name: Deep Tech Finance
colors:
  surface: '#0d141d'
  surface-dim: '#0d141d'
  surface-bright: '#333a44'
  surface-container-lowest: '#080f17'
  surface-container-low: '#151c25'
  surface-container: '#192029'
  surface-container-high: '#232a34'
  surface-container-highest: '#2e353f'
  on-surface: '#dce3f0'
  on-surface-variant: '#c8c4d7'
  inverse-surface: '#dce3f0'
  inverse-on-surface: '#2a313b'
  outline: '#928fa0'
  outline-variant: '#474554'
  surface-tint: '#c5c0ff'
  primary: '#c5c0ff'
  on-primary: '#2600a1'
  primary-container: '#8b80ff'
  on-primary-container: '#20008e'
  inverse-primary: '#5646d7'
  secondary: '#4de082'
  on-secondary: '#003919'
  secondary-container: '#00b55d'
  on-secondary-container: '#003e1c'
  tertiary: '#ffb3b0'
  on-tertiary: '#670211'
  tertiary-container: '#ea6767'
  on-tertiary-container: '#5b000d'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e4dfff'
  primary-fixed-dim: '#c5c0ff'
  on-primary-fixed: '#150067'
  on-primary-fixed-variant: '#3d28bf'
  secondary-fixed: '#6dfe9c'
  secondary-fixed-dim: '#4de082'
  on-secondary-fixed: '#00210c'
  on-secondary-fixed-variant: '#005227'
  tertiary-fixed: '#ffdad8'
  tertiary-fixed-dim: '#ffb3b0'
  on-tertiary-fixed: '#410006'
  on-tertiary-fixed-variant: '#881d24'
  background: '#0d141d'
  on-background: '#dce3f0'
  surface-variant: '#2e353f'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-margin: 20px
  gutter-md: 16px
  stack-sm: 4px
  stack-md: 12px
  stack-lg: 24px
---

## Brand & Style

This design system is engineered for a high-tech, mobile-first financial environment. The aesthetic is rooted in **Modern Corporate** minimalism with a "dark mode first" philosophy. It prioritizes clarity, precision, and trust through a disciplined use of space and high-contrast accents.

The visual narrative evokes a sense of "digital vault" security—utilizing deep, ink-like backgrounds contrasted with vibrant, glowing functional accents. It avoids unnecessary decoration, focusing instead on data density and legibility to empower both personal and business financial management.

## Colors

The palette is anchored by a three-tier grayscale system designed to create natural depth without relying on heavy shadows. 

- **Primary Accent (#7C6FFF):** Used for primary actions, branding elements, and active states.
- **Semantic Accents:** Success (Green) and Danger (Red) are used strictly for financial direction—Green for income/growth and Red for expenses/loss. Yellow is reserved for pending transactions or system warnings.
- **Hierarchy:** Text follows a strict contrast ratio, using Pure White (Off-white) for primary information and a muted gray for metadata and labels.

## Typography

The typography system relies exclusively on **Inter** to maintain a neutral, systematic, and highly legible interface. 

Tight letter-spacing is applied to larger display headings to create a "compact" tech feel, while labels utilize increased tracking and uppercase styling to differentiate them from body text. For financial figures (amounts), always use a medium or semi-bold weight to ensure they remain the primary focal point of any screen.

## Layout & Spacing

This design system uses an **8px linear scale** for all spacing and layout decisions. 

- **Mobile PWA:** Employs a fluid 4-column grid with 20px side margins and 16px gutters.
- **Desktop/Tablet:** Scales to a 12-column grid with a maximum content width of 1200px.
- **Rhythm:** Vertical stack spacing follows the 8px rule (8, 16, 24, 32, 48) to ensure a consistent vertical rhythm across long transaction lists and dashboard views.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** rather than traditional physical shadows. 

1. **Level 0 (Background):** The primary canvas (#0F0F14).
2. **Level 1 (Surface):** Default card and input backgrounds (#1A1A24).
3. **Level 2 (Elevated):** Hover states, modals, or featured cards (#242432).

Each elevated element must be defined by a **Low-contrast Outline** (rgba(255,255,255,0.08)). This hairline border replaces heavy shadows to maintain a "flat" yet structured high-tech appearance. Subtle backdrop blurs (12px) should be used for fixed navigation bars and overlaying menus.

## Shapes

The shape language is characterized by "Soft Geometric" forms. 

A standard radius of **16px (1rem)** is applied to all primary containers and cards to soften the technical aesthetic. Smaller elements like buttons and input fields follow a secondary radius of 8px. This creates a nested visual logic where internal components feel "housed" within their parent containers.

## Components

### Buttons
- **Primary:** Solid #7C6FFF background with white text. 8px border radius.
- **Secondary:** Transparent background with a 1px border of primary color.
- **Ghost:** No background, #9CA3AF text, used for less frequent actions.

### Cards & Containers
- **Standard Card:** #1A1A24 background, 16px radius, 1px subtle border.
- **Personal vs. Business:** Personal transactions use standard styling. Business transactions (VitaSteps) are distinguished by a subtle vertical 4px accent stripe on the left edge of the card using the primary purple color.

### Inputs
- **Field:** #1A1A24 background, 1px border. On focus, the border changes to #7C6FFF with a subtle 2px outer glow.
- **Labels:** Always positioned above the field in `label-md` style.

### Lists
- Transaction list items should have a minimum height of 72px to ensure touch-target safety on mobile.
- Use Lucide-style icons (1.5px stroke weight) in circular 40px containers with 10% opacity backgrounds of the icon's color.

### Chips & Tags
- Used for categories (e.g., "Food," "Invoicing"). These use a "Pill-shaped" radius with 10% opacity backgrounds to remain secondary to primary buttons.
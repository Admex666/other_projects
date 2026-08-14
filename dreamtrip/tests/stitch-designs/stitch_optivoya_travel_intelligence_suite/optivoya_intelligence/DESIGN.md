---
name: Optivoya Intelligence
colors:
  surface: '#FFFFFF'
  surface-dim: '#d8dad9'
  surface-bright: '#f8faf8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f2'
  surface-container: '#eceeec'
  surface-container-high: '#e6e9e7'
  surface-container-highest: '#e1e3e1'
  on-surface: '#191c1b'
  on-surface-variant: '#414940'
  inverse-surface: '#2e3130'
  inverse-on-surface: '#eff1ef'
  outline: '#71796f'
  outline-variant: '#c1c9bd'
  surface-tint: '#37693c'
  primary: '#003710'
  on-primary: '#ffffff'
  primary-container: '#1c4e24'
  on-primary-container: '#89bf89'
  inverse-primary: '#9dd49d'
  secondary: '#406900'
  on-secondary: '#ffffff'
  secondary-container: '#a7f540'
  on-secondary-container: '#436e00'
  tertiary: '#521a2c'
  on-tertiary: '#ffffff'
  tertiary-container: '#6e3042'
  on-tertiary-container: '#ed9aae'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b8f1b7'
  primary-fixed-dim: '#9dd49d'
  on-primary-fixed: '#002107'
  on-primary-fixed-variant: '#1f5026'
  secondary-fixed: '#aaf843'
  secondary-fixed-dim: '#8fdb24'
  on-secondary-fixed: '#102000'
  on-secondary-fixed-variant: '#2f4f00'
  tertiary-fixed: '#ffd9e0'
  tertiary-fixed-dim: '#ffb1c3'
  on-tertiary-fixed: '#3a071a'
  on-tertiary-fixed-variant: '#713244'
  background: '#f8faf8'
  on-background: '#191c1b'
  surface-variant: '#e1e3e1'
  border-subtle: '#E5E7EB'
  status-success: '#10B981'
  status-caution: '#F59E0B'
  status-alert: '#E11D48'
  text-main: '#08090A'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
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
  label-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '450'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  max-width: 1440px
---

## Brand & Style
The design system is engineered for **Optivoya**, a high-end B2B Travel Intelligence platform. The brand personality is rooted in precision, intelligence, and "Quiet Luxury"—conveying deep technical capability through a restrained, high-fidelity aesthetic. 

The design style is **Modern European SaaS**, blending **Minimalism** with subtle **Glassmorphism**. It prioritizes extreme clarity, generous whitespace, and high-precision typography. The emotional goal is to make complex logistical data feel effortless and curated. Visual interest is generated through micro-interactions and high-contrast accents rather than decorative elements.

## Colors
The palette is anchored by **Deep Emerald Forest**, providing an authoritative and sophisticated base. **Electric Lime** is used sparingly as a high-energy "laser" accent to draw attention to critical insights, CTA triggers, or data peaks. 

The background uses a **Crisp Warm Light Canvas** to avoid the clinical feel of pure white, while **Pure White** is reserved for elevated surface cards to create a clear "layering" effect. Borders should remain extremely subtle, acting as structural guides rather than decorative frames.

## Typography
The system utilizes a dual-font approach. **Plus Jakarta Sans** provides a modern, slightly geometric character for headlines and display elements, giving the brand a welcoming yet professional "tech-forward" voice. 

**Inter** is the workhorse for all UI and body text, chosen for its exceptional legibility in data-dense environments. For specialized travel intelligence metrics (coordinates, flight numbers, pricing), a secondary monospace font (JetBrains Mono) is suggested to reinforce the "intelligence" and "data-precision" aspect of the tool.

## Layout & Spacing
The layout follows a **12-column fluid grid** for the main content area, with a fixed-width sidebar for navigation (typically 240px). 

The spacing rhythm is built on a 4px baseline, but emphasizes large vertical gaps to maintain the "high-end" feel. 
- **Desktop:** 24px gutters, 40px outer margins.
- **Tablet:** 20px gutters, 24px outer margins.
- **Mobile:** 16px gutters, 16px outer margins.

Content is grouped into clear logical containers. Use "Inertia-based" layout patterns where primary intelligence cards have more breathing room (padding) than secondary utility lists.

## Elevation & Depth
Elevation is achieved through a combination of **Tonal Layers** and **Soft Ambient Shadows**. 

1.  **Canvas:** The base layer (#F8FAF8).
2.  **Surface:** White cards (#FFFFFF) with a 1px border (#E5E7EB) and a very soft, high-diffusion shadow (0px 4px 20px rgba(0,0,0,0.03)).
3.  **Overlay/Glass:** For modals and dropdowns, use a backdrop-blur (12px) with 80% opacity white, creating a "Glassmorphism" effect that maintains context.
4.  **Floating:** For high-priority action menus, use a dual-shadow approach: one crisp 1px shadow for definition and one deep, soft shadow for height.

## Shapes
The shape language is refined and approachable. The standard radius is **8px (0.5rem)** for primary containers and input fields. 

**Pill shapes** are strictly reserved for status badges, tags, and specific toggle switches to differentiate them from functional buttons. Interactive buttons should use the standard 8px radius to maintain a professional, structured appearance. Icons should utilize a consistent 1.5pt stroke weight with slightly rounded terminals.

## Components

- **Buttons:** Primary buttons use the Deep Emerald Forest (#1C4E24) with white text. Hover states should subtly darken the green. Secondary buttons use a transparent background with a subtle border.
- **Pill Badges:** Used for "Intelligence Insights." These use a light tint of the status colors (e.g., light lime background) with high-contrast text.
- **Input Fields:** Minimalist design with a 1px #E5E7EB border. On focus, the border transitions to Primary Emerald with a soft 2px glow.
- **Cards:** White background, 8px radius, subtle border. Content within cards should follow a strict hierarchy with Plus Jakarta Sans for the card title.
- **Data Visualizations:** Charts should utilize the Primary Emerald for the main data series and Electric Lime for "Optimal" or "Recommended" paths.
- **Navigation:** Vertical sidebar with a slight gray-to-white gradient and active states marked by a 2px Electric Lime vertical indicator.
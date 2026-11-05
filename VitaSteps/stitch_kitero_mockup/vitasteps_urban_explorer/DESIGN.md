---
name: VitaSteps Urban Explorer
colors:
  surface: '#111416'
  surface-dim: '#111416'
  surface-bright: '#37393c'
  surface-container-lowest: '#0c0e11'
  surface-container-low: '#191c1e'
  surface-container: '#1d2022'
  surface-container-high: '#282a2d'
  surface-container-highest: '#333537'
  on-surface: '#e2e2e5'
  on-surface-variant: '#c3caac'
  inverse-surface: '#e2e2e5'
  inverse-on-surface: '#2e3133'
  outline: '#8d9479'
  outline-variant: '#434933'
  surface-tint: '#a5d700'
  primary: '#ffffff'
  on-primary: '#273500'
  primary-container: '#bdf500'
  on-primary-container: '#526d00'
  inverse-primary: '#4d6700'
  secondary: '#ddfcff'
  on-secondary: '#00363a'
  secondary-container: '#00f1fe'
  on-secondary-container: '#006a70'
  tertiary: '#ffffff'
  on-tertiary: '#3c2f00'
  tertiary-container: '#ffe088'
  on-tertiary-container: '#7b6100'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#bdf500'
  primary-fixed-dim: '#a5d700'
  on-primary-fixed: '#151f00'
  on-primary-fixed-variant: '#394d00'
  secondary-fixed: '#74f5ff'
  secondary-fixed-dim: '#00dbe7'
  on-secondary-fixed: '#002022'
  on-secondary-fixed-variant: '#004f54'
  tertiary-fixed: '#ffe088'
  tertiary-fixed-dim: '#e9c349'
  on-tertiary-fixed: '#241a00'
  on-tertiary-fixed-variant: '#574500'
  background: '#111416'
  on-background: '#e2e2e5'
  surface-variant: '#333537'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 3.25rem
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 2.25rem
    fontWeight: '800'
    lineHeight: '1.15'
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.75rem
    fontWeight: '700'
    lineHeight: '1.25'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.5rem
    fontWeight: '700'
    lineHeight: '1.3'
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: '1.35'
    letterSpacing: -0.01em
  body-xl:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '400'
    lineHeight: '1.65'
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: '1.55'
    letterSpacing: 0.005em
  label-lg:
    fontFamily: Inter
    fontSize: 0.9375rem
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 0.8125rem
    fontWeight: '600'
    lineHeight: '1.35'
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: '700'
    lineHeight: '1.25'
    letterSpacing: 0.06em
  mono-metric:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-md: 1.5rem
  gutter-lg: 2rem
  margin: 1rem
  margin-md: 1.5rem
  margin-lg: 2.5rem
  space-2xs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
---

## Brand & Style

This design system defines an immersive, mobile-first web app experience for urban exploration and thematic city walks. The product marries technological precision with the sensory thrill of urban curiosity. It bridges the gap between a high-end night-mode utility and an editorial architectural walking journal.

### Personality & Emotional Resonance
- **Technological & Electric:** Sharp, luminescent accents over deep obsidian surfaces evoke late-night exploration, cyber-cartography, and contemporary city energy.
- **Authoritative & Premium:** High contrast, deliberate micro-interactions, and gold curation accents convey deep local knowledge and curated quality.
- **Effortless In-Motion Utility:** Outdoor readability under varying street lighting, immediate tactile feedback, and ergonomic thumb-zone controls.

### Design Style: Dark Technical Glassmorphism
The aesthetic combines deep obsidian layers (`#06080A`), frosted backdrop blurs (`backdrop-filter: blur(16px)`), micro-thin translucent borders (`rgba(255, 255, 255, 0.08)`), and targeted high-intensity luminescent glows (Electric Volt Lime and Neon Cyan). Tactile surfaces rely on layered dark surface elevations rather than heavy drop shadows, paired with generous rounded corners (`rounded-2xl` to `rounded-3xl`) for an organic, pocket-sized hardware feel.

## Colors

The palette is engineered specifically for outdoor nighttime and low-light street legibility while maintaining a luxurious, high-tech identity.

### Palette Architecture
- **Primary — Electric Volt Lime (`#C4FF00` / `#BFFF00`):** Reserved for primary navigation waypoints, key conversion CTAs, active route segments, and live GPS step status. Paired with soft ambient glow filters (`box-shadow: 0 0 20px rgba(196, 255, 0, 0.35)`). Text on Volt Lime surfaces must always be solid dark slate (`#06080A`) for WCAG AAA compliance.
- **Secondary — Neon Cyan (`#00F2FF` / `#38BDF8`):** Applied to telemetry data, turn-by-turn guidance lines, duration indicators, interactive map pins, and digital route badges.
- **Tertiary — Antique Gold (`#D4AF37` / `#F59E0B`):** Reserved for curated stop badges, verified guide seals, historical archive highlights, and premium tour tiers.
- **Base Neutral — Obsidian Canvas (`#06080A`):** The foundational backdrop across all viewports.
- **Surface Tier 1 — Deep Slate (`#0C0F15` to `#111418`):** Cards, carousels, and section containers.
- **Surface Tier 2 — Elevated Panel (`#12161E` to `#1A202C`):** Modals, sticky bottom action bars, bottom sheets, and floating HUD overlays.
- **Translucent Borders:**
  - Standard containment: `rgba(255, 255, 255, 0.08)`
  - Active waypoint / focused element: `rgba(191, 255, 0, 0.3)`
  - Interactive route node: `rgba(0, 242, 255, 0.25)`

### Functional Text Hierarchy
- **Text Primary:** `#F8FAFC` (High-contrast outdoor readability)
- **Text Secondary:** `#94A3B8` (Subtitles, metadata, timestamps)
- **Text Muted:** `#64748B` (Inactive states, divider legends)
- **Text On Lime:** `#06080A` (Heavy weight contrast)

## Typography

The type system balances architectural charisma with high-speed glanceability on mobile screens during movement.

### Hierarchy & Pairing
- **Headlines (Plus Jakarta Sans):** Geometric construction with friendly aperture curves. High tracking condensation (`-0.015em` to `-0.03em`) creates a punchy, magazine-grade visual rhythm on section headers, tour names, and waypoint titles.
- **Body & Captions (Inter):** Highly rationalized grotesque sans with open counters and robust x-height. Mobile body copy never drops below `16px` (`1rem`) for narrative paragraphs to prevent user eye fatigue when walking outdoors in ambient sunlight or deep shadows.
- **Micro-metrics & Badges (`label-sm`, `mono-metric`):** Uppercase with expanded letter-spacing (`0.06em`) for categorical tags (e.g., `TÖRTÉNELMI SÉTA`, `2.4 KM`, `45 PERC`).

## Layout & Spacing

A mobile-first fluid layout based on an 8-point spatial system, optimized for dynamic browser chrome, bottom gesture bars, and one-handed thumb interaction.

### Breakpoints & Layout Logic
- **Mobile (Base, `< 640px`):** Single column fluid container with `16px` (`1rem`) outer margins. Navigation bars and action drawers clamp to the viewport bottom with safe-area insets (`env(safe-area-inset-bottom)`).
- **Tablet (`640px – 1024px`):** 6-column fluid grid, `24px` gutters and margins. Splits into split-screen mode: sticky map viewport on the left, scrollable tour itinerary cards on the right.
- **Desktop (`> 1024px`):** 12-column grid capped at `1280px` max-width, `32px` gutters. Two-to-three pane dashboard layout (Navigation sidebar, map telemetry canvas, detailed story cards).

### Safe Areas & Tap Insets
All interactive targets feature an absolute minimum footprint of `44px × 44px` (recommended `48px`). On mobile devices, bottom sticky cards incorporate `space-lg` (`1.5rem`) buffer zones above device home indicators.

## Elevation & Depth

Visual hierarchy does not use harsh drop shadows; instead, it relies on darkness tiers, frosted glassmorphism, and targeted luminescent light leaks.

### Surface Tiers
1. **Tier 0 — Canvas (`#06080A`):** Pure background, map canvas base, full-screen audio player backdrop.
2. **Tier 1 — Base Panels (`#0C0F15`, `#111418`):** Primary cards, list clusters, tour detail intros. Uses a crisp outline: `1px solid rgba(255, 255, 255, 0.08)`.
3. **Tier 2 — Floating HUD & Overlays (`#12161E` with 85% opacity):** Frosted glass surfaces with `backdrop-filter: blur(16px) saturate(180%)`. Border: `1px solid rgba(255, 255, 255, 0.12)`.
4. **Tier 3 — Modals & Bottom Drawers (`#181D26`):** Deep ambient spread: `box-shadow: 0 12px 40px rgba(0, 0, 0, 0.8), 0 0 1px 1px rgba(255, 255, 255, 0.1)`.

### Luminescent Accents
- **Volt Active Glow:** `box-shadow: 0 0 24px -2px rgba(196, 255, 0, 0.35)` applied to primary FABs and active tour step nodes.
- **Cyan Waypoint Pulse:** `box-shadow: 0 0 16px -1px rgba(0, 242, 255, 0.4)` on GPS target pins and active audio wave visualizers.

## Shapes

The interface embraces oversized modern curves (`rounded-2xl` and `rounded-3xl`), evoking handheld gadgets and modern sports-tech hardware rather than rigid enterprise grids.

### Corner Radius Tokens
- **Micro UI (`rounded-sm` / `6px`):** Step checkmarks, micro-tooltips, status indicator dots.
- **Controls & Badges (`rounded-lg` / `12px` to `rounded-xl` / `16px`):** Form inputs, chips, tag pills, secondary buttons.
- **Cards & Panes (`rounded-2xl` / `20px` to `rounded-3xl` / `28px`):** Walk cards, stop preview panels, story carousels, audio player wrappers.
- **Full Shells (`rounded-full` / `9999px`):** Primary action buttons (CTAs), floating map action icons, audio play/pause controls, waypoint markers.

## Components

### Buttons & Interactive Controls
- **Primary CTA ("Indulás / Start Walk"):** Fully rounded (`rounded-full`), Electric Volt Lime (`#C4FF00`) background, deep obsidian bold typography (`#06080A`), minimum height `52px`. Hover/Active: Volt glow effect (`0 0 24px rgba(196, 255, 0, 0.45)`) and slight `scale(0.98)` tactile compression.
- **Secondary Ghost ("Útvonal megtekintése"):** Dark surface (`#111418`), border `1px solid rgba(255, 255, 255, 0.12)`, text `#F8FAFC`. Active state triggers `border-color: #00F2FF` with text `#00F2FF`.
- **Floating Map Action Button (FAB):** Circular (`48px × 48px`), elevated dark glass (`#12161E`, 80% opacity, `backdrop-filter: blur(12px)`), containing a high-contrast icon (Compass, Recenter, Audio).

### Cards
- **Tour Overview Card:** Background `#0C0F15`, border `1px solid rgba(255, 255, 255, 0.08)`, corner radius `24px`. Features an edge-to-edge 16:9 imagery slot topped with a dark gradient scrim (`linear-gradient(to top, #0C0F15, transparent)`). Houses tag pills for duration, distance, and historical era.
- **Waypoint Live Stop Card:** Elevated glass container anchored to the bottom sheet. Left side features the step sequence index (`01`, `02`) encased in a Neon Cyan circle; right side displays audio preview and direction trigger.

### Chips & Badges
- **Status Chip:** Height `28px`, padding `0 12px`, radius `full`.
  - *Volt Variant:* Border `rgba(196, 255, 0, 0.3)`, text `#C4FF00`, bg `rgba(196, 255, 0, 0.08)`.
  - *Cyan Variant:* Border `rgba(0, 242, 255, 0.3)`, text `#00F2FF`, bg `rgba(0, 242, 255, 0.08)`.
  - *Curated Gold Badge:* Border `rgba(212, 175, 55, 0.4)`, text `#D4AF37`, bg `rgba(212, 175, 55, 0.1)`. Features a miniature star/crest glyph.

### Form Inputs & Search Fields
- **Search & Street Filter:** Height `48px`, background `#111418`, border `1px solid rgba(255, 255, 255, 0.1)`, radius `16px`, text `#F8FAFC`. Placeholder in `#64748B`. Focus transitions border to `#00F2FF` with `box-shadow: 0 0 12px rgba(0, 242, 255, 0.2)`.

### Checkboxes & Segmented Controls
- **Audio/Walk Toggle:** Pill container in `#0C0F15` with an active sliding pill in `#1A202C` bordered by `rgba(255, 255, 255, 0.12)`. Active label illuminates in `#F8FAFC`.
- **Stop Complete Checkbox:** `24px × 24px` rounded circle. Unchecked: `border: 2px solid #64748B`. Checked: fill `#C4FF00`, inner glyph `#06080A`.

### Dedicated Walk & Audio Components
- **Audio Guide Bar:** Floating persistent bottom pill player (`64px` height). Progress line anchored directly along the top border in Electric Volt Lime. Features scrubbing controls, chapter title, and Play/Pause trigger (`44px` Volt button).
- **Turn-by-turn Telemetry Header:** Top-pinned HUD item displaying distance to next waypoint (e.g. `120 m`), dynamic directional arrow in Neon Cyan, and upcoming street instruction.
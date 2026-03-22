# Design System Strategy: The Folk-Punk Grimoire

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Living Grimoire."** 

This is not a static interface; it is a digital artifact that feels as though it were hand-inked on aged parchment and bound in weathered leather. Inspired by the iconic *Magyar népmesék* (Hungarian Folk Tales) animation style, we are blending traditional Kalocsai and Matyó floral motifs with a "folk-punk" edge—raw, tactile, and intentionally subversive.

To break the "template" look of modern SaaS, this system embraces **Organic Asymmetry**. Components should not always align to a rigid 1px grid; instead, they should feel like paper cutouts layered onto a storyteller’s desk. We use overlapping floral flourishes, deckled edges (simulated through masking), and high-contrast typography scales to create a sense of editorial depth and narrative urgency.

---

## 2. Colors: A Palette of Earth & Ink
Our palette is rooted in the "Dark Storybook" aesthetic. We move away from digital grays and toward deep, oxidized browns and vibrant, ritualistic reds.

*   **Primary (#ffb3ac / #a62121):** The "Blood & Rose." Use this for high-impact calls to action and critical narrative moments.
*   **Secondary (#acd0ac / #315035):** The "Forest Canopy." Used for positive states, growth-related metrics, and grounding elements.
*   **Tertiary (#f9bc50 / #734f00):** The "Gilded Ochre." Reserved for highlights, legendary-tier items, and warnings that demand a storybook flair.
*   **Surface Hierarchy:** Our `background` (#1a120d) is a deep, near-black umber. Use `surface-container-low` (#221a15) for large layout sections and `surface-container-high` (#322823) for interactive cards.

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to define sections. Sectioning must be achieved through background color shifts. A `surface-container-lowest` card sitting on a `surface` background provides all the separation required. If a boundary feels "lost," use a subtle background-blur or a tonal shift, never a stroke.

### The "Glass & Gradient" Rule
To inject "soul," CTAs should use a subtle vertical gradient from `primary` to `primary-container`. For floating UI elements (like a Grimoire navigation overlay), use semi-transparent `surface-variant` with a 12px backdrop-blur to create a "Smoked Glass" effect that allows the underlying floral textures to peek through.

---

## 3. Typography: The Chronicler’s Voice
We pair the brutalist utility of **Space Grotesk** with the literary elegance of **Newsreader**.

*   **Display & Headlines (Space Grotesk):** These are our "Punk" elements. Large, high-contrast, and unapologetic. Use `display-lg` (3.5rem) for chapter titles. The tight tracking and geometric shapes provide a modern, game-like urgency.
*   **Body & Titles (Newsreader):** These are our "Folk" elements. This serif typeface brings the warmth of a printed book. Use `body-lg` (1rem) for descriptions to ensure readability against textured backgrounds.
*   **The Calligraphic Accent:** While not in the token set, designers are encouraged to use hand-drawn Kalocsai motifs (birds, vines, flowers) as "Initial Caps" or paragraph breaks to reinforce the Hungarian animation heritage.

---

## 4. Elevation & Depth: Tonal Layering
In this system, "Elevation" is not a shadow; it is a **Physical Stacking**.

*   **The Layering Principle:** Depth is achieved by stacking `surface-container` tiers. Place a `surface-container-highest` card atop a `surface-container-low` background. This creates a soft, natural lift reminiscent of stacked paper.
*   **Ambient Shadows:** If a floating element (like a modal) requires a shadow, it must be "Ink-Bleed" style. Use the `on-surface` color at 6% opacity with a 32px blur and 12px Y-offset. It should feel like a soft glow of shadow, not a harsh drop-shadow.
*   **The "Ghost Border" Fallback:** If accessibility requires a border, use the `outline-variant` token at **20% opacity**. This creates a "watermark" effect rather than a hard line.
*   **Organic Shapes:** Avoid perfect circles for anything other than icons. Use the `xl` (1.5rem) or `lg` (1rem) roundedness tokens to mimic the soft, hand-cut edges of the *Magyar népmesék* style.

---

## 5. Components: Tactile Artifacts

### Buttons (The Wax Seals)
*   **Primary:** Solid `primary-container` background with `on-primary-container` text. Use `rounded-md` (0.75rem). Add a subtle "grain" texture overlay to make it feel like painted wood.
*   **Secondary:** `surface-container-high` with an `outline-variant` Ghost Border (20% opacity).

### Cards (The Parchment Scraps)
*   Forbid divider lines. Use `spacing-6` (2rem) of vertical white space to separate headers from content. 
*   **Corner Detail:** Integrate a Matyó floral motif SVG in the bottom-right corner of cards at 10% opacity using the `primary` color.

### Input Fields (The Scribe's Ledger)
*   **State:** Unfocused inputs should be `surface-container-lowest` with no border. On focus, transition to a `secondary` Ghost Border and a subtle `surface-bright` inner glow.

### Additional Component: The "Ornate Divider"
Standard horizontal rules are banned. Use a custom SVG component—a hand-drawn vine with a central flower (Kalocsai style)—that scales horizontally to separate major story beats or page sections.

---

## 6. Do’s and Don’ts

### Do:
*   **Embrace Asymmetry:** Offset images or text blocks by `spacing-2` to create a hand-placed feel.
*   **Layer Textures:** Use a subtle "parchment grain" SVG overlay on the `background` layer (opacity 3-5%).
*   **Use High-Contrast Type:** Pair a `display-sm` Space Grotesk header directly with a `body-md` Newsreader paragraph.

### Don't:
*   **Don't use 1px solid borders.** This kills the "storybook" immersion and makes the UI look like a generic dashboard.
*   **Don't use pure white or pure gray.** Every neutral must be tinted with the "parchment" warmth of our `surface` and `on-surface` tokens.
*   **Don't use standard easing.** For transitions, use "Heavy" easing (e.g., `cubic-bezier(0.34, 1.56, 0.64, 1)`) to give components a physical, springy "pop" as if they are being flipped in a book.

### Accessibility Note:
While we use "Ghost Borders" and tonal shifts, always ensure the contrast ratio between `on-surface` text and its `surface-container` background meets WCAG AA standards. The deep ochres and reds in this system are chosen specifically to maintain readability against the dark parchment background.
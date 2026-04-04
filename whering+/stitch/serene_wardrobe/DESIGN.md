```markdown
# Design System Document: The Editorial Curator

## 1. Overview & Creative North Star
**Creative North Star: "The Digital Atelier"**
This design system moves beyond the utility of a standard app and into the realm of a high-end, personal wardrobe curator. For the neurodivergent user, traditional interfaces are often noisy, rigid, and overwhelming. Our approach—**The Digital Atelier**—uses "Soft Minimalism" to create a sanctuary of focus. 

We break the "template" look by rejecting the rigid grid in favor of **intentional asymmetry and organic layering**. By utilizing overlapping elements and generous negative space, we reduce cognitive load, allowing the user to focus on one decision at a time. The experience should feel like flipping through a high-end fashion editorial: spacious, authoritative, yet deeply calming.

---

## 2. Colors: Tonal Depth & The "No-Line" Rule
The palette is a sophisticated blend of `surface` neutrals and supportive botanical and maritime tones. 

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections. Layout boundaries must be established solely through background color shifts. 
*   *Example:* A navigation rail or side panel should use `surface-container-low` against a `background` main stage.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—stacked sheets of fine paper.
*   **Base:** `surface` (#fbf9f5) – The canvas.
*   **Low-Level Grouping:** `surface-container-low` (#f5f4ee).
*   **Active/Hero Containers:** `surface-container-highest` (#e2e3db).
*   **Nesting:** Place a `surface-container-lowest` card inside a `surface-container` section to create a "recessed" or "lifted" feel without a single line of stroke.

### The "Glass & Gradient" Rule
To add "soul" to the minimalist aesthetic:
*   **Glassmorphism:** Use for floating action menus or top navigation bars. Apply `surface` at 70% opacity with a `24px` backdrop blur.
*   **Signature Textures:** Use a subtle linear gradient from `primary` (#546255) to `primary-container` (#d7e7d6) for "Confidence Score" cards to give them a premium, tactile presence.

---

## 3. Typography: The Editorial Voice
We utilize a dual-font system to balance character with extreme readability.

*   **Display & Headlines (Manrope):** Chosen for its geometric modernism. Large-scale `display-lg` and `headline-lg` should be used sparingly to anchor pages, providing a clear "You Are Here" signal for ADHD users.
*   **Body & UI (Inter):** The workhorse. Its tall x-height ensures clarity for "Rationale" text and outfit descriptions.
*   **Hierarchy as Focus:** Use `on-surface-variant` (#5d6059) for secondary labels to create a natural "visual quiet," reserving the high-contrast `on-surface` (#31332e) for the most critical information.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are often messy. We use **Ambient Depth**.

*   **The Layering Principle:** Stack `surface-container-lowest` on top of `surface-container-high` to create organic separation.
*   **Ambient Shadows:** For floating elements (like a FAB), use: `box-shadow: 0 12px 32px rgba(49, 51, 46, 0.06);`. The shadow color is a tint of our `on-surface` color, not pure black.
*   **The "Ghost Border":** If a separation is required for accessibility in high-sunlight modes, use `outline-variant` (#b1b3ab) at **15% opacity**. Never 100%.

---

## 5. Components

### Cards & Lists
*   **Rule:** Forbid divider lines. 
*   **Implementation:** Use `1.5rem` (xl) spacing between list items or shift the background color of alternating items to `surface-container-low`.
*   **Cards:** Use `lg` (1rem) corner radius. Content should have generous internal padding (`2rem`) to prevent visual "cramping."

### Buttons
*   **Primary:** Gradient of `primary` to `primary-dim`. `xl` (1.5rem) roundedness or full pill shape.
*   **Secondary:** `surface-container-highest` background with `on-surface` text. No border.
*   **Tertiary:** Text only, using `primary` color with a `label-md` weight.

### Confidence Score Indicators
*   **Styling:** A large `display-sm` number paired with a `tertiary_container` (#dafce6) background. This creates a high-contrast "Confidence Zone" that is immediately identifiable.

### Inputs & Selection
*   **Fields:** Use `surface-variant` (#e2e3db) as a solid background fill. When focused, transition the background to `surface-container-lowest` and add a `2px` `primary` underline.
*   **Chips:** For "Styles" or "Tags," use `md` (0.75rem) corners. Unselected: `surface-container`. Selected: `secondary` (#4d607f) with `on-secondary` text.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use asymmetrical layouts (e.g., a large photo on the left, staggered text blocks on the right) to create an editorial feel.
*   **Do** use "Soothing Feedback": Transitions should be timed at `300ms` with a `cubic-bezier(0.4, 0, 0.2, 1)` easing to feel organic, not mechanical.
*   **Do** prioritize "Rationale" text. Use `body-lg` to give the AI's explanation enough room to be read without squinting.

### Don’t
*   **Don’t** use pure black (#000000) for text. It causes "haloing" for many neurodivergent readers. Use `on-surface` (#31332e).
*   **Don’t** use "Shake" animations for errors. Use a gentle "Fade & Slide" with the `error` (#9f403d) color to avoid triggering sensory overstimulation.
*   **Don’t** use icons without labels unless they are universal (e.g., Home, Settings). For niche outfit planning icons, always pair with a `label-sm`.

---

## 7. Accessibility for Focus
To support ADHD/AuDHD users, this system employs **Information Scenting**. Critical paths (like "Plan Tomorrow's Outfit") are always anchored in the `primary` color, while "archive" or "history" functions use the neutral `outline` tokens to recede into the background. We never present more than three primary choices on a single screen level.```
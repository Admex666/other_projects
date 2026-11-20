---
name: anti-ai-slop-design
description: Human-crafted, editorial, and anti-AI-slop design principles for executive enterprise UI, ONA visualization, and client-facing interfaces.
---

# 🏛️ Anti-AI-Slop & Human-Crafted Executive Design Skill

## Purpose
Strictly eliminate generic AI-generated aesthetic ("AI Slop") across all web applications, BI dashboards, SVG charts, and executive reporting. Enforce human-crafted, editorial, and high-contrast design that commands respect from C-level executives and enterprise buyers.

---

## 🚫 The 6 Cardinal Sins of AI Slop (WHAT TO AVOID)

1. **Card-Within-Card Avalanche (`rounded-2xl border bg-slate-900`)**:
   - Do NOT wrap every single metric, sentence, chart, and button inside nested cards.
   - Excessive borders and nested containers clutter the eye and destroy vertical cadence.

2. **Neon & Sci-Fi Gradients in Dark Mode**:
   - Avoid pitch-black backgrounds with glowing neon green, violet, or cyan accents.
   - Looks like a toy crypto exchange or student hackathon project, not a credible management diagnostic.

3. **Emoji Crutch**:
   - NEVER use decorative emojis (`📊`, `🛑`, `⭐`, `💡`, `👑`, `🚀`) on headers, badges, or buttons.
   - Use clean, 1.25px stroke SVG icons (Lucide / Feather) or rely on pure typography.

4. **"Everything is Urgent" Syndrome**:
   - Avoid pulsating radar pings (`animate-ping`), glowing borders, and multiple bright primary badges competing for attention simultaneously.
   - A screen must have ONE clear hero focal point.

5. **Typographical Monoculture**:
   - Avoid generic, uniform sans-serif across all elements with the same letter-spacing and weight.
   - Lack of editorial contrast makes interfaces look cheap and unauthored.

6. **Over-explanatory Jargon & Fluff**:
   - Eliminate textbook-like explanations and fake metrics (e.g. simulated "termelt érték").
   - Replace with terse, factual diagnostic findings.

---

## 📐 Human-Crafted, Editorial Standards (WHAT TO DO)

1. **Editorial & Paper-Inspired Foundations**:
   - Canvas: Warm off-white or daylight canvas (`#F8FAFC`, `#FBFBFA`, `#FFFFFF`).
   - Structural division: Generous negative space (`whitespace`) and hairline divider rules (`1px solid #E2E8F0` or `#CBD5E1`) instead of nested boxes.

2. **Distinct Typographical Hierarchy (Editorial Pair)**:
   - **Headings & Narrative**: Premium serif or structured editorial groteszk (e.g. `Newsreader`, `Instrument Serif`, `Cabinet Grotesk`, `Plus Jakarta Sans` 700/800 with tight tracking `-0.03em`).
   - **Metrics, Timers & Data**: Monospaced tabular numerals (`JetBrains Mono`, `font-feature-settings: "tnum"`).
   - **Body & Labels**: Clean, neutral, high-legibility sans-serif with comfortable line height (`1.5`).

3. **Precise Technical Diagrams (Engineering Precision)**:
   - Network diagrams (ONA) should resemble clean architectural blueprints: fine slate-gray edges, subdued node fills, dark high-contrast typography.
   - Color is used surgically: only the critical pathology (e.g., the broken silo edge) receives an intentional accent (e.g., `#DC2626` red or `#0d4638` deep forest green).

4. **Calm, Executive Tone of Voice**:
   - Use direct, objective statements:
     - ❌ *"Lenyűgöző hálózati sebesség és szuper együttműködés!"*
     - ✅ *"Tranzakciós aszimmetria: Béta ↔ Gamma elutasítási arány 100%. Átfutási késleltetés: 3.8x."*

5. **Tactile Utility & 1-Click Affordance**:
   - Controls must look clearly interactive with subtle tactile depth (subtle border, light neutral background hover), never blending into static text.

---
name: skill-mobile-companion-hud-touch-and-inp
description: >-
  Use this skill when handling mobile companion hud touch & input patterns or related operational workflows in domain 'peerplay'. Synthesized from canonical operational learning: mobile_companion_hud_touch_and_input_patterns.md.
---

# Mobile Companion HUD Touch & Input Patterns

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `mobile_companion_hud_touch_and_input_patterns.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
# Mobile Companion HUD Touch & Input Patterns

## Problem
1. **Trade Numbers Stuck at Default 0**:
   - The HUD previously rendered hidden inputs (`type="hidden"`) alongside a static `<span>$0</span>`.
   - On mobile screens without keyboard input fields, users could not type values directly.
   - The +/- buttons had small touch targets (28px), and during pre-hydration or slow hydration phases, the DOM span had no ID, so clicks updated the hidden input value in memory without updating what was shown on screen.
   - When React hydrated, initial state `{ cash: 0, ... }` overwrote any pre-hydration input.

2. **Bank Sale Submit Request Blocked**:
   - The submit button was initially rendered with `disabled={loadingBank || expectedPayout === 0}`.
   - The pre-hydration script recalculated totals and updated displayed payouts, but failed to toggle `submitBtn.disabled = totalPayout <= 0;`.
   - As a result, the native DOM element retained `disabled=""`, completely blocking mobile user submissions.

## Solution & Architecture Rules
1. **Direct Numeric Input Fields**:
   - Replace hidden inputs and static spans with visible `<input type="number" min="0" placeholder="0" />` fields positioned between comfortable touch-sized (40x40px, `w-10 h-10`) `+` and `-` buttons.
   - Use `value={val === 0 ? '' : val}` with `placeholder="0"` so mobile users can tap into the field and type numbers without fighting leading zeros.
   - Ensure `onChange` parses `Math.max(0, parseInt(e.target.value, 10) || 0)` and clamps to limits (e.g. `myTeam.cashBalance`).

2. **Pre-Hydration & Post-Hydration State Sync**:
   - Both in React handlers and in progressive enhancement scripts, `stepOffered`, `stepRequested`, and `stepQuantity` read from the visible input element (`el.value`) as the base value before applying deltas, preventing drift between keyboard typing and button stepping.
   - On React mount (`useEffect`), sync any values already entered into the DOM (`qty-input-*`, `trade-offered-*`, `trade-requested-*`) into React state.
   - In form submissions, fallback sequentially: `document.getElementById()?.value` -> `fd.get()` -> React state.

3. **Dynamic Submit Button Unlock**:
   - In `recalcBankTotals()`, always manage `submitBtn.disabled = totalPayout <= 0;` alongside visual styling (`bg-emerald-600` vs disabled slate).
   - Listen to `input` and `change` events on all quantity fields to trigger immediate payout recalculation and submit button unlocking.


## Canonical Source of Truth
- Primary Reference: [mobile_companion_hud_touch_and_input_patterns.md](./references/mobile_companion_hud_touch_and_input_patterns.md)
- Original Location: `E:\Data\other_projects\PeerPlay\knowledge\learnings\mobile_companion_hud_touch_and_input_patterns.md`

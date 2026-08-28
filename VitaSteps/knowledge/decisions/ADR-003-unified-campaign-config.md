---
id: ADR-003
type: decision
name: ADR-003 Centralized Campaign Configuration Model
status: accepted
date: 2026-07-26
replaces: null
related:
  - "[[unified-campaign-config|Unified Campaign Config]]"
  - "[[campaign-predikaloszek|Campaign Predikaloszek]]"
  - "[[campaign-nagykevely|Campaign Nagy-Kevely]]"
---

# Decision: Centralized Campaign Configuration Model

## Context
When launching the second challenge (Nagy-Kevély), checkout and success pages risked code divergence and duplication across different folders.

## Decision
Unify all frontend checkout (`checkout.html`), success redirects (`siker.html`), customer portal (`portal.html`), and email templates to read dynamically from a single canonical JSON configuration: `config/campaigns.json`.

## Consequences
* New challenges can be launched in minutes by adding a single JSON block.
* Bugfixes and styling enhancements deploy globally across all campaigns simultaneously.

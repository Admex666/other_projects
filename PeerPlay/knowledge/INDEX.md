# 🗺️ Project Knowledge Index: Peerplay

This document is the root navigational index of persistent project truth.
Agents must consult this map before making architectural assumptions.

---

## 📚 Structure Overview

### 🎯 Core MVP Blueprint (Current Target)
- [MVP_PLAN_v2.md](file:///E:/Data/other_projects/PeerPlay/knowledge/MVP_PLAN_v2.md) — **Canonical MVP Plan & Technical Architecture for The Trading Game (V2)**, including system architecture, user flows, economic mechanics, data schema, 5-layer ONA reporting, and AI agent RACI matrix.
- [wireframes.html](file:///E:/Data/other_projects/PeerPlay/public/wireframes.html) — **Interactive HTML Prototype & Wireframes** demonstrating the Facilitator Console, Team Station Tablet, Player Mobile, and Debrief Diagnostics.

### 1. Facts (`knowledge/facts/`)
Canonical truth, runtime configuration, data sources, endpoints, ports, schemas.
- [screens_specification.md](file:///E:/Data/other_projects/PeerPlay/knowledge/facts/screens_specification.md) — **UI & Screen Architecture Specification** (14 screens across 4 suites: Facilitator, Team Station, Player Mobile, Workplace ONA & Debrief, Stripe Enterprise 1A system).
- [backend_contracts_and_state_machine.md](file:///E:/Data/other_projects/PeerPlay/knowledge/facts/backend_contracts_and_state_machine.md) — **Backend Contracts, State Machine & ACID Transaction Engine** (11 workshop phases, P2P Escrow locking, Bank commodity sales, Survey & ONA engine, Prisma schema).
- [qa_specifications_audit_report.md](file:///E:/Data/other_projects/PeerPlay/knowledge/facts/qa_specifications_audit_report.md) — **QA & Architectural Audit Report** for UI and Backend Specifications.
- [qa_milestone2_audit_report.md](file:///E:/Data/other_projects/PeerPlay/knowledge/facts/qa_milestone2_audit_report.md) — **Milestone 2 Frontend QA & Validation Report** (Pages, Server Actions, Design System, Zero Emoji).
- `canonical_sources.md` — Primary data stores and authoritative boundaries.

### 2. Architectural Decisions (`knowledge/decisions/`)
Numbered Architectural Decision Records (ADRs).
- [0001_mvp_pivot_trading_game_v2.md](file:///E:/Data/other_projects/PeerPlay/knowledge/decisions/0001_mvp_pivot_trading_game_v2.md) — Pivot to Hybrid Trading Game & 5-Layer ONA Platform (V2).
- [0002_design_system_stripe_enterprise.md](file:///E:/Data/other_projects/PeerPlay/knowledge/decisions/0002_design_system_stripe_enterprise.md) — Selection of Stripe Enterprise (1A) as the canonical UI/UX design system standard.

### 3. Inviolable Rules & Standards (`knowledge/rules/`)
Non-negotiable engineering principles, safety constraints, design system, and QA quality gates.
- [brand_and_design_guidelines.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/brand_and_design_guidelines.md) — **Canonical Stripe Enterprise Design System Tokens & Component Standards** (Colors, Plus Jakarta Sans & JetBrains Mono, Card Layouts).
- [human_centered_design_standards.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/human_centered_design_standards.md) — **Anti-"AI Slop" Design Principles**: Guidelines to eliminate generic AI aesthetics.
- `architecture_rules.md` — Module boundaries, transaction integrity (ACID), and forbidden cross-dependencies.

### 4. Operational Learnings (`knowledge/learnings/`)
Reusable operational insights, debugging solutions, and edge-case recoveries.
- [escrow_and_survey_contract_patterns.md](file:///E:/Data/other_projects/PeerPlay/knowledge/learnings/escrow_and_survey_contract_patterns.md) — Architectural patterns for Immediate Escrow reservation, survey scale alignment, batch inspection, and $k$-anonymity.

### 5. Context Layer (`context/`)
High-level overview and terminology.
- [overview.md](file:///E:/Data/other_projects/PeerPlay/context/overview.md) — Project mission and North Star.

---
name: skill-qa-validation-kern-martin-2025-202
description: >-
  Use this skill when handling qa validation certificate: kern martin nb i 2025-2027 profiles or related operational workflows in domain 'a_profil20261019'. Synthesized from canonical operational learning: qa_validation_kern_martin_2025_2027.md.
---

# QA Validation Certificate: Kern Martin NB I 2025-2027 Profiles

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `qa_validation_kern_martin_2025_2027.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
# QA Validation Certificate: Kern Martin NB I 2025-2027 Profiles

**Date:** 2026-11-16  
**Agent:** 🧪 QA / Validation Agent  
**Target Deck:** `presentations/Kern_Martin_NB1_profilok_2025_2027.pptx`  
**Target Figures:** `figures/kern_martin/*.png`  
**QA Validation Script:** `scratch/qa_validate_kern_martin.py`  
**Overall Verdict:** **100% PASS (32/32 checks passed)**

---

## 1. Summary of Verification Gates

### Gate 1: Presentation Structure & Layout
- **Slide Count:** Exactly 2 slides (PASS)
- **Slide Dimensions:** 13.333" x 7.500" (16:9 widescreen, exact match) (PASS)
- **Clipping / Out-of-Bounds:** 0 shapes outside slide boundary (PASS)
- **Overlaps:** 0 unintended bounding box collisions among layout elements (PASS)

### Gate 2: Data Correctness & Traceability
- **Dia 1 (2025/2026):**
  - Minutes: 513
  - Matches: 19
  - Shots: 4
  - Key Passes: 5
  - 1v1: 23
  - Pass Accuracy: 65.4% (159 / 243)
  - Pass Receptions: 194
  - Progressive passes received from own half: 32
  - *Result:* Exact match across raw CSV, `scratch/kern_martin_stats.json`, and presentation text.
- **Dia 2 (2026/2027):**
  - Minutes: 849
  - Matches: 13
  - Shots: 14
  - Key Passes: 8
  - 1v1: 26
  - Pass Accuracy: 74.6% (320 / 429)
  - Pass Receptions: 355
  - Progressive passes received from own half: 80
  - *Result:* Exact match across raw CSV, `scratch/kern_martin_stats.json`, and presentation text.

### Gate 3: Ternary Benchmark Midfielder Subsetting
- Full CSV contains all positions (715 rows total).
- 2025/2026 Midfielder sample: **171** players.
- 2026/2027 Midfielder sample: **139** players.
- Benchmark percentiles and ternary coordinates strictly filtered to `pos.str.contains('Midfielder')`.

### Gate 4: Figure Integrity
- All 6 figures exist, open cleanly in PIL, have high resolution (>= 800x600 px), and pure white `#FFFFFF` / clean borders.


## Canonical Source of Truth
- Primary Reference: [qa_validation_kern_martin_2025_2027.md](./references/qa_validation_kern_martin_2025_2027.md)
- Original Location: `E:\MLSZ\mlsz_reports\reports\tmp\A_profil20261019\knowledge\learnings\qa_validation_kern_martin_2025_2027.md`

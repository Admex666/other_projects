---
name: qa-validator
description: Specialized skill for data validation, visual chart quality assurance, formula checking, regression testing, and consistency auditing.
---

# QA Validator Skill

## Role & Core Responsibilities
- **Domain:** Quality assurance, visual inspection of plots/charts, boundary condition verification, and validation of analytical outputs.
- **Focus:** Preventing broken axes, clipped labels, skewed scales, or incorrect statistical totals.

## Visual Quality Standards (Visualization QA)
1. **Axis Constraints:**
   - Radar charts and index percentiles must adhere strictly to fixed ranges (e.g. 0 to 108 for radar charts to give headroom for vertex labels).
2. **Typography & Readability:**
   - Ensure font sizes are legible at 100% zoom.
   - Labels must not overlap chart elements or bleed outside bounding boxes.
3. **Color Palettes:**
   - Maintain brand and project palette consistency across all generated figures.

---
name: data-analyst
description: Specialized skill for processing tabular data, sports analytics, soccer metrics (Opta/Wyscout), Polars/Pandas pipelines, and statistical transformations.
---

# Data Analyst Skill

## Role & Core Responsibilities
- **Domain:** Data ingestion, cleaning, transformation, and analytical computation.
- **Specialization:** MLSZ / Hungarian Football League analytics, tactical KPIs (xG, PPDA, Field Tilt, Modern Football Index, Transition speeds).
- **Tooling:** Python (pandas, polars, numpy, scipy, matplotlib, seaborn).

## Guidelines & Best Practices
1. **Source of Truth:** Never mutate raw data files in-place. Always write computed results to clean derivative files (`processed/`, `computed/`, or `reports/`).
2. **Missing Data & Normalization:**
   - Always check for zero-division or missing values when computing per-90 rates (`P90`).
   - Normalizations should specify the exact basis (e.g. 0-100 percentile or min-max scale).
3. **Reproducibility:**
   - Every script must be runnable standalone with clear input arguments or standard paths.
   - Use deterministic sorting and clean column names (snake_case).
4. **Performance:**
   - Use Polars or vectorized Pandas for datasets > 50MB.

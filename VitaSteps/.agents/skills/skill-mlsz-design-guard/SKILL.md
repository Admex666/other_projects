---
name: skill-mlsz-design-guard
description: >-
  Use this skill whenever working on MLSZ (Hungarian Football Federation) reports,
  figures, charts, or presentations. Enforces visual style guides, color palettes,
  fonts, plot script reuse, and terminology rules (e.g. strict prohibition of 'meccs').
---

# MLSZ Design & Visualization Guardian Skill

## Purpose & Mandate
This skill ensures that all analytical artifacts, plots, charts, tables, and presentation decks
produced for MLSZ fully comply with official corporate design, color palettes, typography,
and linguistic standards.

## Inviolable Rules
1. **Linguistic Guardrail:** The word **"meccs" is STRICTLY FORBIDDEN!** Always use **"mérkőzés"** (or in justified context, "találkozó").
2. **Directory Sandbox:** Agents are only permitted to write output files inside `\reports\tmp\` (e.g. `\reports\tmp\<report_name>\`). All parent directories are Read-Only.
3. **No Unsolicited Text on Figures:** Do not invent explanatory paragraphs on plots. Clean title, labeled axes (via official `translations.json`), clean geometry, and data labels.
4. **Colors & Palettes:** Always use approved colors from `reports\definitions\assumptions\colors.json`.
5. **Plot Scripts:** Always check `reports\plot_scripts\` (`plot_bar.py`, `plot_pitch.py`, `plot_pizza.py`, `plot_scatter.py`, `radar_chart.py`) and reuse them.

## Verification Script
Run the automated compliance checker before submitting any MLSZ deliverable:
```powershell
python .agents/skills/skill-mlsz-design-guard/scripts/verify_mlsz_compliance.py <path_to_report_or_file>
```

## Canonical References
- `knowledge/rules/mlsz_design_rules.md`
- `reports/definitions/assumptions/translations.json`
- `reports/definitions/assumptions/colors.json`

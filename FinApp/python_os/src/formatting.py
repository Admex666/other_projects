import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Colour Palette
# ─────────────────────────────────────────────────────────────────────────────
DARK_BG   = '#1E293B'  # Slate 800
MID_BG    = '#334155'  # Slate 700
ACCENT    = '#10B981'  # Emerald 500
ACCENT2   = '#3B82F6'  # Blue 500
RED       = '#EF4444'  # Red 500
WARN      = '#F59E0B'  # Amber 500
AUTO_BG   = '#F1F5F9'  # Slate 100 – "do not edit"
WHITE     = '#FFFFFF'
TEXT_DARK = '#0F172A'
TEXT_LIGHT= '#FFFFFF'


def apply_formats(workbook):
    f = {}

    # ── Headers ──────────────────────────────────────────────────────────────
    f['header'] = workbook.add_format({
        'bold': True, 'font_color': TEXT_LIGHT, 'bg_color': DARK_BG,
        'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10,
    })

    # ── Editable (white) ─────────────────────────────────────────────────────
    f['edit'] = workbook.add_format({'bg_color': WHITE, 'border': 1, 'border_color': '#E2E8F0'})
    f['edit_num'] = workbook.add_format({
        'bg_color': WHITE, 'border': 1, 'border_color': '#E2E8F0', 'num_format': '#,##0',
    })
    f['edit_date'] = workbook.add_format({
        'bg_color': WHITE, 'border': 1, 'border_color': '#E2E8F0', 'num_format': 'yyyy-mm-dd',
    })

    # ── Auto / locked (light grey) ───────────────────────────────────────────
    f['auto'] = workbook.add_format({
        'bg_color': AUTO_BG, 'border': 1, 'border_color': '#CBD5E1',
        'font_color': '#64748B', 'locked': True,
    })
    f['auto_num'] = workbook.add_format({
        'bg_color': AUTO_BG, 'border': 1, 'border_color': '#CBD5E1',
        'font_color': '#64748B', 'num_format': '#,##0', 'locked': True,
    })

    # ── Dashboard KPI cards ──────────────────────────────────────────────────
    f['kpi_label'] = workbook.add_format({
        'bold': True, 'font_size': 11, 'bg_color': MID_BG,
        'font_color': TEXT_LIGHT, 'border': 1, 'valign': 'vcenter',
    })
    f['kpi_green'] = workbook.add_format({
        'bold': True, 'font_size': 13, 'bg_color': ACCENT, 'font_color': WHITE,
        'num_format': '#,##0', 'border': 1, 'align': 'right', 'valign': 'vcenter',
    })
    f['kpi_blue'] = workbook.add_format({
        'bold': True, 'font_size': 13, 'bg_color': ACCENT2, 'font_color': WHITE,
        'num_format': '#,##0', 'border': 1, 'align': 'right', 'valign': 'vcenter',
    })
    f['kpi_red'] = workbook.add_format({
        'bold': True, 'font_size': 13, 'bg_color': RED, 'font_color': WHITE,
        'num_format': '#,##0', 'border': 1, 'align': 'right', 'valign': 'vcenter',
    })
    f['kpi_neutral'] = workbook.add_format({
        'bold': True, 'font_size': 13, 'bg_color': MID_BG, 'font_color': WHITE,
        'num_format': '#,##0', 'border': 1, 'align': 'right', 'valign': 'vcenter',
    })
    f['section_title'] = workbook.add_format({
        'bold': True, 'font_size': 12, 'bg_color': DARK_BG, 'font_color': TEXT_LIGHT,
        'border': 1,
    })
    f['section_title_right'] = workbook.add_format({
        'bold': True, 'font_size': 12, 'bg_color': DARK_BG, 'font_color': TEXT_LIGHT,
        'border': 1,
    })

    # ── Settings section headers ─────────────────────────────────────────────
    f['settings_block'] = workbook.add_format({
        'bold': True, 'font_color': WHITE, 'bg_color': MID_BG, 'border': 1,
    })
    f['settings_val'] = workbook.add_format({
        'bg_color': '#F8FAFC', 'border': 1, 'border_color': '#E2E8F0',
    })

    return f

def apply_formats(workbook):
    formats = {}
    
    # Header format
    formats['header'] = workbook.add_format({
        'bold': True,
        'bg_color': '#1E293B', # Slate 800
        'font_color': '#FFFFFF',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # Editable cell (white bg)
    formats['editable'] = workbook.add_format({
        'bg_color': '#FFFFFF',
        'border': 1,
        'border_color': '#E2E8F0'
    })
    
    # Auto cell (light gray bg, locked)
    formats['auto'] = workbook.add_format({
        'bg_color': '#F1F5F9', # Slate 100
        'border': 1,
        'border_color': '#E2E8F0',
        'locked': True
    })
    
    # Auto cell numeric
    formats['auto_num'] = workbook.add_format({
        'bg_color': '#F1F5F9',
        'border': 1,
        'border_color': '#E2E8F0',
        'num_format': '#,##0',
        'locked': True
    })
    
    # Editable numeric
    formats['editable_num'] = workbook.add_format({
        'bg_color': '#FFFFFF',
        'border': 1,
        'border_color': '#E2E8F0',
        'num_format': '#,##0'
    })
    
    # Dashboard highlights
    formats['dash_title'] = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'bg_color': '#0F172A',
        'font_color': '#FFFFFF'
    })
    
    formats['dash_metric'] = workbook.add_format({
        'bold': True,
        'bg_color': '#10B981',
        'font_color': '#FFFFFF',
        'num_format': '#,##0',
        'border': 1
    })
    
    return formats

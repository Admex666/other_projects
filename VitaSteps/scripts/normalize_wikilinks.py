#!/usr/bin/env python3
import os
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, 'knowledge')

# Map from names / variations to actual file stems
stem_map = {}
for dirpath, _, filenames in os.walk(KNOWLEDGE_DIR):
    for f in filenames:
        if f.endswith('.md'):
            stem = os.path.splitext(f)[0]
            stem_map[stem.lower()] = stem
            # Variations
            stem_map[stem.replace('-', ' ').lower()] = stem
            stem_map[stem.replace('_', ' ').lower()] = stem

# Custom aliases
stem_map['admin'] = 'admin-panel'
stem_map['admin panel'] = 'admin-panel'
stem_map['campaign predikaloszek'] = 'campaign-predikaloszek'
stem_map['campaign nagy-kevely'] = 'campaign-nagykevely'
stem_map['campaign nagy kevely'] = 'campaign-nagykevely'
stem_map['szamlazz.hu'] = 'szamlazz-hu'
stem_map['adr-001'] = 'ADR-001-supabase-migration'
stem_map['adr-002'] = 'ADR-002-webhook-free-payment'
stem_map['adr-003'] = 'ADR-003-unified-campaign-config'
stem_map['adr-004'] = 'ADR-004-consolidated-shipping'
stem_map['adr-005'] = 'ADR-005-strict-rls-security'

WIKILINK_RE = re.compile(r'\[\[(.*?)\]\]')

for dirpath, _, filenames in os.walk(KNOWLEDGE_DIR):
    for f in filenames:
        if not f.endswith('.md'):
            continue
        path = os.path.join(dirpath, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        def replace_link(match):
            raw = match.group(1)
            parts = raw.split('|')
            target = parts[0].strip()
            alias = parts[1].strip() if len(parts) > 1 else None
            
            clean_key = target.lower().strip()
            if clean_key in stem_map:
                actual_stem = stem_map[clean_key]
                if alias:
                    return f"[[{actual_stem}|{alias}]]"
                elif actual_stem.lower() != target.lower():
                    return f"[[{actual_stem}|{target}]]"
                else:
                    return f"[[{actual_stem}]]"
            return f"[[{raw}]]"
            
        new_content = WIKILINK_RE.sub(replace_link, content)
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new_content)
            print(f"Normalized links in: {f}")

print("Done normalizing wikilinks for Obsidian!")

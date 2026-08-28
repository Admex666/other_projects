#!/usr/bin/env python3
"""
validate_knowledge_graph.py
Validates the integrity, frontmatters, wikilinks, and code references
across the VitaSteps AI-Native Project Knowledge Graph.
"""

import os
import re
import sys
import yaml

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, 'knowledge')

WIKILINK_RE = re.compile(r'\[\[(.*?)\]\]')

def load_nodes():
    nodes = {}
    errors = []
    
    for dirpath, _, filenames in os.walk(KNOWLEDGE_DIR):
        for f in filenames:
            if not f.endswith('.md'):
                continue
            path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(path, ROOT_DIR).replace('\\', '/')
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            
            # Extract frontmatter
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except Exception as e:
                        errors.append(f"YAML Syntax error in {rel_path}: {e}")
            
            node_id = frontmatter.get('id')
            node_name = frontmatter.get('name')
            node_type = frontmatter.get('type')
            
            if not node_id:
                errors.append(f"Missing 'id' in frontmatter: {rel_path}")
            if not node_type and f != 'INDEX.md':
                errors.append(f"Missing 'type' in frontmatter: {rel_path}")
            if node_id in nodes:
                errors.append(f"Duplicate node id '{node_id}' in {rel_path}")
            
            nodes[node_id or f] = {
                'path': rel_path,
                'name': node_name or node_id or f,
                'frontmatter': frontmatter,
                'content': content
            }
            
    return nodes, errors

def validate_links_and_code(nodes):
    errors = []
    
    # Set of known link targets (names and ids)
    valid_targets = set()
    for n in nodes.values():
        valid_targets.add(n['name'].lower().strip())
        if n['frontmatter'].get('id'):
            valid_targets.add(n['frontmatter']['id'].lower().strip())
        # Also basename
        base = os.path.splitext(os.path.basename(n['path']))[0].lower().strip()
        valid_targets.add(base)
    
    for n_id, n_data in nodes.items():
        rel_path = n_data['path']
        content = n_data['content']
        
        # Check wikilinks
        for match in WIKILINK_RE.findall(content):
            clean_link = match.split('|')[0].lower().strip()
            if clean_link not in valid_targets:
                errors.append(f"Broken wikilink [[{match}]] in {rel_path}")
                
        # Check code references in frontmatter
        code_refs = n_data['frontmatter'].get('code', [])
        if isinstance(code_refs, str):
            code_refs = [code_refs]
        for c_ref in code_refs:
            # Check relative to landing_predikalo1 or root
            abs_c1 = os.path.join(ROOT_DIR, c_ref)
            abs_c2 = os.path.join(ROOT_DIR, 'landing_predikalo1', c_ref)
            if not os.path.exists(abs_c1) and not os.path.exists(abs_c2):
                # Warning only if directory or pattern
                if not any(char in c_ref for char in ['*', '?']):
                    print(f"  [Notice] Code reference not directly found: '{c_ref}' in {rel_path}")

    return errors

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("=" * 60)
    print(" [VALIDATION] VitaSteps AI-Native Project Knowledge Graph")
    print("=" * 60)
    
    nodes, load_errors = load_nodes()
    print(f"Total Knowledge Nodes scanned: {len(nodes)}")
    
    link_errors = validate_links_and_code(nodes)
    
    all_errors = load_errors + link_errors
    
    if all_errors:
        print(f"\n[ERROR] Validation FAILED with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"  * {err}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Validation PASSED! 0 broken wikilinks, all YAML frontmatters valid.")
        print("Nodes distribution:")
        types = {}
        for n in nodes.values():
            t = n['frontmatter'].get('type', 'other')
            types[t] = types.get(t, 0) + 1
        for t, count in sorted(types.items()):
            print(f"  * {t:<15}: {count} node(s)")
        print("=" * 60)

if __name__ == '__main__':
    main()

import os
import re
import sys
import yaml

KNOWLEDGE_DIR = os.path.abspath("knowledge")
CONTEXT_DIR = os.path.abspath("context")

VALID_TYPES = {
    "entity", "concept", "process", "system", 
    "metric", "decision", "learning", "operation"
}

VALID_STATUSES = {
    "active", "draft", "deprecated", "superseded", "archived", "accepted"
}

def parse_frontmatter(content):
    content = content.lstrip("\ufeff\r\n \t")
    if not content.startswith("---"):
        return None, content
    # Remove initial ---
    after_first = content[3:].lstrip("\r\n")
    if "---" not in after_first:
        return None, content
    parts = after_first.split("---", 1)
    fm_str = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    try:
        data = yaml.safe_load(fm_str)
        if isinstance(data, dict):
            return data, body
        return None, content
    except Exception as e:
        return None, content

def find_all_markdown_files():
    files = []
    for root_dir in [KNOWLEDGE_DIR, CONTEXT_DIR]:
        if not os.path.exists(root_dir):
            continue
        for root, _, filenames in os.walk(root_dir):
            for fn in filenames:
                if fn.endswith(".md"):
                    files.append(os.path.join(root, fn))
    return files

def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 80)
    print("KNOWLEDGE GRAPH VALIDATOR — OPTIVOYA")
    print("=" * 80)

    md_files = find_all_markdown_files()
    print(f"Found {len(md_files)} documentation / knowledge markdown files.")

    nodes_by_id = {}
    nodes_by_name = {}
    nodes_by_basename = {}
    errors = []
    warnings = []

    # 1. Parse all nodes
    for fpath in md_files:
        rel_path = os.path.relpath(fpath, os.getcwd())
        basename = os.path.splitext(os.path.basename(fpath))[0]
        nodes_by_basename[basename.lower()] = rel_path

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip INDEX.md from mandatory frontmatter
        if os.path.basename(fpath) == "INDEX.md":
            continue

        frontmatter, body = parse_frontmatter(content)
        if not frontmatter:
            warnings.append(f"[{rel_path}] Missing or invalid YAML frontmatter.")
            continue

        node_id = str(frontmatter.get("id", "")).strip()
        node_type = str(frontmatter.get("type", "")).strip()
        node_name = str(frontmatter.get("name", "")).strip()
        node_status = str(frontmatter.get("status", "")).strip()

        if not node_id:
            errors.append(f"[{rel_path}] Missing 'id' in frontmatter.")
        elif node_id in nodes_by_id:
            errors.append(f"[{rel_path}] Duplicate node ID: '{node_id}' (already in {nodes_by_id[node_id]['file']}).")
        else:
            nodes_by_id[node_id] = {"file": rel_path, "meta": frontmatter, "content": content}

        if node_name:
            nodes_by_name[node_name.lower()] = rel_path
            # Also add hyphenated version
            slug = node_name.lower().replace(" ", "-")
            nodes_by_name[slug] = rel_path

        if node_type not in VALID_TYPES:
            errors.append(f"[{rel_path}] Invalid type '{node_type}'. Expected one of: {VALID_TYPES}")

        if node_status and node_status not in VALID_STATUSES:
            warnings.append(f"[{rel_path}] Unknown status '{node_status}'.")

    print(f"Parsed {len(nodes_by_id)} unique knowledge nodes.")

    # 2. Check all wikilinks [[...]]
    link_pattern = re.compile(r'\[\[(.*?)\]\]')
    checked_links = 0

    for fpath in md_files:
        rel_path = os.path.relpath(fpath, os.getcwd())
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        for match in link_pattern.findall(content):
            checked_links += 1
            target = match.strip()
            # Clean display label if present [[target|label]]
            if "|" in target:
                target = target.split("|")[0].strip()

            target_clean = target.lower()
            target_slug = target_clean.replace(" ", "-")

            found = (
                target_clean in nodes_by_basename or
                target_slug in nodes_by_basename or
                target in nodes_by_id or
                target_clean in nodes_by_id or
                target_clean in nodes_by_name or
                target_slug in nodes_by_name
            )

            if not found:
                errors.append(f"[{rel_path}] Broken wikilink: [[{target}]] -> Target node not found.")

    print(f"Verified {checked_links} wikilinks across graph.")

    # Output results
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNINGS:")
        for w in warnings:
            print("  -", w)

    if errors:
        print(f"\n❌ {len(errors)} ERRORS:")
        for e in errors:
            print("  -", e)
        print("\nGraph validation FAILED.")
        sys.exit(1)
    else:
        print("\n" + "=" * 80)
        print("✅ ALL GRAPH NODES, IDS, TYPES, AND WIKILINKS ARE 100% VALID!")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    main()

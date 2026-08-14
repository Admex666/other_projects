#!/usr/bin/env python3
"""
Fetch and convert public Notion pages to Markdown.
Usage:
    python scripts/fetch_notion.py [URL_OR_PAGE_ID] [--output OUTPUT_FILE]
"""

import sys
import os
import re
import json
import requests
from typing import Dict, Any, List, Optional

# Force UTF-8 on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def extract_page_id(url_or_id: str) -> str:
    """Extracts 32-character Notion page ID and formats it with hyphens."""
    clean = url_or_id.split("?")[0].split("#")[0]
    match = re.search(r"([0-9a-fA-F]{32})", clean)
    if match:
        raw_id = match.group(1).lower()
        return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
    
    match_dashes = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", clean)
    if match_dashes:
        return match_dashes.group(1).lower()
    
    raise ValueError(f"Could not extract a valid Notion page ID from: {url_or_id}")

def get_block_value(block_wrapper: Any) -> Optional[Dict]:
    if not block_wrapper:
        return None
    val = block_wrapper.get("value", {})
    if "value" in val:
        return val["value"]
    return val

def format_rich_text(prop_title: Optional[List]) -> str:
    """Converts Notion rich text array to Markdown."""
    if not prop_title:
        return ""
    result = []
    for chunk in prop_title:
        if not chunk:
            continue
        text = chunk[0]
        if len(chunk) > 1 and chunk[1]:
            for fmt in chunk[1]:
                tag = fmt[0]
                if tag == "b":
                    text = f"**{text}**"
                elif tag == "i":
                    text = f"*{text}*"
                elif tag == "c":
                    text = f"`{text}`"
                elif tag == "s":
                    text = f"~~{text}~~"
                elif tag == "a":
                    text = f"[{text}]({fmt[1]})"
                elif tag == "_":
                    text = f"<u>{text}</u>"
        result.append(text)
    return "".join(result)

def fetch_all_blocks(page_id: str) -> Dict[str, Any]:
    """Fetches all Notion blocks recursively for a public page."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    chunk_url = "https://www.notion.so/api/v3/loadCachedPageChunk"
    chunk_data = {
        "page": {"id": page_id},
        "limit": 100,
        "cursor": {"stack": []},
        "chunkNumber": 0,
        "verticalColumns": False
    }
    
    res = requests.post(chunk_url, json=chunk_data, headers=headers)
    if res.status_code != 200:
        raise RuntimeError(f"Failed to fetch initial page chunk: HTTP {res.status_code}")
    
    record_map = res.json().get("recordMap", {})
    blocks = {k: get_block_value(v) for k, v in record_map.get("block", {}).items()}
    
    # Recursively fetch missing child blocks
    sync_url = "https://www.notion.so/api/v3/syncRecordValues"
    while True:
        missing = set()
        for b in blocks.values():
            if b and "content" in b:
                for child_id in b["content"]:
                    if child_id not in blocks or blocks[child_id] is None:
                        missing.add(child_id)
        if not missing:
            break
        
        # Batch in chunks of 100
        missing_list = list(missing)
        for i in range(0, len(missing_list), 100):
            batch = missing_list[i:i+100]
            sync_data = {"requests": [{"table": "block", "id": m_id, "version": -1} for m_id in batch]}
            sync_res = requests.post(sync_url, json=sync_data, headers=headers)
            if sync_res.status_code == 200:
                for k, v in sync_res.json().get("recordMap", {}).get("block", {}).items():
                    blocks[k] = get_block_value(v)
            else:
                break
                
    return blocks

def render_blocks_to_markdown(blocks: Dict[str, Any], root_id: str, depth: int = 0) -> str:
    """Renders Notion block tree into Markdown format."""
    lines = []
    root = blocks.get(root_id)
    if not root:
        return ""
    
    # If this is the root page block
    if depth == 0 and root.get("type") == "page":
        title = format_rich_text(root.get("properties", {}).get("title", []))
        icon = root.get("format", {}).get("page_icon", "")
        if icon:
            lines.append(f"# {icon} {title}\n")
        else:
            lines.append(f"# {title}\n")
            
        children = root.get("content", [])
        for child_id in children:
            child_md = render_block(blocks, child_id, depth=0)
            if child_md:
                lines.append(child_md)
        return "\n".join(lines)
    
    return render_block(blocks, root_id, depth=depth)

def render_block(blocks: Dict[str, Any], block_id: str, depth: int = 0) -> str:
    block = blocks.get(block_id)
    if not block:
        return ""
    
    b_type = block.get("type", "")
    props = block.get("properties", {})
    text = format_rich_text(props.get("title", []))
    children = block.get("content", [])
    
    indent = "  " * depth
    out = []
    
    if b_type == "header":
        out.append(f"\n## {text}\n")
    elif b_type == "sub_header":
        out.append(f"\n### {text}\n")
    elif b_type == "sub_sub_header":
        out.append(f"\n#### {text}\n")
    elif b_type == "text":
        out.append(f"{text}" if text else "")
    elif b_type == "bulleted_list":
        out.append(f"{indent}- {text}")
    elif b_type == "numbered_list":
        out.append(f"{indent}1. {text}")
    elif b_type == "to_do":
        checked = props.get("checked", [["No"]])[0][0] == "Yes"
        box = "[x]" if checked else "[ ]"
        out.append(f"{indent}- {box} {text}")
    elif b_type == "toggle":
        out.append(f"\n<details>\n<summary>{text}</summary>\n")
    elif b_type == "quote":
        out.append(f"> {text}")
    elif b_type == "callout":
        icon = block.get("format", {}).get("page_icon", "💡")
        out.append(f"> {icon} {text}")
    elif b_type == "divider":
        out.append("\n---\n")
    elif b_type == "code":
        lang = props.get("language", [[""]])[0][0].lower()
        out.append(f"```{lang}\n{text}\n```")
    elif b_type == "table_row":
        cells = [format_rich_text(props.get(k, [])) for k in sorted(props.keys())]
        out.append("| " + " | ".join(cells) + " |")
    elif b_type in ["column_list", "column"]:
        pass # Handle children directly
    elif b_type == "page":
        out.append(f"\n📄 **{text}**\n")
    else:
        if text:
            out.append(f"{text}")
            
    # Process children
    for child_id in children:
        child_depth = depth + 1 if b_type in ["bulleted_list", "numbered_list", "to_do", "toggle"] else depth
        child_md = render_block(blocks, child_id, depth=child_depth)
        if child_md:
            out.append(child_md)
            
    if b_type == "toggle":
        out.append("\n</details>\n")
        
    return "\n".join(out)

def main():
    # 1. Determine URL or Page ID
    target = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        target = sys.argv[1]
    else:
        # Fallback to notion_northstar.md in root
        ref_file = os.path.join(os.path.dirname(__file__), "..", "notion_northstar.md")
        if os.path.exists(ref_file):
            with open(ref_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                match = re.search(r"https?://[^\s]+", content)
                if match:
                    target = match.group(0)
                    
    if not target:
        target = "https://fast-peripheral-39e.notion.site/Optivoya-DreamTripPlanner-DTP-2cbfe7beaf9d806ba599cf6e852a01a9"
        
    page_id = extract_page_id(target)
    print(f"[INFO] Fetching Notion page: {page_id}...", file=sys.stderr)
    
    blocks = fetch_all_blocks(page_id)
    print(f"[INFO] Fetched {len(blocks)} blocks successfully.", file=sys.stderr)
    
    md_content = render_blocks_to_markdown(blocks, page_id)
    
    # Save output to docs/notion_northstar_content.md
    out_path = os.path.join(os.path.dirname(__file__), "..", "docs", "notion_northstar_content.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[INFO] Saved content to {out_path}\n", file=sys.stderr)
    
    # Print to stdout
    print(md_content)

if __name__ == "__main__":
    main()

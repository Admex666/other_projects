"""
Slice Card Spritesheet into Individual Images for Bear Necessities.

This utility slices the full spritesheet (default: assets/sources/cards.jpg) into
individual card image files (WEBP, PNG, or JPEG) with configurable scaling,
quality, naming conventions, and optional CSS stylesheet generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image


DEFAULT_MAP_PATH = Path("docs/card_spritesheet_map.json")
DEFAULT_SPRITESHEET_PATH = Path("assets/sources/cards.jpg")
DEFAULT_OUTPUT_DIR = Path("public/assets/cards")


def load_card_map(map_path: Path) -> Dict[str, Any]:
    if not map_path.exists():
        raise FileNotFoundError(
            f"Mapping file not found at {map_path}. "
            "Please run 'python scripts/analyze_spritesheet.py' first."
        )
    with open(map_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_filename_for_slot(
    slot: Dict[str, Any], naming_scheme: str, ext: str
) -> Optional[str]:
    slot_idx = slot["slot_index"]
    slot_type = slot["slot_type"]

    if slot_type == "blank":
        return f"slot_{slot_idx:02d}_blank.{ext}"

    if slot_type == "card_back":
        suit_key = slot.get("suit_key") or "unknown"
        # e.g. back_water_blue.webp or back_water.webp
        short_suit = suit_key.split("_")[0]
        return f"back_{short_suit}.{ext}"

    # slot_type == "game_card"
    card_id = slot["game_card_id"]
    if naming_scheme == "slot":
        return f"slot_{slot_idx:02d}.{ext}"
    elif naming_scheme == "semantic":
        suit_key = slot.get("suit_key") or "card"
        short_suit = suit_key.split("_")[0]
        suit_idx = slot.get("suit_index", 1)
        return f"{short_suit}_{suit_idx:02d}_card_{card_id:02d}.{ext}"
    else:  # default "card"
        return f"card_{card_id:02d}.{ext}"


def generate_css_spritesheet_stylesheet(
    metadata: Dict[str, Any], slots: List[Dict[str, Any]], css_path: Path, sprite_image_url: str = "../sources/cards.jpg"
) -> None:
    """
    Generate CSS utility classes for sprite-based card rendering.
    """
    lines = [
        "/* ========================================================================= */",
        "/* Bear Necessities - Card Spritesheet CSS Utilities                        */",
        "/* Generated automatically by scripts/slice_cards.py                        */",
        "/* ========================================================================= */",
        "",
        ":root {",
        "  --bn-card-aspect-ratio: 1.5594;",
        f"  --bn-card-sprite-url: url('{sprite_image_url}');",
        "}",
        "",
        "/* Base Card Face using Spritesheet */",
        ".bn-card-face {",
        "  display: block;",
        "  width: 100%;",
        "  height: 100%;",
        "  background-image: var(--bn-card-sprite-url);",
        "  background-size: 1000% 1000%;",
        "  background-repeat: no-repeat;",
        "  border-radius: 4px;",
        "}",
        "",
        "/* --- Game Cards (1-94) --- */",
    ]

    for slot in slots:
        if slot["slot_type"] == "game_card":
            cid = slot["game_card_id"]
            sidx = slot["slot_index"]
            pos = slot["css_background_position"]
            suit = slot["suit"]
            lines.append(
                f'.bn-card-face[data-card-id="{cid}"], '
                f'.bn-card-{cid:02d}, '
                f'.bn-slot-{sidx:02d} '
                f'{{ background-position: {pos}; }} /* {suit} #{slot["suit_index"]} */'
            )

    lines.extend([
        "",
        "/* --- Card Backs (4 Suits) --- */",
    ])

    for slot in slots:
        if slot["slot_type"] == "card_back":
            suit_key = slot["suit_key"]
            short_suit = suit_key.split("_")[0]
            pos = slot["css_background_position"]
            sidx = slot["slot_index"]
            lines.append(
                f'.bn-card-back-{short_suit}, '
                f'.bn-card-face[data-card-back="{short_suit}"], '
                f'.bn-slot-{sidx:02d} '
                f'{{ background-position: {pos}; }} /* {slot["suit"]} Back */'
            )

    lines.append("")
    css_path.parent.mkdir(parents=True, exist_ok=True)
    with open(css_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated CSS stylesheet: {css_path}")


def slice_cards(
    spritesheet_path: Path,
    map_path: Path,
    output_dir: Path,
    image_format: str = "webp",
    quality: int = 85,
    scale: float = 1.0,
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    naming_scheme: str = "card",
    include_backs: bool = True,
    include_blanks: bool = False,
    generate_css: bool = False,
    css_output_path: Optional[Path] = None,
    dry_run: bool = False,
) -> int:
    card_map = load_card_map(map_path)
    metadata = card_map["metadata"]
    slots = card_map["slots"]

    print(f"Loading spritesheet: {spritesheet_path}")
    if not spritesheet_path.exists():
        raise FileNotFoundError(f"Spritesheet not found at {spritesheet_path}")

    sheet = Image.open(spritesheet_path)

    # Determine dimensions
    base_cw = metadata["card_width_px"]
    base_ch = metadata["card_height_px"]

    if target_width is not None and target_height is not None:
        out_w, out_h = target_width, target_height
    elif target_width is not None:
        out_w = target_width
        out_h = int(round(target_width * (base_ch / base_cw)))
    elif target_height is not None:
        out_h = target_height
        out_w = int(round(target_height * (base_cw / base_ch)))
    elif scale != 1.0:
        out_w = int(round(base_cw * scale))
        out_h = int(round(base_ch * scale))
    else:
        out_w, out_h = base_cw, base_ch

    resample_needed = (out_w != base_cw) or (out_h != base_ch)
    format_clean = image_format.lower()
    if format_clean == "jpeg":
        format_clean = "jpg"

    print(f"Slicing configuration:")
    print(f"  Target Card Size: {out_w} x {out_h} px (Resampling: {resample_needed})")
    print(f"  Format: {format_clean.upper()} (Quality: {quality})")
    print(f"  Naming Scheme: {naming_scheme}")
    print(f"  Include Backs: {include_backs}, Include Blanks: {include_blanks}")
    print(f"  Output Directory: {output_dir}")
    print(f"  Dry Run: {dry_run}")

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    exported_count = 0
    manifest: List[Dict[str, Any]] = []

    for slot in slots:
        stype = slot["slot_type"]
        if stype == "blank" and not include_blanks:
            continue
        if stype == "card_back" and not include_backs:
            continue

        filename = get_filename_for_slot(slot, naming_scheme, format_clean)
        if not filename:
            continue

        coords = slot["pixel_coords"]
        x, y, w, h = coords["x"], coords["y"], coords["width"], coords["height"]

        target_file = output_dir / filename

        if not dry_run:
            cropped = sheet.crop((x, y, x + w, y + h))
            if resample_needed:
                cropped = cropped.resize((out_w, out_h), Image.Resampling.LANCZOS)

            save_kwargs: Dict[str, Any] = {}
            if format_clean in ("jpg", "jpeg"):
                save_kwargs["quality"] = quality
                # Convert to RGB if needed
                if cropped.mode != "RGB":
                    cropped = cropped.convert("RGB")
            elif format_clean == "webp":
                save_kwargs["quality"] = quality
                save_kwargs["method"] = 6  # High quality encoding
            elif format_clean == "png":
                save_kwargs["optimize"] = True

            cropped.save(target_file, **save_kwargs)

        exported_count += 1
        manifest.append({
            "slot_index": slot["slot_index"],
            "slot_type": slot["slot_type"],
            "game_card_id": slot.get("game_card_id"),
            "suit": slot.get("suit"),
            "file": filename,
            "width": out_w,
            "height": out_h,
        })

    # Save manifest in output dir
    if not dry_run:
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"card_count": exported_count, "cards": manifest}, f, indent=2)
        print(f"Wrote slice manifest to: {manifest_path}")

    # Optional CSS generation
    if generate_css:
        css_target = css_output_path or (output_dir / "cards.css")
        generate_css_spritesheet_stylesheet(metadata, slots, css_target)

    print(f"Exported {exported_count} cards to {output_dir}")
    return exported_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Slice Bear Necessities card spritesheet into individual assets."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_SPRITESHEET_PATH,
        help="Path to source spritesheet image",
    )
    parser.add_argument(
        "--map",
        type=Path,
        default=DEFAULT_MAP_PATH,
        help="Path to card spritesheet map JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for sliced card images",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="webp",
        choices=["webp", "png", "jpg", "jpeg"],
        help="Output image format (default: webp)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="Encoding quality for WEBP / JPEG (1-100, default: 85)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale multiplier for resolution (default: 1.0)",
    )
    parser.add_argument(
        "--target-width",
        type=int,
        default=None,
        help="Explicit width in pixels",
    )
    parser.add_argument(
        "--target-height",
        type=int,
        default=None,
        help="Explicit height in pixels",
    )
    parser.add_argument(
        "--naming",
        type=str,
        default="card",
        choices=["card", "slot", "semantic"],
        help="Naming pattern: 'card' (card_01.webp), 'slot' (slot_00.webp), or 'semantic' (water_01_card_01.webp)",
    )
    parser.add_argument(
        "--no-backs",
        action="store_true",
        help="Exclude card back images from export",
    )
    parser.add_argument(
        "--include-blanks",
        action="store_true",
        help="Include blank slots in export",
    )
    parser.add_argument(
        "--generate-css",
        action="store_true",
        help="Generate CSS stylesheet with background-position sprite utility classes",
    )
    parser.add_argument(
        "--css-output",
        type=Path,
        default=None,
        help="Custom path for generated CSS stylesheet",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without saving files",
    )

    args = parser.parse_args()

    slice_cards(
        spritesheet_path=args.input,
        map_path=args.map,
        output_dir=args.output_dir,
        image_format=args.format,
        quality=args.quality,
        scale=args.scale,
        target_width=args.target_width,
        target_height=args.target_height,
        naming_scheme=args.naming,
        include_backs=not args.no_backs,
        include_blanks=args.include_blanks,
        generate_css=args.generate_css,
        css_output_path=args.css_output,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

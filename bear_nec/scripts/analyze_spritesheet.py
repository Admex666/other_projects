"""
Analyze Card Spritesheet for Bear Necessities.

This script analyzes the cards spritesheet (default: assets/sources/cards.jpg),
verifies the 10x10 layout grid, extracts color metrics, classifies card types
(game cards, card backs, blanks) and suits (City/Red, Desert/Yellow, Mountain/Green, Water/Blue),
and exports a comprehensive JSON mapping to docs/card_spritesheet_map.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image


# Grid specifications
DEFAULT_COLUMNS = 10
DEFAULT_ROWS = 10
TOTAL_SLOTS = DEFAULT_COLUMNS * DEFAULT_ROWS

# Known structural landmarks based on visual analysis:
# Suit partitions:
# Blue/Water: 23 cards (slots 0-22), followed by slot 23 (Water card back)
# Yellow/Desert: 21 cards (slots 24-44), followed by slot 45 (Desert card back)
# Red/City: 24 cards (slots 46-69), followed by slot 70 (City card back)
# Green/Mountain: 26 cards (slots 71-96), followed by slot 97 (Mountain card back)
# Blank slots: 98, 99
KNOWN_CARD_BACKS: Dict[int, Dict[str, str]] = {
    23: {"suit": "Water", "suit_key": "water_blue", "color_name": "Blue"},
    45: {"suit": "Desert", "suit_key": "desert_yellow", "color_name": "Yellow"},
    70: {"suit": "City", "suit_key": "city_red", "color_name": "Red"},
    97: {"suit": "Mountain", "suit_key": "mountain_green", "color_name": "Green"},
}
KNOWN_BLANKS = {98, 99}


@dataclass
class PixelRect:
    x: int
    y: int
    width: int
    height: int


@dataclass
class ColorStats:
    overall_rgb: List[float]
    overall_hex: str
    border_rgb: List[float]
    border_hex: str
    art_rgb: List[float]
    art_hex: str
    text_box_rgb: List[float]
    text_box_hex: str


@dataclass
class SlotMapping:
    slot_index: int
    column: int
    row: int
    slot_type: str  # "game_card", "card_back", "blank"
    game_card_id: Optional[int]  # 1 to 94 for game cards, None for backs/blanks
    suit: Optional[str]  # "Water", "Desert", "City", "Mountain", None
    suit_key: Optional[str]  # "water_blue", "desert_yellow", "city_red", "mountain_green"
    suit_color: Optional[str]  # "Blue", "Yellow", "Red", "Green"
    suit_index: Optional[int]  # 1-based index within suit
    pixel_coords: PixelRect
    css_bg_percent_x: str
    css_bg_percent_y: str
    css_background_position: str
    color_stats: ColorStats
    is_blank: bool
    is_card_back: bool


def rgb_to_hex(rgb: Tuple[float, float, float] | List[float]) -> str:
    r = max(0, min(255, int(round(rgb[0]))))
    g = max(0, min(255, int(round(rgb[1]))))
    b = max(0, min(255, int(round(rgb[2]))))
    return f"#{r:02x}{g:02x}{b:02x}"


def classify_card_suit(border_rgb: np.ndarray) -> Tuple[str, str, str]:
    """
    Classify card color/suit based on sampled border color RGB.
    Water: Blue / Teal
    Desert: Yellow / Amber
    City: Red / Coral
    Mountain: Green / Lime
    """
    r, g, b = border_rgb
    if b > 170 and g > 160 and r < 140:
        return "Water", "water_blue", "Blue"
    elif r > 210 and g > 170 and b < 150:
        return "Desert", "desert_yellow", "Yellow"
    elif r > 190 and g < 160 and b < 140:
        return "City", "city_red", "Red"
    elif g > 180 and r > 160 and b < 150:
        return "Mountain", "mountain_green", "Green"
    else:
        # Fallback comparison by dominant delta
        if b > r and b > 140:
            return "Water", "water_blue", "Blue"
        elif r > 180 and g > 160:
            return "Desert", "desert_yellow", "Yellow"
        elif r > g and r > b:
            return "City", "city_red", "Red"
        else:
            return "Mountain", "mountain_green", "Green"


def analyze_slot(
    sheet: Image.Image,
    slot_idx: int,
    col: int,
    row: int,
    card_width: int,
    card_height: int,
    total_cols: int,
    total_rows: int,
    game_card_counter: List[int],
    suit_counters: Dict[str, int],
) -> SlotMapping:
    x = col * card_width
    y = row * card_height

    # Crop slot
    crop = sheet.crop((x, y, x + card_width, y + card_height))
    arr = np.array(crop, dtype=np.float32)

    # CSS background-position calculations
    # In CSS: background-position: (c / (total_cols - 1)) * 100% (r / (total_rows - 1)) * 100%
    pct_x = (col / (total_cols - 1)) * 100.0 if total_cols > 1 else 0.0
    pct_y = (row / (total_rows - 1)) * 100.0 if total_rows > 1 else 0.0
    css_bg_pos = f"{pct_x:.4f}% {pct_y:.4f}%"

    # Color measurements
    overall_mean = arr.mean(axis=(0, 1)).tolist()

    # Border sample (around pixel 10,10 or 8:14, 8:14)
    border_sample = arr[8:16, 8:16].mean(axis=(0, 1))

    # Art area sample (center: y 180:260, x 80:240)
    art_sample = arr[180:260, 80:240].mean(axis=(0, 1)).tolist()

    # Text box sample (bottom cream box on standard cards: y 440:475, x 60:260)
    text_box_sample = arr[440:475, 60:260].mean(axis=(0, 1)).tolist()

    color_stats = ColorStats(
        overall_rgb=[round(v, 2) for v in overall_mean],
        overall_hex=rgb_to_hex(overall_mean),
        border_rgb=[round(float(v), 2) for v in border_sample],
        border_hex=rgb_to_hex(border_sample.tolist()),
        art_rgb=[round(v, 2) for v in art_sample],
        art_hex=rgb_to_hex(art_sample),
        text_box_rgb=[round(v, 2) for v in text_box_sample],
        text_box_hex=rgb_to_hex(text_box_sample),
    )

    # Determine slot type & identity
    is_blank = bool(slot_idx in KNOWN_BLANKS or float(arr.mean()) > 254.0)
    is_card_back = bool(slot_idx in KNOWN_CARD_BACKS)

    if is_blank:
        slot_type = "blank"
        game_card_id = None
        suit = None
        suit_key = None
        suit_color = None
        suit_index = None
    elif is_card_back:
        slot_type = "card_back"
        game_card_id = None
        back_info = KNOWN_CARD_BACKS[slot_idx]
        suit = back_info["suit"]
        suit_key = back_info["suit_key"]
        suit_color = back_info["color_name"]
        suit_index = None
    else:
        slot_type = "game_card"
        game_card_counter[0] += 1
        game_card_id = game_card_counter[0]
        suit, suit_key, suit_color = classify_card_suit(border_sample)
        suit_counters[suit_key] = suit_counters.get(suit_key, 0) + 1
        suit_index = suit_counters[suit_key]

    return SlotMapping(
        slot_index=slot_idx,
        column=col,
        row=row,
        slot_type=slot_type,
        game_card_id=game_card_id,
        suit=suit,
        suit_key=suit_key,
        suit_color=suit_color,
        suit_index=suit_index,
        pixel_coords=PixelRect(x=x, y=y, width=card_width, height=card_height),
        css_bg_percent_x=f"{pct_x:.4f}%",
        css_bg_percent_y=f"{pct_y:.4f}%",
        css_background_position=css_bg_pos,
        color_stats=color_stats,
        is_blank=is_blank,
        is_card_back=is_card_back,
    )


def run_analysis(
    spritesheet_path: Path, output_json_path: Path
) -> Dict[str, Any]:
    print(f"Loading spritesheet: {spritesheet_path}")
    if not spritesheet_path.exists():
        raise FileNotFoundError(f"Spritesheet not found at {spritesheet_path}")

    sheet = Image.open(spritesheet_path)
    total_w, total_h = sheet.size
    cols = DEFAULT_COLUMNS
    rows = DEFAULT_ROWS
    cw = total_w // cols
    ch = total_h // rows

    print(f"Sheet Dimensions: {total_w} x {total_h} px")
    print(f"Grid Layout: {cols} columns x {rows} rows (Total: {cols * rows} slots)")
    print(f"Cell Dimensions: {cw} x {ch} px (Aspect ratio: {ch / cw:.4f})")

    game_card_counter = [0]
    suit_counters: Dict[str, int] = {}
    slots: List[SlotMapping] = []

    for idx in range(TOTAL_SLOTS):
        r, c = divmod(idx, cols)
        slot_data = analyze_slot(
            sheet=sheet,
            slot_idx=idx,
            col=c,
            row=r,
            card_width=cw,
            card_height=ch,
            total_cols=cols,
            total_rows=rows,
            game_card_counter=game_card_counter,
            suit_counters=suit_counters,
        )
        slots.append(slot_data)

    # Verification checks
    total_game_cards = game_card_counter[0]
    total_backs = sum(1 for s in slots if s.slot_type == "card_back")
    total_blanks = sum(1 for s in slots if s.slot_type == "blank")

    summary = {
        "spritesheet_image": str(spritesheet_path.as_posix()),
        "spritesheet_width": total_w,
        "spritesheet_height": total_h,
        "grid_columns": cols,
        "grid_rows": rows,
        "total_slots": len(slots),
        "card_width_px": cw,
        "card_height_px": ch,
        "card_aspect_ratio": round(ch / cw, 4),
        "counts": {
            "game_cards": total_game_cards,
            "card_backs": total_backs,
            "blank_slots": total_blanks,
            "by_suit": {
                "Water (Blue)": suit_counters.get("water_blue", 0),
                "Desert (Yellow)": suit_counters.get("desert_yellow", 0),
                "City (Red)": suit_counters.get("city_red", 0),
                "Mountain (Green)": suit_counters.get("mountain_green", 0),
            },
        },
        "card_back_slots": {
            s.slot_index: {"suit": s.suit, "color": s.suit_color}
            for s in slots
            if s.slot_type == "card_back"
        },
        "blank_slots": [s.slot_index for s in slots if s.slot_type == "blank"],
    }

    result = {
        "metadata": summary,
        "slots": [asdict(s) for s in slots],
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\nAnalysis Results:")
    print(f"  Game Cards: {total_game_cards} (Expected: 94) -> {'PASS' if total_game_cards == 94 else 'FAIL'}")
    print(f"  Card Backs: {total_backs} (Expected: 4)  -> {'PASS' if total_backs == 4 else 'FAIL'}")
    print(f"  Blank Slots: {total_blanks} (Expected: 2) -> {'PASS' if total_blanks == 2 else 'FAIL'}")
    print(f"  Suit breakdown:")
    for suit_name, count in summary["counts"]["by_suit"].items():
        print(f"    - {suit_name}: {count} cards")
    print(f"  Saved mapping to: {output_json_path}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Bear Necessities card spritesheet")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("assets/sources/cards.jpg"),
        help="Path to cards spritesheet",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/card_spritesheet_map.json"),
        help="Path to output JSON mapping",
    )
    args = parser.parse_args()

    run_analysis(args.input, args.output)


if __name__ == "__main__":
    main()

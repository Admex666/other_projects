"""
Vision & Card Recognition Module for Schnapsen Android App
- Exact 216x343 Card Boundaries and (23, 23) RGB Playability / Emptiness check
- Clockwise 90-deg Trump Card Matching against Template Top-Half
- Full Hungarian Naming (Piros, Tök, Zöld, Makk / Ász, Tízes, Király, Felső, Alsó)
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import cv2
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from schnapsen.game import Card, Suit, Rank

CARD_W = 216
CARD_H = 343
STEP_X = 229

# 5 Hand slots
CARD_SLOT_BOXES = [
    (14 + i * STEP_X, 729, 230 + i * STEP_X, 1072)
    for i in range(5)
]

# Centers for swiping cards up into Table Center
CARD_SWIPE_STARTS = [
    (int(x1 + (x2 - x1) / 2), 900) for (x1, y1, x2, y2) in CARD_SLOT_BOXES
]

TABLE_CENTER_TARGET = (950, 430)
OPPONENT_CARD_BOX = (662, 207, 662 + CARD_W, 207 + CARD_H)
TRUMP_BOX = (1431, 265, 1620, 481)
TALON_BOX = (1630, 150, 1880, 500)

SUIT_HU = {
    "HEARTS": "Piros",
    "DIAMONDS": "Tök",
    "SPADES": "Zöld",
    "CLUBS": "Makk"
}

RANK_HU = {
    "ACE": "Ász",
    "TEN": "Tízes",
    "KING": "Király",
    "QUEEN": "Felső",
    "JACK": "Alsó"
}


def card_to_hungarian(card_name: Optional[str]) -> str:
    """Converts internal card name (e.g. HEARTS_JACK) to Hungarian (Piros Alsó)."""
    if not card_name:
        return "Ismeretlen"
    parts = card_name.split("_")
    if len(parts) == 2 and parts[0] in SUIT_HU and parts[1] in RANK_HU:
        return f"{SUIT_HU[parts[0]]} {RANK_HU[parts[1]]}"
    return card_name


def suit_to_hungarian(suit_name: Optional[str]) -> str:
    """Converts suit name (e.g. HEARTS) to Hungarian (Piros)."""
    if not suit_name:
        return "Ismeretlen"
    return SUIT_HU.get(suit_name, suit_name)


class AndroidCardDetector:
    """
    Detects Schnapsen cards, trump, turn, and table state using template matching.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or (ROOT_DIR / "templates")
        self.templates: Dict[str, np.ndarray] = {}
        self.last_known_trump_card: Optional[str] = None
        self._load_templates()

    def _load_templates(self):
        if not self.templates_dir.exists():
            return
        for file in self.templates_dir.glob("*.png"):
            if file.name.startswith("unmapped"):
                continue
            card_name = file.stem
            img = cv2.imread(str(file), cv2.IMREAD_COLOR)
            if img is not None:
                self.templates[card_name] = img
        print(f"Loaded {len(self.templates)} card templates from {self.templates_dir}")

    def inspect_slot_color(self, crop_bgr: np.ndarray) -> Tuple[str, Tuple[int, int, int]]:
        """
        Samples the card at relative coordinate (23, 23) inside the crop (with small 5x5 patch).
        - LEGAL: RGB ~ (255, 255, 255)
        - DISABLED: RGB ~ (192, 123, 123)
        - EMPTY: RGB ~ (191, 124, 52)
        """
        if crop_bgr.size == 0 or crop_bgr.shape[0] < 30 or crop_bgr.shape[1] < 30:
            return "EMPTY", (0, 0, 0)

        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        patch = crop_rgb[21:26, 21:26]
        r = int(np.median(patch[:, :, 0]))
        g = int(np.median(patch[:, :, 1]))
        b = int(np.median(patch[:, :, 2]))
        rgb = (r, g, b)

        # Clear white threshold
        if r > 230 and g > 230 and b > 230:
            return "LEGAL", rgb

        # Asztal barna (B < 85 és R > 140)
        if b < 85 and r > 140:
            return "EMPTY", rgb

        # Distance comparison
        dist_white = np.linalg.norm(np.array([r, g, b]) - np.array([255, 255, 255]))
        dist_red = np.linalg.norm(np.array([r, g, b]) - np.array([192, 123, 123]))
        dist_brown = np.linalg.norm(np.array([r, g, b]) - np.array([191, 124, 52]))

        closest = min([("LEGAL", dist_white), ("DISABLED", dist_red), ("EMPTY", dist_brown)], key=lambda x: x[1])
        return closest[0], rgb

    def is_slot_empty(self, crop_bgr: np.ndarray) -> bool:
        status, _ = self.inspect_slot_color(crop_bgr)
        return status == "EMPTY"

    def is_card_playable(self, crop_bgr: np.ndarray) -> bool:
        status, _ = self.inspect_slot_color(crop_bgr)
        return status == "LEGAL"

    def match_card(self, crop_bgr: np.ndarray, min_score: float = 0.50) -> Tuple[Optional[str], float]:
        """
        Matches card crop against templates.
        Uses normalized cross correlation on standard and Green/Blue channels.
        """
        if not self.templates:
            return None, 0.0

        best_card = None
        best_val = -1.0

        h_c, w_c = crop_bgr.shape[:2]

        for name, tmpl in self.templates.items():
            if tmpl.shape[:2] != (h_c, w_c):
                resized_tmpl = cv2.resize(tmpl, (w_c, h_c))
            else:
                resized_tmpl = tmpl

            res = cv2.matchTemplate(crop_bgr, resized_tmpl, cv2.TM_CCOEFF_NORMED)
            val = float(res[0][0])
            if val > best_val:
                best_val = val
                best_card = name

        if best_val >= min_score:
            return best_card, best_val
        return None, best_val

    def detect_hand_cards(self, screen_bgr: np.ndarray) -> List[Dict]:
        """Detects cards in all 5 hand slots."""
        results = []
        for idx, (x1, y1, x2, y2) in enumerate(CARD_SLOT_BOXES, 1):
            crop = screen_bgr[y1:y2, x1:x2]
            status, rgb = self.inspect_slot_color(crop)

            if status == "EMPTY":
                results.append({
                    "slot": idx,
                    "empty": True,
                    "playable": False,
                    "card_name": None,
                    "card_hu": "Üres",
                    "confidence": 0.0,
                    "pixel_rgb": rgb,
                    "status": "EMPTY"
                })
                continue

            card_name, conf = self.match_card(crop)
            is_playable = (status == "LEGAL")

            results.append({
                "slot": idx,
                "empty": False,
                "playable": is_playable,
                "card_name": card_name,
                "card_hu": card_to_hungarian(card_name),
                "confidence": conf,
                "pixel_rgb": rgb,
                "status": status
            })
        return results

    def detect_trump_card(self, screen_bgr: np.ndarray, save_debug: bool = True) -> Tuple[Optional[str], str, float]:
        """
        Rotates trump crop 90 deg CLOCKWISE and matches ONLY against the TOP portion of templates.
        Saves debug images for visual verification.
        """
        tx1, ty1, tx2, ty2 = TRUMP_BOX
        crop = screen_bgr[ty1:ty2, tx1:tx2]
        if crop.size == 0:
            return self.last_known_trump_card, card_to_hungarian(self.last_known_trump_card), 0.0

        # Rotate 90 degrees CLOCKWISE
        crop_upright = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)
        h_u, w_u = crop_upright.shape[:2]

        if save_debug:
            out_dir = ROOT_DIR / "browser_state"
            out_dir.mkdir(exist_ok=True)
            cv2.imwrite(str(out_dir / "trump_crop_raw.png"), crop)
            cv2.imwrite(str(out_dir / "trump_crop_rotated.png"), crop_upright)

        best_card = None
        best_val = -1.0

        for name, tmpl in self.templates.items():
            # Match strictly against the TOP part of the template matching the crop height
            tmpl_top = tmpl[:h_u, :w_u]
            if tmpl_top.shape[:2] != (h_u, w_u):
                tmpl_top = cv2.resize(tmpl_top, (w_u, h_u))

            res = cv2.matchTemplate(crop_upright, tmpl_top, cv2.TM_CCOEFF_NORMED)
            val = float(res[0][0])
            if val > best_val:
                best_val = val
                best_card = name

        if best_card and best_val > 0.40:
            self.last_known_trump_card = best_card

        chosen = best_card or self.last_known_trump_card
        return chosen, card_to_hungarian(chosen), best_val

    def detect_opponent_card(self, screen_bgr: np.ndarray) -> Tuple[Optional[str], str, float]:
        """Detects if opponent has played a card on table."""
        ox1, oy1, ox2, oy2 = OPPONENT_CARD_BOX
        crop = screen_bgr[oy1:oy2, ox1:ox2]
        status, _ = self.inspect_slot_color(crop)
        if status == "EMPTY":
            return None, "Nincs lap", 0.0
        card_name, conf = self.match_card(crop)
        return card_name, card_to_hungarian(card_name), conf

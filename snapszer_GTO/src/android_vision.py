"""
Vision & Card Recognition Module for Schnapsen Android App (Calibrated Layout)
Exact RGB Background matching: White (255, 255, 255) vs Red Disabled (192, 123, 123).
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from PIL import Image

# 1920x1080 Calibrated Layout Coordinates

# 5 Hand card contiguous non-overlapping bounding boxes (x1, y1, x2, y2)
CARD_SLOT_BOXES = [
    (5, 675, 240, 1080),     # Slot 1
    (240, 675, 475, 1080),   # Slot 2
    (475, 675, 710, 1080),   # Slot 3
    (710, 675, 945, 1080),   # Slot 4
    (945, 675, 1180, 1080),  # Slot 5
]

# Exact swipe start coordinates (centers of the 5 cards)
CARD_SWIPE_STARTS = [
    (122, 950),   # Slot 1
    (357, 950),   # Slot 2
    (592, 950),   # Slot 3
    (827, 950),   # Slot 4
    (1062, 950),  # Slot 5
]

# Table Center target where cards must be swiped to
TABLE_CENTER_TARGET = (950, 430)

# Trump Card Box (under talon on the right) & Tap point
TRUMP_BOX = (1420, 235, 1660, 450)
TRUMP_TAP = (1535, 340)

# Talon Stack (Zárás / Csere)
TALON_BOX = (1630, 150, 1880, 500)
TALON_TAP = (1750, 325)

# Table Center Area (Hívás & Ütés)
TABLE_CENTER_BOX = (750, 170, 1300, 620)

# Action Buttons
MARRIAGE_BUTTON_TAP = (1250, 700)
PASS_BUTTON_TAP = (1250, 830)


class AndroidCardDetector:
    """
    Detects Schnapsen cards, trump, turn, and table state from Android screen captures.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or (Path(__file__).resolve().parent.parent / "templates")
        self.templates_dir.mkdir(exist_ok=True)
        self.templates: Dict[str, np.ndarray] = {}
        self._load_templates()

    def _load_templates(self):
        if not self.templates_dir.exists():
            return
        for file in self.templates_dir.glob("*.png"):
            card_name = file.stem
            img = cv2.imread(str(file), cv2.IMREAD_COLOR)
            if img is not None:
                self.templates[card_name] = img

    def is_my_turn(self, screen_bgr: np.ndarray) -> bool:
        """
        Checks if it's currently the player's turn (at least one playable white card).
        """
        h, w, _ = screen_bgr.shape
        if h != 1080 or w != 1920:
            return False
        playable = self.get_playable_slots(screen_bgr)
        return len(playable) > 0

    def is_card_playable(self, crop_bgr: np.ndarray) -> bool:
        """
        Exact RGB classification:
        - White (playable): Background RGB is ~ (255, 255, 255)
        - Red (disabled): Background RGB is ~ (192, 123, 123)
        - Wood Table (empty slot): Brown wood background
        """
        if crop_bgr.size == 0:
            return False

        # Convert to RGB
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        
        # Sample the top margin background of the card (inside the card border, away from illustrations)
        # In each slot crop: Y: 20..50, X: 20..70
        h, w, _ = crop_rgb.shape
        margin_sample = crop_rgb[int(h*0.06):int(h*0.16), int(w*0.08):int(w*0.35)]

        # Distance to White (255, 255, 255)
        white_diff = np.abs(margin_sample.astype(np.float32) - np.array([255, 255, 255], dtype=np.float32)).mean(axis=-1)
        white_pixels = np.count_nonzero(white_diff < 45)

        # Distance to Red Disabled (192, 123, 123)
        red_diff = np.abs(margin_sample.astype(np.float32) - np.array([192, 123, 123], dtype=np.float32)).mean(axis=-1)
        red_pixels = np.count_nonzero(red_diff < 45)

        total_sample_pixels = margin_sample.shape[0] * margin_sample.shape[1]
        
        white_ratio = white_pixels / total_sample_pixels
        red_ratio = red_pixels / total_sample_pixels

        # If red background is dominant -> Disabled (False)
        if red_ratio > 0.30:
            return False

        # If white background is dominant -> Playable (True)
        if white_ratio > 0.25:
            return True

        # Fallback check across whole card: check if B & G channels are bright (>180) vs red-tinted (B < 150)
        r, g, b = margin_sample[:, :, 0].mean(), margin_sample[:, :, 1].mean(), margin_sample[:, :, 2].mean()
        if (r - g) > 40 and (r - b) > 40:
            return False # Red disabled

        return g > 170 and b > 170

    def get_playable_slots(self, screen_bgr: np.ndarray) -> List[int]:
        """
        Returns a list of 0-based slot indices [0..4] that are currently legal / playable.
        """
        playable = []
        for idx, (x1, y1, x2, y2) in enumerate(CARD_SLOT_BOXES):
            crop = screen_bgr[y1:y2, x1:x2]
            if self.is_card_playable(crop):
                playable.append(idx)
        return playable

    def get_hand_crops(self, screen_bgr: np.ndarray) -> List[np.ndarray]:
        crops = []
        for (x1, y1, x2, y2) in CARD_SLOT_BOXES:
            crop = screen_bgr[y1:y2, x1:x2]
            crops.append(crop)
        return crops

    def get_trump_crop(self, screen_bgr: np.ndarray) -> np.ndarray:
        x1, y1, x2, y2 = TRUMP_BOX
        return screen_bgr[y1:y2, x1:x2]

    def get_opponent_played_card_crop(self, screen_bgr: np.ndarray) -> np.ndarray:
        x1, y1, x2, y2 = TABLE_CENTER_BOX
        return screen_bgr[y1:y2, x1:x2]

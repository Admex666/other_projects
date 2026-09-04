"""
Crops hand card slots, opponent card, and trump card from current screen
using exact user-calibrated boundaries.
"""

import sys
from pathlib import Path
import time
import cv2
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from adbutils import adb

CARD_W = 216
CARD_H = 343
STEP_X = 229

# 5 Hand slots
# Slot 1: (14, 729) to (230, 1072)
CARD_SLOT_BOXES = [
    (14 + i * STEP_X, 729, 230 + i * STEP_X, 1072)
    for i in range(5)
]

# Opponent card: top-left (662, 207)
OPPONENT_CARD_BOX = (662, 207, 662 + CARD_W, 207 + CARD_H)

# Trump (rotated 90 deg): top-left (1431, 265)
# Rotated card height is 216 (Y: 265..481), visible width from 1431 to ~1620
TRUMP_BOX = (1431, 265, 1620, 481)


def main():
    devices = adb.device_list()
    out_dir = ROOT_DIR / "templates" / "unmapped"
    out_dir.mkdir(parents=True, exist_ok=True)

    if devices:
        print(f"Connecting to device {devices[0].serial}...")
        pil_img = devices[0].screenshot()
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    else:
        print("No ADB device found, falling back to latest screenshot in browser_state...")
        fallback = ROOT_DIR / "browser_state" / "live_debug_screen.png"
        img = cv2.imread(str(fallback))

    if img is None:
        print("Could not get image!")
        return

    ts = int(time.time())
    print(f"Extracting unmapped crops to {out_dir}...")

    # Crop hand cards
    for idx, (x1, y1, x2, y2) in enumerate(CARD_SLOT_BOXES, 1):
        crop = img[y1:y2, x1:x2]
        crop_path = out_dir / f"slot_{idx}_{ts}.png"
        cv2.imwrite(str(crop_path), crop)
        print(f"Saved: {crop_path.name} (size: {crop.shape[1]}x{crop.shape[0]})")

    # Crop Opponent played card
    ox1, oy1, ox2, oy2 = OPPONENT_CARD_BOX
    opp_crop = img[oy1:oy2, ox1:ox2]
    opp_path = out_dir / f"opponent_played_{ts}.png"
    cv2.imwrite(str(opp_path), opp_crop)
    print(f"Saved: {opp_path.name} (size: {opp_crop.shape[1]}x{opp_crop.shape[0]})")

    # Crop Trump
    tx1, ty1, tx2, ty2 = TRUMP_BOX
    trump_crop = img[ty1:ty2, tx1:tx2]
    trump_path = out_dir / f"trump_{ts}.png"
    cv2.imwrite(str(trump_path), trump_crop)
    print(f"Saved: {trump_path.name} (size: {trump_crop.shape[1]}x{trump_crop.shape[0]})")

    # Rotated Trump (so it stands upright for easy reading / template matching)
    trump_rot = cv2.rotate(trump_crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
    trump_rot_path = out_dir / f"trump_upright_{ts}.png"
    cv2.imwrite(str(trump_rot_path), trump_rot)
    print(f"Saved: {trump_rot_path.name} (size: {trump_rot.shape[1]}x{trump_rot.shape[0]})")


if __name__ == "__main__":
    main()

"""
Interactive Calibration & Grid Overlay Tool for Schnapsen Table
Uses exact user-calibrated card boundaries:
Slot 1: (14, 729) to (230, 1072), X step: +229
Opponent Card: (662, 207)
Trump (rotated 90): (1431, 265)
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np
from adbutils import adb

CARD_W = 216
CARD_H = 343
STEP_X = 229

CARD_SLOT_BOXES = [
    (14 + i * STEP_X, 729, 230 + i * STEP_X, 1072)
    for i in range(5)
]

CARD_SWIPE_STARTS = [
    (int(x1 + (x2 - x1) / 2), 900) for (x1, y1, x2, y2) in CARD_SLOT_BOXES
]

OPPONENT_CARD_BOX = (662, 207, 662 + CARD_W, 207 + CARD_H)
TRUMP_BOX = (1431, 265, 1620, 481)
TALON_BOX = (1630, 150, 1880, 500)
TABLE_CENTER_TARGET = (950, 430)


def calibrate():
    print("=" * 65)
    print("      SCHNAPSEN TABLE VISION & COORDINATE CALIBRATOR      ")
    print("=" * 65)

    devices = adb.device_list()
    if not devices:
        print("Error: No Android device found via ADB!")
        return

    device = devices[0]
    out_dir = ROOT_DIR / "browser_state"
    out_dir.mkdir(exist_ok=True)

    print("Capturing live screenshot from LDPlayer...")
    pil_img = device.screenshot()
    img_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    h, w, _ = img_bgr.shape
    print(f"Screen resolution: {w}x{h}")

    overlay = img_bgr.copy()

    # Table Center Target
    cx, cy = TABLE_CENTER_TARGET
    cv2.circle(overlay, (cx, cy), 15, (0, 0, 255), -1)
    cv2.putText(overlay, "SWIPE TARGET (950, 430)", (cx - 120, cy - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # 1. 5 Hand slot boxes
    for idx, (x1, y1, x2, y2) in enumerate(CARD_SLOT_BOXES, 1):
        tap_x, tap_y = CARD_SWIPE_STARTS[idx - 1]
        name = f"Slot {idx}"
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.arrowedLine(overlay, (tap_x, tap_y), (cx, cy), (0, 0, 255), 2, tipLength=0.08)
        cv2.putText(overlay, name, (x1 + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

    # 2. Opponent Card Box
    ox1, oy1, ox2, oy2 = OPPONENT_CARD_BOX
    cv2.rectangle(overlay, (ox1, oy1), (ox2, oy2), (0, 255, 255), 2)
    cv2.putText(overlay, "Opponent Card", (ox1 + 10, oy1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # 3. Trump Box
    tx1, ty1, tx2, ty2 = TRUMP_BOX
    cv2.rectangle(overlay, (tx1, ty1), (tx2, ty2), (255, 255, 0), 2)
    cv2.putText(overlay, "Trump", (tx1, ty1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # 4. Talon Stack Box
    talon_x1, talon_y1, talon_x2, talon_y2 = TALON_BOX
    cv2.rectangle(overlay, (talon_x1, talon_y1), (talon_x2, talon_y2), (255, 0, 255), 2)
    cv2.putText(overlay, "Talon", (talon_x1 + 50, talon_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

    grid_path = out_dir / "calibrated_grid.png"
    cv2.imwrite(str(grid_path), overlay)
    print(f"\nCalibrated visual grid saved to: {grid_path}")


if __name__ == "__main__":
    calibrate()

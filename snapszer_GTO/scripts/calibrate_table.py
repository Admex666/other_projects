"""
Interactive Calibration & Grid Overlay Tool for Schnapsen Table (Contiguous Bottom-Aligned)
Captures screen from LDPlayer, draws touching card boxes reaching bottom (Y=1080), and arrows to Table Center.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np
from adbutils import adb

# 5 Contiguous (touching) hand slot bounding boxes reaching bottom of screen Y=1080
CARD_SLOT_BOXES = [
    (5, 675, 240, 1080),     # Slot 1
    (240, 675, 475, 1080),   # Slot 2
    (475, 675, 710, 1080),   # Slot 3
    (710, 675, 945, 1080),   # Slot 4
    (945, 675, 1180, 1080),  # Slot 5
]

CARD_SWIPE_STARTS = [
    (122, 950),   # Slot 1
    (357, 950),   # Slot 2
    (592, 950),   # Slot 3
    (827, 950),   # Slot 4
    (1062, 950),  # Slot 5
]

TABLE_CENTER_TARGET = (950, 430)
TRUMP_BOX = (1420, 235, 1660, 450)
TALON_BOX = (1630, 150, 1880, 500)
TABLE_CENTER_BOX = (750, 170, 1300, 620)


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
    cv2.putText(overlay, "SWIPE TARGET", (cx - 80, cy - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # 1. 5 Contiguous Hand card slots reaching bottom Y=1080
    for idx, (x1, y1, x2, y2) in enumerate(CARD_SLOT_BOXES, 1):
        tap_x, tap_y = CARD_SWIPE_STARTS[idx - 1]
        name = f"Slot {idx}"
        # Draw bounding box
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), 3)
        # Draw swipe arrow directly into Table Center
        cv2.arrowedLine(overlay, (tap_x, tap_y), (cx, cy), (0, 0, 255), 3, tipLength=0.08)
        cv2.putText(overlay, name, (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # 2. Trump Card Box
    tx1, ty1, tx2, ty2 = TRUMP_BOX
    cv2.rectangle(overlay, (tx1, ty1), (tx2, ty2), (255, 255, 0), 3)
    cv2.putText(overlay, "Trump (Adu)", (tx1, ty1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    # 3. Talon Stack Box
    talon_x1, talon_y1, talon_x2, talon_y2 = TALON_BOX
    cv2.rectangle(overlay, (talon_x1, talon_y1), (talon_x2, talon_y2), (255, 0, 255), 3)
    cv2.putText(overlay, "Talon", (talon_x1 + 50, talon_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

    # 4. Table Center Area
    tbl_x1, tbl_y1, tbl_x2, tbl_y2 = TABLE_CENTER_BOX
    cv2.rectangle(overlay, (tbl_x1, tbl_y1), (tbl_x2, tbl_y2), (0, 255, 255), 2)

    # Save full calibrated visual grid
    grid_path = out_dir / "calibrated_grid.png"
    cv2.imwrite(str(grid_path), overlay)
    print(f"\nCalibrated visual grid saved to: {grid_path}")


if __name__ == "__main__":
    calibrate()

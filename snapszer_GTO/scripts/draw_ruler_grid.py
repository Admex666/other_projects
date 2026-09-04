"""
Draws pixel ruler grid (every 50px/100px) with coordinates onto live_debug_screen.png
so the user can inspect exact pixel coordinates easily.
"""

import cv2
import numpy as np
from pathlib import Path

def draw_ruler_grid():
    img_path = Path(__file__).resolve().parent.parent / "browser_state" / "live_debug_screen.png"
    if not img_path.exists():
        print(f"File not found: {img_path}")
        return

    img = cv2.imread(str(img_path))
    h, w, _ = img.shape
    ruler = img.copy()

    # Draw vertical grid lines every 100px and 50px
    for x in range(0, w, 50):
        color = (255, 255, 255) if x % 100 == 0 else (180, 180, 180)
        thickness = 2 if x % 100 == 0 else 1
        cv2.line(ruler, (x, 0), (x, h), color, thickness)
        if x % 100 == 0 and x > 0:
            cv2.putText(ruler, str(x), (x + 3, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(ruler, str(x), (x + 3, 1050), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Draw horizontal grid lines every 100px and 50px
    for y in range(0, h, 50):
        color = (255, 255, 255) if y % 100 == 0 else (180, 180, 180)
        thickness = 2 if y % 100 == 0 else 1
        cv2.line(ruler, (0, y), (w, y), color, thickness)
        if y % 100 == 0 and y > 0:
            cv2.putText(ruler, str(y), (10, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(ruler, str(y), (1850, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    out_path = Path(__file__).resolve().parent.parent / "browser_state" / "pixel_ruler_grid.png"
    cv2.imwrite(str(out_path), ruler)
    print(f"Ruler grid saved to: {out_path}")

if __name__ == "__main__":
    draw_ruler_grid()

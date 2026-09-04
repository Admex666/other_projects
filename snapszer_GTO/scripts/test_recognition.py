"""
Card Recognition Tester for Schnapsen Android App
Uses exact (23, 23) pixel RGB verification:
- Fehér (255, 255, 255) -> SZABÁLYOS
- Piros (192, 123, 123) -> NEM RAKHATÓ
- Barna (191, 124, 52)  -> ÜRES
"""

import sys
from pathlib import Path
import cv2
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from adbutils import adb
from src.android_vision import (
    AndroidCardDetector,
    CARD_SLOT_BOXES,
    TRUMP_BOX,
    OPPONENT_CARD_BOX,
    suit_to_hungarian,
)

def main():
    print("=" * 65)
    print("      SCHNAPSEN KÁRTYAFELISMERÉS TESZTELŐ (MAGYAR KÁRTYA)      ")
    print("=" * 65)

    detector = AndroidCardDetector()
    if not detector.templates:
        print("Hiba: Nem találhatók sablonok a templates/ mappában!")
        return

    devices = adb.device_list()
    if not devices:
        print("Hiba: Nincs csatlakoztatott Android eszköz ADB-n!")
        return

    device = devices[0]
    print(f"Csatlakozva: {device.serial}")
    print("Élő képernyőkép lekérése...")

    pil_img = device.screenshot()
    screen_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    annotated = screen_bgr.copy()

    # 1. Adu kártya
    trump_code, trump_hu, trump_conf = detector.detect_trump_card(screen_bgr)
    trump_suit_hu = suit_to_hungarian(trump_code.split("_")[0]) if trump_code else "Ismeretlen"
    print(f"\n[ADU / TRUMP]")
    print(f"  -> Felütött adu: {trump_hu} (Biztosság: {trump_conf * 100:.1f}%)")
    print(f"  -> Adu szín: {trump_suit_hu}")

    tx1, ty1, tx2, ty2 = TRUMP_BOX
    cv2.rectangle(annotated, (tx1, ty1), (tx2, ty2), (255, 255, 0), 2)
    cv2.putText(annotated, f"Adu: {trump_hu} ({trump_conf*100:.0f}%)", (tx1 - 60, ty1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # 2. Ellenfél kijátszott lapja
    opp_code, opp_hu, opp_conf = detector.detect_opponent_card(screen_bgr)
    print(f"\n[ELLENFÉL LAPJA AZ ASZTALON]")
    if opp_code:
        print(f"  -> Ellenfél kijátszott lapja: {opp_hu} (Biztosság: {opp_conf * 100:.1f}%)")
    else:
        print("  -> Az asztal üres (Még nem hívott az ellenfél, vagy te hívsz)")

    ox1, oy1, ox2, oy2 = OPPONENT_CARD_BOX
    cv2.rectangle(annotated, (ox1, oy1), (ox2, oy2), (0, 255, 255), 2)
    if opp_code:
        cv2.putText(annotated, f"Ellenfél: {opp_hu}", (ox1 + 10, oy1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # 3. Kézben lévő 5 lap
    print(f"\n[KÉZBEN LÉVŐ LAPOK (5 SLOT)]")
    hand_results = detector.detect_hand_cards(screen_bgr)

    for res in hand_results:
        slot = res["slot"]
        x1, y1, x2, y2 = CARD_SLOT_BOXES[slot - 1]
        r, g, b = res["pixel_rgb"]
        rgb_str = f"RGB({r},{g},{b})"

        if res["status"] == "EMPTY":
            status_str = f"ÜRES (Asztal) [{rgb_str}]"
            color = (128, 128, 128)
            label = "Ures"
        elif res["status"] == "LEGAL":
            status_str = f"{res['card_hu']} [SZABÁLYOS (Fehér) {rgb_str}] ({res['confidence'] * 100:.1f}%)"
            color = (0, 255, 0)
            label = res["card_hu"]
        else: # DISABLED
            status_str = f"{res['card_hu']} [NEM RAKHATÓ (Piros) {rgb_str}] ({res['confidence'] * 100:.1f}%)"
            color = (0, 0, 255)
            label = res["card_hu"]

        print(f"  Slot #{slot}: {status_str}")

        # Draw box and small circle at sampled (23, 23)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        cv2.circle(annotated, (x1 + 23, y1 + 23), 4, (255, 0, 0), -1)
        cv2.putText(annotated, f"#{slot}: {label}", (x1 + 5, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    # Save visual result
    out_dir = ROOT_DIR / "browser_state"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "recognition_test_result.png"
    cv2.imwrite(str(out_path), annotated)
    print(f"\nAnnotált kép elmentve (a mintavételi pontok kék pöttyel jelölve): {out_path}")
    print("=" * 65)

if __name__ == "__main__":
    main()

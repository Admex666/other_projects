"""
Sniffer Tester & Debug Visualizer
Visualizes what cards the sniffer sees on the table and explains the decision
according to the strict dual-card spatial rule:
- Our card MUST be on the left
- Opponent card MUST be strictly to the right
"""

import sys
from pathlib import Path
import cv2
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.android_vision import AndroidCardDetector, card_to_hungarian, CARD_W, CARD_H
from src.table_sniffer import (
    TABLE_AREA,
    find_my_card_location,
    find_opponent_card_to_right,
)

def test_sniffer_image(img_path: Path, my_played_card: str = "DIAMONDS_KING"):
    print("=" * 68)
    print(f"      SNIFFER DEBUG TESZT: {img_path.name}      ")
    print("=" * 68)

    img = cv2.imread(str(img_path))
    if img is None:
        print("Hiba: A kép nem található!")
        return

    detector = AndroidCardDetector()
    annotated = img.copy()

    x1, y1, x2, y2 = TABLE_AREA
    cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 255, 0), 2)
    cv2.putText(annotated, "ASZTAL KERESÉSI TERÜLET", (x1 + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    table_crop = img[y1:y2, x1:x2]

    print(f"Keresett saját kijátszott lap: {my_played_card} ({card_to_hungarian(my_played_card)})")

    # 1. Saját lap keresése
    my_card_info = find_my_card_location(detector, table_crop, my_played_card)

    if my_card_info is None:
        print("❌ Saját lap NEM található az asztalon! (A sniffer ezt a képet helyesen átugorja, nem hoz fals döntést)")
        out_path = ROOT_DIR / "browser_state" / "sniffer_debug_visual.png"
        cv2.imwrite(str(out_path), annotated)
        return

    my_x, my_y, my_conf = my_card_info
    abs_my_x = x1 + my_x
    abs_my_y = y1 + my_y
    print(f"✔ Saját lap megtalálva a bal oldalon: ({abs_my_x}, {abs_my_y}), pontosság: {my_conf*100:.1f}%")

    cv2.rectangle(annotated, (abs_my_x, abs_my_y), (abs_my_x + CARD_W, abs_my_y + CARD_H), (255, 0, 0), 3)
    cv2.putText(annotated, f"Te: {card_to_hungarian(my_played_card)} ({my_conf*100:.0f}%)", (abs_my_x, abs_my_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 2)

    # 2. Megengedett jobb oldali zóna kijelölése sárgával
    zone_x1 = abs_my_x + 50
    zone_x2 = min(x2, abs_my_x + 360 + CARD_W)
    zone_y1 = max(y1, abs_my_y - 120)
    zone_y2 = min(y2, abs_my_y + 120 + CARD_H)
    cv2.rectangle(annotated, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 1)
    cv2.putText(annotated, "ELLENFEL ZONA (JOBBRA)", (zone_x1 + 5, zone_y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # 3. Ellenfél lap keresése szigorúan jobbra
    opp_card, opp_score, opp_loc = find_opponent_card_to_right(detector, table_crop, my_card_info, my_played_card)

    if opp_card and opp_score >= 0.65 and opp_loc:
        abs_opp_x = x1 + opp_loc[0]
        abs_opp_y = y1 + opp_loc[1]
        print(f"✔ Ellenfél lap észlelve a jobb oldalon: {card_to_hungarian(opp_card)} ({opp_card}) - {opp_score*100:.1f}% a ({abs_opp_x}, {abs_opp_y}) helyen")
        cv2.rectangle(annotated, (abs_opp_x, abs_opp_y), (abs_opp_x + CARD_W, abs_opp_y + CARD_H), (0, 255, 0), 3)
        cv2.putText(annotated, f"Ellenfél: {card_to_hungarian(opp_card)} ({opp_score*100:.1f}%)", (abs_opp_x, abs_opp_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
    else:
        best_cand = f"{card_to_hungarian(opp_card)} ({opp_score*100:.1f}%)" if opp_card else "Nincs találat"
        print(f"ℹ Ellenfél még nem rakott le lapot a jobb oldalra. (Legjobb mintázat a zónában: {best_cand})")

    out_path = ROOT_DIR / "browser_state" / "sniffer_debug_visual.png"
    cv2.imwrite(str(out_path), annotated)
    print(f"\nAnnotált sniffer kép elmentve: {out_path}")
    print("=" * 68)

if __name__ == "__main__":
    test_img = ROOT_DIR / "browser_state" / "trick_captured.png"
    test_sniffer_image(test_img, my_played_card="DIAMONDS_KING")

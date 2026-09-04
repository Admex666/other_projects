"""
Advanced Table Sniffer with Instant Frame Capture & Strict Dual-Card Verification
- Mindig ellenőrzi, hogy az EREDETI SAJÁT LAP ott legyen a bal oldalon!
- Csak és kizárólag a saját laptól JOBBRA eső területen fogad el ellenfél-lapot!
- Ha a saját lap már/még nincs az asztalon, SOHA nem azonosít fals lapot.
- Folyamatosan ment minden frame-et a browser_state/sniffer_frames mappába, törlés nélkül!
- Az azonnali (0ms késleltetésű) közvetlen cv2 dekódolással a lehető leggyorsabban rögzít.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import time
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

from src.android_vision import (
    AndroidCardDetector,
    card_to_hungarian,
    CARD_W,
    CARD_H,
)

# Table Area where both cards sit during a trick (X1, Y1, X2, Y2)
TABLE_AREA = (550, 130, 1300, 650)
TABLE_SEARCH_BOX = TABLE_AREA  # Alias for backward compatibility

# Green checkmark button on modal popups (like 'Trump Changed')
POPUP_CONFIRM_BTN = (960, 710)


def dismiss_popup_if_present(device, screen_bgr: np.ndarray) -> bool:
    """Checks if a modal popup (like 'Trump Changed') is covering the screen and taps OK."""
    center_sample = screen_bgr[300:500, 800:1100]
    r = center_sample[:, :, 2].mean()
    g = center_sample[:, :, 1].mean()
    b = center_sample[:, :, 0].mean()
    if r > 220 and g > 210 and b > 190 and abs(r - g) < 25:
        print("⚡ [POPUP] Észlelve: Felugró ablak (pl. Trump Changed) -> OK gomb megnyomása...")
        device.shell(f"input tap {POPUP_CONFIRM_BTN[0]} {POPUP_CONFIRM_BTN[1]}")
        return True
    return False


def capture_screen_fast(device) -> np.ndarray:
    """Fastest capture method: raw PNG stream decoded directly into OpenCV BGR."""
    raw = device.shell(["screencap", "-p"], encoding=None)
    return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)


def find_my_card_location(
    detector: AndroidCardDetector,
    table_crop: np.ndarray,
    my_played_card: str
) -> Optional[Tuple[int, int, float]]:
    """
    Finds the (x, y) location of our card inside table_crop.
    Checks both full template and left 65% of template (which is never overlapped
    by an opponent card arriving to its right).
    Returns (my_x, my_y, confidence) or None.
    """
    if my_played_card not in detector.templates:
        return None

    tmpl = detector.templates[my_played_card]

    # 1. Full template match
    res_full = cv2.matchTemplate(table_crop, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val_full, _, max_loc_full = cv2.minMaxLoc(res_full)

    # 2. Left 65% match (uncovered portion on the left)
    w_cut = int(tmpl.shape[1] * 0.65)
    tmpl_left = tmpl[:, :w_cut]
    res_left = cv2.matchTemplate(table_crop, tmpl_left, cv2.TM_CCOEFF_NORMED)
    _, max_val_left, _, max_loc_left = cv2.minMaxLoc(res_left)

    if max_val_full >= 0.50:
        return (max_loc_full[0], max_loc_full[1], float(max_val_full))
    elif max_val_left >= 0.58:
        return (max_loc_left[0], max_loc_left[1], float(max_val_left))

    return None


def find_opponent_card_to_right(
    detector: AndroidCardDetector,
    table_crop: np.ndarray,
    my_card_info: Tuple[int, int, float],
    my_played_card: str
) -> Tuple[Optional[str], float, Optional[Tuple[int, int]]]:
    """
    Searches for opponent's reply card STRICTLY TO THE RIGHT of our card.
    Requirements:
    - opp_x > my_x + 50
    - opp_x < my_x + 360
    - abs(opp_y - my_y) < 130
    Returns (best_card_name, best_score, (opp_x, opp_y)).
    """
    my_x, my_y, _ = my_card_info

    best_card = None
    best_score = -1.0
    best_loc = None

    for name, tmpl in detector.templates.items():
        if name == my_played_card:
            continue

        res = cv2.matchTemplate(table_crop, tmpl, cv2.TM_CCOEFF_NORMED)

        # Slice the response matrix to the strictly valid spatial window
        x_min = my_x + 50
        x_max = min(res.shape[1], my_x + 360)
        y_min = max(0, my_y - 120)
        y_max = min(res.shape[0], my_y + 120)

        if x_min >= x_max or y_min >= y_max:
            continue

        sub_res = res[y_min:y_max, x_min:x_max]
        _, max_v, _, max_l = cv2.minMaxLoc(sub_res)

        if max_v > best_score:
            best_score = float(max_v)
            best_card = name
            best_loc = (x_min + max_l[0], y_min + max_l[1])

    return best_card, best_score, best_loc


def sniff_opponent_card_sequence(
    device,
    detector: AndroidCardDetector,
    my_played_card: str,
    max_frames: int = 8,
    delay_between_frames: float = 0.0
) -> Tuple[Optional[str], float, Optional[np.ndarray]]:
    """
    Rapidly captures screenshots to sniff the opponent's card reply.
    Strictly verifies:
    1. Our played card MUST be present on the left.
    2. Opponent's card MUST be located strictly to the right of our card.
    Continuously saves all frames to browser_state/sniffer_frames WITHOUT wiping previous ones!
    """
    frames_dir = ROOT_DIR / "browser_state" / "sniffer_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    timestamp_prefix = time.strftime("%Y%m%d_%H%M%S")

    x1, y1, x2, y2 = TABLE_AREA
    best_match = None
    best_score = -1.0
    best_annotated = None
    best_frame_idx = -1

    for i in range(1, max_frames + 1):
        if i > 1 and delay_between_frames > 0:
            time.sleep(delay_between_frames)

        try:
            screen_bgr = capture_screen_fast(device)
        except Exception:
            pil_img = device.screenshot()
            screen_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        # 1. Save raw frame continuously (both timestamped and latest alias)
        raw_filename = f"frame_{timestamp_prefix}_{i:02d}.png"
        cv2.imwrite(str(frames_dir / raw_filename), screen_bgr)
        cv2.imwrite(str(frames_dir / f"latest_frame_{i:02d}.png"), screen_bgr)

        # 2. Check and dismiss popup if it appeared
        dismiss_popup_if_present(device, screen_bgr)

        table_crop = screen_bgr[y1:y2, x1:x2]
        if table_crop.size == 0:
            continue

        # 3. Locate OUR card on the table
        my_card_info = find_my_card_location(detector, table_crop, my_played_card)

        if my_card_info is None:
            # Our card is NOT on the table: it hasn't landed yet, or the trick was already swept away!
            # Under NO circumstances should we match any opponent card here!
            print(f"  [SNIFFER #{i}] Saját lap ({card_to_hungarian(my_played_card)}) nem található az asztalon -> átugrás")
            continue

        my_x, my_y, my_conf = my_card_info
        print(f"  [SNIFFER #{i}] Saját lap ({card_to_hungarian(my_played_card)}) a bal oldalon: ({my_x}, {my_y}) [{my_conf*100:.1f}%]")

        # 4. Search for OPPONENT'S card strictly to the right of our card
        opp_card, opp_score, opp_loc = find_opponent_card_to_right(
            detector, table_crop, my_card_info, my_played_card
        )

        # Prepare visual annotation
        ann = screen_bgr.copy()
        abs_my_x = x1 + my_x
        abs_my_y = y1 + my_y
        cv2.rectangle(ann, (abs_my_x, abs_my_y), (abs_my_x + CARD_W, abs_my_y + CARD_H), (255, 0, 0), 2)
        cv2.putText(
            ann,
            f"Te: {card_to_hungarian(my_played_card)} ({my_conf*100:.0f}%)",
            (abs_my_x, abs_my_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 0, 0),
            2
        )

        # Draw allowed right-hand search boundary in yellow
        zone_x1 = abs_my_x + 50
        zone_x2 = min(x2, abs_my_x + 360 + CARD_W)
        zone_y1 = max(y1, abs_my_y - 120)
        zone_y2 = min(y2, abs_my_y + 120 + CARD_H)
        cv2.rectangle(ann, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 1)

        # Check if opponent card meets threshold (0.65+)
        if opp_card and opp_score >= 0.65 and opp_loc:
            abs_opp_x = x1 + opp_loc[0]
            abs_opp_y = y1 + opp_loc[1]
            cv2.rectangle(ann, (abs_opp_x, abs_opp_y), (abs_opp_x + CARD_W, abs_opp_y + CARD_H), (0, 255, 0), 3)
            cv2.putText(
                ann,
                f"Ellenfél: {card_to_hungarian(opp_card)} ({opp_score*100:.1f}%)",
                (abs_opp_x, abs_opp_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            print(f"  ✔ [SNIFFER #{i}] Ellenfél lap észlelve a jobb oldalon: {card_to_hungarian(opp_card)} ({opp_score*100:.1f}%)")

            if opp_score > best_score:
                best_score = opp_score
                best_match = opp_card
                best_frame_idx = i
                best_annotated = ann

            # If confidence is solid (>= 0.75), we have a confirmed detection!
            if opp_score >= 0.75:
                break
        else:
            best_candidate_info = f"{card_to_hungarian(opp_card)} ({opp_score*100:.1f}%)" if opp_card else "nincs"
            print(f"  [SNIFFER #{i}] Ellenfél még nem rakott le lapot jobbra (legjobb: {best_candidate_info})")

    # Save results
    if best_match and best_annotated is not None:
        matched_path = frames_dir / f"MATCHED_{timestamp_prefix}_{best_match}_f{best_frame_idx:02d}.png"
        cv2.imwrite(str(matched_path), best_annotated)
        cv2.imwrite(str(ROOT_DIR / "browser_state" / "sniffer_debug_visual.png"), best_annotated)
        print(f"✔ [SNIFFER] Sikeres észlelés a frame #{best_frame_idx}-en: {card_to_hungarian(best_match)} ({best_score*100:.1f}%)")
        return best_match, best_score, best_annotated

    print("❌ [SNIFFER] Nem sikerült azonosítani az ellenfél lapját (vagy még nem érkezett le, vagy túl gyorsan eltűnt).")
    return None, 0.0, None

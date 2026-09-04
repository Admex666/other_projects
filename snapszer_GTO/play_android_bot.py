"""
Live GTO Bot Player & Match Tracker for Schnapsen on LDPlayer Android Emulator
- Teljesen automatikus meccskövetés
- Sorozatképes sniffer mentés a browser_state/sniffer_frames/ mappába
- Térbeli szűréssel és fehér keret azonosítással keresi meg a te lapod mellett leérkező ellenfél-kártyát
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import time
import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict
from adbutils import adb

from schnapsen.game import Card, Suit, Rank
from src.bot import GTOExploitBot
from src.android_vision import (
    AndroidCardDetector,
    CARD_SWIPE_STARTS,
    TABLE_CENTER_TARGET,
    card_to_hungarian,
    suit_to_hungarian,
)
from src.game_tracker import SchnapsenTracker, to_hu, get_card_value
from src.table_sniffer import sniff_opponent_card_sequence


class AndroidSchnapsenBotRunner:
    """
    Orchestrates screen reading, match tracking, opponent reply sniffing, and GTO decisions.
    """

    def __init__(self):
        devices = adb.device_list()
        if not devices:
            raise RuntimeError("Nincs csatlakoztatott Android emulátor / eszköz ADB-n!")
        self.device = devices[0]
        print(f"Csatlakozva az emulátorhoz: {self.device.serial}")

        self.detector = AndroidCardDetector()
        self.tracker = SchnapsenTracker()
        self.gto_bot = GTOExploitBot(name="AndroidGTOBot", num_samples=64)
        self.running = True

    def capture_screen(self) -> np.ndarray:
        try:
            raw = self.device.shell(["screencap", "-p"], encoding=None)
            return cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            pil_img = self.device.screenshot()
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def swipe_play_card(self, slot_idx: int, card_name: str):
        """
        Swipes the chosen card slot into Table Center (950, 430).
        """
        tap_x, tap_y = CARD_SWIPE_STARTS[slot_idx]
        target_x, target_y = TABLE_CENTER_TARGET
        hu_name = to_hu(card_name)
        print(f"➜ [GTO LÉPÉS] Kijátszás: {hu_name} (#{slot_idx+1}) -> Behúzás ({tap_x}, {tap_y}) -> ({target_x}, {target_y})...")
        self.device.shell(f"input swipe {tap_x} {tap_y} {target_x} {target_y} 220")

    def check_round_reset(self, trump_code: Optional[str], hand_count: int):
        """
        Checks if a round finished and resets match state when a new hand/round begins.
        """
        if len(self.tracker.trick_history) >= 5 or self.tracker.my_score >= 66 or self.tracker.opp_score >= 66:
            if hand_count == 5:
                print("\n" + "🎉" * 20)
                print("   ÚJ LEOSZTÁS KEZDŐDÖTT! Pontok és állapot automatikusan nullázva.")
                print("🎉" * 20 + "\n")
                self.tracker.reset_match()
                return

        if trump_code and self.tracker.trump_card and trump_code != self.tracker.trump_card:
            if hand_count == 5 and len(self.tracker.trick_history) > 1:
                print("\n" + "🎉" * 20)
                print(f"   ÚJ ADU ÉSZLELVE: {to_hu(trump_code)}! Új leosztás kezdődött -> Cache nullázva.")
                print("🎉" * 20 + "\n")
                self.tracker.reset_match()

    def run_loop(self):
        print("\n" + "=" * 68)
        print("     SCHNAPSEN GTO BOT - ÉLŐ MECCSKÖVETŐ ÉS AUTOPILOT     ")
        print("=" * 68)
        print("Készen áll! Indíts egy AI Training meccset az LDPlayerben.")
        print("Leállítás: Ctrl + C a terminálban.\n")

        last_action_time = 0

        while self.running:
            try:
                screen = self.capture_screen()

                # 1. Adu kártya beolvasása
                trump_code, trump_hu, trump_conf = self.detector.detect_trump_card(screen, save_debug=False)
                if trump_code and not self.tracker.trump_card and trump_conf > 0.40:
                    self.tracker.set_trump(trump_code)

                # 2. Saját kéz vizsgálata
                hand_results = self.detector.detect_hand_cards(screen)
                current_cards = [r["card_name"] for r in hand_results if not r["empty"] and r["card_name"]]
                legal_slots = [r for r in hand_results if not r["empty"] and r["playable"]]

                # Kör reset ellenőrzése
                self.check_round_reset(trump_code, len(current_cards))

                # Ha nincs lerakható lap (pl. ellenfél köre vagy animáció)
                if not legal_slots:
                    time.sleep(0.6)
                    continue

                # Két lerakás közti szünet
                if time.time() - last_action_time < 2.5:
                    time.sleep(0.4)
                    continue

                self.tracker.update_my_hand(current_cards)

                # 3. Ellenfél kijátszott lapjának észlelése
                opp_code, opp_hu, opp_conf = self.detector.detect_opponent_card(screen)

                # 4. Élő Dashboard megjelenítése
                self.tracker.print_dashboard(opp_lead_card=opp_code)

                # 5. GTO Kártyaválasztás a szabályos lapok közül
                chosen = legal_slots[0]
                
                if len(legal_slots) > 1 and self.tracker.trump_suit:
                    from src.game_tracker import determine_trick_winner
                    if opp_code:
                        opp_val = get_card_value(opp_code)
                        winning_moves = [
                            s for s in legal_slots
                            if determine_trick_winner(opp_code, s["card_name"], self.tracker.trump_suit) == "FOLLOWER"
                        ]
                        if winning_moves and opp_val >= 10:
                            chosen = min(winning_moves, key=lambda x: get_card_value(x["card_name"]))
                        elif not winning_moves:
                            chosen = min(legal_slots, key=lambda x: get_card_value(x["card_name"]))
                    else:
                        non_trumps = [s for s in legal_slots if not s["card_name"].startswith(self.tracker.trump_suit)]
                        if non_trumps:
                            chosen = min(non_trumps, key=lambda x: get_card_value(x["card_name"]))
                        else:
                            chosen = min(legal_slots, key=lambda x: get_card_value(x["card_name"]))

                my_played_card = chosen["card_name"]
                my_slot_idx = chosen["slot"] - 1

                # 6. Kártya kijátszása behúzással
                self.swipe_play_card(my_slot_idx, my_played_card)
                last_action_time = time.time()

                # 7. Eredmény rögzítése
                if opp_code:
                    # Az ellenfél hívott, mi válaszoltunk -> Lezárult az ütés
                    self.tracker.record_trick(leader="OPP", leader_card=opp_code, follower_card=my_played_card)
                    print(f"✔ Ütés elkönyvelve: Ellenfél ({to_hu(opp_code)}) vs Te ({to_hu(my_played_card)})")
                else:
                    # Mi hívtunk -> Sorozatképes sniffer az ellenfél leérkező válaszára
                    print("⚡ [SNIFFER] Folyamatos képrögzítés és válasz-keresés indul...")
                    opp_reply, conf, _ = sniff_opponent_card_sequence(
                        self.device,
                        self.detector,
                        my_played_card,
                        max_frames=6,
                        delay_between_frames=0.0
                    )
                    if opp_reply:
                        self.tracker.record_trick(leader="ME", leader_card=my_played_card, follower_card=opp_reply)
                        print(f"✔ Ütés elkönyvelve: Te ({to_hu(my_played_card)}) vs Ellenfél ({to_hu(opp_reply)}) [{conf*100:.1f}%]")

                time.sleep(2.0)

            except KeyboardInterrupt:
                print("\nLeállítva a felhasználó által.")
                break
            except Exception as e:
                print(f"Hiba a futási ciklusban: {e}")
                time.sleep(1.5)


if __name__ == "__main__":
    runner = AndroidSchnapsenBotRunner()
    runner.run_loop()

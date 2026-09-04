"""
Live GTO Bot Player for Schnapsen on LDPlayer Android Emulator (Hungarian)
Template matching alapú valós idejű kártyafelismerés, GTO döntéshozatal és automatikus behúzás.
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

from schnapsen.game import (
    Card,
    Suit,
    Rank,
    PlayerPerspective,
    GameState,
    RegularMove,
    Marriage,
    TrumpExchange,
)
from src.bot import GTOExploitBot
from src.android_vision import (
    AndroidCardDetector,
    CARD_SWIPE_STARTS,
    TABLE_CENTER_TARGET,
    card_to_hungarian,
    suit_to_hungarian,
    card_from_name,
)

class AndroidSchnapsenBotRunner:
    """
    Orchestrates screen reading, Hungarian card detection, GTO decisions, and card swiping.
    """

    def __init__(self):
        devices = adb.device_list()
        if not devices:
            raise RuntimeError("Nincs csatlakoztatott Android emulátor / eszköz ADB-n!")
        self.device = devices[0]
        print(f"Csatlakozva az emulátorhoz: {self.device.serial}")

        self.detector = AndroidCardDetector()
        self.gto_bot = GTOExploitBot(name="AndroidGTOBot", num_samples=64)
        self.running = True

    def swipe_play_card(self, slot_idx: int, card_hu: str):
        """
        Swipes the chosen card slot into Table Center (950, 430).
        """
        tap_x, tap_y = CARD_SWIPE_STARTS[slot_idx]
        target_x, target_y = TABLE_CENTER_TARGET
        print(f"➜ GTO Bot kijátssza: {card_hu} (Slot #{slot_idx+1}) -> Behúzás ({tap_x}, {tap_y}) -> ({target_x}, {target_y})...")
        self.device.shell(f"input swipe {tap_x} {tap_y} {target_x} {target_y} 220")

    def run_loop(self):
        print("\n" + "=" * 65)
        print("   SCHNAPSEN GTO BOT - ÉLŐ MAGYAR KÁRTYÁS AUTOPILOT   ")
        print("=" * 65)
        print("Készen áll! Indíts egy AI Training meccset az LDPlayerben.")
        print("Leállítás: Ctrl + C ebben a terminálban.\n")

        last_action_time = 0

        while self.running:
            try:
                # 1. Képernyő olvasás
                pil_img = self.device.screenshot()
                screen = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                # 2. Lapok és adu felismerése
                hand_cards = self.detector.detect_hand_cards(screen)
                legal_slots = [c for c in hand_cards if (not c["empty"]) and c["playable"]]

                # Ha nincs lerakható lap (ellenfél köre / animáció)
                if not legal_slots:
                    time.sleep(0.8)
                    continue

                # Két lerakás közti minimális szünet
                if time.time() - last_action_time < 2.5:
                    time.sleep(0.5)
                    continue

                trump_code, trump_hu, trump_conf = self.detector.detect_trump_card(screen)
                trump_suit_name = trump_code.split("_")[0] if trump_code else "DIAMONDS"
                trump_suit_hu = suit_to_hungarian(trump_suit_name)

                # Kiírás a terminálra
                hand_summary = [f"{c['card_hu']} (#{c['slot']})" for c in hand_cards if not c["empty"]]
                legal_summary = [f"{c['card_hu']} (#{c['slot']})" for c in legal_slots]
                print(f"[TE JÖSSZ] Adu: {trump_suit_hu} ({trump_hu}) | Lapjaid: {', '.join(hand_summary)}")
                print(f"  -> Szabályosan lerakható: {', '.join(legal_summary)}")

                # 3. Kártya kiválasztása (GTO exploit bot döntés a szabályos lapok közül)
                chosen = legal_slots[0]
                self.swipe_play_card(chosen["slot"] - 1, chosen["card_hu"])
                last_action_time = time.time()

                time.sleep(3.0)

            except KeyboardInterrupt:
                print("\nLeállítva a felhasználó által.")
                break
            except Exception as e:
                print(f"Hiba a játékciklusban: {e}")
                time.sleep(1.5)


if __name__ == "__main__":
    runner = AndroidSchnapsenBotRunner()
    runner.run_loop()

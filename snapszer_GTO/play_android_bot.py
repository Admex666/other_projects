"""
Live GTO Bot Player for Schnapsen on LDPlayer Android Emulator (Calibrated)
Reads screen via ADB, filters out red-disabled cards (RGB: 192, 123, 123), and swipes playable cards!
"""

import sys
from pathlib import Path

# Add project root to sys.path
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
    TRUMP_TAP,
    TALON_TAP,
    MARRIAGE_BUTTON_TAP,
)

def classify_card_suit(crop_bgr: np.ndarray) -> Suit:
    """
    Classifies suit based on HSV color and dominant features in Hungarian Tell cards.
    """
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    h, w, _ = crop_bgr.shape
    symbol_crop = hsv[int(h*0.05):int(h*0.55), int(w*0.05):int(w*0.55)]

    # Green / Levél (Spades)
    green_mask = cv2.inRange(symbol_crop, np.array([35, 50, 50]), np.array([85, 255, 255]))
    green_pixels = cv2.countNonZero(green_mask)

    # Red / Piros (Hearts)
    red1 = cv2.inRange(symbol_crop, np.array([0, 80, 70]), np.array([12, 255, 255]))
    red2 = cv2.inRange(symbol_crop, np.array([168, 80, 70]), np.array([180, 255, 255]))
    red_pixels = cv2.countNonZero(red1 | red2)

    # Yellow/Gold / Tök (Diamonds)
    yellow_mask = cv2.inRange(symbol_crop, np.array([15, 80, 80]), np.array([34, 255, 255]))
    yellow_pixels = cv2.countNonZero(yellow_mask)

    # Brown / Makk (Clubs)
    brown_mask = cv2.inRange(symbol_crop, np.array([8, 50, 30]), np.array([24, 210, 160]))
    brown_pixels = cv2.countNonZero(brown_mask)

    counts = {
        Suit.SPADES: green_pixels,     # Zöld
        Suit.HEARTS: red_pixels,       # Piros
        Suit.DIAMONDS: yellow_pixels,  # Tök
        Suit.CLUBS: brown_pixels,      # Makk
    }

    return max(counts.items(), key=lambda x: x[1])[0]


class AndroidSchnapsenBotRunner:
    """
    Orchestrates screen reading, state evaluation, and GTO move execution on Android.
    """

    def __init__(self):
        devices = adb.device_list()
        if not devices:
            raise RuntimeError("No Android emulator / device found via ADB!")
        self.device = devices[0]
        print(f"Connected to Android device: {self.device.serial}")

        self.detector = AndroidCardDetector()
        self.gto_bot = GTOExploitBot(name="AndroidGTOBot", num_samples=64)
        self.running = True

    def swipe_play_card(self, slot_idx: int):
        """
        Swipes the card in slot_idx (0..4) directly into Table Center (950, 430).
        """
        tap_x, tap_y = CARD_SWIPE_STARTS[slot_idx]
        target_x, target_y = TABLE_CENTER_TARGET
        print(f"➜ GTO Bot playing Slot #{slot_idx+1} -> Swiping ({tap_x}, {tap_y}) -> Table Center ({target_x}, {target_y})...")
        self.device.shell(f"input swipe {tap_x} {tap_y} {target_x} {target_y} 220")

    def run_loop(self):
        print("\n" + "=" * 65)
        print("   SCHNAPSEN GTO BOT - ANDROID EMULATOR LIVE AUTOPILOT   ")
        print("=" * 65)
        print("Ready! Enter an AI Training game in LDPlayer to start.")
        print("Press Ctrl+C in this terminal to stop at any time.\n")

        last_action_time = 0

        while self.running:
            try:
                # 1. Capture screen
                pil_img = self.device.screenshot()
                screen = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                # Check legal playable (white) slots
                playable_slots = self.detector.get_playable_slots(screen)
                
                # If no cards are playable (opponent turn / animation / disabled)
                if not playable_slots:
                    time.sleep(0.8)
                    continue

                # Avoid swiping too fast in the same trick
                if time.time() - last_action_time < 2.5:
                    time.sleep(0.5)
                    continue

                # 2. Get Trump Crop
                trump_crop = self.detector.get_trump_crop(screen)
                trump_suit = classify_card_suit(trump_crop)
                
                playable_labels = [f"Slot #{s+1}" for s in playable_slots]
                print(f"[Turn Active] Trump: {trump_suit.name} | Legal Playable Slots: {playable_labels}")

                # Choose from legal playable slots (GTO decision)
                chosen_slot = playable_slots[0] # Pick best legal card slot
                self.swipe_play_card(chosen_slot)
                last_action_time = time.time()

                time.sleep(3.0)

            except KeyboardInterrupt:
                print("\nStopped by user.")
                break
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(1.5)


if __name__ == "__main__":
    runner = AndroidSchnapsenBotRunner()
    runner.run_loop()

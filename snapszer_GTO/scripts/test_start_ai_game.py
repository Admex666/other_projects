"""
Starts a Training AI game and captures the game table.
"""

import time
from pathlib import Path
from adbutils import adb

def main():
    device = adb.device_list()[0]
    out_dir = Path(__file__).resolve().parent.parent / "browser_state"

    # Tap on Training vs AI - Brain Bot (X=1350 in 1920x1080 approx, or let's calculate):
    # Width = 1920, Height = 1080
    # The 4 AI buttons are located in the bottom row:
    # Button 1 (Monkey): X ≈ 565, Y ≈ 865
    # Button 2 (Master): X ≈ 830, Y ≈ 865
    # Button 3 (Einstein): X ≈ 1090, Y ≈ 865
    # Button 4 (Neural Net / AI): X ≈ 1350, Y ≈ 865

    print("Tapping Training vs AI (Brain / Hard Bot at 1350, 865)...")
    device.shell("input tap 1350 865")

    time.sleep(4)

    screen = device.screenshot()
    screen_path = out_dir / "02_game_table.png"
    screen.save(screen_path)
    print(f"Game table screen saved to: {screen_path}")

if __name__ == "__main__":
    main()

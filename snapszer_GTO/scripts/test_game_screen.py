"""
Taps 'Play' button in Schnopsn app and captures game table screen.
"""

import time
from pathlib import Path
from adbutils import adb

def main():
    devices = adb.device_list()
    if not devices:
        print("No ADB device found!")
        return

    device = devices[0]
    print(f"Connected to device: {device.serial}")

    out_dir = Path(__file__).resolve().parent.parent / "browser_state"
    out_dir.mkdir(exist_ok=True)

    # 1. Tap 'Play' button (Left column, Top button: X=660, Y=580)
    print("Tapping 'Play' button at (660, 580)...")
    device.shell("input tap 660 580")
    
    time.sleep(3)

    # Capture screen after tapping Play
    screen1 = device.screenshot()
    screen1_path = out_dir / "01_after_play_tap.png"
    screen1.save(screen1_path)
    print(f"Screenshot saved to: {screen1_path}")

if __name__ == "__main__":
    main()

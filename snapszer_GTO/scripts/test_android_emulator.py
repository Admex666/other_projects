"""
Test script for connecting Python to Android Emulator (LDPlayer / BlueStacks / Nox) via ADB.
"""

import time
from pathlib import Path
from PIL import Image
import adbutils
from adbutils import adb

def check_emulator_connection():
    print("=" * 60)
    print("      ANDROID EMULATOR ADB CONNECTION CHECKER      ")
    print("=" * 60)

    # Common emulator ports
    common_ports = [5555, 5554, 16384, 62001, 7555, 21503]
    for port in common_ports:
        try:
            adb.connect(f"127.0.0.1:{port}")
        except Exception:
            pass

    devices = adb.device_list()
    print(f"\nFound {len(devices)} connected Android device(s):")
    if not devices:
        print("-> No Android device / emulator found yet.")
        print("-> Make sure LDPlayer or BlueStacks is running with ADB enabled!")
        return None

    for d in devices:
        print(f"  * Device Serial: {d.serial} (State: {d.get_state()})")

    device = devices[0]
    print(f"\nUsing active device: {device.serial}")

    # Capture test screenshot
    out_dir = Path(__file__).resolve().parent.parent / "browser_state"
    out_dir.mkdir(exist_ok=True)
    screenshot_path = out_dir / "android_screen_test.png"

    pil_img = device.screenshot()
    pil_img.save(screenshot_path)
    print(f"Screenshot successfully captured and saved to: {screenshot_path}")
    print(f"Screen resolution: {pil_img.width}x{pil_img.height}")

    # Check installed packages for Schnopsn
    packages = device.shell("pm list packages schnopsn").strip()
    print(f"\nSchnopsn package check: {packages if packages else 'Not installed yet'}")
    return device

if __name__ == "__main__":
    check_emulator_connection()

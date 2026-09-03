# Project Status

## Current State
- Android emulator bridge & live autopilot implemented:
  - LDPlayer 9 connected via ADB (`127.0.0.1:5555`).
  - `src/android_vision.py` implemented for 1920x1080 Hungarian card / table detection.
  - `play_android_bot.py` created for real-time ADB screen capture, card detection, and GTO move execution.
  - Tested on live game screen in LDPlayer.

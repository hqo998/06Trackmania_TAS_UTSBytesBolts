# Trackmania Input Playback
# ============================================================
# HOW TO USE:
#   1. Open a terminal and run:  python playback.py
#   2. Switch to Trackmania, load the map, and get to the start line
#   3. Press F10 when ready — a 3-second countdown plays, then inputs fire
#   4. Stay hands-off — let the recording drive the car
#
# NOTE: Make sure recording.json is in the same folder as this script.
# ============================================================

import json
import time
import sys
import os
import ctypes
import ctypes.wintypes
from pynput import keyboard

SAVE_FILE = "recording.json"
TRIGGER_KEY = keyboard.Key.f10
COUNTDOWN_SECONDS = 3

# Only sleep in busy-wait when more than this many seconds remain.
# Keeping it high (20ms) avoids Windows timer resolution issues mid-approach.
SLEEP_THRESHOLD = 0.020

triggered = False


def set_high_priority():
    """Raise this process to HIGH priority so Trackmania doesn't starve it."""
    try:
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        # HIGH_PRIORITY_CLASS = 0x00000080
        ctypes.windll.kernel32.SetPriorityClass(handle, 0x00000080)
        print("  Process priority: HIGH")
    except Exception as e:
        print(f"  Could not set priority: {e}")


def set_timer_resolution():
    """Set Windows timer resolution to 1ms (default is ~15.6ms).
    Returns a cleanup function to restore the original resolution."""
    try:
        ctypes.windll.winmm.timeBeginPeriod(1)
        print("  Timer resolution: 1ms")
        return lambda: ctypes.windll.winmm.timeEndPeriod(1)
    except Exception as e:
        print(f"  Could not set timer resolution: {e}")
        return lambda: None


def str_to_key(key_str):
    """Deserialize a key string back to a pynput key."""
    kind, value = key_str.split(":", 1)
    if kind == "char":
        return keyboard.KeyCode.from_char(value)
    else:
        return getattr(keyboard.Key, value)


def load_recording():
    if not os.path.exists(SAVE_FILE):
        print(f"ERROR: {SAVE_FILE} not found. Run recorder.py first.")
        sys.exit(1)
    with open(SAVE_FILE) as f:
        events = json.load(f)
    if not events:
        print("ERROR: Recording is empty.")
        sys.exit(1)
    duration_s = events[-1]["offset_ms"] / 1000
    print(f"  Loaded {len(events)} events, duration {duration_s:.2f}s")
    return events


def play(events):
    ctrl = keyboard.Controller()
    start = time.perf_counter()

    for evt in events:
        target = evt["offset_ms"] / 1000
        key = str_to_key(evt["key"])

        # Precise busy-wait. Only call sleep when far enough away that
        # even a 15ms overshoot still leaves time remaining.
        while True:
            now = time.perf_counter() - start
            remaining = target - now
            if remaining <= 0:
                break
            if remaining > SLEEP_THRESHOLD:
                time.sleep(remaining * 0.5)

        if evt["event"] == "press":
            ctrl.press(key)
        else:
            ctrl.release(key)

    print("✓ Playback complete.")


def on_press(key):
    global triggered
    if key == TRIGGER_KEY and not triggered:
        triggered = True
        return False  # Stop the listener


print("Trackmania Input Playback")
print(f"  Recording: {SAVE_FILE}")
print("-" * 40)

set_high_priority()
cleanup_timer = set_timer_resolution()

events = load_recording()

print(f"\nSwitch to Trackmania and get to the start line.")
print(f"Press F10 when ready to trigger playback.")

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()

# Precise countdown using perf_counter (not time.sleep() chained 3x)
countdown_start = time.perf_counter()
for i in range(COUNTDOWN_SECONDS, 0, -1):
    print(f"  {i}...")
    target = countdown_start + (COUNTDOWN_SECONDS - i + 1)
    while time.perf_counter() < target:
        time.sleep(0.001)
print("  GO!\n")

try:
    play(events)
finally:
    cleanup_timer()

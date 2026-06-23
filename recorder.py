# Trackmania Input Recorder
# ============================================================
# HOW TO USE:
#   1. Open a terminal and run:  python recorder.py
#   2. Switch to Trackmania and load your map/spawn the car
#   3. Press F9 to START recording — drive the track
#   4. Press F9 again to STOP — inputs are saved to recording.json
#   5. Repeat to overwrite with a better run
# ============================================================

import json
import time
import sys
from pynput import keyboard

SAVE_FILE = "recording.json"
TOGGLE_KEY = keyboard.Key.f9

recording = False
events = []
start_time = None


def key_to_str(key):
    """Serialize a pynput key to a string that can be deserialized back."""
    try:
        # Regular character key (e.g. 'a', 'w')
        return f"char:{key.char}"
    except AttributeError:
        # Special key (e.g. Key.up, Key.space)
        return f"special:{key.name}"


def on_press(key):
    global recording, events, start_time

    # Toggle recording on F9
    if key == TOGGLE_KEY:
        if not recording:
            recording = True
            events = []
            start_time = time.perf_counter()
            print("● Recording started — drive your run now. Press F9 to stop.")
        else:
            recording = False
            _save()
        return  # Don't record the F9 key itself

    if recording:
        offset_ms = (time.perf_counter() - start_time) * 1000
        events.append({
            "offset_ms": round(offset_ms, 2),
            "event": "press",
            "key": key_to_str(key)
        })


def on_release(key):
    global recording

    if key == TOGGLE_KEY:
        return

    if recording:
        offset_ms = (time.perf_counter() - start_time) * 1000
        events.append({
            "offset_ms": round(offset_ms, 2),
            "event": "release",
            "key": key_to_str(key)
        })


def _save():
    if not events:
        print("No events recorded.")
        return

    duration_s = events[-1]["offset_ms"] / 1000
    with open(SAVE_FILE, "w") as f:
        json.dump(events, f, indent=2)
    print(f"■ Recording stopped.")
    print(f"  Saved {len(events)} events over {duration_s:.2f}s → {SAVE_FILE}")
    print("Press F9 to record a new run, or Ctrl+C to quit.")


print("Trackmania Input Recorder")
print(f"  Press F9 to start/stop recording")
print(f"  Output: {SAVE_FILE}")
print("-" * 40)

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)

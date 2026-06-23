"""Unseen course: reactive pure-pursuit controller (generalizes, no per-track tuning).

Each frame: read LIDAR beams -> steer toward the most open direction ->
modulate throttle/brake by how open the road ahead is and current speed.
Includes stuck-detection so we don't waste one of our 3 attempts.

Tune the constants below on the seen course + 2-3 practice tracks, then freeze.
"""
import numpy as np
from tminterface.interface import TMInterface
from tminterface.client import Client, run_client

from src.common import lidar

# --- tunables (freeze after Day-3 testing) -------------------------------
STEER_GAIN = 45000.0      # maps target angle (rad) -> steer units
MAX_STEER = 65536
BRAKE_SPEED = 30.0        # m/s above which we brake into tight corners
CORNER_TIGHTNESS = 0.45   # forward-beam openness below this => corner
STUCK_SPEED = 2.0         # m/s
STUCK_FRAMES = 120        # ~ a couple seconds of no progress
# -------------------------------------------------------------------------


class ReactiveDriver(Client):
    def __init__(self) -> None:
        self._slow_frames = 0

    def on_run_step(self, iface: TMInterface, time_ms: int) -> None:
        if time_ms < 0:
            return
        state = iface.get_simulation_state()
        speed = float(np.linalg.norm(state.velocity))

        # --- stuck detection / recovery ---
        if speed < STUCK_SPEED:
            self._slow_frames += 1
        else:
            self._slow_frames = 0
        if self._slow_frames > STUCK_FRAMES:
            iface.respawn()           # or reverse routine; saves the attempt
            self._slow_frames = 0
            return

        # --- perception + control ---
        beams = lidar.get_beams(state)
        target = lidar.furthest_open_angle(beams)
        steer = int(np.clip(target * STEER_GAIN, -MAX_STEER, MAX_STEER))

        forward_openness = float(beams[len(beams) // 2])
        cornering = forward_openness < CORNER_TIGHTNESS
        brake = cornering and speed > BRAKE_SPEED
        accelerate = not brake

        iface.set_input_state(accelerate=accelerate, brake=brake, steer=steer)


if __name__ == "__main__":
    run_client(ReactiveDriver(), server_name="TMInterface0")

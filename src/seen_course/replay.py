"""Seen course: deterministic TAS replay.

Workflow:
  1. Record/refine an optimized input sequence (see recordings/).
  2. This client replays it frame-by-frame via input injection -> fully
     autonomous, reproducible lap. This is what banks the seen-course points
     and chases the judges' target time.

Input format (simple, editable): list of (start_ms, end_ms, action) where
action sets steering/throttle/brake. Replace with a TMInterface .inputs file
once tuned.
"""
from tminterface.interface import TMInterface
from tminterface.client import Client, run_client

# Minimal demo plan: hold full throttle. Replace with the optimized sequence.
INPUT_PLAN = [
    {"start_ms": 0, "end_ms": 60_000, "accelerate": True, "brake": False, "steer": 0},
]


def action_at(time_ms: int):
    for seg in INPUT_PLAN:
        if seg["start_ms"] <= time_ms < seg["end_ms"]:
            return seg
    return {"accelerate": False, "brake": False, "steer": 0}


class ReplayClient(Client):
    def on_run_step(self, iface: TMInterface, time_ms: int) -> None:
        if time_ms < 0:
            return
        a = action_at(time_ms)
        iface.set_input_state(
            accelerate=a["accelerate"],
            brake=a["brake"],
            steer=a["steer"],   # -65536..65536
        )


if __name__ == "__main__":
    run_client(ReplayClient(), server_name="TMInterface0")

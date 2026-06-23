"""Day-1 milestone: confirm the Python client can talk to TMInterface.

Run with the game open (TMNF + TMInterface 1.x):
    python -m src.common.connection_check

This is the single most important early check. If state prints every frame,
the whole automation pipeline is unblocked.
"""
from tminterface.interface import TMInterface
from tminterface.client import Client, run_client


class ConnectionCheck(Client):
    def on_registered(self, iface: TMInterface) -> None:
        print(f"[ok] registered to {iface.server_name}")

    def on_run_step(self, iface: TMInterface, _time: int) -> None:
        state = iface.get_simulation_state()
        # position (x, y, z) and velocity confirm we can read telemetry
        print(f"t={_time:>7} pos={state.position} vel={state.velocity}")


if __name__ == "__main__":
    # Default server name; TMInterface exposes TMInterface0..N for multiple instances.
    run_client(ConnectionCheck(), server_name="TMInterface0")

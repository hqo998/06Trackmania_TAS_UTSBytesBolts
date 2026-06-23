"""LIDAR-style perception for the reactive agent.

TMNF has no real LIDAR, so we synthesize beam distances to the track edges.
Two strategies (pick based on what TMInterface exposes reliably):

  A) Geometry/state-based: raycast from the car using simulation state.
     Preferred when available — robust to lighting/visual changes.

  B) Screenshot-based (TMRL-style): grab the frame, detect track borders,
     cast N rays from the car and measure pixel distance to the first edge.
     Use as a fallback.

This module is a STUB defining the interface the controller depends on.
Fill in one strategy on Day 1.
"""
from __future__ import annotations
import numpy as np

N_BEAMS = 19            # odd number → one beam points straight ahead
FOV_DEGREES = 180.0     # spread of beams around the car's heading


def beam_angles() -> np.ndarray:
    """Evenly spaced beam angles (radians) relative to car heading."""
    half = np.deg2rad(FOV_DEGREES) / 2.0
    return np.linspace(-half, half, N_BEAMS)


def get_beams(sim_state) -> np.ndarray:
    """Return an array of N_BEAMS normalized distances in [0, 1].

    1.0 = clear road far ahead, 0.0 = wall right at the car.

    TODO(Day1): implement strategy A or B. Placeholder returns 'all clear'.
    """
    raise NotImplementedError("Implement geometry- or screenshot-based LIDAR.")


def furthest_open_angle(beams: np.ndarray) -> float:
    """Steering target: the angle of the most open beam (pure-pursuit heading)."""
    angles = beam_angles()
    return float(angles[int(np.argmax(beams))])

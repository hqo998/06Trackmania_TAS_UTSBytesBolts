# Trackmania Time Attack Bot

Autonomous bot for the Time Attack challenge (TrackMania Nations Forever).
See **[PLAN.md](PLAN.md)** for the full 3-day strategy, timeline, and risks.

## TL;DR strategy
- **Seen course** → deterministic scripted TAS via TMInterface (bank the safe points).
- **Unseen course** → lightweight reactive LIDAR controller that generalizes (no per-track tuning).

## Repo layout
```
src/
  common/        TMInterface client wrapper, LIDAR extraction, lap timing
  seen_course/   record + replay optimized input files (TAS)
  unseen_agent/  reactive pure-pursuit controller for unknown tracks
recordings/      saved input files / reference laps
PLAN.md          the 3-day plan
```

## Setup (Day 1 — do the connection check first)
1. Install TrackMania Nations Forever.
2. Install **TMInterface 1.x** (NOT 2.0+ — the Python client needs the 1.x socket API).
3. `pip install -r requirements.txt`
4. Launch TMNF with TMInterface, then run `python -m src.common.connection_check` and confirm it reads game state.

## Quick start
- Drive the car under script control: `python -m src.seen_course.replay` (after recording).
- Run the reactive agent: `python -m src.unseen_agent.drive`

> ⚠️ Confirm with the judges that input injection (TMInterface) is permitted before relying on the TAS approach. See PLAN.md §6.

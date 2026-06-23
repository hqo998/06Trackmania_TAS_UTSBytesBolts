# Trackmania Time Attack Bot — 3-Day Plan

**Game:** TrackMania Nations Forever (TMNF)
**Goal:** An autonomous bot that completes both the "seen" course and an "unseen" course (revealed on test day) with no human input, and publishes lap times to the online leaderboard.
**Constraint:** 3 days of build time. Test day allows **5 minutes setup + 3 attempts** on the unseen course.

---

## 1. Strategy: split the problem by what each course rewards

The two courses reward different things, so we use two different tools rather than one general AI.

| Course | What scores points | Best tool in 3 days |
|---|---|---|
| **Seen** (given now) | A *deterministic, repeatable* fast lap. We can optimize it all week and replay the exact inputs on demand. | **Scripted TAS** via TMInterface input injection. |
| **Unseen** (test day) | Completing a brand-new track with only 5 min setup + 3 tries. Must *generalize* with zero per-track tuning. | **Lightweight reactive controller** (LIDAR + pure-pursuit / steering heuristic), optionally seeded from a TMRL pretrained policy. |

Reinforcement learning *trained from scratch* is deliberately **out of scope** — TMRL/SAC runs need days-to-weeks of wall-clock training to converge, which we don't have. We only use RL if a working *pretrained* checkpoint can be adapted quickly.

### Scoring math this targets
- Seen course completion (autonomous): **5 pts** — locked in early via TAS.
- Beat judges' time on seen course: **15 pts** — TAS optimization is built for exactly this.
- Top-10 leaderboard placement on seen course: **up to 10 pts** — depends on how hard we optimize.
- Unseen course completion (autonomous): **20 pts** — the reactive agent's job.
- Beat dev-team time on unseen course: **15 pts** — stretch goal if the agent is fast and stable.
- Top-10 on unseen course: **up to 10 pts** — stretch.

Priority order: **lock the seen-course points first** (they're deterministic and safe), then invest remaining time in the generalizing unseen agent.

---

## 2. Architecture

```
                ┌─────────────────────────────┐
                │  TrackMania Nations Forever  │
                │        (game process)        │
                └───────────────▲──────────────┘
                                │ TMInterface
              telemetry / state │ + input injection
                                ▼
        ┌───────────────────────────────────────────┐
        │            Python control layer            │
        │                                            │
        │  seen_course/   ← scripted TAS replay      │
        │  unseen_agent/  ← LIDAR + reactive control │
        │  common/        ← TMInterface client,      │
        │                   LIDAR extraction, timing │
        └───────────────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │   Leaderboard publishing (online platform) │
        └───────────────────────────────────────────┘
```

### Key tooling decisions
- **TMInterface** ([donadigo.com/tminterface](https://donadigo.com/tminterface/)) is the standard TAS/automation layer for TMNF. It exposes game state and lets us inject inputs frame-by-frame.
  - **Critical version note:** the Python client (`pip install tminterface`) talks to the **socket API in TMInterface < 2.0.0**. TMInterface 2.0+ switched to an in-game **AngelScript plugin API**. **Pin TMInterface to a 1.x release** (e.g. 1.4.3) for the Python workflow, or be prepared to write an AngelScript bridge. Decide this on Day 0 — it's the single biggest setup risk.
- **TMRL** ([github.com/trackmania-rl/tmrl](https://github.com/trackmania-rl/tmrl)) ships pretrained `SAC_4_LIDAR_pretrained` weights and a LIDAR-from-screenshot pipeline. Useful as a *fallback* generalizing driver, but its pretrained weights target newer Trackmania and tracks with black borders — treat as optional, not the critical path.
- **LIDAR observation:** TMNF doesn't expose a real LIDAR. We synthesize one either from TMInterface raycasts/state or, TMRL-style, from screenshot edge detection (the car sees N beam distances to track borders). The reactive controller consumes these beams.

---

## 3. The two subsystems

### 3.1 Seen course — scripted TAS (deterministic)
1. Drive/record a clean reference lap (manual or rough autopilot) to get a baseline input file.
2. Use TMInterface to **replay and iteratively refine** inputs: brake points, steering angles, gear/throttle timing. This is classic input optimization and is where the "beat the judges' time" points come from.
3. Save the final optimized input sequence. On demand, the bot replays it identically — fully autonomous, no human input at run time.
4. Publish the resulting time to the leaderboard.

**Why this is safe:** once an input file produces a valid lap, it reproduces every time. The seen-course points are effectively bankable by end of Day 2.

### 3.2 Unseen course — reactive controller (generalizes)
The agent must drive a track it has never seen. Build a controller that needs **zero per-track tuning**:

1. **Perception:** each frame, compute a set of distance "beams" (LIDAR) from the car to the track edges, plus current speed and heading from TMInterface state.
2. **Control:** a **pure-pursuit / potential-field steering law** — steer toward the furthest open beam (the racing direction), modulate throttle/brake by how open the road ahead is and current speed. This is hand-tuned on the *seen* course and any extra practice tracks, then frozen.
3. **Safety/recovery:** detect "stuck" (low speed, no progress) and trigger a respawn/reverse routine so we don't waste an attempt.
4. **(Optional) RL seed:** if time allows on Day 3, load TMRL's pretrained LIDAR policy as an alternative driver and pick whichever (heuristic vs. policy) is faster/more stable on practice tracks.

**Test-day playbook (5 min setup, 3 attempts):**
- Setup: launch game + TMInterface, load the unseen track, confirm LIDAR beams render sanely, set throttle profile to "conservative."
- Attempt 1: conservative profile — *finish first*, bank the 20 pts.
- Attempt 2: aggressive profile — push for the dev-team time.
- Attempt 3: best-known-good profile — insurance / improve placement.

---

## 4. Three-day timeline

### Day 1 — Environment + control loop (de-risk the plumbing)
- Install TMNF + **TMInterface 1.x** (pinned), confirm `pip install tminterface` connects to the game and reads state. **This is the make-or-break milestone — do it first.**
- Stand up the Python control loop: read state every frame, inject a hardcoded input (e.g. "hold forward") and confirm the car moves under script control.
- Implement LIDAR beam extraction and visualize it. Implement timing/lap-detection.
- **End-of-day gate:** the bot can drive the car forward autonomously and read back position + beam distances.

### Day 2 — Lock the seen course + first reactive driver
- Record a reference lap on the seen course; replay it via TMInterface.
- Iterate the input file until it's a clean, valid autonomous lap → **publish to leaderboard (5 pts banked).**
- Begin optimizing brake/steer timing toward the judges' time (**15 pts**).
- In parallel: implement the pure-pursuit reactive controller; test it on the seen course (it should complete it without the scripted file).
- **End-of-day gate:** seen course completed autonomously and published; reactive controller finishes the seen course unaided.

### Day 3 — Generalization + hardening + dry run
- Tune the reactive controller on 2–3 *other* community tracks (proxy for "unseen") so it isn't overfit to the seen course.
- Add stuck-detection + respawn recovery.
- (Optional) wire up TMRL pretrained policy as an alternative driver; compare.
- Finalize seen-course optimization for leaderboard placement.
- **Full dry run of the test-day playbook**: time the 5-minute setup, run 3 attempts on a fresh track end-to-end, confirm leaderboard publish works automatically.
- Write a one-page run-book for test day.

---

## 5. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| TMInterface API version mismatch (2.0+ has no Python socket API) | Blocks everything | Pin TMInterface 1.x on Day 0; verify Python client connects before any other work. |
| Reactive agent crashes/overfits to seen course | Lose unseen-course points | Tune on multiple practice tracks; conservative Attempt 1 to bank completion. |
| LIDAR beams unreliable on unfamiliar visuals/lighting | Agent drives blind | Prefer geometry/state-based beams over screenshot CV where possible; validate on varied tracks. |
| Leaderboard publishing is manual or has auth friction | Can't score | Test the full publish flow Day 2, not test day. Confirm "no human input" rules with judges. |
| 5-min setup overrun on test day | Lose an attempt | Rehearse setup as a timed checklist; script as much of launch/load as possible. |
| Only 3 attempts on unseen | One bad run is costly | Attempt 1 = finish conservatively; never gamble the completion points. |

---

## 6. Open questions for the judges
- Exact definition of "no human input" — is launching the game / loading the track allowed during setup, or must the bot do that too?
- What is the leaderboard / online platform, and what does the publish flow require (account, replay file, validation)?
- Is TMInterface (input injection) permitted, or must control go through screen-capture + simulated key presses only? This determines whether the TAS approach is legal for scoring.

> Resolve these **before Day 1** — the answer to the TMInterface question can change the whole architecture.

---

## 7. Definition of done
- [ ] Seen course completed autonomously and time published to leaderboard.
- [ ] Seen-course time beats the judges' reference time.
- [ ] Reactive agent completes an unseen practice track with zero per-track tuning.
- [ ] Stuck-detection + respawn recovery working.
- [ ] Test-day run-book rehearsed within the 5-minute setup budget.

---

*Sources: [TMInterface](https://donadigo.com/tminterface/) · [TMInterface Python client](https://github.com/donadigo/TMInterfaceClientPython) · [TMInterface Python docs](https://tminterface.readthedocs.io/en/stable/) · [TMRL](https://github.com/trackmania-rl/tmrl)*

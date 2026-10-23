# P3-001 — Offline six-phase joint waveform (planning only)

**Status:** source prototype and Python unit tests only; **P3 native walking remains BLOCKED by P2.2**. Do not import the waveform into the Webots controller, simulate weight shift, or command any physical servo until the P2 acceptance gate and operator review are complete.

## Scope and design

`host/robotis/gait.py` provides a pure-Python `OfflineGait` class. It accepts the existing `configs/robot.json` structure and returns detached `GaitFrame` samples with precisely ten canonical joint positions in radians. Its six labelled phases are `DOUBLE_SUPPORT_A → SHIFT_LEFT → SWING_RIGHT → DOUBLE_SUPPORT_B → SHIFT_RIGHT → SWING_LEFT`. Each nominal SWING phase contains a smooth rise to a proposed leg-bend pose and a return to neutral; the complete cycle begins and ends at neutral. Every keyframe is checked against configured joint limits. Each cubic smoothstep segment is rejected if its analytical maximum speed, `1.5 * abs(delta_angle) / segment_duration`, exceeds the joint `rate_limit`.

**ASSUMPTION / UNVERIFIED:** Default offsets (shift 0.03 rad; swing hip 0.06 rad; knee 0.10 rad; ankle 0.05 rad) and timing (double support 0.4 s; shift 0.8 s; swing 1.2 s) are small synthetic test values, *not* validated inverse kinematics, support polygon, contact dynamics, foot clearance or safe stepping. Local joint sign/motor axis mapping is also unverified. This implementation does not command motors, add `WALK` to the runtime state machine, alter safety parameters, or make balance claims. Even when all offline unit tests pass, physical and native-Webots walking acceptance remains unverified.

## Reproduce the offline checks

From the repository root on Python 3.10+:

```bash
python3 -m unittest discover -s tests -p 'test_gait.py' -v
python3 -m unittest discover -s tests -v
python3 -m compileall -q host/robotis tests
```

`tests/test_gait.py` verifies phase ordering, 10 finite radians, joint bounds, sampled slew limits over two cycles, the periodic neutral boundary, independent output frames, and rejection of invalid config/time/limits/rates. No hardware, Webots controller or external service is touched by those tests.

## Acceptance gates / next steps

- **P3-001 offline code:** ACCEPT only after the PR's offline Python 3.10/3.12 test matrix is green and code review confirms no motor/Webots output path.
- **P2-CONTACT-001:** operator on Webots R2025a must observe foot collision and floor contacts in an undisturbed >=30 s neutral baseline, including screenshots, dated run_id, exact commit, CSV/JSON metadata, and no anchoring/penetration/slip. Test evidence is **NOT RUN by this PR**.
- **P2.2 recovery gate:** >=3 matched baseline/PID pairs *per pitch +/- and roll +/- direction*, measured tilt excitation >=0.008 rad, no FAULT, recovery within the specified window, and >=10% peak-tilt improvement per direction. **NOT ACCEPTED**.
- **P3 live trials:** remain **BLOCKED** until both preceding gates are reviewed and accepted. Later design must add measured contact/COM/foot clearance, stronger acceleration/jerk bounds and independent runtime safety/watchdog guards before any walking actuation.

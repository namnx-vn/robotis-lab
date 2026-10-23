# Repository entrypoints, evidence rules and P2 snapshot

## Canonical project and files

`namnx-vn/robotis-lab`, default branch `master` (check at time of review). Read latest files and related PRs, **not these stale notes**:

| Area | Current known path (2026-10-22 snapshot) |
|---|---|
| Project contract | `README.md`, `AGENTS.md`, `PROJECT_INSTRUCTIONS.md`, `IMPLEMENTATION_PLAN.md`, `docs/ROADMAP.md` |
| Active work | `tasks/backlog.md`, `docs/experiments/balance-matrix.md`, `docs/experiments/controlled-disturbance.md` |
| Kinematic/control config | `configs/robot.json` |
| Pure offline motion/safety logic | `simulation/webots/controllers/rl_h25_controller/motion.py` |
| Webots runtime integration | `simulation/webots/controllers/rl_h25_controller/rl_h25_controller.py` |
| Physics model | `simulation/webots/worlds/rl_h25_lab.wbt`, `simulation/webots/protos/RLH25.proto` |
| Automated checks | `tests/test_motion.py`, `tests/test_balance.py`, `tests/test_controller_fake.py`, `tests/test_balance_matrix.py` (and other tests) |
| CI and report workflow | `.github/workflows/python-tests.yml`, `.github/workflows/simulation.yml`, `.github/workflows/disturbance-pilot.yml`, `docs/operations/ci-report-feedback-loop.md` |

**As inspected 2026-10-22, not a release certification:** v0.2 simulator config has 10 joints with neutral, min/max, direction, rate limits, max velocity and max torque fields. `SafetySupervisor` latches `STOP/FAULT/E_STOP`, with an explicitly gated reset method, while runtime `STAND` and IMU PID are research implementations. No full BOOT→EXPLORE lifecycle and no physical adapter evidence. `tilt_fault_rad=0.45`, `time_step_ms=16`, `minimum_root_height_m=0.1`, `obstacle_stop_m=0.18` were config values, **not hardware-validated safety limits**. `baseline` mode is default.

P2 undisturbed standing documented as 5/5 native Webots ~31.92-second runs. P2 controlled pitch±/roll± balance **not yet accepted**, P3 walking **BLOCKED**. An open draft PR #9 dated 2026-10-22 documents force-probe viability but insufficient body excitation in a native pilot; this is not merged `master` evidence. **Recheck before reporting.**

## Real evidence hierarchy

1. **Native Webots R2025a, exact code SHA and artifact**: telemetry, simulator log, force input and application, contacts, roll/pitch, duration and trial count.
2. **Offline Python unit/fake-Webots**: useful for pure logic and injected faults, **not** proof of 3D dynamics.
3. **Static analysis/source review**: may expose hazards, cannot certify running physics/response time.
4. **Screenshot/animation/controller state**: demonstration only; insufficient for standing/balance/gait acceptance.
5. **Hardware bench with operator approval and actual measurements**: separate physical evidence category; not equivalent to CI simulation.

CI jobs: PR 8s smoke, merge-to-master five 32s static baseline trials and opt-in / PR one-pair disturbance pilot have different scope. Green CI with `INCONCLUSIVE` pulse pilot is **not** P2 acceptance. All source claims must link commit SHA and test profile to run artifact; never equate PR test-merge SHA with source SHA.

## P2 controlled balance acceptance protocol

Per `docs/experiments/balance-matrix.md` (recheck latest): four independent directions **pitch+, pitch-, roll+, roll-**; **at least 3 valid matched baseline/balance pairs for each direction**, with comparable world and timestep, *measurably applied disturbance*, no FAULT, defined settling and **at least 10% smaller mean peak tilt** in active PID vs baseline **for each direction**. Inspect physical foot contact/foot slip in GUI and verify actuator feedback signs. `force API works` is not `body was sufficiently excited`. A one-pair pilot cannot pass the full gate. Do not raise force blindly or bypass the hard tilt/height trip.

## Reproducible commands (repo root, when available)

```bash
# static checks / offline logic
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q simulation/webots/controllers tools tests

# inspect case plan only: DOES NOT launch Webots
python3 tools/run_balance_matrix.py --dry-run --pairs 1

# Native Webots R2025a macOS; only when simulation execution is authorized
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14

# Repeated native matrix only after reviewing safe/valid pilot results
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 --force 0.10 --pulse 0.112 --duration 14
```

The commands and values above reflect the repository's documented research protocol; **not independently certified safe/adequate thresholds**. A dry run is not a simulator test. Do not execute hardware commands on the basis of these examples.

## Report provenance checklist

For every observed result collect, where available:

- repository and exact SHA, branch, pull request, `source_commit_sha`, `test_merge_sha`, config/world checksums;
- Webots version, host/container OS, profile, timestep, controller mode, trial reset strategy;
- run ID, start/end duration, requested and actually applied pulse (steps/axis/time), timestamps;
- roll, pitch, position/root height, velocity, joint target vs measured, current mode, state, stop reason, **first fault**;
- stance/support evidence and contact/slip observations, COM estimates and uncertainty if used;
- criteria with numeric bounds and expected/observed per direction/per trial;
- output classifications **separately**: offline, smoke, static standing, controlled recovery, gait, physical hardware.

If artifacts are expired or inaccessible, mark the relevant claim `UNVERIFIED`/`NEEDS EVIDENCE`, not PASS. If test not executed, `NOT RUN`.

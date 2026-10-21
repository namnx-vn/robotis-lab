# Robotis Lab — RL-H25 (Webots R2025a)

**Source of truth:** `namnx-vn/robotis-lab` on GitHub. Open a feature/fix branch and PR against `master` for changes. No direct AI/cloud control of hardware motors.

## Current capabilities

- **P1:** ~25 cm humanoid Webots world and generated PROTO; two feet, passive arms, 10 actuated leg joints, Physics/bounding objects, IMU/Gyro/GPS/camera/distance.
- **P2 baseline:** position hold plus safety supervisor. The operator measured 5/5 undisturbed 31.92 s macOS Webots R2025a baseline trials (terminal report, not uploaded raw CSV).
- **P2 active balance:** opt-in bounded pitch/roll IMU PID and joint/rate limits; **not yet certified** for disturbance recovery.
- **Sprint 02.1:** opt-in Supervisor force pulse; matched baseline/balance paired trials and data-based report.
- **Sprint 02.2 (proposed PR):** matrix of pitch/roll in both directions, fail-closed experimental gate, GitHub CI. **Native results pending.**

A manual disturbance previously caused `FAULT excessive_tilt`. Do not treat a momentary `STAND` log, animation, or deterministic neutral pose as active balance. P3 gait and hardware trials remain blocked until P2 criteria are met.

## Quick start

Install Python 3.10+ and Webots R2025a on macOS. From the repository root:

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q simulation/webots/controllers tools tests

# Visually inspect the robot and its physical contact with the floor:
RL_H25_MODE=baseline /Applications/Webots.app/Contents/MacOS/webots simulation/webots/worlds/rl_h25_lab.wbt

# Static standing baseline: 5 fresh Webots runs:
python3 tools/run_standing_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --mode baseline --trials 5 --duration 32
```

### Controlled balance validation (simulation only)

```bash
# Experimental protocol check; does not launch Webots
python3 tools/run_balance_matrix.py --dry-run --pairs 1

# One pair per direction, stop on first fault or inconclusive case
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14

# ONLY after pilot review; 5 pairs in each of four directions
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 --force 0.10 --pulse 0.112 --duration 14
```

A pilot intentionally exits nonzero even with valid data; it cannot establish recovery with only one pair. Review `experiments/logs/` (CSV + JSON). See [four-direction validation protocol](docs/BALANCE_MATRIX.md) and [individual disturbance trial protocol](docs/CONTROLLED_DISTURBANCE.md).

## Project structure

- `simulation/webots/worlds/rl_h25_lab.wbt`, `simulation/webots/protos/RLH25.proto` — physical world and articulated model
- `simulation/webots/controllers/rl_h25_controller/` — Webots controller, motion/PID, force injector
- `configs/robot.json` — mass assumptions, named joints, calibrated simulation limits, PID
- `tools/` — generators, validators, headless Webots runners and metrics
- `tests/` — offline unit and fake-Webots tests
- `docs/` — mechanical/safety decisions, gates, experimental protocols
- `.github/workflows/python-tests.yml` — Python tests on PRs (cannot certify Webots physics)

## Engineering and release boundaries

See [AGENTS.md](AGENTS.md), [architecture instructions](PROJECT_INSTRUCTIONS.md), [roadmap](docs/ROADMAP.md), [current implementation plan](IMPLEMENTATION_PLAN.md) and [backlog](tasks/backlog.md). Use radians in simulation, bounded deterministic controller/safety, no AI command of raw PWM. **No physical robot walking and no validated budget BOM.** Never power multiple servos from Arduino Uno 5V. Hardware requires independent servo rail, fuse, E-STOP and operator approval.

Ignored: `.env`, local experiment CSV/JSON, recorded videos and other data. Never commit secrets, identifying sensor data, or private camera footage.

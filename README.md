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
## Running after source import
```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --axis pitch --force 0.10 --pulse 0.112 --duration 14
```
These scripts **do not exist on `master` yet**; import the maintained source and review its tests first. Native Webots physics tests must run locally on a machine with Webots R2025a.

## Automated Webots reports

GitHub Actions runs offline checks plus a native Webots simulation in the pinned R2025a container. Pull requests into `master` use the 8-second smoke profile; pushes to `master` run five independent 32-second baseline trials. Each run publishes a 30-day artifact named `robotis-lab-report-<commit-sha>-<run-id>-<run-attempt>` containing the Markdown/JSON CI report, console logs, and generated telemetry. A green baseline is evidence of static simulated standing only; it does not certify active balance or physical hardware.

From another machine with the GitHub CLI authenticated, inspect and download a report with:

```bash
gh run list --workflow=simulation.yml
gh run download <run-id> --name <artifact-name>
```

The workflow can also be started manually from the Actions page with either the `smoke` or `baseline` profile. Generated reports and telemetry are uploaded as artifacts and are not committed to the repository.

## Documents
- [AGENTS.md](AGENTS.md) — engineering and safety contribution contract.
- [docs/SOURCE_IMPORT.md](docs/SOURCE_IMPORT.md) — one-time source migration from local v0.2.1.
- [docs/ROADMAP.md](docs/ROADMAP.md) — milestone and acceptance gates.

Private video, raw camera images, `.env` secrets and experimental logs must not be committed by default.

# Robotis Lab — research bootstrap documents

Tài liệu khởi tạo RL-H25: robot hình người cao ~25 cm, hai chân 10 DOF, Arduino Uno + PC host + Webots.

- `CHATGPT_PROJECT_INSTRUCTIONS.md` — **bản ngắn** dán trực tiếp vào ChatGPT Project Instructions (PROJECT_ID `robotis-lab`).
- `PROJECT_INSTRUCTIONS.md` — **đặc tả chi tiết**: kiến trúc, hardware/firmware, AI boundaries, an toàn, quy tắc AI coding agent.
- `IMPLEMENTATION_PLAN.md` — **roadmap 24 tuần**: backlog từng tuần, nghiệm thu, ngân sách sơ bộ, rủi ro và nhiệm vụ phiên đầu tiên.

**Trạng thái:** đây là bộ kế hoạch/instructions, **chưa phải source code Webots `.wbt`, firmware Arduino hoặc robot vật lý đã thử thành công**. Thông số khung, servo, nguồn và giá cần kiểm chứng khi triển khai.

**Bước kế tiếp:** P0 → dự án Webots đầu tiên chạy được với robot RL-H25.


# Robotis Lab RL-H25 v0.2.1 — Standing Baseline, IMU PID & Disturbance Validation

**Scope:** Webots **R2025a** humanoid, 25 cm, 10 DOF leg joints, Y-up `NUE`, physics, IMU, GPS, laser and camera. Upgraded *in place* from the Sprint 01 `RLH25.proto` + `.wbt`. **No walking, no proof of balanced locomotion, and no Arduino/hardware control.**

**Evidence status (2026-10-21):** The user ran Webots R2025a on macOS. Five **undisturbed v0.2 baseline** runs passed the automated 30s gate (5/5; owner-provided terminal output, not original CSV files). A later manually disturbed balance run showed `FAULT excessive_tilt` at ~28.91s. This upgraded package preserves that code and introduces reproducible applied-force tests. Native v0.2.1 physics and gain signs are NOT verified here (Webots is unavailable in the authoring container). No historical success/failure logs were invented.

## Deliverables

- Existing mechanical model and physics: `simulation/webots/worlds/rl_h25_lab.wbt`, `simulation/webots/protos/RLH25.proto`, unchanged from Sprint 01 (except configuration/metadata, no unjustified axis swaps).
- **`baseline` mode (default):** same idealized neutral angle hold, with expanded telemetry. Use FIRST, repeat fresh Webots processes/trials.
- **`balance` mode (opt-in):** closed-loop IMU orientation angle PID on roll + pitch, derivative-on-measurement, low-pass derivative, anti-windup, bounded outputs. Weighted joint targets (both ankles plus small opposing hips); knees neutral. Output is a *position offset in radians*, not a torque controller. **Gain signs and effectiveness remain experimental.**
- Joint min/max and target slew-rate remain enforced after PID mixing; latching `FAULT`/`STOP` freezes targets, `E_STOP` disables available motor torque **in simulation only**. No automatic FAULT reset.
- Baseline acceptance checks: duration, sample continuity, max tilt, min root height, planar GPS drift, state transitions, metadata/run independence. CSV cannot prove foot contact; visually confirm no sliding.
- Test suite includes nominal, saturation, timegap, sensor fault, obstacle and E-STOP (mocked Webots).

## Requirements

- macOS with Webots R2025a (user has it), Python 3.10+; standard library only.
- From extracted directory, run:

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

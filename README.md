# Robotis Lab — RL-H25 (Webots R2025a)

Browse [the documentation index](docs/README.md) for architecture, experiments, operations, and historical reports.

Robotis Lab researches a ~25 cm autonomous humanoid with 10 leg DOF. **Simulation first, evidence before hardware, safety independent of AI.** The canonical source repository is `namnx-vn/robotis-lab`; development uses reviewable PRs targeting `master`.

## Current verified and unverified capabilities

| Phase | Evidence | Status |
|---|---|---|
| P1: 10-DOF world/robot | Webots R2025a on operator macOS and GitHub CI | Source/model available |
| P2: undisturbed neutral standing | 5/5 Webots 31.92s trials, repeated locally and in GitHub CI | Automated static gate PASS |
| P2: IMU PID under force | Manual run once faulted; reproducible force protocol implemented | **Not yet validated** |
| P3: weight shift/walking | No reproducible successful walking tests | BLOCKED |
| P5+: Arduino/hardware | Inventory and torque/power sizing not complete | NOT STARTED |

Never equate `STAND` controller state, an animation, or smoke-test PASS with active disturbance recovery.

## Quick start

Requires Python 3.10+ and Webots R2025a. From repo root:

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q simulation/webots/controllers tools tests

# On the operator's Mac:
RL_H25_MODE=baseline /Applications/Webots.app/Contents/MacOS/webots \
  simulation/webots/worlds/rl_h25_lab.wbt

python3 tools/run_standing_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --mode baseline --trials 5 --duration 32
```

## Automatic simulation reports

Every PR to `master` triggers Python offline tests and a native Webots **8 s smoke** run on GitHub-hosted Ubuntu. Every push to `master` runs five independent **32 s static standing** trials. Workflows upload version-linked Markdown/JSON summaries, simulator console logs and telemetry CSV/JSON as a downloadable artifact retained for 30 days.

**The GitHub runner is not the operator's Mac.** It executes Webots R2025a in a pinned container; differences from the local GPU/OS remain possible.

- [Continuous simulation & AI report review workflow](docs/operations/ci-report-feedback-loop.md)
- [GitHub Actions — Webots simulation](.github/workflows/simulation.yml)
- [Python offline CI](.github/workflows/python-tests.yml)

From a GitHub CLI session:

```bash
gh run list --repo namnx-vn/robotis-lab --workflow simulation.yml
gh run download <run-id> --repo namnx-vn/robotis-lab --dir reports-from-ci
```

ChatGPT can inspect completed GitHub Actions reports through the connected GitHub capability when requested, or through an explicitly enabled watch. A GitHub push by itself does not spontaneously start a ChatGPT response.

## Active balance research (P2)

Disturbance runs remain an explicit opt-in research experiment, **not** a default gate in GitHub CI:

```bash
# Show force envelope and all four cases without launching Webots
python3 tools/run_balance_matrix.py --dry-run --pairs 1

# Mac: 1 paired baseline/balance pilot per direction, stop on a safety concern
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14
```

The pilot does not certify active balance. Review force-applied metadata, measurable tilt response, faults and settling time first; move to matched `--pairs 5` only after review. See [matrix acceptance protocol](docs/experiments/balance-matrix.md) and [force injection protocol](docs/experiments/controlled-disturbance.md).

## Layout

- `simulation/webots/worlds/rl_h25_lab.wbt` — Y-up (`NUE`) world with Physics, floor and obstacle
- `simulation/webots/protos/RLH25.proto` — 10-DOF humanoid, sensors and body collisions
- `simulation/webots/controllers/rl_h25_controller/` — Python IMU PID, joint/rate limits, safety and opt-in force injector
- `configs/robot.json` — geometry assumptions and controller settings
- `tools/`, `tests/` — simulator runners, reports and normal/fault tests
- `docs/`, `tasks/` — decisions, plans, risk boundaries and phase gates

Read [AGENTS.md](AGENTS.md), [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md), [implementation plan](IMPLEMENTATION_PLAN.md), [backlog](tasks/backlog.md) and [roadmap](docs/ROADMAP.md). Hardware changes need explicit operator approval. Never power multiple servos from Arduino Uno 5V, route AI output to raw PWM, or commit credentials/private recordings.

## Native Webots disturbance pilot in GitHub CI

`.github/workflows/disturbance-pilot.yml` launches the **actual Webots R2025a** controller in a pinned Ubuntu container on every PR to `master`. It runs one bounded matched baseline/balance pair per direction (pitch ±, roll ±) and publishes `balance-pilot-ci-report.json`, `.md`, the simulator console and per-run CSV/JSON as a 30-day artifact. Any `FAULT` or `INCONCLUSIVE` result is made explicit. A workflow marked green means **evidence was recorded and structurally validated**, *not* that PID balance has been proven. Full scientific acceptance still needs >=3 comparable pairs per direction, verified settling and real foot contact. See [CI report feedback loop](docs/operations/ci-report-feedback-loop.md).

# Repository checkpoint — 2026-10-22 (snapshot, not perpetual truth)

Source: owner-connected GitHub `namnx-vn/robotis-lab` on `master`, examined 2026-10-22. **Recheck current branch/PR/actions before every future task; do not cite this snapshot as newer state.**

| Area | Observed project evidence | Scope limitation |
|---|---|---|
| P1 model | `simulation/webots/worlds/rl_h25_lab.wbt`, `simulation/webots/protos/RLH25.proto`, 10 joint controller | Native Webots model exists; operator contact verification unfinished |
| P2 standing | Repo reports native `baseline` 5/5 × 31.92s; `tools/run_standing_trials.py`, `tools/baseline_report.py` | Standing without perturbation; not active dynamic balance |
| P2.2 | `tools/run_balance_matrix.py`, `tools/disturbance_report.py`, `tests/test_balance_matrix.py` | Four sign/axis paired gate. Native force API probe exists; near-zero induced tilt trials were INCONCLUSIVE |
| Native CI | `.github/workflows/simulation.yml`, `.github/workflows/disturbance-pilot.yml`, `.github/workflows/python-tests.yml` | CI `success` on an evidence report is **not** active balance certification |
| Current PR | Draft #9 `docs(P2.2): capture native force API PASS and blocked balance acceptance` | Recheck merge status and scientific acceptance before relying on it |
| Walking | P3 in `docs/ROADMAP.md` and `tasks/backlog.md` | BLOCKED until P2 controlled balance gate and operator contact inspection |
| Hardware | Planned Uno+PCA9685, source does not show bench results | NOT STARTED / unverified performance; no physical test authority |

Documented native pilot (PR #9 description, not a new execution by this skill): `Webots R2025a` free-body force API probe 8/8 PASS, while robot pitch+ baseline/PID 0.10 N, 0.112s peak change around 0.00012/0.00016 rad (<0.008 rad excitation gate) and **INCONCLUSIVE**. Do not promote a successful tool or probe run to P2 acceptance.

Key files to inspect at task time:
- `README.md`, `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `PROJECT_INSTRUCTIONS.md`
- `docs/ROADMAP.md`, `tasks/backlog.md`, `docs/experiments/balance-matrix.md`, `docs/experiments/p2-2-acceptance-report.md`
- `docs/operations/ci-report-feedback-loop.md`, `configs/robot.json`
- `tools/run_standing_trials.py`, `tools/baseline_report.py`, `tools/run_balance_matrix.py`, `tools/disturbance_report.py`, `tools/ci_disturbance_report.py`
- `tests/test_motion.py`, `tests/test_balance.py`, `tests/test_balance_matrix.py`, `tests/test_controller_fake.py`, native Actions artifacts

The repository primarily uses `unittest`. Add `pytest` as a reviewed change if required, not by silently swapping the test framework. Everything in this bundle is portable guidance and example offline analysis, **not source code already installed in robotis-lab**.

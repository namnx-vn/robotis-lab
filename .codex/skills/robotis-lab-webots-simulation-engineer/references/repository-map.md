# Robotis Lab repository navigation (checkpoint, not guaranteed current)

Observed from `namnx-vn/robotis-lab` README/AGENTS/plan on 2026-10-22. Re-fetch before working.

- `simulation/webots/worlds/rl_h25_lab.wbt` — Y-up `NUE` Webots world with ground, obstacle, gravity/physics.
- `simulation/webots/protos/RLH25.proto` — 10-DOF model, sensors and collision geometry.
- `simulation/webots/controllers/rl_h25_controller/` — deterministic Python movement, IMU PID, safety and opt-in force injector.
- `configs/robot.json` — current robot geometry/controller constraints; inspect rather than replace with preferred YAML.
- `tools/verify_project.py` — static verification.
- `tools/run_standing_trials.py` — independent static-standing runs.
- `tools/run_balance_matrix.py` — four-direction matched force experiments; dry-run and pilot/full modes.
- `tests/` — actual offline test layout; inspect before adding subfolders.
- `docs/experiments/balance-matrix.md`, `docs/experiments/controlled-disturbance.md` — acceptance and injection protocol.
- `docs/operations/ci-report-feedback-loop.md` — which native CI artifacts and profiles to interpret.
- `.github/workflows/simulation.yml`, `.github/workflows/python-tests.yml`, `.github/workflows/disturbance-pilot.yml` — CI jobs; their green status alone is not scientific acceptance.
- `docs/ROADMAP.md`, `tasks/backlog.md`, `IMPLEMENTATION_PLAN.md` — phase and task gates.

Before source edits: inspect Git default branch, recent source commits, open PRs, last applicable **native** simulator run and its exact commit SHA, plus controller + config + tests. Prefer new branch / PR rather than modifying default branch directly.

Do not claim CI artifact contents were reviewed unless they were actually downloaded or inspected. Do not assert Webots is available locally solely from repo documentation.

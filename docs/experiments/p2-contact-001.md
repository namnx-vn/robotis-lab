# P2-CONTACT-001 — Native Webots contact observation (operator)

**Status: NOT RUN / UNVERIFIED.** This procedure requires the operator's local macOS Webots R2025a GUI. GitHub CI/headless logs cannot replace visible contact points, bounding objects and independent confirmation of no artificial anchoring. No P3 weight shift or walking is authorized by this document.

## Goal and prerequisites

Confirm both feet have plausible load-bearing floor contacts in a neutral, undisturbed, >=30 simulated-second baseline (target 32 s), with Webots gravity 9.81, 10 actuated joints, foot/floor friction 1.1, collisions and physics active. Record exactly which version, robot configuration and commit were actually observed. Verify no foot penetration, skating, hovering, unexpected root constraint or scene-tree fixed anchoring. The operator must actively inspect both feet (zoom/rotate camera) and any foot collision/support polygon; do not infer two contacts from a static screenshot of an upright robot.

Before starting, close other Webots instances, use an unmodified world, and verify that the Python offline/CI fix PR is reviewed. Do not start the balance disturbance matrix or modify PID/safety thresholds for this task.

## Commands on the operator's Mac

From the local repository root, use the **reviewed** P2 branch until it is merged to master. Use `git status` to protect local changes, and ensure Webots is actually R2025a via **Webots → About**.

```bash
# The fix branch is deliberately not automatically merged.
git fetch origin
git switch fix/p2-ci-001-world-verification
git pull --ff-only
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v

mkdir -p experiments/logs
export RL_H25_RUN_ID="p2contact-$(date -u +%Y%m%dT%H%M%SZ)"
export RL_H25_MODE=baseline
export RL_H25_DURATION_S=32
export RL_H25_LOG_DIR="$PWD/experiments/logs"
export RL_H25_BUILD_COMMIT="$(git rev-parse HEAD)"
export RL_H25_SOURCE_COMMIT_SHA="$RL_H25_BUILD_COMMIT"
unset RL_H25_FORCE_FAULT RL_H25_DISTURBANCE
printf 'run_id=%s commit=%s\n' "$RL_H25_RUN_ID" "$RL_H25_BUILD_COMMIT"
/Applications/Webots.app/Contents/MacOS/webots \\
  simulation/webots/worlds/rl_h25_lab.wbt
```

In the GUI, **before unpausing**, open **View → Optional Rendering → Show All Bounding Objects** and **Show Contact Points**, then play at a moderate/slow UI simulation speed so there is time to capture evidence near 2 s and 30 s *of simulation time*. Step the simulation after toggling contact display (it is not instantaneous); look for active contact markers under both feet and correct collision outlines. Take screen captures of the full Webots window plus close-ups of each foot with the simulation clock visible where possible.

In a **second terminal**, replace `ACTUAL_RUN_ID` with the printed run_id; save screenshots locally, for example:

```bash
screencapture -i "experiments/logs/ACTUAL_RUN_ID-contact-early.png"
screencapture -i "experiments/logs/ACTUAL_RUN_ID-contact-late.png"
```

After completion, verify output and preserve `<run_id>.csv`, `<run_id>.json`, both screenshots, Webots About/version and `git rev-parse HEAD` together. Do not commit raw screenshots or telemetry to the public repository unless deliberately sanitized and approved.

## Operator checklist — acceptance review (initially UNVERIFIED)

- [ ] Exact Webots R2025a version, repo SHA, mode `baseline`, unique run_id and unmodified robot/world identified
- [ ] 32 simulated seconds completed with matching CSV/JSON and no STOP, FAULT, E_STOP, non-finite telemetry or unexplained gaps
- [ ] View menu has both **Show Contact Points** and **Show All Bounding Objects** enabled; screenshots of each foot and late-run state are attached
- [ ] Both left and right feet physically contact the floor, no penetration/hovering/floating/false static anchoring and no significant slip; collision feet/floor are present
- [ ] Foot contact indicators checked while simulation is advancing, not inferred from neutral joint targets, screenshots alone, or a single GUI snapshot
- [ ] Operator explicitly signs off contact observation; discrepancies cause FAIL/INCONCLUSIVE, not a silent acceptance

**Status classification:** `PASS` only for supported static contact if the evidence meets all above; `FAIL` for observed anomaly; `INCONCLUSIVE` if screenshots/contacts or telemetry are missing. This does **not** prove active balance (P2.2) or walking (P3).

## Blocked follow-up

P2.2 remains **NOT ACCEPTED** until >=3 comparable matched baseline/PID pairs *per* pitch +/− and roll +/−, with intended-axis excitation >=0.008 rad, safe recovery, no FAULT, contact validation and >=10% lower peak tilt per direction. Do not enable weight shift, swing, or gait even if P2-CONTACT-001 passes. See [balance matrix](balance-matrix.md) and [P2.2 debug](p2-2-debug-p3-readiness.md).

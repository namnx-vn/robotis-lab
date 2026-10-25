# P2-CONTACT-001 — Native Webots contact observation (operator)

**Status: STATIC CONTACT PASS ON PR #15 CANDIDATE / ACTIVE BALANCE UNVERIFIED.** Exact-source native telemetry and a tool-assisted interactive Webots GUI observation support plausible static contact at both feet. This does not measure load distribution, prove active recovery or authorize P3 weight shift/walking.

## Native CI evidence (2026-10-23 UTC)

On PR [#15](https://github.com/namnx-vn/robotis-lab/pull/15), manually dispatched [Webots simulation run #43](https://github.com/namnx-vn/robotis-lab/actions/runs/39980857060) executed five independent 32 s baseline trials on source/test SHA `24ac0c5e29f8869a40e1f942a3948d8d86a72ad1` with Webots R2025a. Artifact `12514130335` contains the CI report plus all CSV/JSON telemetry.

All five trials finished `STAND` with no fault. Each trial recorded 286/286 samples with contacts, always eight contact points, exactly two descendant `Solid` IDs (`78` and `138`), and 1,144 observations per ID. Contact world-Y stayed between `-0.000045883 m` and `-0.000030567 m`. The first/last snapshots form two separate `0.044 m × 0.076 m` rectangles matching the two foot collision geometries. Static standing metrics also passed 5/5: 31.92 s telemetry duration, roll `0 rad`, maximum pitch `0.0002 rad`, minimum root height `0.183 m`, and planar drift `0 m`.

The report verifies that both IDs were present in every recorded sample. This is repeatable headless evidence consistent with contact on both descendant foot solids, but it does **not** measure load distribution, independently exclude a hidden constraint or certify active balance.

## Interactive GUI observation (2026-10-24 UTC)

A tool-assisted operator-machine session ran the unmodified PR candidate at source/test/build SHA `24ac0c5e29f8869a40e1f942a3948d8d86a72ad1` in Webots R2025a. Run ID `p2contact-24ac0c5-gui-side-final` completed 32.0 simulated seconds in `baseline` mode, ended in `STAND`, and recorded no fault. Its CSV contained 286 telemetry rows; the matching JSON contact evidence reports 286/286 samples with eight contact points, with descendant solid IDs `78` and `138` present in every sample (1,144 observations per ID). Contact world-Y remained between `-0.000045883 m` and `-0.000030567 m`. The individual 31.92 s baseline trial passed its standing limits; it is not a replacement for the separate five-trial CI suite.

With **Show All Bounding Objects** and **Show Contact Points** enabled while simulation advanced, the unchanged side viewport was captured at GUI clocks 6.096 s and 28.336 s. Both images have the identical SHA-256 `ba2c1eee8cac3e22b83a881ea2be1f05ebff647dac0d234bf98c490d56f8adc9`, consistent with no visible slip or posture change during that interval. A supplemental top view from a separate exact-source GUI restart separated the two foot collision outlines and has SHA-256 `e12ac08f9d99be741840314a1140dba089bbd4df148f1c234f145008ec9639f0`. The side view showed the upright robot, floor-level foot collision/contact markers, and no visible penetration, hovering or indication of artificial anchoring. Scene/model review and per-sample telemetry provide supporting evidence; GUI inspection alone cannot prove load sharing or cryptographically exclude every hidden constraint.

The matching local artifacts are intentionally Git-ignored and were not uploaded: CSV SHA-256 `a7c84f0f14445f3828fd4c93dfddfe2d70568d4a985be09d4559725193f35fb0`, JSON SHA-256 `d9ec5d99d98b2fdce01e9203719ae5885ed7bb90bc94dc22e4c660f74621028e`, and the screenshot hashes above. The viewport image files do not embed the clock; clock values were observed in the live GUI and paired with the run filenames. This was an operator-authorized tool-assisted observation, not an independent second-person witness.

## Goal and prerequisites

Confirm both feet have plausible load-bearing floor contacts in a neutral, undisturbed, >=30 simulated-second baseline (target 32 s), with Webots gravity 9.81, 10 actuated joints, foot/floor friction 1.1, collisions and physics active. Record exactly which version, robot configuration and commit were actually observed. Verify no foot penetration, skating, hovering, unexpected root constraint or scene-tree fixed anchoring. The operator must actively inspect both feet (zoom/rotate camera) and any foot collision/support polygon; do not infer two contacts from a static screenshot of an upright robot.

Before starting, close other Webots instances, use an unmodified world, and verify that the Python offline/CI fix PR is reviewed. Do not start the balance disturbance matrix or modify PID/safety thresholds for this task.

## Commands on the operator's Mac

From the local repository root, use the current reviewed `master`. Use `git status` to protect local changes, record the exact commit before the run, and ensure Webots is actually R2025a via **Webots → About**.

```bash
git fetch origin
git switch master
git pull --ff-only
git status --short --branch
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

## Operator checklist — acceptance review

- [x] Webots R2025a, exact repo SHA, mode `baseline`, unique run ID and unmodified robot/world identified
- [x] 32 simulated seconds completed with matching CSV/JSON and no STOP, FAULT, E_STOP, non-finite telemetry or unexplained gaps
- [x] **Show Contact Points** and **Show All Bounding Objects** enabled; early/late side views and a supplemental two-foot top view captured locally
- [x] Both contact-solid IDs present in every sample; no visible penetration, hovering, unexplained slip or indication of false static anchoring
- [x] Contact indicators checked while simulation advanced and cross-checked against native per-sample telemetry
- [x] Operator-authorized tool-assisted observation recorded with exact hashes; no independent second-person witness is claimed

**Status classification:** `PASS` only for supported static contact if the evidence meets all above; `FAIL` for observed anomaly; `INCONCLUSIVE` if screenshots/contacts or telemetry are missing. This does **not** prove active balance (P2.2) or walking (P3).

## Blocked follow-up

P2.2 remains **NOT ACCEPTED** until >=3 comparable matched baseline/PID pairs *per* pitch +/− and roll +/−, with intended-axis excitation >=0.008 rad, safe recovery, no FAULT, contact validation and >=10% lower peak tilt per direction. Do not enable weight shift, swing, or gait even if P2-CONTACT-001 passes. See [balance matrix](balance-matrix.md) and [P2.2 debug](p2-2-debug-p3-readiness.md).

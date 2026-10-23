# P2.2 Acceptance Report — Controlled Disturbance & Active Balance Recovery

**Status: INCONCLUSIVE — P2.2 not accepted; P3 remains blocked.**
**Date:** 2026-10-22
**Scope:** Webots-only compatibility, telemetry and regression tests. No hardware, PID gain/sign, robot mechanics, gait or safety-limit changes.
**Local follow-up branch:** `fix/p22-r2025a-force-api`; native RL-H25 runs used controller source commit `576473200b818c881373067bd3081d22379d92e4`.

## Goal and baseline evidence

Prove a repeatable world-frame force applied at an actual *node-local* +Y offset, then measure 4-direction baseline vs PID recovery. The preceding [native CI pilot](https://github.com/namnx-vn/robotis-lab/actions/runs/39648900940) used test-merge SHA `e0ba9c1e453c6927fe73e213b1faa57839b906cf` and produced only one pitch +1 pair:

| Measurement | Baseline | Active balance |
|---|---:|---:|
| Requested force / pulse | 0.10 N / 0.112 s | 0.10 N / 0.112 s |
| Python calls logged | 7 | 7 |
| Peak intended-axis tilt | 0.00011 rad | 0.00014 rad |
| Fault | none | none |
| Evidence verdict | INCONCLUSIVE | INCONCLUSIVE |

Both peaks are far below the mandatory `0.008 rad` excitation gate. A recorded function call is not proof of applied offset torque. Old data may not be re-labelled as recovered after a source patch.

## Source root cause, fix and trade-offs

Webots R2025a Python `Node.addForceWithOffset` calls `wb_supervisor_node_add_force`, not `wb_supervisor_node_add_force_with_offset` (Webots [#6881](https://github.com/cyberbotics/webots/pull/6881)). The R2025a C header declares `void wb_supervisor_node_add_force_with_offset(WbNodeRef, const double[3], const double[3], bool)`.

This branch uses **Option B**, a narrowly scoped `ctypes` adapter bound to the same `controller.wb.wb` shared library and the Webots `Node._ref` (`c_void_p`). It explicitly configures four argument types and void return; there is **no silent Python-wrapper fallback**. This is smaller than changing the Webots build across all workflows, but an independent *native physics* probe is still mandatory to check that the C symbol is present and offsets/frames work on the actual runtime.

The adapter, native probe, telemetry and CI guard were merged in [PR #8](https://github.com/namnx-vn/robotis-lab/pull/8), master merge SHA `576473200b818c881373067bd3081d22379d92e4`. Follow-up runner/report change is [PR #10](https://github.com/namnx-vn/robotis-lab/pull/10), head SHA `a1730375957699d0694f52919f0cea04f888e628`. Its [Webots simulation](https://github.com/namnx-vn/robotis-lab/actions/runs/39745945926), [offline validation](https://github.com/namnx-vn/robotis-lab/actions/runs/39745945978), and [disturbance pilot](https://github.com/namnx-vn/robotis-lab/actions/runs/39745945862) workflows all succeeded. The exact-SHA disturbance job log confirms the native free-body probe passed 8 cases; its one-pair pitch+ RL-H25 pilot was `INCONCLUSIVE`, and the CI report explicitly says `SCIENTIFIC CERTIFICATION: NO`. Artifact 12411381955 was uploaded with raw telemetry, but its download endpoint returned HTTP 403 in this review session, so its JSON/CSV was not independently inspected here. The local native evidence below was produced separately on the installed Webots R2025a bundle.

## Changed files

- `simulation/webots/controllers/rl_h25_controller/disturbance.py` — correct C call; mode + actual API call count.
- `simulation/webots/controllers/rl_h25_controller/rl_h25_controller.py` — provenance and force/velocity time series.
- `simulation/webots/worlds/force_api_probe.wbt` and `simulation/webots/controllers/force_api_probe/force_api_probe.py` — independent dynamic unanchored body, gravity, zero/nonzero local offset, ±X/±Z and rotated frames.
- `tools/run_force_api_probe.py` — native probe execution, report JSON/log, fail-closed parser.
- `tools/run_standing_trials.py` — pass source SHA, test-merge SHA, exact version if observable.
- `tools/disturbance_report.py` — strict API/provenance checks, cross-axis peak, first fault time, no dropping failed/incomplete pairs.
- `tests/test_disturbance.py`, `tests/test_force_api_abi.py`, `tests/test_force_api_probe.py` — mock-only regression.
- `.github/workflows/disturbance-pilot.yml` — native independent force API probe runs before robot pilot; preserves raw artifacts.
- `tools/run_force_api_probe.py`, `tests/test_force_api_probe.py` — local timeout regression: terminate the Webots process group so a child cannot keep inherited output pipes open.
- `tools/run_standing_trials.py`, `tests/test_run_standing_trials.py` — read the macOS app bundle's `Contents/Resources/version.txt` when `WEBOTS_HOME` is absent.

## Executed verification and native results

- Installed simulator: Webots `R2025a`; exact bundle version file reports `R2025a38`. Source, config and world metadata for RL-H25 runs: source/test SHA `576473200b818c881373067bd3081d22379d92e4`, config SHA `ab4675358c4448313d4f36f3451f26d630b7f44be4c150effa818edbec05890b`, world SHA `9c8e171aa95ecc7a1d8ef228ad7e199ede567d9531cd9d35f40e5886717d5731`, timestep 0.016 s.
- Native free-body probe: **PASS, 8/8 cases**, unanchored `Solid` with `Physics`; gravity displacement `-0.01507 m`. Offset cases measured `|omega| = 3.3975 rad/s` with expected signs: pitch ± about X, roll ± about Z. Zero-offset X/Z produced zero angular velocity. A yaw-rotated body retained world-frame +Z force; a rotated local +Y offset produced the expected +Y torque. API mode: `r2025a_ctypes_force_with_offset`. Raw JSON/log: `/private/tmp/p22-native-probe/force-api-probe.json` and `.log`.
- Four-direction RL-H25 pilot at 0.10 N, 0.112 s, 0.04 m offset, one baseline/balance pair per direction: all eight runs completed `STAND`, applied 7 steps, had no fault, minimum root height 0.18296 m and maximum planar drift <=0.00003 m. Tilt peaks remained below 0.008 rad:

| Direction | Baseline peak (rad) | Balance peak (rad) | Signed response | Cross-axis peak (rad) | Pair run IDs (baseline / balance) | Verdict |
|---|---:|---:|---|---:|---|---|
| pitch + | 0.00012 | 0.00016 | positive | 0.000000 | `baseline-20261022T070315Z-01-37865a` / `balance-20261022T070317Z-01-542746` | INCONCLUSIVE |
| pitch - | 0.00012 | 0.00015 | negative | 0.000000 | `baseline-20261022T070319Z-01-29f65e` / `balance-20261022T070322Z-01-110409` | INCONCLUSIVE |
| roll + | 0.00014 | 0.00013 | positive | 0.000047 | `baseline-20261022T070324Z-01-81757e` / `balance-20261022T070326Z-01-11417d` | INCONCLUSIVE |
| roll - | 0.00014 | 0.00013 | negative | 0.000047 | `baseline-20261022T070329Z-01-9fe956` / `balance-20261022T070331Z-01-d9c8ab` | INCONCLUSIVE |

- Force ladder after safe but insufficient 0.10 N pilots: pitch+ at 0.15 N measured 0.00018 rad baseline / 0.00024 rad balance (`baseline-20261022T070424Z-01-3cde3d` / `balance-20261022T070427Z-01-c5ab88`); at 0.20 N measured 0.00024 / 0.00032 rad (`baseline-20261022T070442Z-01-1df807` / `balance-20261022T070445Z-01-97fe9e`). All remained `STAND`, 7 steps, no first fault, root height >=0.18295 m, max drift <=0.00006 m. Both verdicts were `INCONCLUSIVE`; escalation stopped at 0.20 N as specified.
- Raw RL-H25 files and matrix reports are preserved under ignored `experiments/logs/`, including `balance-matrix-20261022T070333Z.json`, `disturbance-pitch-20261022T070429Z.json`, and `disturbance-pitch-20261022T070447Z.json`; no CSV was edited.
- First local free-body launch exposed a runner timeout defect: Webots' child inherited output pipes and outlived `subprocess.run` timeout handling. The runner now starts a process group, kills/reaps it on timeout, and has a regression test. The first hung process was stopped; its output was not treated as experiment evidence.
- Offline verification after the local changes: project verifier PASS, unit tests 103/103 PASS, documentation links PASS, compileall PASS, dry-run matrix PASS. Native simulation is reported separately above.
- The earlier 5/5 31.92 s undisturbed standing gate is static-standing evidence only, not recovery evidence.

Commands to reproduce in a Webots R2025a environment (do not substitute mock results for physical simulation):

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 tools/check_docs_links.py
python3 -m compileall -q simulation/webots/controllers tools tests
python3 tools/run_balance_matrix.py --dry-run --pairs 1
python3 tools/run_force_api_probe.py --webots /Applications/Webots.app/Contents/MacOS/webots
# ONLY after native free-body probe passes:
python3 tools/run_balance_matrix.py --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14
```

If a direction is `INCONCLUSIVE`, `FAIL` or has unexplained drift/fault, stop and inspect raw data before adjusting anything.

## Scientific acceptance gate — NOT MET

| Required evidence | Current evidence |
|---|---|
| Native C force-with-offset physics on a free body and world/local-frame signs | PASS, local Webots R2025a, 8/8 cases |
| Four directions: pitch ±, roll ± | One paired pilot each; all INCONCLUSIVE |
| >=3 independently valid paired runs per direction (5 preferred) | PENDING |
| Every trial peak response >=0.008 rad, initial target-axis tilt <0.08 rad | PENDING |
| No FAULT, fall, root-height loss, unacceptable drift | No faults in pilots; full-matrix gate pending |
| Settle within 0.025 rad for >=0.8s within 5s | PENDING |
| >=10% mean peak reduction for PID vs baseline **per direction** | PENDING |
| Independent run IDs, matching force schedule, source/config/world/version provenance | PASS for 0.10 N pilot and calibration pairs |
| Foot contact, no interpenetration, anchoring or unexplained slip | PENDING_OPERATOR_VISUAL_CHECK |

The acceptance matrix must retain failed runs, first-fault times, CSV/JSON/console logs and run IDs. **No `ACCEPTED` claim until all mandatory evidence is present.** P3 gait is blocked.

## Risks, blockers and next action

**Risks:** The free-body diagnostic validates the C API and frame/offset semantics, but not RL-H25 contact forces, foot slip or torque. All robot tilt peaks at 0.10–0.20 N are at least 25× below the required excitation gate, so PID effectiveness/sign cannot be inferred. Controller motors are idealized; friction and sensor noise are not characterized.

**Next action:** Review a GUI Webots recording/contact view and the ignored raw CSVs, then decide whether the allowed force envelope, pulse duration or experiment model needs a separately reviewed change. Do not tune PID from these sub-threshold runs. Run >=3 paired trials per direction only after a safe pilot reaches >=0.008 rad; require operator visual contact confirmation. P2.2 remains INCONCLUSIVE and P3 gait remains blocked.

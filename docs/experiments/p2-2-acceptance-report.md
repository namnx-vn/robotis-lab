# P2.2 Acceptance Report — Controlled Disturbance & Active Balance Recovery

**Status: NOT_ACCEPTED (provisional; update only from native evidence).**  
**Date:** 2026-10-22  
**Scope:** Webots-only compatibility, telemetry and regression tests. No hardware, PID gain/sign, robot mechanics, gait or safety-limit changes.

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

Review PR: [#8 — force-with-offset compatibility and regression evidence](https://github.com/namnx-vn/robotis-lab/pull/8). Base `master` SHA `02fc43a9bbdacb1157c34cdf97e556049c9a69dd`. Branch `fix/p22-supervisor-force-abi`. **PR is draft and unmerged.** Head/test merge SHAs and Webots version must be taken from the *same* CI artifacts before claiming results.

## Changed files

- `simulation/webots/controllers/rl_h25_controller/disturbance.py` — correct C call; mode + actual API call count.
- `simulation/webots/controllers/rl_h25_controller/rl_h25_controller.py` — provenance and force/velocity time series.
- `simulation/webots/worlds/force_api_probe.wbt` and `simulation/webots/controllers/force_api_probe/force_api_probe.py` — independent dynamic unanchored body, gravity, zero/nonzero local offset, ±X/±Z and rotated frames.
- `tools/run_force_api_probe.py` — native probe execution, report JSON/log, fail-closed parser.
- `tools/run_standing_trials.py` — pass source SHA, test-merge SHA, exact version if observable.
- `tools/disturbance_report.py` — strict API/provenance checks, cross-axis peak, first fault time, no dropping failed/incomplete pairs.
- `tests/test_disturbance.py`, `tests/test_force_api_abi.py`, `tests/test_force_api_probe.py` — mock-only regression.
- `.github/workflows/disturbance-pilot.yml` — native independent force API probe runs before robot pilot; preserves raw artifacts.

## Executed verification vs pending experiments

- Local executor environment is Linux without Webots; the owner-specified macOS executable `/Applications/Webots.app/Contents/MacOS/webots` is not accessible here. **No Mac-native Webots trial is claimed.**
- The PR triggers GitHub Actions offline validation and native Webots smoke/pilot; verify their exact URLs, commit SHAs and raw artifacts before updating the status.
- Existing baseline v0.2 result, 5/5 undisturbed standing trials, is **not** recovery evidence.

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
| Native C force-with-offset physics on a free body and world/local-frame signs | PENDING PR CI |
| Four directions: pitch ±, roll ± | PENDING |
| >=3 independently valid paired runs per direction (5 preferred) | PENDING |
| Every trial peak response >=0.008 rad, initial target-axis tilt <0.08 rad | PENDING |
| No FAULT, fall, root-height loss, unacceptable drift | PENDING |
| Settle within 0.025 rad for >=0.8s within 5s | PENDING |
| >=10% mean peak reduction for PID vs baseline **per direction** | PENDING |
| Independent run IDs, matching force schedule, source/config/world/version provenance | PENDING |
| Foot contact, no interpenetration, anchoring or unexplained slip | PENDING_OPERATOR_VISUAL_CHECK |

The acceptance matrix must retain failed runs, first-fault times, CSV/JSON/console logs and run IDs. **No `ACCEPTED` claim until all mandatory evidence is present.** P3 gait is blocked.

## Risks, blockers and next action

**Risks:** Native C ABI must be checked on the exact installed build; the free-body diagnostic validates injection but does not validate robot contacts. Controller motors are idealized, friction uncertain and sensor noise omitted. A failed native probe blocks force calibration and PID tuning.

**Next action:** Inspect the native free-body probe artifact from PR #8 at its exact test-merge SHA, repair any failures first; if it passes, inspect one bounded four-direction pilot, **without automatically increasing force**. Run the full paired matrix only after pilots show safe measurable excitation and operator confirms foot contact. No hardware work or P3 transition.

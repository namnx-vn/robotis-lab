# P2.2 Acceptance Report — Controlled Disturbance & Active Balance Recovery

**Status: NOT_ACCEPTED — native force API repaired and calibrated, but robot disturbance remains subthreshold.**  
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

## Verified new native CI evidence (2026-10-22)

The exact PR head **`43ec56dd3f7d89edbaa870056c085b9f45af1d5a`** was tested as GitHub Actions **test merge** `ed57598daa33eaea6dc61a953a52592313cf7c70` in `cyberbotics/webots:R2025a-ubuntu22.04`, with the actual Webots installation reporting `Webots R2025a`. Source SHA and test-merge SHA are now separate telemetry fields.

- [Native disturbance pilot run 39713137894](https://github.com/namnx-vn/robotis-lab/actions/runs/39713137894) — GitHub Actions workflow **SUCCESS**, but **scientific status INCONCLUSIVE**. Raw JSON/CSV/simulator/probe logs are in the artifact attached to this exact run.
- [Python offline validation run 39713137893](https://github.com/namnx-vn/robotis-lab/actions/runs/39713137893) — **SUCCESS**, 99 Python unit tests passed; compileall passed.
- [Native Webots smoke run 39713137953](https://github.com/namnx-vn/robotis-lab/actions/runs/39713137953) — **SUCCESS**. Smoke is not balance acceptance.

**Independent native force probe PASSED 8/8 checks** on a free Physics body, including ±X/±Z, zero vs 0.04 m offset, world-force and local-offset rotated frames. It observed a gravity-only `-0.01506816 m` Y displacement over three simulation steps. With zero offset, measured angular velocity was zero for the two tested vectors; with 0.04 m offset, intended rotation was approximately ±3.3975 rad/s. This demonstrates that the C offset API physically applies the intended wrench on the independent test body, not yet that RL-H25 recovers from it.

**RL-H25 pilot — native telemetry, pitch +1 only:**

| Metric | Baseline | Balance PID |
|---|---:|---:|
| Run ID | `baseline-20261022T024613Z-01-79e363` | `balance-20261022T024617Z-01-11101f` |
| 0.10 N, 0.112 s at +0.04 m offset | 7 applied steps | 7 applied steps |
| Peak pitch change from pre-pulse mean | **0.00012 rad** | **0.00016 rad** |
| Peak cross-axis change | 0 rad (rounded) | 0 rad (rounded) |
| Maximum root planar drift | 0.00002 m | 0.00003 m |
| Minimum root height | 0.18296 m | 0.18296 m |
| FAULT | None | None |
| Run verdict | `INCONCLUSIVE` (insufficient excitation) | `INCONCLUSIVE` (insufficient excitation) |

The paired run has matching schedule, API mode, source/config/world hashes, Webots version and 7 recorded C calls. Both modes stayed in `STAND`; neither reached the required **0.008 rad** perturbation. The analyzer correctly rejected scientific acceptance and stopped the matrix *before* pitch -1 / roll ±. The fact that PID's tiny measured peak is larger than baseline's is **not** a valid conclusion about PID stability in this unexcited trial. CI passing here means reliable evidence collection (`ci_evidence_ok=true`), not a balance recovery pass (`scientific_balance_certified=false`).

## Scientific acceptance gate — NOT MET

| Required evidence | Current evidence |
|---|---|
| Native C force-with-offset physics on a free body and world/local-frame signs | **PASS**: 8/8 native checks, run 39713137894 |
| Four directions: pitch ±, roll ± | **NOT MET**: pitch + only; early stop is intentional |
| >=3 independently valid paired runs per direction (5 preferred) | PENDING |
| Every trial peak response >=0.008 rad, initial target-axis tilt <0.08 rad | **NOT MET**: 0.00012/0.00016 rad pitch+; no measurable excitation |
| No FAULT, fall, root-height loss, unacceptable drift | PENDING |
| Settle within 0.025 rad for >=0.8s within 5s | PENDING |
| >=10% mean peak reduction for PID vs baseline **per direction** | PENDING |
| Independent run IDs, matching force schedule, source/config/world/version provenance | PASS for one pitch+ pair only; insufficient full matrix |
| Foot contact, no interpenetration, anchoring or unexplained slip | PENDING_OPERATOR_VISUAL_CHECK |

The acceptance matrix must retain failed runs, first-fault times, CSV/JSON/console logs and run IDs. **No `ACCEPTED` claim until all mandatory evidence is present.** P3 gait is blocked.

## Risks, blockers and next action

**Risks:** Native C ABI must be checked on the exact installed build; the free-body diagnostic validates injection but does not validate robot contacts. Controller motors are idealized, friction uncertain and sensor noise omitted. A failed native probe blocks force calibration and PID tuning.

**Next action:** Force path is now verified by free-body native evidence, but RL-H25 remains underexcited. Diagnose whether strong ideal joint holding/contact physics masks body tilt; if appropriate within the existing validated safety envelope, perform one carefully monitored 0.15 N pitch+ pilot, then 0.20 N only if the preceding data remain safe and trustworthy. Do not tune PID or run the full matrix until delivered rotational excitation >=0.008 rad is verified. Inspect all root/joint/cross-axis traces and require operator foot-contact confirmation. No hardware work or P3 transition.

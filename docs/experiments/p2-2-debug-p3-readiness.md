# P2.2 Debug Findings and P3 Implementation Readiness

**Date:** 2026-10-22
**Repository state reviewed:** `master` at `99b2444dca784c4198c4dd98003d4b8b04cfa693`
**Native evidence reviewed:** GitHub Actions run `39648900940`, test merge SHA `e0ba9c1e453c6927fe73e213b1faa57839b906cf`
**Audience:** RL-H25 operator and developers
**Scope:** Webots simulation only. No hardware, firmware, autonomous motion, or safety-limit changes.

## Decision

P2.2 is **not accepted**, and P3 native gait implementation remains **blocked**. The one available P2.2 pair is valid evidence of an inconclusive experiment, not evidence of active balance.

The primary P2.2 defect is now identifiable: the project calls the Python `Node.addForceWithOffset` method on Webots R2025a, but that release's Python binding incorrectly calls the plain C `addForce` function. The requested 0.04 m application offset is discarded, and the offset argument is passed where the C function expects the `relative` flag. The experiment therefore does not apply the requested world-frame force plus moment. Cyberbotics fixed this after R2025a in pull request [#6881](https://github.com/cyberbotics/webots/pull/6881), listed under the R2025b changelog.

The downloaded artifact is consistent with this failure mode: the +Z force caused a +Z root displacement and a gyro/pitch response, proving that a force was applied, but the response was far below the rotational excitation gate. Ideal position-servo stiffness, high-friction double support, and missing contact/torque telemetry remain secondary limitations.

P3 planning may proceed, together with neutral-pose contact/provenance instrumentation that does not generate gait motion. Gait trajectories, a gait state machine, weight shift, foot lift, and walking implementation must wait until the P2.2 force path is repaired and the existing four-direction recovery gate passes.

## Evidence reviewed

The review used the following sources:

- [Operator handoff](../OPERATOR_HANDOFF.md), including the reported `INCONCLUSIVE` result.
- The complete artifact from [GitHub Actions run 39648900940](https://github.com/namnx-vn/robotis-lab/actions/runs/39648900940): CI report, matrix report, simulator log, two JSON metadata files, and two telemetry CSV files.
- Current disturbance injector, matrix runner, analyzer, controller, robot configuration, generated PROTO, world, and tests.
- The Webots R2025a Python `controller/node.py` implementation and Cyberbotics fix [#6881](https://github.com/cyberbotics/webots/pull/6881).
- [Webots Supervisor force documentation](https://github.com/cyberbotics/webots/blob/master/docs/reference/supervisor.md), which defines the offset in node coordinates and the force frame through the `relative` argument.

The artifact report records the workflow test merge SHA, but each run's own metadata says `build_commit: unverified` and `webots_version: unverified`. This is a provenance gap to correct before accepting new scientific evidence.

## Observed P2.2 result

| Metric | Baseline position hold | Balance PID |
|---|---:|---:|
| Axis and direction | pitch +1 | pitch +1 |
| Requested force | 0.10 N | 0.10 N |
| Requested pulse | 0.112 s | 0.112 s |
| Recorded API calls | 7 | 7 |
| Peak intended-axis tilt change | 0.00011 rad | 0.00014 rad |
| Peak signed pitch change from pre-pulse mean | +0.000106 rad | +0.000140 rad |
| Peak roll change | approximately 0 | approximately 0 |
| Peak +Z root displacement | +0.0000196 m | +0.0000270 m |
| Peak gyro X magnitude | 0.001608 rad/s | 0.001616 rad/s |
| FAULT | no | no |
| Verdict | `INCONCLUSIVE` | `INCONCLUSIVE` |

The pulse began at 4.000 s and the peak response occurred at 4.112 s. The response direction and timing show that the force call had an effect. They do not show that the requested offset torque was delivered.

The balance run's peak response was about 27% larger than the baseline run, but this is one pair with excitation 57 times below the 0.008 rad gate. It is not evidence that the PID sign is wrong or that PID is worse.

## Root cause analysis

### Confirmed primary defect

`simulation/webots/controllers/rl_h25_controller/disturbance.py` calls:

```python
self.solid.addForceWithOffset(force, [0.0, offset_m, 0.0], False)
```

In Webots R2025a, the Python implementation of `addForceWithOffset` dispatches to `wb_supervisor_node_add_force` instead of `wb_supervisor_node_add_force_with_offset`. Its extra offset argument occupies the C call's `relative` position, while the requested `False` argument is extra. The exact interpreted frame is therefore not trustworthy. The same release also misroutes Python `addTorque`. Therefore:

- `applied_steps=7` proves seven Python calls, not seven correctly offset force applications;
- the intended moment from the 0.04 m offset was not applied through this binding, and the requested world-frame semantics were not reliably preserved;
- increasing force before fixing or bypassing the binding would repeat an invalid experiment;
- the current CI image is tagged `cyberbotics/webots:R2025a-ubuntu22.04`, while the raw run metadata fails to record its exact Webots build. Native API isolation is still required to close that provenance gap.

### Secondary experimental limitations

Even after the binding is corrected, the initial stimulus may still be too weak. A 0.10 N force is about 2.7% of the modeled 0.38 kg robot's weight. The offset-only moment is 0.004 N m, while ten idealized Webots position motors actively hold the neutral pose and each motor is configured for up to 0.8 N m. Baseline mode is therefore an active, stiff position hold rather than a passive robot.

This secondary hypothesis must be tested after the force API is repaired. It must not be used to lower the excitation threshold or relax the 0.45 rad tilt fault limit.

### Observability and reporting gaps

1. The analyzer checks only the intended tilt axis. A swapped or cross-axis response can be labeled `no_measurable_excitation` without being shown.
2. Accelerometer data are enabled but not logged.
3. No measured foot contact, contact force, motor torque, root velocity, or delivered wrench is recorded.
4. Root drift is reduced to an unsigned scalar, hiding response direction.
5. Pair comparability does not enforce commit, Webots version, world hash, or log-period equality.
6. The default matrix stops after the first `INCONCLUSIVE` case. The latest artifact therefore contains only pitch +1, despite workflow and README wording that suggests all four directions run.
7. `ci_evidence_ok=true` means the partial artifact is structurally valid. It does not mean the four-direction matrix is complete or scientifically successful.

## P2.2 corrective scenarios

All scenarios below are simulation-only. D1 uses an isolated inert test body and does not generate robot gait. Every full-robot scenario keeps the current tilt, height, joint, rate, STOP, FAULT, and E_STOP behavior. Runtime sensor freshness and an independent watchdog are not current capabilities; they are prerequisites before gait motion.

| ID | Scenario | Change under test | Required observation | Pass or stop rule |
|---|---|---|---|---|
| D0 | Preserve current run | No source change | Archive exact raw artifact and metrics above | Reference only; never relabel as recovery |
| D1 | R2025a API isolation | On a deliberately rotated free body, compare the Python method with the correct C Supervisor function at zero and nonzero offset | Correct path preserves requested world-frame translation and produces the expected signed angular velocity only for nonzero offset | Stop if frame/offset behavior or exact Webots build is ambiguous |
| D2 | Compatibility fix | Either pin a Webots release containing fix #6881 or add a narrowly tested R2025a C-API adapter | Offset path and API/version recorded in run metadata | No full robot test until D1 proves the path |
| D3 | Zero-force sham | Same duration and logging, force disabled | Roll/pitch/gyro/root noise floor and run-to-run variance | Excitation threshold must remain comfortably above measured noise |
| D4 | Four-direction calibration | One baseline-only pilot for pitch +/-, roll +/- using the repaired path | Correct signed intended-axis response; cross-axis response also reported | Stop on FAULT, contact anomaly, wrong axis, or wrong sign |
| D5 | Bounded envelope ladder | Separate one-pair runs at 0.10 N, then 0.15 N, then 0.20 N only if the prior artifact and GUI/contact evidence are reviewed and safe | First safe envelope with peak change >=0.008 rad | Never auto-escalate; stop at measurable response, FAULT, invalid telemetry, wrong axis/sign, or any contact uncertainty; do not jump to 0.35 N |
| D6 | PID sign check | At the first measurable envelope, compare correction sign with measured excursion | Correction initially opposes excursion; target and measured joints respond within bounds | Change only one axis sign or mix term per rerun |
| D7 | Full P2.2 matrix | At least 3, preferably 5, matched pairs per direction | Repeatable recovery metrics for all four conditions | Existing [balance matrix](balance-matrix.md) gate; any missing direction blocks P3 |

### Recommended compatibility strategy

Prefer one explicit, reviewable choice rather than silently changing behavior:

1. **Upgrade path:** validate and pin an exact Webots release or image digest that demonstrably contains Cyberbotics fix #6881. Do not assume an R2025b changelog heading means a stable build is available. If only a development build contains the fix, pin its exact commit and treat the simulator change as experimental. Rerun parser, standing, contact, and disturbance evidence on that build.
2. **R2025a compatibility path:** call the correct C Supervisor function through a small adapter, because the R2025a C API exists and only its Python wrapper is wrong. Explicitly bind the C symbol and argument types; unit-test dispatch, vector order, frame flag, and offset; record the adapter path in metadata; and prove it in scenario D1 before running the robot matrix.

The upgrade path reduces private API usage but changes the project simulator baseline. The adapter path preserves R2025a compatibility but depends on Webots' internal Python binding objects. This decision requires a focused source PR and native artifact review.

### P2.2 acceptance gate

P2.2 passes only when every pitch +/- and roll +/- condition has:

- at least 3 comparable paired runs, with 5 preferred;
- measured excitation of at least 0.008 rad using a verified force path;
- initial intended-axis tilt below 0.08 rad;
- identical documented force schedule and comparable applied-step count;
- no FAULT, fall, excessive drift, low root height, or invalid telemetry;
- return within 0.025 rad for at least 0.8 s within the 5 s recovery window;
- at least 10% lower mean peak tilt in balance mode than baseline for that condition;
- distinct run IDs and commit-, config-, world-, and Webots-version-linked native artifacts;
- operator-confirmed foot contact with no penetration, hidden anchoring, or unexplained slip.

## P3 readiness assessment

### What exists

- Ten leg joints with position sensors, hard joint limits, motor velocity/torque settings, and controller-side slew limits.
- IMU, gyro, accelerometer, GPS, distance sensor, safety state, and telemetry logging.
- A latching safety supervisor with STOP, FAULT, E_STOP, tilt, height, obstacle, and finite-value checks. A separate controller guard faults when the balance-loop timestep exceeds its configured maximum.
- Static standing evidence and a deterministic Webots world.

### What is missing

- Per-foot contact/load measurement and a support-foot safety condition.
- Verified center of mass and support-polygon telemetry.
- Runtime freshness checks for IMU, joint, contact, COM, and phase data, plus an independent watchdog design appropriate to the eventual hardware path.
- A nominal gait-pose generator or gait phase state machine.
- Balance correction around a moving nominal pose. The current balance controller always starts from neutral joint targets.
- Swing-foot clearance and touchdown detection.
- Gait phase, transition-reason, step-event, and fall-reason telemetry.
- Native evidence that load transfer and foot contact behave physically.

P3 must not count elapsed phase time or leg animation as a completed step. A step is valid only after measured unload, toe-off, clearance, forward swing, touchdown, and stable double support.

## Proposed P3 architecture

Keep safety independent and outermost:

```text
observations + immutable current-phase safety context
        (expected contacts, deadline, tracking status)
                              |
                              v
                   latching SafetySupervisor
                              |
                   phase motion authorization
                              v
            deterministic phase and nominal pose proposal
                              |
          bounded roll and pitch correction about nominal pose
                              |
                              v
             raw final-target safety validation
                              |
                              v
                  joint clamp and existing slew limit
                              |
             bounded-command safety validation
                              |
                              v
                 Webots motors and evidence telemetry
```

The gait generator returns a new immutable target map for each control tick. The balance controller adds bounded corrections to that nominal map rather than mutating the neutral configuration. No cloud or local LLM may produce joint angles, gait phase transitions, motor currents, or PWM.

The smallest gait state machine is:

```text
STAND -> SHIFT -> UNLOAD -> LIFT -> SWING -> PLACE -> TRANSFER -> STAND
```

Each transition requires sensor evidence and a timeout. The gait generator supplies immutable context describing the current phase, expected contacts, transition deadline, and tracking status. Safety first authorizes the phase from observations and that context. After gait and balance compose a raw request, safety inspects the unclamped final targets; the clamp and slew limiter remain defense in depth; safety then sees the actual bounded command before motor authorization. It retains authority over both gates and cancels further phase progression when latched.

## P3 implementation scenarios

The success rates below are proposed engineering gates for approval after P2.2 passes. Before that gate, this table is planning only; do not implement P3-0 trajectories or any gait state machine. Neutral-pose P3-A observability may be prepared as pre-P3 instrumentation because it commands no motion. These criteria do not replace the roadmap's minimum of five physically simulated steps.

| Stage | Scenario | Required telemetry | Proposed acceptance |
|---|---|---|---|
| P3-0 | Offline trajectories for left- and right-leading cycles; abort injected from every phase | phase, phase time, nominal targets, final bounded targets, transition reason | Deterministic; all values finite; targets within joint limits; per-tick target change <=0.008 rad; safety abort prevents later transitions |
| P3-A | Native contact instrumentation and neutral double support | left/right contact state and force, raw contact values, foot pose, COM, support polygon | Sensors parse in native Webots; both feet show plausible support; GUI agrees; no penetration or false anchoring |
| P3-B | Shift left, hold, return; then mirror right, with both feet down | all P3-A signals plus IMU, root pose/velocity, targets/measured joints | One pilot then 5 resets/side; both feet retain contact; COM enters documented target region; returns to neutral; no FAULT |
| P3-C | Unload and lift right foot 5-10 mm, replace in place; mirror left | contact ratio/state, foot clearance, COM margin, phase events | Support foot never loses contact; swing foot unloads and clears floor; touchdown is measured; stable double-support settle; at least 4/5 per leg |
| P3-D | One bounded forward step, right-leading and left-leading | toe-off, clearance, touchdown, support transfer, root displacement, final settle | One pilot then 5 trials/lead leg; real positive body displacement; valid contact sequence; final stable double support; at least 4/5 each side |
| P3-E | Five alternating forward steps | all gait telemetry, valid step index, stride time/length, net progress, first fault | 10 fresh native trials; every successful trial has at least 5 valid touchdown/transfer events; proposed >=8/10 success; every failure retained |
| P3-F | Safety negatives for each proposed motion stage | safety state/reason, first-fault time, post-fault motion | Run the relevant native negative before its motion stage: freshness/contact before lift, touchdown/timeout before a full step, and obstacle/E_STOP before repeated gait; every event latches correctly and never advances phase |
| P3-G | Characterization after nominal gate | exact friction, mass, delay and seed metadata | Small controlled variations are reported without per-case hidden retuning; degradation and falls remain explicit |

### Scenario parameterization gate

Before implementing a P3 motion scenario, its reviewed specification must replace qualitative terms with deterministic definitions derived from neutral-contact data and robot geometry. At minimum it defines:

- raw contact-force threshold, debounce interval, stale-data deadline, and exact contact-loss injection;
- floor and foot reference frames, foot-clearance calculation, and early-collision rule;
- support-polygon construction, COM projection, required signed margin, and target region;
- phase deadlines, settle duration, permitted pose/velocity/tilt bands, and tracking-error duration;
- minimum forward root displacement for a valid step and the complete contact-event sequence;
- reset procedure, trial count, seed policy, and first-fault classification.

Until those values are approved, `plausible support`, `stable settle`, `valid contact sequence`, and success-rate goals are design placeholders rather than executable gates.

### Required P3 telemetry

At minimum, every native P3 run records:

- run ID, PR head/source SHA, tested merge SHA, config hash, world hash, actual `webots --version` output, immutable container digest, seed, and exact model parameters;
- gait phase, phase elapsed time, lead leg, step index, requested transition, and accepted transition reason;
- left/right raw contact or force, debounced contact state, foot world XYZ, and swing clearance;
- center of mass XYZ, active support polygon, and signed COM margin;
- root XYZ and velocity, roll/pitch/yaw, gyro XYZ, and accelerometer XYZ;
- all joint nominal targets, bounded targets, measured positions, tracking error, and available/measured torque when supported;
- safety state/reason, first-fault timestamp, and telemetry after a fault until the run ends.

### P3 gait-specific safety conditions

Retain the existing safety limits. Add fail-closed gait conditions for:

- expected support-foot contact loss;
- both feet losing contact, because P3 has no flight phase;
- COM leaving the permitted active support region;
- swing-foot collision before the touchdown window;
- missing, stale, or nonfinite contact/COM data;
- landing or phase timeout;
- requested target outside joint/rate limits;
- persistent target-tracking error beyond a documented bound;
- ground penetration or unexpected torso/leg contact.

On any fault, cancel phase progression and any experiment disturbance, preserve the first fault and subsequent motion in telemetry, and require a fresh reset. Holding the last target does not guarantee that the robot will stop falling, so post-fault evidence is required.

## Implementation work packages

### Package 1 P2.2 force compatibility and provenance

- Add a unit-tested compatibility layer or adopt a pinned Webots release containing fix #6881.
- Record PR head/source SHA, tested merge SHA, actual Webots version, container digest, force API path, world hash, and application schedule.
- Add D1 and D3 native diagnostic scenarios.

**Gate:** corrected offset produces the expected signed angular response in a calibration scene.

### Package 2 P2.2 observability and complete pilot

- Report both tilt axes, signed root motion/velocity, accelerometer, gyro, and correction/target/measured response.
- Add contact and torque evidence where Webots supports it.
- Make the CI report distinguish `artifact_valid`, `matrix_complete`, and `scientific_gate`.
- Run all four directions at the same force only when the prior case is valid, no-fault, and inconclusive solely because of low excitation. FAULT, INVALID data, wrong sign/axis, or contact uncertainty must stop the matrix immediately; the current broad `--continue-on-concern` behavior is not sufficient for this distinction.

**Gate:** all four pilots are interpretable; no result is hidden by early stop or a single-axis summary.

### Package 3 P2.2 scientific gate

- Determine the first measurable safe envelope one variable at a time.
- Verify sign before gain tuning.
- Run the full paired matrix without changing safety limits.

**Gate:** the acceptance criteria in this report and [balance matrix protocol](balance-matrix.md) pass on native Webots artifacts.

### Package 4 P3 contact observability then state-machine foundation

- Before P2.2 passes, add only neutral-pose per-foot instrumentation, COM/support calculations, and evidence schemas; do not add gait targets or transitions.
- After P2.2 passes, add runtime freshness checks, the independent watchdog design, P3-0 offline state-machine tests, and balance correction around a nominal gait pose.
- Implement P3-A observability first, then P3-0 after the P2.2 gate.

**Gate:** native contact evidence agrees with GUI inspection; freshness/contact fault injections pass natively before any foot lift; every phase abort path is also covered offline.

### Package 5 P3 staged motion

- Implement P3-B, review its artifact, then P3-C, then P3-D.
- Before each stage, run the relevant P3-F native negatives: contact/freshness before lift, and early-contact/touchdown/timeout before a full step.
- Change one trajectory or control variable per experiment.
- Do not start repeated gait until both lead-leg single-step gates pass.

**Gate:** stage-specific native acceptance criteria pass with retained failure evidence.

### Package 6 P3 repeated gait and characterization

- Implement P3-E only after prior gates.
- Prove obstacle STOP and E_STOP natively before repeated gait, then keep the full P3-F suite as a regression gate.
- Add P3-G bounded characterization only after repeated gait passes nominal conditions.

**Gate:** at least five valid physically simulated steps with sustained support evidence, plus the approved success-rate criterion.

## Verification and evidence boundary

Offline verification can prove schema handling, finite bounded trajectories, state transitions, limit enforcement, deterministic reports, and fault latching. It cannot prove Webots parser acceptance, delivered wrench, foot contact, load transfer, dynamic stability, or walking.

Every source PR must therefore follow the repository evidence loop:

1. inspect the exact previous native artifact and commit;
2. run offline tests and native Webots smoke on the PR;
3. download and inspect the PR artifact before another controller change;
4. after merge, inspect five independent baseline trials on the merged SHA;
5. retain first-fault telemetry and never equate a green workflow with balance or gait success.

## Verification performed for this review

- Downloaded and inspected the complete native artifact from run `39648900940` at test merge SHA `e0ba9c1e453c6927fe73e213b1faa57839b906cf`.
- `python3 tools/verify_project.py` passed. This is an offline structure check and explicitly does not test Webots contacts or dynamics.
- `python3 -m unittest discover -s tests -v` passed 89 of 89 tests. These are offline/fake-Webots tests, not native physics evidence.
- `PYTHONPYCACHEPREFIX=/private/tmp/robotis-lab-p22-pycache python3 -m compileall -q simulation/webots/controllers tools tests` passed.
- `git diff --check` passed.
- No new native Webots run was possible in the local workspace, and no controller or robot source was changed. P2.2 remains inconclusive.

## Acceptance gate and next step

**Current gate:** P2.2 `INCONCLUSIVE`; P3 gait trajectories, state machine, and native motion `BLOCKED`. Only planning and neutral-pose observability/provenance work may proceed.

**Next falsifiable step:** create a small source PR that either uses an exact pinned Webots build demonstrably containing fix #6881 or bypasses only the broken R2025a Python wrapper through the correctly typed C function. Prove the repaired offset in a minimal native Webots calibration scene, add version/API provenance to the artifact, and rerun one bounded pitch +1 pair before changing force, PID signs, gains, gait code, or safety limits.

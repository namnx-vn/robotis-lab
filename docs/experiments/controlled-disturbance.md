# Sprint 02.1 — Controlled Disturbance Validation (Webots R2025a)

## Objective / background

The real macOS Webots v0.2 static standing test passed 5/5 at 31.92s each. A subsequent manual balance-mode run showed a late `FAULT excessive_tilt` around 28.91s, with initial roll already at -0.243 rad. A manual mouse tug is **not reproducible**; no valid conclusion about controller sign was possible.

This sprint measures whether active IMU feedback performs better than the open-loop neutral position hold under **the same small, deliberate simulated force pulse**. It is still not a walking or hardware test.

## Experimental architecture

- `RLH25.proto`: untouched 25cm model, already `supervisor TRUE` + Physics on root. Current controller loads `controller.Supervisor()` **only** when `RL_H25_DISTURBANCE=1`; otherwise its normal `Robot()` path is unchanged.
- `disturbance.py`: a one-shot bounded world-frame force at a small local +Y offset (torso). Uses `Supervisor.getSelf().addForceWithOffset(force_vector, [0, offset_m, 0], False)` for each physics step during a short pulse, automatically cancels upon `STOP`/`FAULT`/`E_STOP`.
- Only an explicitly launched experiment enables this. No physical servo, Arduino, network or AI is involved. The existing tilt hard limit remains **0.45 rad**; DO NOT increase it to improve pass rate.
- `tools/run_disturbance_trials.py`: starts completely fresh Webots processes for pairs: `baseline` then `balance`, repeated 3/5 times. Fixed random seed, world, model and all force parameters. Saves matching CSV + JSON.
- `tools/disturbance_report.py`: rejects missing force evidence, inconsistent metadata, zero actual perturbation, initial tilt >0.08rad, time gaps, faults, insufficient post-pulse observation and non-unique session IDs. If an input is invalid/inconclusive, DO NOT treat it as a successful PID result.
- Disturbance logs use telemetry schema v2. They must include build/source/test provenance, root angular velocity and COM, static-balance status, all ten joint target/measured/torque channels, and explicit left/right foot coverage. The analyzer also requires balance-mode correction and actuator response evidence; contact continuity is a hard gate.

## Force protocol (unverified initial assumptions)

**World coordinates:** `NUE` / Y-up. Direction ±Z targets pitch, ±X targets roll. A world-frame force at root-local Y offset ≈4 cm creates a moment around the corresponding horizontal body axis.

| Parameter | Initial pilot | Hard software bound |
|---|---:|---:|
| Magnitude | 0.10 N | 0.01..0.50 N reviewed force gate |
| Pulse | 0.112 s | 0.016..0.20 s |
| Start time | 4.0 s | 2..15 s |
| Offset | +0.04 m local Y | 0..0.06 m |
| Sampling period | 0.016 s | 0.016..0.20 s |
| Total run | 14 s | Up to 60 s (runner) |

The maximum bounded calibration pilot (`0.35 N`, `0.20 s`, `0.06 m`) remained below the `0.008 rad` excitation threshold in all four directions. It must therefore remain classified `INCONCLUSIVE`; do not infer PID recovery or improvement from it.

An exact-source ladder later reviewed `0.50 N`, `0.20 s`, `0.06 m` as the maximum ordinary force-pilot envelope: all four directions completed without FAULT or contact loss, but only pitch+ was measurably excited. The `1.00 N` pitch+ calibration failed with `excessive_tilt`, fall and contact loss. Values above `0.50 N` remain explicit calibration-only inputs and can never satisfy the P2 scientific gate; do not escalate further without a new reviewed protocol.

Approximate nominal impulse: **0.0112 N·s**, ignoring mechanical joint compliance and exact timestep quantization. Effective torque, support polygon and actual COM response must be measured. Pulses can be shorter/longer by up to one step due to discrete simulation timing; metadata reports real applied-step count.

## Direct-torque compatibility probe — not an RL-H25 experiment yet

Webots R2025a's Python `Node.addTorque()` wrapper calls the wrong C function. The source now includes a narrow `ctypes` adapter for the declared three-argument `wb_supervisor_node_add_torque` ABI and extends the independent free-body probe with pitch ±, roll ±, zero-torque and yaw-rotated world-frame cases. The existing CI disturbance job must reject the probe unless every force and torque case passes. The parser independently rechecks raw angular velocity, signs, cross-axis response, probe magnitude, pulse length, exact Webots version and build/source/test SHA instead of trusting the controller's `pass` flag.

The probe uses `0.01 N·m` for eight 16 ms steps on the isolated 0.5 kg cube. That value is chosen only to make the free-body angular response measurable; it is **not** an approved RL-H25 torque, a hardware limit or evidence that direct root torque represents a collision. No direct-torque call is connected to the RL-H25 controller or matrix runner in this change. A separate reviewed robot pilot and metadata schema are required after native probe evidence passes.

## Mac commands — safe order

From the extracted `robotis-lab-v021` directory, close Webots GUI instances before batch runs:

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v

# Pilot, 1 pair (baseline + PID), initial 0.10 N, do NOT jump to gait:
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --axis pitch --force 0.10 --pulse 0.112 --duration 14

# If pulse is visible/measurable and both trials are safe, 5 pairs:
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 --axis pitch --force 0.10 --pulse 0.112 --duration 14

# Optional second axis, separately; initially one pair only:
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --axis roll --force 0.10 --pulse 0.112 --duration 14
```

**Return code:** `0` only when at least three comparable, unfailed pairs demonstrate ≥10% lower mean peak response using balance. Nonzero does not always indicate a software crash; `INCONCLUSIVE`, `FAIL`, and `NO_DEMONSTRATED_IMPROVEMENT` are scientifically useful findings. A pilot with one pair will deliberately return status `1` (not enough evidence for declaring improvement) despite producing two complete files.

To visually watch the experiment, use `--graphics`. The command runner starts/terminates Webots automatically; do not interact via drag during an automated run because that invalidates force equality. If macOS rendering is black, the default headless `--no-rendering` runs still record sensors. Do not mix in manually altered worlds or GUI-reset poses.

### If the force is not measurable

`INCONCLUSIVE no_measurable_excitation` means peak change below **0.008 rad**; do not call it PID success. Inspect evidence first. If robot starts level, no faults, actual applied_steps > 0, and max tilt too small, rerun **one pair** with 0.15 N, then 0.20 N only if needed (still within cap). Never jump to max force and never edit safety threshold. Force is not equivalent to a real collision.

### Important interpretation

- `RECOVERED`: in that *individual synthetic/real run*, tilt change ≥0.008rad, maintained nominal root height and no `FAULT`, and returned within 0.025rad for ≥0.8s after the peak in the first 5s. It is NOT certification of whole-body balance.
- `FAIL`: excited robot enters `FAULT`, falls, large drift, or fails to settle in time.
- `INCONCLUSIVE`: perturbation never measured, insufficient pairs or incompatible conditions.
- `IMPROVED`: ≥3 distinct non-calibration paired experiments, same force schedule, all balance trials recovered, and ≥10% reduction in mean peak tilt vs baseline. A stronger claim requires roll+pitch, opposite directions and a wider range of forces; even then this remains simulation-only.
- `CALIBRATION_ONLY`: a high-force calibration completed, but it is excluded from scientific P2 acceptance even when individual runs recovered.
- `NO_DEMONSTRATED_IMPROVEMENT`: recovered but did not beat baseline under the explicit rule; tune PID sign/gains only from evidence.
- `INVALID`: corrupt data, force didn't apply, missing metadata, pre-pulse already tilted/fallen, incomplete run, etc.

## Risks and next gate

Weak active PID can inject energy and destabilize the biped. On `FAULT`, the controller freezes targets; the robot may continue falling under gravity. Operator should not use this simulator code to command real servos. The experiment relies on idealized motors/mass/friction and no external sensor noise.

**Acceptance to progress:** native free-body force/torque probe passes first; then a separately reviewed RL-H25 disturbance protocol must produce comparable evidence in all four directions. The P2.2 gate still requires at least three matched pairs per direction, no FAULT/contact loss, recovery, and at least 10% lower mean peak tilt with balance before weight shift. Even if evidence is positive, inspect contact geometry and root rigid-body freedom in GUI.

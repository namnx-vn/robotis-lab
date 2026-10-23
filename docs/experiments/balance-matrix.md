# Sprint 02.2 — Four-direction balance evidence gate

## Goal

Before P3 gait, establish measurable and repeatable pitch and roll disturbance recovery **for both signs** in Webots R2025a. This extends, rather than replaces, the original v0.2.1 protocol. Hardware and walking are out of scope. Prior Webots 5/5 standing results only prove *undisturbed static standing*, not active recovery. A manual disturbance previously ended in `FAULT excessive_tilt`.

## Procedure (macOS Webots R2025a)

Close Webots GUI sessions to avoid port and state conflicts. In the repository root:

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v

# Protocol sanity check: NO Webots processes are launched
python3 tools/run_balance_matrix.py --dry-run --pairs 1

# Exactly 1 pair per direction; intentionally does not declare PASS
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14

# Only if all pilot directions generated valid, measurable, non-FAULT data:
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 --force 0.10 --pulse 0.112 --duration 14
```

The script runs `pitch +1`, `pitch -1`, `roll +1`, `roll -1` in that order. Each case runs a fresh Webots process for `baseline` followed by `balance` with identical force schedule. It writes paired CSV+JSON telemetry and the aggregate `experiments/logs/balance-matrix-<UTC>.json` (ignored by Git). The `--dry-run` output does not establish simulator compatibility.

An **exit code of 1 for the pilot is expected**: one pair per direction cannot satisfy the three-pair minimum. `READY_FOR_FULL` only means a direction showed valid excitation and *both modes recovered*. An `INCONCLUSIVE` or `REVIEW_REQUIRED` result stops the matrix before subsequent axes by default. Inspect that pair's telemetry before repeating; don't increase the force blindly.

## Acceptance gate

`PASS` requires four distinct conditions (two axes × two signs) with >=3 comparable paired runs each, measurable excitation, no FAULT, settling within the stated report criteria, and >=10% lower average peak tilt in PID vs baseline **for each condition**, not only on average across directions. Each measurably excited run must initially respond with the requested sign on the intended axis; an opposite signed response is `FAIL` and requires review before any full matrix.

This is a strict experimental goal, **not an observed result**. A non-PASS is useful debugging evidence and **blocks P3 walking**. Inspect GUI contacts and verified motor command signs separately. Baseline/active parity is important: use the same world, model version, timestep and disturbance envelope.

## Risks and required operator review

The inertial PID gains and direction signs are uncalibrated; the synthetic force may not translate to a real impact. Webots friction, idealized motor torque, missing sensor noise and body contact can overstate performance. Do not disable the angle/height FAULT gate. No Arduino or real motor commands are made. Stop after any unexpected FAULT and inspect first-fault CSV. Visual contact/foot-slip inspection remains mandatory before entering weight-shift gait.

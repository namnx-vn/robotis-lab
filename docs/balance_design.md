# RL-H25 0.2 — Bounded IMU feedback design and limits

**Requirements**: preserving Webots 10-DOF geometry; add roll/pitch feedback without violating joint limits, maintain FAULT/E_STOP priority, no API/LLM in loop. No hardware command path.

## Architecture

```
Webots IMU + joint position sensors + GPS + laser + gyro
       |
       v
 SafetySupervisor -> latching STOP/FAULT/E_STOP
       |           (no new pose commands after latch)
       v
 BalanceController (mode=baseline -> neutral; mode=balance -> 2 AnglePIDs)
       |
 roll/pitch PID corrections (rad, bounded) -> joint mixing -> per-joint slew + hard bounds
       |
 Webots RotationalMotor target positions + PositionSensor feedback + logs
```

`AnglePID`: `error=-angle`, derivative-on-measurement with first-order filter, conditional-integration antiwindup, integral/output caps, reset on safety state or unusually long timestep. `BalanceController` drives ankle pitch/roll equally on two legs and adds small negative hip offsets to avoid upper-body overreaction. It leaves knees at neutral. The chosen gains and signs are **hypotheses**, not verified optimal gains.

- `control.tilt_fault_rad = 0.45`: unchanged hard fault threshold from Sprint01; does not move to make graphs pass.
- `balance.pitch.output_limit_rad = 0.10`, `balance.roll.output_limit_rad = 0.08`: outer-loop correction amplitude limits, must still pass joint limits.
- `joints.*.rate_limit = 0.5 rad/s`: max target slew (0.008 rad/step at 16ms).
- Webots motors have separate internal servo dynamics; outer PID does not command torque directly.
- `balance.axis_sign` and `joint_mix` **unverified**: one axis convention inversion could amplify tilt. Test with **small controlled perturbations in simulator only**; if a small measured positive error grows when feedback turns on, stop simulation and review sign (only +/-1) and ankle/hip mixing. Do not bypass safety or move to gait while unstable.
- Integral cannot hide sustained tilt: if offsets saturate at output cap, the robot may still topple -> FAULT.
- Derivative uses filtered IMU finite difference, not raw Gyro coordinate axes; gyro is logged as diagnostic. This avoids assuming a gyro-axis mapping without a measured sign calibration.

## Proposed tuning sequence

1. Collect 5 independent **baseline** (PID off) trials, report tilt/height/drift/gaps and first FAULT samples.
2. Confirm standing and feet contacts by 3D video, compare measured joint targets vs sensors.
3. Switch to `RL_H25_MODE=balance RL_H25_DURATION_S=8` (operator present). Inspect correction signs and whether |roll|/|pitch| decay after a **small controlled tilt**. In case of oscillation or increasing tilt, stop and flip only the relevant `axis_sign`, retest. **Do not change everything at once.**
4. Increase to five 32-second balance trials, compare with same scenario/seed/baseline.
5. If 4/5 success in both, only claim 'bounded IMU-based posture correction demonstrated', not self-stabilizing walking or disturbance rejection until additional controlled external-perturbation trials are added.

## Safety/test matrix

| Scenario | Expected |
|---|---|
| Baseline without tilt | target=neutral, PID disabled, log fields filled |
| Mild tilt in balance mode | opposite signed position offset, within output cap |
| Correction saturates | output bounded, anti-windup integral bounded |
| Missing/nonfinite IMU | latched FAULT, freeze targets |
| Joint sensor invalid | latched FAULT, freeze last targets |
| `dt` exceeds configured maximum | latched FAULT, PID reset |
| Obstacle closer than safety threshold | latched STOP, no fresh commands |
| Simulated E_STOP | torque disabled, no auto-unlock (robot may fall) |

**Out of scope**: ZMP/contact-force feedback, center-of-pressure, balance during gait, hardware servo dynamics, torque budgeting and fall recovery. These require future instrumentation and actual tests.

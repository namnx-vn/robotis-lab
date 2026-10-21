# Robotis Lab — Sprint backlog and phase gates

## P1 — Initial Webots RL-H25 skeleton (completed for native launch)
- [x] Webots R2025a parser and 10 DOF geometry seen running on operator macOS.
- [x] Add IMU/gyro/accelerometer/GPS/camera/distance telemetry and Physics.
- [ ] Visually verify bounding boxes, both foot contacts and absence of false static anchoring in Webots.

## P2.1 — Static standing baseline (automated gate passed)
- [x] Bounded IMU pitch/roll PID implemented (offline tests; native recovery unverified).
- [x] Native Webots baseline: operator-reported **5/5 PASS**, 31.92 s each, no FAULT.
- [ ] Upload or attach real CSV/JSON runs for independent analysis; confirm foot contact GUI observations.

## P2.2 — Controlled balance recovery (current sprint)
- [x] Opt-in, bounded Supervisor pulse for matched baseline/balance simulations.
- [x] Experiment runner and telemetry validity checks; FAULT and absent excitation are not passes.
- [x] Add four-case pitch+/pitch-/roll+/roll- matrix and fail-closed aggregate gate.
- [x] Add Python 3.10/3.12 CI on pull requests; offline suite.
- [ ] Operator: one-pair pilot matrix in native Webots R2025a.
- [ ] Check whether all four directions receive measurable force without faults.
- [ ] Operator: five matched pairs/direction only after pilot review.
- [ ] Validate PID axis signs/gains from observed telemetry and controlled recovery.
- [ ] Confirm surface contacts and COM dynamics in GUI; maintain 0.45 rad hard FAULT limit.

## P3 — Weight shift and gait (BLOCKED)
- [ ] Gate: >=3 matched comparable pairs **for each of four directions**, >=10% lower peak tilt with balance, no FAULT and measured recovery; validate contact/friction.
- [ ] Only after gate approval: supported weight shift, then single simulation step with contact logs.

## Hardware (NOT STARTED)
- [ ] Inventory actual servo/IMU/Uno/components and fabrication.
- [ ] Torque/power calculations; one-joint current/thermal bench before purchasing.
- [ ] Independent servo rail, fusing, E-STOP; operator authorization.

## Evidence discipline
Python/fake-Webots test results do not prove native Webots dynamics. Logs in `experiments/logs/` are intentionally Git-ignored. The code cannot make safe hardware claims or walk unassisted merely because animation is visible.

# Robotis Lab phase gates

| Phase | Scope | Evidence required |
|---|---|---|
| P0 | Requirements, current components, cost and environment | Physical inventory and assumptions documented |
| P1 | Webots RL-H25 25 cm 10-DOF + sensors | Native Webots world/parser and physically articulated geometry |
| **P2 (current)** | Undisturbed stand, IMU feedback, disturbance recovery | 5 fresh standing trials plus paired controlled pitch/roll disturbances (both directions) with contact/tilt logs |
| P3 | Weight shift, single step, repeated gait | Sustained ground contact and >=5 physically simulated steps with falls/logs verified |
| P4 | Obstacle/safety | Fault/STOP response with obstacle scenarios and sensor failure tests |
| P5 | Arduino + PCA9685 bench | 1 servo jig with safe independent supply, peak current, torque/thermal verification and E-STOP |
| P6 | Supported physical steps | Human-supervised jig/tether trial with matched simulation data |
| P7 | Bounded autonomy | Local deterministic planner and optional validated AI high-level intents |

**Current evidence:** operator reported v0.2 native Webots unperturbed 5/5 standing gate. Manual perturbation caused FAULT, so active balance and gait are not verified. Budget goal <=3,000,000 VND is a planning constraint, not a verified full-build quote.

Do not advance phase based on animation, mocked testing, or an ideal deterministic standing pose alone.

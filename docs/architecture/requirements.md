# RL-H25 Sprint 01 — Requirements

## Goal

A downloadable Webots project, not just a still model: a 250 mm articulated humanoid with
head/torso/two passive arms, two legs × 5 DOF, gravity, meaningful collisions, cameras and
sensors, neutral stance control, bounded joint targets and reproducible telemetry.

## Constraints

- R01: Webots `.wbt` world with 2 × 2 m floor and an obstacle.
- R02: local `RLH25.proto` with 10 `HingeJoint`, 10 `RotationalMotor`, 10 `PositionSensor`.
- R03: rough rigid-body mass and contact for every moving link, tunable feet/floor friction.
- R04: root position at 0.183 m and zero-joint height about 0.250 m (geometrical assumption).
- R05: InertialUnit, Gyro, Accelerometer, GPS, laser DistanceSensor, Camera; no API/network.
- R06: control/measure joint angles in radians, rate limiting + hard/soft angle stops.
- R07: STOP on front distance, FAULT on tilt/height/non-finite sensor, E_STOP injection.
- R08: CSV+JSON logs with run_id, state, raw readings, joint targets and measurements.
- R09: error paths, fake-controller tests, offline structural check and optional real Webots smoke.

## Explicitly not in Sprint 01

- Balanced standing validated for >=30 s on multiple runs (P2 gate).
- Biped walking (P3), avoidance maneuvers (P4), Arduino firmware, procurement or AI API.
- Physical E-STOP; this is only the simulation software state. No real servo may use this code unreviewed.

## Acceptance ladder

1. Python compile, model generation and all offline tests PASS.
2. User opens `.wbt`, no parser errors, motor/sensor names resolve, gravity and feet contact visible.
3. Under simulator, run for >=8 seconds with telemetry produced and no parser/runtime errors.
4. Later P2: >=4 of 5 independent 30-second reset trials satisfy predefined measured stability criteria.

Stages 2–4 require a real installation of Webots and cannot be inferred from offline tests.

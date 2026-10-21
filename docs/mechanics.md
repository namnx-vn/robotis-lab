# Geometry, mass and coordinate assumptions

| Parameter | Sprint 01 value | Evidence status |
|---|---:|---|
| Robot model top at all-zero | 0.250 m | Computed ideal box geometry only |
| Root elevation (Robot translation Y) | 0.183 m | Design parameter |
| Left/right hip pivot X | -0.031 / +0.031 m | ASSUMPTION |
| Hip to knee | 0.070 m | ASSUMPTION |
| Knee to ankle | 0.070 m | ASSUMPTION |
| Foot collision geometry | 0.044 × 0.018 × 0.076 m | ASSUMPTION |
| Foot collision sole at neutral | Y = 0 m | Computed ideal box geometry |
| Body mass | 0.140 kg | ASSUMPTION; includes passive head/arms |
| Each leg mass | 0.120 kg | ASSUMPTION |
| Total modeled mass | 0.380 kg | ASSUMPTION |
| Motor maximum torque | 0.8 N·m | Unverified simulation assumption |
| Floor–foot friction coefficient | 1.1 | Unverified simulation assumption |

This *is not* a mechanical drawing that can directly be printed and assembled.
The box volumes, ideal position servos, fixed arm/head, absence of gear backlash,
zero wiring mass and simplified joint pivot geometry are not representative of real hardware.

## Coordinate frame

WorldInfo `coordinateSystem "NUE"` makes **Y up**; X is left/right and **-Z forward**.
Servo angles in radians; hip/ankle roll about Webots Z, pitch joints about X. Each
joint has a PositionSensor named `<motor_name>_sensor`.

## 10 leg joints

Left + right: hip_roll, hip_pitch, knee_pitch, ankle_pitch, ankle_roll.
Hip yaw is absent, so turning/walking is out of scope until gait feasibility is tested.

## Simulation physical risks

The model begins with flat feet touching the floor geometrically. However, a realistic
motor-limited biped can fall rapidly; neutral pose alone is not dynamic balance.
The body's visual parts do not all contribute separate collision shapes. Root Physics
lumps head/arm masses into a single mass with approximate auto-computed inertia.
For sim-to-real, obtain actual link masses and inertias, servo sustained torque/current,
gear backlash, plantar friction and controller delay. Re-run tests with perturbations.

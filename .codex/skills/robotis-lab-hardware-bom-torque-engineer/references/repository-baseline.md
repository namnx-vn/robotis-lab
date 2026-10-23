# Dated repository orientation — **recheck before use**

Observed from connected GitHub `namnx-vn/robotis-lab` **on 2026-10-22** (this is an orientation snapshot, not authoritative future status):

- `README.md`: Webots R2025a RL-H25 with 10 DOF. Native **undisturbed** standing 5/5 × 31.92s documented; active IMU PID disturbance recovery unvalidated; P3 gait blocked; hardware not started.
- `AGENTS.md`: simulation-first; Webots radian units; AI must not issue raw PWM. Independent servo power, common ground, current/fuse/E-STOP review and explicit operator approval required before risky hardware work. One-joint bench before procurement of all ten motors.
- `configs/robot.json`: version RL-H25-v0.2; geometry assumptions height 0.25m, hip-to-knee 0.07m, knee-to-ankle 0.07m, **assumed** mass 0.38kg and idealized position servo model. Joint entries include idealized `max_torque: 0.8` N·m for simulation—not measured physical actuator capability.
- `IMPLEMENTATION_PLAN.md`: nominal ≤3,000,000 VND physical prototype budget (planning only); its historic component cost ranges are **not contemporary verified quotes**. Sequence is inventory → mechanics/mass/torque → servo bench → supply/E-STOP → final BOM.
- `tasks/backlog.md`: actual servo/IMU/Uno inventory, torque/power calculations, one-joint current/thermal bench remain unchecked. Operator indicated existing Arduino Uno separately in the current skill requirements; verify exact model/revision physically.
- `docs/ROADMAP.md`: P2 balance current; P5 Arduino+PCA9685 hardware bench requires safe one-servo rig, independent source, measured current/thermal and E-STOP.

## Source navigation

Repository URL: https://github.com/namnx-vn/robotis-lab

Read before each substantive activity:

```
README.md
AGENTS.md
PROJECT_INSTRUCTIONS.md
IMPLEMENTATION_PLAN.md
docs/ROADMAP.md
tasks/backlog.md
configs/robot.json
docs/architecture/requirements.md
simulation/webots/protos/RLH25.proto
simulation/webots/controllers/rl_h25_controller/motion.py
```

Check `docs/OPERATOR_HANDOFF.md`, active PRs, manufacturer/vendor materials and any recent inventory files as relevant; do not assume listed sources exist unchanged. Respect repo architecture rather than create redundant folders. Proposed target file paths for future *requested* work should follow established repository layout; do not modify source from the skill alone.

# Safety contract — Sprint 01 (simulation ONLY)

The software is intended solely for Webots. No direct motor electronics are present.

- STAND: hold neutral targets at rate_limit. This is *not* an active balance controller.
- STOP: proximity under 0.18 m latches pose target; does not start avoidance.
- FAULT: bad sensor, excessive roll/pitch (0.45 rad) or root height below 0.10 m.
- E_STOP: simulation-only `RL_H25_FORCE_FAULT=estop` sets simulated available motor torque to zero.
  On a physical robot, this can cause free-fall and **cannot** replace a hardware E-STOP.
- Latches do not automatically reset. An explicit approved reset helper exists but is not called
  by the Sprint 01 controller.
- Control rate is Webots `basicTimeStep` 16 ms. There is no network/LLM in motor loop.
- Simulated torque and friction are UNVERIFIED, and no real servo specs are implied.
- No hardware electrical wiring, purchase or free autonomous exploration approved here.

## Deferred safety engineering (before hardware!)

Physical E-STOP cutting servo power through rated switching device, appropriate fusing,
external servo 5–6V rail with GND shared with Uno, watchdog independent from cloud,
calibration and joint travel stops on microcontroller, safe harness for brownout/fall.

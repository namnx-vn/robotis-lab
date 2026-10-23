# Motion and safety review checklist (RL-H25)

Use for source, configuration, PR and architecture reviews. Mark every relevant item as `CHECKED`, `GAP`, `NOT APPLICABLE (phase/scope)`, or `UNVERIFIED`; never assume a future feature exists.

## Requirements and architecture

- [ ] Name branch, exact base/head/source/test merge SHA, diff, experiment mode, target Webots version and phase gate.
- [ ] Locate all five architectural layers; identify existing classes vs proposed interfaces and authority to issue commands.
- [ ] Trace high-level intent → schema/authorization/deadline filter → behavior → safety gate → motion controller → simulator/hardware adapter.
- [ ] Demonstrate no LLM/network dependency on real-time control or safety reaction.
- [ ] Confirm independent physical hardware E-STOP is **future hardware obligation**, not satisfied by software sim.
- [ ] Confirm past/current tests match changed paths and not merely an unrelated green CI job.

## Motion bounds and transitions

- [ ] Exactly ten leg actuator names in current config, defined axis/sign and radians; `neutral` inside `min,max`.
- [ ] Validate `min <= target <= max`, finite inputs, timestamp/time delta > 0; controller honors per-joint `rate_limit` even at startup, reset and emergency transition.
- [ ] Compare motor `max_velocity`, controller slew limit and future servo observed speed; check acceleration and jerk as necessary. Distinguish command slew from physical acceleration.
- [ ] Saturation never bypasses bounds; PID integral is reset or limited on disable/saturation and stale sampling.
- [ ] Disallow arbitrary angle changes from AI or planner bypassing controller limits.
- [ ] Safe trajectory transition: feasible initial joint pose, collision/contact, COM/support, no discontinuous motor step.
- [ ] Verify joint direction and PID negative feedback with **measured** ± pitch and ± roll perturbation; do not infer from sign variable names.
- [ ] Bound estimated COM uncertainty and polygon of support; without reliable contact force/pressure, don't claim dynamically validated support/ZMP.
- [ ] Check periodic jitter, `dt`, PID derivative filtering, integral windup and NaN propagation.

## State-machine required target

Main sequence is `BOOT → SELF_TEST → CALIBRATE → IDLE → STAND → WALK → EXPLORE`. FAULT/E_STOP safety preemption must be possible in every normal state. `STOP` or safe-stopped motor state may be distinct according to design. Check every edge and opposite edge.

| Transition / override | Minimal required guard or response |
|---|---|
| BOOT → SELF_TEST | Safe startup: no unvalidated actuator enable; testable dependencies and timestamps |
| SELF_TEST → CALIBRATE | Sensors/actuators/config healthy; protected calibration context |
| CALIBRATE → IDLE | Calibration bounded, operator concurrence where required; neutral targets verified |
| IDLE → STAND | Approved mode and ready motors/sensors, contact and safe pose; rate-limited transition |
| STAND → WALK | P2 active balance gate accepted, accurate contacts and valid gait prerequisite |
| WALK → EXPLORE | P3 gait and P4 sensing/STOP gates met, validated bounded planner intent |
| ANY → FAULT | Trip on non-finite/stale sensor, overtilt, missed loop deadline or invalid safety-critical condition; cause latched |
| ANY → E_STOP | Highest priority, independent of cloud/command source; appropriate physical inhibit |
| FAULT/E_STOP → safe inactive | No automatic rearm; authorized operator reset, cleared cause, fresh self-tests |
| ANY → STOP/inhibit | Obstacle, lost perception, stale planning/deadline or safety uncertainty inhibits unsafe movement |

**Design caution:** direct e-stop torque-zero can cause collapse; physical E-STOP and mitigation (tether/rig) require hazard analysis. “Hold target” can also overheat servo or fail when unpowered. Do not hardcode either action as universally safe.

## Failure modes and threat/command boundaries

For each hazard, record **source, trigger, observable signal, detector, worst-case latency, response, latching/rearm rule, test evidence, residual risk**. At minimum cover:

- Lost heartbeat, unplugged MCU link, dropped/reordered/duplicated packets and stale command replay.
- Unknown/unauthorized intent, arbitrary PWM or torque payload, expired `deadline`, malformed JSON, non-finite float, unexpected mode/state.
- IMU stale, NaN, clipped or frame-inverted; gyro disagreement; encoder missing/jumping; obstacles missed or false-positive; floor contact ambiguous.
- Controller overrun, `dt` spike, servo saturation/stall/overtemperature (hardware stage), brownout/restart, supply sag.
- E-STOP active at startup, asserted mid-ramp, E-STOP while falling; fault latch retained across parser errors/controller restart.
- Planner attempts to transition to WALK/EXPLORE without phase gate.

## Quantification, reports and regression

- [ ] Specify what is **observed** (sample, measured axis, contact evidence, exact time, run ID) vs **estimated** (COM, friction, torque assumption).
- [ ] Preserve first-fault timestamp/reason; don't replace it with a secondary downstream error.
- [ ] Include successes **and** independent failed/inconclusive trials; reset each trial.
- [ ] Verify configuration and world checksums, simulator profile and commit correspondence.
- [ ] Verify rollback behavior / old version config; no safety supervisor bypass under error recovery.
- [ ] Check actual motor target vs encoder/position and drive limits during active disturbance, not only controller `STAND` flag.
- [ ] Check release approval does not authorize power rail changes, hardware tests, merge or gait when gate is missing.

## Example lightweight FMEA entry

| Field | Example (unverified until tested) |
|---|---|
| Hazard | Unexpected pose motion during stale IMU |
| Initiating fault | Sensor stops updating but repeats last finite sample |
| Detection | Data timestamp/sequence/heartbeat age beyond validated freshness threshold |
| Failure response | Inhibit WALK and high-level intents, latch appropriate FAULT, execute safety-reviewed motor response |
| Evidence required | Fault-injection timeline, observed stop latency, motor targets, root tilt and contact |
| Residual risk | Unsupported robot may fall even when actuator commands stop; guarded bench required |

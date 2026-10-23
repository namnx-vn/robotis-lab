# Test design matrix — normal/error/fault/regression

Keep safety layer implementation boundaries explicit: hardware/sim adapter → deterministic motion controller → independent safety supervisor → behavior/perception → optional validated AI intent. **Not all planned states exist in v0.2**; proposals are not executed test results.

| Test ID | Layer | Input/scenario | Expected invariant / oracle | Evidence class |
|---|---|---|---|---|
| UT-01 | joint config | 10 unique joints; neutral inside min/max | reject duplicate/missing or bad range | Python unit |
| UT-02 | joint motion | commands beyond ±limits | limit at controller and separately at hardware adapter when implemented | Python unit + future bench |
| UT-03 | joint motion | different dt, rate/acceleration ramp | `Δq <= rate*dt`; no unbounded acceleration when implemented | Python unit |
| UT-04 | command validation | NaN, Inf, wrong units/type/unknown joint | reject safely; no actuator target applied | Python unit |
| UT-05 | command validation | expired deadline, sequence replay, out-of-order | reject and log reason; don't resume motion | Integration, future feature |
| UT-06 | PID | zero tilt, modest signed tilt | bounded response, anti-windup, correct sign under perturbation | Python + native, not unit only |
| UT-07 | PID | dt=0, large dt, sample gaps | fail closed or reset estimator, no derivative spike | Unit/integration |
| UT-08 | sensor | roll/pitch NaN/Inf or missing | FAULT latch / safe mode | Unit + fake-Webots |
| UT-09 | sensor | frozen IMU, inconsistent gyro | detect loss of confidence and stop autonomous motion | Future integration |
| UT-10 | sensor | position sensor missing | fault; no assumption of measured pose | Fake-Webots |
| UT-11 | physical model | no gravity/contact/false anchoring | test must fail validity; not scientific PASS | Native Webots + visual/contact |
| UT-12 | safety | excessive tilt, root too low | FAULT with reason/time; no unsafe transition | Unit + native |
| UT-13 | safety | obstacle near/moving | STOP prioritized over gait/AI; adequate stopping margin | Unit + native when gait available |
| UT-14 | safety | E_STOP during STAND/FAULT | E_STOP dominates and remains latched | Unit + future hardware rig |
| UT-15 | safety | operator reset with unsafe observation | reject reset, require local approval and safe state | Unit/integration |
| UT-16 | watchdog | missing heartbeat, delayed serial | safe state by specified measured deadline | Future mock + hardware jig |
| UT-17 | AI boundary | malformed/unauthorized high-level intent | schema reject; never raw PWM/torque | Unit/integration future |
| UT-18 | AI/network | timeout/disconnect/reconnect | safe behavior, no uncontrolled motion on reconnect | Integration future |
| UT-19 | simulation | fresh neutral stand 30+s × 5 | >=4/5 under gravity/contact metrics | Native Webots |
| UT-20 | simulation | four-direction force injection | measurable response, contact/no faults, recovery vs baseline | Native Webots pilot/full |
| UT-21 | simulation | force API offset-sign probe | gravity and world/local-force signs corroborated | Native free-body probe |
| UT-22 | simulation | >=5 gait steps | stance contact and body displacement, not animation | Native Webots future |
| UT-23 | obstacle | sensor dropout/false positive | stop safely and reject stale data | Native Webots future |
| UT-24 | hardware | servo stall/voltage droop/temp | operator-approved instrumented stop conditions | Future supervised bench |
| UT-25 | regression | same scenario on base vs PR SHA | comparable logs, first fault, no new limit bypass | CI artifact review |
| UT-26 | data pipeline | missing CSV, corrupt JSON, duplicate run_id | explicit INCONCLUSIVE/BLOCKED, not zero or PASS | Python unit |

For every added test, specify setup, stimuli, expected transition, measured fields, confidence/precision, teardown/reset, stop conditions, and a **negative oracle** that would invalidate success. Record which rows are `NOT RUN` rather than implying a complete suite.

`pytest` suite suggestions: parameterize invalid numeric payloads and each joint; use fixtures/fakes only for controller unit logic; tag native Webots/hardware as separate opt-in integration suites (never mock their results). Existing project uses unittest, so additions should coexist with its CLI/CI unless migration is explicitly approved.

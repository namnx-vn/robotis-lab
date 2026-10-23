# Fault-injection and negative-testing matrix

This is a **test design library**, not a declaration that tests exist or passed. Run software/unit/simulation checks only when tools and task authorization permit. Do not run fault injection on live hardware without explicit operator approval and a physical risk assessment. Every executed case must record source SHA, configuration, exact steps, logs, expected and observed outcomes, first fault, reset behavior and outcome status.

| ID | Layer / environment | Stimulus | Expected safety property | Minimum evidence |
|---|---|---|---|---|
| FI-01 | unit / config | target just below `min` and above `max` | clamp or reject safely, never unbounded actuator output | input/output angles and reason |
| FI-02 | unit / config | NaN, ±Inf and nonnumeric joint command | reject; no non-finite motor target | validator result and latched response |
| FI-03 | unit / timing | `dt=0`, negative, NaN or over threshold | deterministic reject/FAULT, no derivative spike | dt/log and motor targets |
| FI-04 | unit / slew | alternating max/min target every tick | per-step rate bound always respected | target deltas / dt |
| FI-05 | unit / PID | sustained saturation then reverse error | output bound and anti-windup recovery | P/I/D signals, output, response |
| FI-06 | native Webots | pitch+ disturbance vs matched baseline | meaningful excitation, correct negative feedback and settling without FAULT | requested/applied force, roll/pitch time series, contacts |
| FI-07 | native Webots | pitch- disturbance | sign symmetry and same independent gate | same as FI-06 |
| FI-08 | native Webots | roll+ disturbance | correct compensating sign and active recovery | same as FI-06 |
| FI-09 | native Webots | roll- disturbance | correct compensating sign and active recovery | same as FI-06 |
| FI-10 | sim controller | IMU NaN or Inf | FAULT latch; no new motion command | state/reason, targets, first fault |
| FI-11 | sim/controller (new test needed) | IMU freezes at finite previous sample | freshness/confidence gate inhibits unsafe motion | sample timestamps / actuation trace |
| FI-12 | sim/controller | encoder missing or position jump | motion inhibit, FAULT with original cause | sensor values / targets |
| FI-13 | sim/controller | `obstacle_m` below stop threshold | STOP/inhibit overrides STAND/WALK/AI | distance, state transition latency |
| FI-14 | sim/controller (new test needed) | obstacle sensor stale or missing | do not continue autonomous exploration normally | validity timestamps, stop |
| FI-15 | unit / supervisory | assert E_STOP during pose interpolation | highest priority, latch; no motion continuation | state transition and adapter outputs |
| FI-16 | unit / reset | reset E_STOP with `approved=false` | reset denied, no rearm | reset result / state |
| FI-17 | unit / reset | operator approval but unsafe sensor observation | reset denied until cause cleared | observations and state |
| FI-18 | unit / command (future adapter) | expired/replayed/duplicated intent or sequence | reject, motion not revived | sequence/deadline, policy decision |
| FI-19 | unit / command (future adapter) | AI command includes raw PWM/torque/joint angle | reject schema/authority boundary | input and rejection reason |
| FI-20 | unit / comms (future adapter) | host heartbeat stops | watchdog trips within **measured** configured latency | last heartbeat, trip, outputs |
| FI-21 | unit / comms (future adapter) | out-of-order packets or malformed CRC | reject frame, no stale motion replay | parser and sequence logs |
| FI-22 | unit / FSM (future mode) | jump BOOT→WALK or FAULT→EXPLORE | reject forbidden transition; fault remains latched | state/guard trace |
| FI-23 | unit / resilience | AI/API timeout during valid STAND/WALK | deterministic motion safety independent of cloud | timestamps/state and outputs |
| FI-24 | native Webots | contact lost/foot slips under modeled load | distinguish fall/contact failure; do not certify gait | actual foot/contact/COM proxy and tilt |
| FI-25 | hardware *approval-only* | E-STOP while servos energized on secured jig | rail/safe-inhibit response meets measured design envelope | voltage/current and operator signoff |
| FI-26 | hardware *approval-only* | USB disconnect, MCU reset/brownout, servo stall | watchdog and load protections act within validated margins | electrical/thermal/stop measurements |

## Layered execution sequence

1. **Static:** config validation, schema, call graph, dangerous bypass search, test plan.
2. **Offline unit/fake Webots:** command bounds, latch/reset, deterministic timing and invalid sensor/data conditions. Mark physical dynamics `NOT RUN`.
3. **Native Webots:** force calibration and valid contact dynamics, matched four-direction baseline/PID runs, state/tilt/motor evidence. A one-pair pilot is not a scientific balance acceptance.
4. **Hardware:** *no execution under this skill without explicit operator approval*. Use a protected single-servo jig, current-limited supply and independent power stop after power/torque analysis.

## Pass/fail conventions

- Mark each case `PASS`, `FAIL`, `INCONCLUSIVE` or `NOT RUN`, never infer from analogous tests.
- `PASS` is scenario-specific. An expected injected FAULT can be a **PASS of the safety test**, even while the robot failed to remain standing; report both clearly.
- A valid test with observed violated invariant is `FAIL`, not `INCONCLUSIVE`.
- No actual force delivered, wrong signed axis, too few pairs, missing foot contact or missing logs => `INCONCLUSIVE`.
- No execution => `NOT RUN` even if code inspection suggests it should pass.
- Maintain first-fault reason and time, distinguish fail-closed response from actual preservation of balance.

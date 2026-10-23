# Phase gates and verdict discipline

**Read active repo protocols first**; these criteria are a human-readable orientation, not a replacement for current executable guards. Declare every threshold before the experiment. Allow null/missing fields but mark dependent decision `INCONCLUSIVE`.

| Gate | Minimum quantitative evidence | Classify carefully |
|---|---|---|
| P1 dynamics | Native Webots parser, robot physics + gravity/collision contact, joints/sensors, repeatable log | Python source checks alone are not native physics |
| P2 static standing | >=5 reset trials; >=4 valid runs of >=30s each, predeclared tilt/drift/height; no relevant faults; contact validity inspected | Static gate can be PASS even though contact/active recovery are **not independently verified** |
| P2.2 active balance | 4 cases pitch± / roll±; >=3 independent comparable baseline/PID pairs each (5 preferred); measured injection/excitation >= current script minimum; valid settling, no faults; >=10% mean peak improvement in EACH direction; contact checks | Pilot with 1 pair **never PASS**; absent excitation -> INCONCLUSIVE; FAULT valid -> FAIL; no selective filtering |
| P3 walking | Gate P2.2 accepted first; >=5 consecutive physically simulated steps; actual stance-swing contacts and displacement, roll/pitch/fall logs | Animated joint sequence without COM/root motion or contact -> INCONCLUSIVE |
| P4 obstacle | Stopping margin + timing before defined obstacle, invalid/timeout sensor handling and STOP > WALK/AI | Missing sensor and collision fault must never yield false pass |
| P5–P6 hardware | Approved jig/protocol; measured servo output/current/voltage/temperature/tether/contact/E-STOP, sim-to-real uncertainties | Webots evidence cannot certify hardware rail or E-STOP |
| P7 bounded autonomy | High-level intent schema/permission, timeouts, safe fallback, no LLM raw PWM | Mocked schema test only proves the validator logic |

## P2.2 reported acceptance details (verify live version)

- Excitation threshold: intended-axis peak change `>=0.008 rad`; initial target-axis abs tilt `<0.08 rad`.
- Fault/height/drift must remain within actual experiment predicates; do not change limits to pass.
- Recovery requires settling inside `0.025 rad` for `>=0.8s`, within `5s` after pulse onset, according to existing analyzer.
- Same world/config/source build, known native Webots version, equal force schedule and timestep, unique run IDs, actual force-API calls and post-pulse samples.
- A valid scientific aggregate needs all four directions, >=3 comparable pairs/direction, and PID mean peak <=90% of baseline mean in each.
- Contact observation and lack of false anchoring/foot slip are still required; root GPS is not foot-contact instrumentation.

## Classification decision path

1. Was the test executed? No -> `NOT RUN`, or `BLOCKED` if a dependency/permission prevents running.
2. Was provenance/data quality sufficient? No -> `INCONCLUSIVE` for observed artifacts, preserving reasons. Do not discard a failure because its data are inconvenient.
3. Did a validated safety or acceptance limit fail? Yes -> `FAIL` and first fault details.
4. Were all declared success predicates proven at required sample/trial count? Yes -> `PASS` **for exactly this gate**.
5. Otherwise -> `INCONCLUSIVE` (e.g. exposure too small, missing contact) or `FAIL` for confirmed unachieved criterion with adequate measurements.

Always report execution status (`completed`, `failed`, `not_run`, etc.), data quality, experiment result, and release decision separately. A successful CI workflow merely says its *programmed CI checks* completed.

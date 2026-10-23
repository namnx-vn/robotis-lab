# RL-H25 phase gates and evidence policy

This document defines how the skill interprets gates, not proof that any particular gate has been passed. Recheck the current repo before every consequential decision.

| Phase | Evidence required | Invalid shortcut |
|---|---|---|
| P0 Foundation | Requirements, scope, actual inventory, risks and baseline design | An unchecked parts list |
| P1 Mechanics | Parser-valid physically articulated 10-DOF humanoid, stable coordinate frames, realistic mass/inertia, contacts/collisions, signed axes and joint limits | An attractive rendered model |
| P2 Static standing | Native Webots fresh restarts: documented stand time, count, fall/fault metrics, tilt and foot contact | `STAND` state, a screenshot, offline mocks or 8 s smoke |
| P2 Controlled balance | Paired baseline vs active-balance perturbations, reproducible disturbance input, contact, tilt and settling evidence for pitch/roll ± | No disturbance actually applied; pass based on one direction; green CI without recovery evidence |
| P3 Walking | P2 balance gate passed; grounded support transfer, actual foot displacement/contact, >=5 valid consecutive steps in an accepted protocol, fault/fall data | Moving leg animation or teleportation |
| P4 Obstacle | Measured STOP priority, no collision, sensor-failure handling and safe fallback | Visual obstacle avoidance only |
| P5–P6 Hardware | Explicit operator approval; component inventory, torque/current/power gate; guarded one-joint bench, E-STOP, independent servo power, supported trials | Simulation-only result or Arduino 5 V/USB powering servos |
| P7 Autonomy | Validated intent schema, high-level bounded actions, independent safety supervisor, timeout/invalid command tests | LLM directly controlling joints or PWM |

## Current P2 acceptance (source: `docs/experiments/balance-matrix.md`, checked 2026-10-22)

- Reproducible controlled forces in **pitch+**, **pitch-**, **roll+**, **roll-**; each direction is its own scenario.
- Matched `baseline` and `balance` trials using identical force schedule/world/model/timestep.
- >=3 valid paired trials **per condition**, measurable excitation, **no FAULT**, validated settling under the report criteria and >=10% reduction in average peak tilt for active PID vs baseline **for each condition**, not just aggregate.
- Check real foot contact, verified command signs, plausible force magnitude, reset validity, first-fault reason and sim-to-real limitations separately.
- A one-pair pilot is deliberately **not** an acceptance PASS. Stop to inspect on `FAULT`, `REVIEW_REQUIRED` or `INCONCLUSIVE`; do not increase force automatically.

## Decision matrix

- `PASS`: fully executed matching test with sufficient evidence, thresholds met and safety preserved.
- `FAIL`: executed valid test with an observed adverse or unmet criterion.
- `INCONCLUSIVE`: tests ran, but controls/excitation/data/coverage do not permit an answer.
- `NOT RUN`: environment did not run the test; label exact absent layer.
- `UNVERIFIED`: claim/evidence cannot be independently checked.
- `BLOCKED`: prerequisite gate or safety approval is missing.

When existing documents disagree, prioritize current measured artifacts and stricter safety constraints; report the inconsistency rather than silently deciding by convenience.

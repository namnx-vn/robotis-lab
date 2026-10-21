# RL-H25 v0.2 verification report — 2026-10-20

Environment: Python 3.13.5 Linux container. Webots binary unavailable here.

| Check | Evidence | Result |
|---|---|---|
| Python compilation | `python -m compileall -q .` | PASS |
| Generated RLH25.proto remains consistent | `python tools/generate_model.py`, `python tools/verify_project.py` | PASS |
| Original 10-motor/physics/sensor model consistency | static structure checker | PASS |
| Pure PID normal/error/saturation/rate/timegap/fault tests | tests/test_balance.py | PASS |
| Standing baseline strict gate, simulated data, missing/invalid data | tests/test_baseline_report.py | PASS |
| Webots controller end-to-end fake API, both modes + faults | tests/test_controller_fake.py | PASS |
| Total unit/integration Python tests | `42` tests | **42/42 PASS** |
| Native Webots R2025a smoke | `python tools/smoke_webots.py` | **SKIP exit 2 — binary absent** |
| Real 5×30 s baseline stability | no user macOS logs supplied | **NOT RUN / UNVERIFIED** |
| Real 5×30 s PID stability | no Webots here and not run on user Mac | **NOT RUN / UNVERIFIED** |
| Physical hardware | no hardware actions | OUT OF SCOPE |

## First baseline from previous Sprint01

User screenshot of Webots R2025a successfully loading and rendering RL-H25, with prior late `FAULT excessive_tilt` at t≈332.46 s / pitch≈0.522 rad. Screenshots do **not** establish repeatability. Logs on user's computer unavailable; this implementation deliberately does not invent measurements.

## Next acceptance gate

Collect 5 independent R2025a baseline CSV/JSON runs with `RL_H25_MODE=baseline` and no injected faults; record version/build; run `tools/baseline_report.py` on those specific files. Only after reviewing baseline, try 8 s `RL_H25_MODE=balance`; calibrate sign if necessary, then collect 5 balance trials and compare. Both require visual confirmation of contact and no slip.

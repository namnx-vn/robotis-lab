# Sprint 01 verification report — 2026-10-19

Environment: Python 3.13.5, Linux container, Webots executable **not installed**.

| Check | Result | Evidence |
|---|---|---|
| Python compileall | PASS | `python -m compileall -q .` |
| Generated PROTO consistency | PASS | `python tools/verify_project.py` |
| 10 HingeJoint, 10 RotationalMotor, 10 PositionSensor | PASS (text structure) | offline validator |
| Physics mass nodes, bounding boxes, sensors, contact config | PASS (text structure) | offline validator |
| Pure motion and safety tests | PASS | 15 unittest cases |
| Fake Webots controller integration tests | PASS | 4 unittest cases: normal/obstacle/bad-IMU/E-STOP |
| CSV analyzer synthetic regression | PASS | 1 unittest case |
| Total unit/integration tests | **20 PASS / 0 FAIL** | `python -m unittest discover -s tests -v` |
| Native Webots headless smoke | **NOT RUN** | Webots binary missing; `tools/smoke_webots.py` exit 2 |
| Native Webots VRML/PROTO parser | **NOT VERIFIED** | Requires Webots runtime |
| Real gravity/contact/height stability | **NOT VERIFIED** | Requires independent simulated physics trials |
| Physical Arduino, servo, hardware E-STOP | **NOT IN SCOPE** | Planned later |

**Interpretation:** The code is runnable under mocked Webots interfaces and structurally
consistent; simulation compatibility and dynamic standing remain unproven until the
user runs the actual Webots binary. An all-zero target and upright initial geometry
is not evidence of balanced locomotion.

To reproduce:

```bash
python tools/generate_model.py
python tools/verify_project.py
python -m unittest discover -s tests -v
python tools/smoke_webots.py
```

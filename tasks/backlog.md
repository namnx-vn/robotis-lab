# Sprint 01 task ledger

- [x] Create Webots world and generated `RLH25.proto` with 10 DOF.
- [x] Add approximate per-link Physics, bounding boxes, floor contact friction.
- [x] Add IMU, Gyro, Accelerometer, GPS, Camera, laser DistanceSensor.
- [x] Implement neutral target hold, joint rate limits, FAULT/STOP/E_STOP simulation.
- [x] Add offline tests, fake simulator loop tests and telemetry analyzer.
- [ ] Open and parse the world in a genuine Webots install.
- [ ] Inspect actual joint axes + contacts with the Webots optional rendering tools.
- [ ] Run full 8-second live smoke + save CSV, screenshot and simulator version.
- [ ] Measure 5 × 30-second stand trials (P2; separate sprint/gate).
- [ ] Inventory actual physical parts; no purchases before torque/power estimates.

Next action: user runs `python tools/smoke_webots.py` on a host with Webots installed,
reports warnings/logs. Modify world/model minimally based on actual parser or physics result.

## Sprint 02 v0.2 Standing & Balance status

- [x] Build strict baseline analysis (CSV + metadata + GPS planar drift; 5 independent trials gate)
- [x] Add bounded IMU angle PID roll/pitch with slew/max/min limits
- [x] Simulated FAULT, STOP, E_STOP and integration regressions
- [x] Run Python offline test suite
- [ ] Operator: run 5×32s baseline in actual Webots R2025a and submit logs
- [ ] Operator: validate axis-sign mapping, then run short PID and 5×32s balance trials
- [ ] Only if both: review measured torque/contact/instability and tune

## Sprint 02.1 — Current

- [x] Add opt-in bounded Supervisor force pulse without changing 10-DOF geometry.
- [x] Paired fresh-process baseline/balance experiment + CSV/JSON evidence.
- [x] Make no-perturbation INCONCLUSIVE; assert FAULT/recovery criteria.
- [x] Unit/fake-Webots regression tests.
- [ ] On owner Mac: 1 pilot pair (pitch), inspect measured excitation and fault.
- [ ] On owner Mac: 5 matched pitch pairs; separately roll and reverse directions.
- [ ] Use telemetry to validate/retune sign/gains; reproduce negative cases.
- [ ] Confirm two-foot contact and no false static anchoring in GUI.

**Gate:** P3 weight shift/walking blocked until controlled balance verified.

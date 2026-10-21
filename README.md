# Robotis Lab — RL-H25
Robotics research project building a ~25 cm, 10 leg-DOF biped humanoid. **Simulation first; evidence before hardware; independent safety supervision.**

## Canonical repository
This repository is the sole source-code target for future Robotis Lab changes. Contributions use a focused branch + reviewed pull request against `master`; no blind overwrites of the default branch.

> **Import status:** The GitHub repository was initialized with a short README only. As of this PR, earlier Sprint 01 / v0.2 / v0.2.1 source artifacts are **not yet committed here**. See [docs/SOURCE_IMPORT.md](docs/SOURCE_IMPORT.md) to migrate the operator's current local `robotis-lab-v021` source **without inventing missing files**.

## Target system
- Webots R2025a + Python simulator controller; Y-up (`NUE`) world.
- RL-H25: head/body/passive arms, 10 actuated leg joints, collision geometry, masses, contact and IMU/GPS/distance/camera.
- Motion control: radians, joint hard limits and slew limits, optional IMU pitch/roll PID.
- Safety: STOP / FAULT / E_STOP and watchdog; never route high-level LLM outputs to PWM.
- Physical target later: PC host; Arduino Uno + PCA9685 if hardware sizing and operator approval pass.
- Initial physical budget target: approximately 3,000,000 VND, not a verified build cost.

## Experimental evidence (not a release claim)
The operator reported native macOS Webots R2025a baseline standing gate **5/5** undisturbed trials (31.92 s each, 286 samples, pitch max 0.0002 rad, no planar drift). These logs are not yet versioned or independently rechecked. A later manual balance run entered `FAULT excessive_tilt` at ~28.91 s. **Active balance recovery and walking are not demonstrated.**

**Current milestone:** Sprint 02.1 — repeatable bounded physical-force perturbations in Webots, paired baseline versus IMU PID, pitch and roll. P3 gait must wait for a reliable disturbance gate.

## Running after source import
```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --axis pitch --force 0.10 --pulse 0.112 --duration 14
```
These scripts **do not exist on `master` yet**; import the maintained source and review its tests first. Native Webots physics tests must run locally on a machine with Webots R2025a.

## Documents
- [AGENTS.md](AGENTS.md) — engineering and safety contribution contract.
- [docs/SOURCE_IMPORT.md](docs/SOURCE_IMPORT.md) — one-time source migration from local v0.2.1.
- [docs/ROADMAP.md](docs/ROADMAP.md) — milestone and acceptance gates.

Private video, raw camera images, `.env` secrets and experimental logs must not be committed by default.

# Robotis Lab — research bootstrap documents

Tài liệu khởi tạo RL-H25: robot hình người cao ~25 cm, hai chân 10 DOF, Arduino Uno + PC host + Webots.

- `CHATGPT_PROJECT_INSTRUCTIONS.md` — **bản ngắn** dán trực tiếp vào ChatGPT Project Instructions (PROJECT_ID `robotis-lab`).
- `PROJECT_INSTRUCTIONS.md` — **đặc tả chi tiết**: kiến trúc, hardware/firmware, AI boundaries, an toàn, quy tắc AI coding agent.
- `IMPLEMENTATION_PLAN.md` — **roadmap 24 tuần**: backlog từng tuần, nghiệm thu, ngân sách sơ bộ, rủi ro và nhiệm vụ phiên đầu tiên.

**Trạng thái:** đây là bộ kế hoạch/instructions, **chưa phải source code Webots `.wbt`, firmware Arduino hoặc robot vật lý đã thử thành công**. Thông số khung, servo, nguồn và giá cần kiểm chứng khi triển khai.

**Bước kế tiếp:** P0 → dự án Webots đầu tiên chạy được với robot RL-H25.


# Robotis Lab RL-H25 v0.2.1 — Standing Baseline, IMU PID & Disturbance Validation

**Scope:** Webots **R2025a** humanoid, 25 cm, 10 DOF leg joints, Y-up `NUE`, physics, IMU, GPS, laser and camera. Upgraded *in place* from the Sprint 01 `RLH25.proto` + `.wbt`. **No walking, no proof of balanced locomotion, and no Arduino/hardware control.**

**Evidence status (2026-10-21):** The user ran Webots R2025a on macOS. Five **undisturbed v0.2 baseline** runs passed the automated 30s gate (5/5; owner-provided terminal output, not original CSV files). A later manually disturbed balance run showed `FAULT excessive_tilt` at ~28.91s. This upgraded package preserves that code and introduces reproducible applied-force tests. Native v0.2.1 physics and gain signs are NOT verified here (Webots is unavailable in the authoring container). No historical success/failure logs were invented.

## Deliverables

- Existing mechanical model and physics: `simulation/webots/worlds/rl_h25_lab.wbt`, `simulation/webots/protos/RLH25.proto`, unchanged from Sprint 01 (except configuration/metadata, no unjustified axis swaps).
- **`baseline` mode (default):** same idealized neutral angle hold, with expanded telemetry. Use FIRST, repeat fresh Webots processes/trials.
- **`balance` mode (opt-in):** closed-loop IMU orientation angle PID on roll + pitch, derivative-on-measurement, low-pass derivative, anti-windup, bounded outputs. Weighted joint targets (both ankles plus small opposing hips); knees neutral. Output is a *position offset in radians*, not a torque controller. **Gain signs and effectiveness remain experimental.**
- Joint min/max and target slew-rate remain enforced after PID mixing; latching `FAULT`/`STOP` freezes targets, `E_STOP` disables available motor torque **in simulation only**. No automatic FAULT reset.
- Baseline acceptance checks: duration, sample continuity, max tilt, min root height, planar GPS drift, state transitions, metadata/run independence. CSV cannot prove foot contact; visually confirm no sliding.
- Test suite includes nominal, saturation, timegap, sensor fault, obstacle and E-STOP (mocked Webots).

## Requirements

- macOS with Webots R2025a (user has it), Python 3.10+; standard library only.
- From extracted directory, run:

```bash
python3 tools/generate_model.py
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
```

## **Stage A — collect static baseline FIRST (no PID)**

**Close other Webots windows** to avoid the known port 1234/1235 conflict on macOS. In a new terminal:

```bash
cd /path/to/robotis-lab-v02
RL_H25_MODE=baseline RL_H25_DURATION_S=32 webots simulation/webots/worlds/rl_h25_lab.wbt
```

Start ▶; when the controller exits, inspect `experiments/logs/` for matching CSV and JSON. **Re-launch Webots (or reset simulation, ensuring a fresh unique run ID) for each trial**. Run **five independent 32-second baseline trials**, do not select an old fault run as a success. Prefer automation:

```bash
# close Webots GUI first; launches five independent new instances sequentially:
python3 tools/run_standing_trials.py --mode baseline --trials 5 --duration 32
```

Webots on macOS sometimes launches a GUI via a wrapper; if subprocess auto-trials cannot control it, run GUI manually and collect five `baseline-*.csv` & `.json` from those runs. For a single trial/diagnosis:

```bash
python3 tools/baseline_report.py --min-trials 1 --min-passing 1 experiments/logs/<your-run>.csv
```

For the full gate, provide exactly five independent runs, e.g.:

```bash
python3 tools/baseline_report.py \
  --json-output experiments/standing_baseline_report.json \
  experiments/logs/baseline-*.csv
```

**Do NOT wildcard unrelated logs.** Use a dedicated batch's exact five CSV paths. Acceptance default (conservative initial **ASSUMPTION**, tune from real measurements): >=4/5 independent PASS; each >=30.0 s sampled STAND, no state change; |roll| & |pitch| <0.20 rad; min root Y >=0.10 m; peak planar GPS drift from starting point <0.030 m; telemetry gaps <=0.45 s; run IDs distinct; valid metadata, no injected faults. Further visual inspection: both foot contacts, no sliding, no apparent floor penetration. This is a **static standing baseline**, not active balancing certification.

**Sprint 01 legacy logs:** still readable via `python3 tools/analyze_runs.py old.csv`, but cannot satisfy the strict new baseline gate (missing X/Z and sometimes metadata fields). For v0.2, collect new telemetry.

## **Stage B — enable balance only after reviewing baseline**

PID **is opt-in**. Start with a short trial (~8 s) and physically watch Webots as the robot might destabilize due to unknown real-sim gains/signs:

```bash
RL_H25_MODE=balance RL_H25_DURATION_S=8 webots simulation/webots/worlds/rl_h25_lab.wbt
```

If initial closed-loop response is sane, run five independent full 32-second trials:

```bash
python3 tools/run_standing_trials.py --mode balance --trials 5 --duration 32
python3 tools/baseline_report.py experiments/logs/balance-<batch-run-1>.csv \
  experiments/logs/balance-<batch-run-2>.csv \
  experiments/logs/balance-<batch-run-3>.csv \
  experiments/logs/balance-<batch-run-4>.csv \
  experiments/logs/balance-<batch-run-5>.csv
```

**Replace `<batch-run-N>` with actual filenames**. Do not claim v0.2 better until comparing like-for-like failure rate, pitch/roll maxima and drift under the same initial conditions. Check `pitch_correction_rad`, `roll_correction_rad` and motor targets in CSV. PID error sign / mixing are initially **UNVERIFIED** in the real simulator. Only edit values in `configs/robot.json` and re-run all tests; avoid changing `tilt_fault_rad` merely to hide failures.

## Emergency / fault checks (simulator only)

```bash
RL_H25_MODE=balance RL_H25_FORCE_FAULT=nan_imu RL_H25_DURATION_S=3 webots simulation/webots/worlds/rl_h25_lab.wbt
# also: RL_H25_FORCE_FAULT=obstacle  or =estop
```

Expected `FAULT invalid_sensor_value`, `STOP obstacle_nearby`, or `E_STOP operator_estop` respectively. These deliberately fail standing gates. `E_STOP` simulation changes available torque to 0; the robot can subsequently topple! Only a **separate physical E-STOP cutting servo rail** is acceptable for actual hardware, not this Python path.

## Structure

```text
configs/robot.json                         joint limits, safety, PID gains/mixing
simulation/webots/worlds/rl_h25_lab.wbt   R2025a lab world, gravity, friction
simulation/webots/protos/RLH25.proto      existing 10-DOF humanoid
simulation/webots/controllers/rl_h25_controller/
  motion.py                               deterministic bounded IMU PID, safety
  rl_h25_controller.py                    Webots sensors/devices + CSV/JSON logs
tools/generate_model.py                    regenerate PROTO (when geometry changes)
tools/verify_project.py                   static integrity checks
tools/smoke_webots.py                      8s native Webots smoke, if installed
tools/run_standing_trials.py              fresh-process 5-trial runner
 tools/baseline_report.py                 strict CSV+metadata standing gate
 tools/analyze_runs.py                    Sprint01 compatible heuristic analyzer
tests/test_balance.py                     saturation, signs, faults, rate limits
tests/test_baseline_report.py             synthetic report correctness tests
tests/test_controller_fake.py             fake Webots API integration
 docs/standing_baseline.md               protocol, interpretation & acceptance
 docs/balance_design.md                  control architecture and sign risks
 docs/TEST_REPORT_V02.md                 executed vs not-executed verification
```

## Known limitations / gates

1. Initial controller holds idealized joint targets via Webots motors; servo torque/inertia and Coulomb friction are **assumptions**, not measured real hardware parameters.
2. This implementation is **orientation feedback**, not whole-body zero-moment-point, CoP, foot-contact feedback, or fall recovery. Can be worse than baseline if sign or gain is wrong.
3. Camera and front distance readings are not fed to PID, by design. Cloud AI cannot issue motor targets.
4. Baseline owner-reported 5/5 automated gate passed in native Webots; raw CSV was not shared with this environment. Controlled disturbance PID response is **not yet verified**. A previous screenshot shows late FAULT under an unstandardized disturbance.
5. Next action: run Sprint 02.1 paired force pulse tests on macOS, inspect telemetry before tuning; do **not** buy servos or start gait before gates pass.

Reference: Webots [InertialUnit](https://cyberbotics.com/doc/reference/inertialunit), [Motor](https://cyberbotics.com/doc/reference/motor), [HingeJoint](https://cyberbotics.com/doc/reference/hingejoint).

---

## Sprint 02.1 (v0.2.1) — Reproducible disturbance comparison

**What changed from v0.2:** Added explicit opt-in `Supervisor.getSelf().addForceWithOffset()` pulse injector, timed high-rate telemetry for experiment runs, paired baseline-vs-balance fresh-Webots runner, strict quantitative evidence analyzer, failure/inconclusive handling and additional tests. The 10-DOF robot geometry, PID gains, motor rate/angle caps, tilt hard cutoff, world and hardware boundaries are unchanged.

**Why:** On the owner's actual macOS R2025a, static baseline achieved 5/5 trials; a later unstandardized `balance` run fell with `FAULT excessive_tilt`. This sprint does **not** assume PID already works or proceed to gait.

For macOS R2025a, from this directory (**close Webots first**):

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --axis pitch --force 0.10 --pulse 0.112 --duration 14
```

A one-pair pilot returns nonzero by design (`INCONCLUSIVE` until ≥3 independent matched pairs); it still writes real CSV/JSON. Read the printed per-trial verdicts. After checking the pulse applied and no massive tilt, run five pairs:

```bash
python3 tools/run_disturbance_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 --axis pitch --force 0.10 --pulse 0.112 --duration 14
```

Use `--graphics` to see the motion, but do **not** manually drag while an automated experiment is running. CSV+JSON live under `experiments/logs` (gitignored). If the result is `INCONCLUSIVE`, don't claim improved balance; consult `docs/CONTROLLED_DISTURBANCE.md` for diagnosis and bounded parameter adjustment. Repeat for roll only after verifying pitch safely. Your historical experiments remain in the separate old `robotis-lab-v02` directory.

Key files:

```text
simulation/webots/controllers/rl_h25_controller/disturbance.py  bounded impulse
simulation/webots/controllers/rl_h25_controller/rl_h25_controller.py  opt-in Supervisor and log
 tools/run_disturbance_trials.py                            paired native runs
 tools/disturbance_report.py                               evidence gate
 tests/test_disturbance.py                                 fake-API + fault/evidence tests
 docs/CONTROLLED_DISTURBANCE.md                           lab protocol
 docs/TEST_REPORT_SPRINT021.md                            actual test status
```

API reference: https://github.com/cyberbotics/webots/blob/master/docs/reference/supervisor.md (Node.addForceWithOffset, Supervisor.getSelf). **This branch remains simulation only.**


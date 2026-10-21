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

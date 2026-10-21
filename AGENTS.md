# Robotis Lab — Agent engineering contract

**Project:** RL-H25, 25 cm biped research robot with 10 leg DOF. Canonical code repository: `namnx-vn/robotis-lab`.

## Start here
1. Read `README.md`, `docs/ROADMAP.md`, active sprint documentation, `configs/robot.json` and tests (when present).
2. Inspect the Git branch, actual files and ongoing PRs before editing. Reuse existing code; do not replace the architecture wholesale.
3. For every task report Goal, changed files, commands, executed tests, outstanding risks, acceptance gate and next step. Distinguish mock tests from native Webots physics tests.
4. Work on short-lived feature/fix branches, with reviewable commits and a PR to `master`. Do not auto-merge a safety-critical change.

## Architecture & safety
- Webots R2025a Python controller is the simulation target. Use radians in host/simulation; degree/PWM conversion belongs only in the future hardware adapter.
- Safety supervisor is independent of cloud APIs; STOP/FAULT/E_STOP, joint/rate limits and watchdog must not be bypassed.
- Cloud/local LLMs can suggest **bounded high-level intents** only, never direct joint angles, motor currents, PWM or unsafe autonomous motion.
- Physical electronics require independent appropriately sized servo power, common ground with MCU, fuse/switch and a physical E-STOP. Arduino Uno 5V/USB must not supply multiple servos.
- Any hardware power/firmware/self-directed movement with material risk needs operator approval. No buying 10 servos before inventory, worst-case torque/continuous-duty margin, peak current and one-joint bench testing.
- Do not commit credentials, private camera data, secrets, actual physical telemetry with identifying data or large raw recordings.

## Current milestone, October 2026
- P1: Webots 10-DOF geometry and basic controller, witnessed in operator screenshots.
- P2: v0.2 baseline 5/5 undisturbed native Webots runs from operator-provided terminal output; **not proof of active balance**.
- During a manual disturbed v0.2 run, `excessive_tilt` FAULT occurred (~28.91 s), with initial nonzero roll in the screenshot.
- P2.1 goal: controlled small disturbance at specified time/axis/force, compare paired baseline and balance trials, explicitly reject absent excitation/inconclusive telemetry. Do not advance to gait until repeatable pitch/roll recovery is evidenced.

## Verification after source import
```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q simulation/webots/controllers tools tests
```
Native Webots R2025a 3D parser/foot contact/dynamics **cannot** be certified by Python unit tests alone.

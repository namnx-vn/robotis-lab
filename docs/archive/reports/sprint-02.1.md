# Test Report — RL-H25 Sprint 02.1

## Executed in authoring container

- `python3 -m compileall -q tools tests simulation/webots/controllers`: PASS.
- `python3 tools/verify_project.py`: PASS static model/config structure inherited from v0.2.
- `python3 -m unittest discover -s tests -q`: PASS (55 tests, including v0.2 regression tests).
- Synthetic/stand-in Supervisor tests covered: opt-in, force bounds, pitch/roll axes, discrete pulse, cancellation on unsafe state, artifact recording, reject zero perturbation, reject corrupted CSV/metadata, rejects non-upright initialization, compares 3 distinct synthetic paired runs.

## NOT executed here

- Native Webots R2025a application is not installed in the authoring container. **No validated physics response, force application or PID recovery from genuine Webots.**
- User's macOS CSV/JSON from past fault run was not uploaded: cannot derive root cause from that historical fault.
- Foot contacts/CoP, analog servo behavior, Arduino and real robot are not tested.

## Owner observations motivating this sprint (from conversation)

- Baseline, no pulse: 5/5 automated standing gate PASS, ~31.92 simulated seconds, zero drift, min root height 0.183m.
- On attempted manually perturbed balance run: log printed initial roll ~-0.243rad, later `FAULT excessive_tilt`, pitch ~-0.519rad at 28.91s. Timing and magnitude of mouse interaction unknown.

## Completion status

**Sprint 02.1 engineering source + offline tests: complete.** Native Webots disturbance validation: **pending real user run**. Walking phase P3 remains blocked pending balance evidence.

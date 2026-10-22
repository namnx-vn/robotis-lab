"""Native Webots R2025a force ABI regression on an unanchored free solid.

Independent of RL-H25, PID, foot contact and balancing. Fails closed if actual
angular velocity direction, offset, frame, or gravity disagrees with expectation.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rl_h25_controller"))
from disturbance import ForceWithOffsetAPI


def main() -> None:
    from controller import Supervisor

    robot = Supervisor()
    step_ms = int(round(robot.getBasicTimeStep()))
    node = robot.getFromDef("FREE_BLOCK")
    if node is None or node.getField("physics").getSFNode() is None:
        raise RuntimeError("FREE_BLOCK has no Physics: probe invalid")
    force_api = ForceWithOffsetAPI(node)
    trans = node.getField("translation")
    rotation = node.getField("rotation")
    initial_position = [0.0, 1.0, 0.0]
    force_n, pulse_steps, offset_m = 0.8, 8, 0.04

    def reset(axis_angle: list[float]) -> None:
        trans.setSFVec3f(initial_position)
        rotation.setSFRotation(axis_angle)
        node.resetPhysics()
        if robot.step(step_ms) == -1:
            raise RuntimeError("Webots ended before calibration")

    reset([0, 1, 0, 0])
    y_before = node.getPosition()[1]
    for _ in range(3):
        if robot.step(step_ms) == -1:
            raise RuntimeError("Webots ended in gravity probe")
    y_after = node.getPosition()[1]
    gravity_observed = y_after < y_before - 0.002

    def trial(vector: list[float], offset: float, pose: list[float]) -> list[float]:
        reset(pose)
        for _ in range(pulse_steps):
            force_api.add(vector, [0.0, offset, 0.0], False)
            if robot.step(step_ms) == -1:
                raise RuntimeError("Webots ended during force probe")
        return list(node.getVelocity()[3:6])

    identity = [0, 1, 0, 0]
    cases = [
        ("pitch_plus", [0, 0, force_n], offset_m, identity, 0, +1),
        ("pitch_minus", [0, 0, -force_n], offset_m, identity, 0, -1),
        ("roll_plus", [force_n, 0, 0], offset_m, identity, 2, -1),
        ("roll_minus", [-force_n, 0, 0], offset_m, identity, 2, +1),
        ("pitch_zero_offset", [0, 0, force_n], 0.0, identity, None, 0),
        ("roll_zero_offset", [force_n, 0, 0], 0.0, identity, None, 0),
        # A rotated local body must not rotate a world-frame +Z force into +X.
        ("yaw_rotated_world_force", [0, 0, force_n], offset_m,
         [0, 1, 0, math.pi / 2], 0, +1),
        # Rotating local +Y by +90 degrees around Z gives world -X,
        # whose cross product with world +Z yields world +Y torque.
        ("rotated_local_offset", [0, 0, force_n], offset_m,
         [0, 0, 1, math.pi / 2], 1, +1),
    ]
    results = []
    ok = gravity_observed
    for name, vector, offset, pose, axis, sign in cases:
        omega = trial(vector, offset, pose)
        finite = all(math.isfinite(v) for v in omega)
        if axis is None:
            passed = finite and max(abs(v) for v in omega) < 0.08
        else:
            primary = sign * omega[axis]
            cross = max(abs(omega[i]) for i in range(3) if i != axis)
            passed = finite and primary > 0.10 and cross < max(0.08, 0.3 * primary)
        ok = ok and passed
        results.append({"case": name, "omega_xyz": omega, "pass": passed})
    summary = {"pass": bool(ok), "force_api_mode": force_api.mode,
               "gravity_observed": gravity_observed,
               "gravity_displacement_m": y_after - y_before,
               "pulse_steps": pulse_steps, "results": results}

    # Webots simulationQuit may terminate stdout forwarding before the log is
    # flushed. Save the exact result atomically to the runner-selected file.
    output_path = os.environ.get("RL_H25_FORCE_PROBE_OUT")
    if output_path:
        Path(output_path).write_text(json.dumps(summary, sort_keys=True) + "\n", encoding="utf-8")
    print("FORCE_API_PROBE_RESULT=" + json.dumps(summary, sort_keys=True), flush=True)
    # Exit native Webots cleanly instead of leaving a headless batch process running.
    robot.simulationQuit(0 if ok else 1)
    if not ok:
        raise RuntimeError("Native force-with-offset probe failed: do not tune PID")


if __name__ == "__main__":
    main()

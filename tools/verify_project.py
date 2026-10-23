#!/usr/bin/env python3
"""Offline project consistency checks; cannot replace Webots parsing/physics tests."""
from pathlib import Path
import importlib.util
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "configs/robot.json").read_text())
world = (ROOT / "simulation/webots/worlds/rl_h25_lab.wbt").read_text()
proto = (ROOT / "simulation/webots/protos/RLH25.proto").read_text()
controller = (ROOT / "simulation/webots/controllers/rl_h25_controller/rl_h25_controller.py").read_text()

spec = importlib.util.spec_from_file_location("generate_model", ROOT / "tools/generate_model.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert proto == module.generate(), "generated PROTO differs; run python tools/generate_model.py"

assert config["units"] == "radian"
assert len(config["joints"]) == 10
assert world.startswith("#VRML_SIM R2025a utf8")
assert proto.startswith("#VRML_SIM R2025a utf8")
assert 'coordinateSystem "NUE"' in world
assert 'EXTERNPROTO "../protos/RLH25.proto"' in world
assert re.search(r"(?m)^\s*gravity\s+9\.81\s*$", world), "world gravity must be explicitly 9.81"
assert re.search(r"(?m)^\s*coulombFriction\s*\[\s*1\.1\s*\]", world), "world friction must be 1.1"
assert proto.count('contactMaterial "foot_grip"') == 2
assert "physics Physics { density -1 mass 0.14 }" in proto
assert proto.count("HingeJoint {") == 10
assert proto.count("RotationalMotor {") == 10
assert proto.count("PositionSensor {") == 10
assert proto.count("physics Physics {") == 11
assert "InertialUnit {" in proto and "DistanceSensor {" in proto
assert "Camera {" in proto and "GPS {" in proto
assert "boundingObject" in world and proto.count("boundingObject") == 11
assert "from controller import Robot" in controller
for name in config["joints"]:
    assert f'name "{name}"' in proto
    assert f'name "{name}_sensor"' in proto

# Validate brace/bracket balance while ignoring comments and quoted string values.
def validate_balance(name, contents):
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[\[\]{}]', contents)
    stack = []
    for item in tokens:
        if item.startswith(('"', '#')):
            continue
        if item in '[{':
            stack.append(item)
        else:
            assert stack, f"{name}: closing {item} without opener"
            expected = {'}': '{', ']': '['}[item]
            assert stack.pop() == expected, f"{name}: bracket mismatch"
    assert not stack, f"{name}: unclosed braces/brackets"

validate_balance('world', world)
validate_balance('proto', proto)
print("PASS: offline structure, 10 DOF, config naming, physics nodes, sensors, syntax balance")
print("NOT TESTED: true Webots parser acceptance, simulation contacts and dynamic stability")

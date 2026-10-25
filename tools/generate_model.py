#!/usr/bin/env python3
"""Generate a single-file, non-procedural Webots RLH25.proto from robot.json.

All link dimensions and masses are first-pass assumptions (NOT measured hardware).
No external dependencies. Coordinate frame: Y up (Webots WorldInfo coordinateSystem NUE),
robot's forward is -Z, roll axis Z and pitch axis X for leg joints.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "robot.json"
TARGET = ROOT / "simulation" / "webots" / "protos" / "RLH25.proto"


def shift(code: str, spaces: int) -> str:
    return "\n".join((" " * spaces + l) if l else "" for l in code.splitlines())


def box_shape(size: tuple[float, float, float], loc: tuple[float, float, float], color: str) -> str:
    x, y, z = loc
    a, b, c = size
    return f'''Transform {{
  translation {x:g} {y:g} {z:g}
  children [
    Shape {{
      appearance PBRAppearance {{ baseColor {color} roughness 0.8 metalness 0 }}
      geometry Box {{ size {a:g} {b:g} {c:g} }}
    }}
  ]
}}'''


def bounding(size: tuple[float, float, float], loc: tuple[float, float, float]) -> str:
    x, y, z = loc
    a, b, c = size
    return f'''Transform {{
  translation {x:g} {y:g} {z:g}
  children [ Box {{ size {a:g} {b:g} {c:g} }} ]
}}'''


def link_solid(name: str, translation: str, size: tuple[float, float, float],
               center: tuple[float, float, float], mass: float, color: str,
               nested: str = "") -> str:
    pieces = [box_shape(size, center, color)]
    if nested:
        pieces.append(nested)
    children = "\n".join(shift(piece, 4) for piece in pieces)
    contact = '  contactMaterial "foot_grip"\n' if name.endswith("ankle_roll_link") else ""
    def_prefix = ("DEF LEFT_FOOT " if name == "left_ankle_roll_link" else
                  "DEF RIGHT_FOOT " if name == "right_ankle_roll_link" else "")
    return f'''{def_prefix}Solid {{
  translation {translation}
  name "{name}"
{contact.rstrip()}
  children [
{children}
  ]
  boundingObject {shift(bounding(size, center), 2).lstrip()}
  physics Physics {{ density -1 mass {mass:g} }}
}}'''


def make_leg(side: str, specs: dict[str, dict]) -> str:
    side_sign = -1 if side == "left" else 1
    joint_types = ["hip_roll", "hip_pitch", "knee_pitch", "ankle_pitch", "ankle_roll"]
    # NOTE: Webots hinge axis X = sagittal pitch; axis Z = lateral roll.
    anchors = [f"{0.031 * side_sign:g} -0.031 0", "0 0 0", "0 -0.07 0", "0 -0.07 0", "0 0 0"]
    axes = ["0 0 1", "1 0 0", "1 0 0", "1 0 0", "0 0 1"]
    translations = [anchors[0], "0 0 0", "0 -0.07 0", "0 -0.07 0", "0 0 0"]
    sizes = [(.014, .012, .020), (.024, .065, .025), (.022, .065, .023), (.014, .012, .020), (.044, .018, .076)]
    centers = [(0, 0, 0), (0, -.035, 0), (0, -.035, 0), (0, 0, 0), (0, -.003, -.008)]
    masses = [0.012, 0.039, 0.033, 0.008, 0.028]
    colors = ["0.13 0.22 0.38", "0.88 0.88 0.91", "0.74 0.77 0.82", "0.13 0.22 0.38", "0.13 0.20 0.29"]
    nxt = ""
    for idx in reversed(range(5)):
        joint_name = side + "_" + joint_types[idx]
        spec = specs[joint_name]
        child = link_solid(side + "_" + joint_types[idx] + "_link", translations[idx],
                           sizes[idx], centers[idx], masses[idx], colors[idx], nxt)
        min_p, max_p = spec["min"], spec["max"]
        nxt = f'''HingeJoint {{
  jointParameters HingeJointParameters {{
    axis {axes[idx]}
    anchor {anchors[idx]}
    minStop {min_p:g}
    maxStop {max_p:g}
    dampingConstant 0.006
  }}
  device [
    RotationalMotor {{
      name "{joint_name}"
      minPosition {min_p:g}
      maxPosition {max_p:g}
      maxVelocity {spec['max_velocity']:g}
      maxTorque {spec['max_torque']:g}
    }}
    PositionSensor {{ name "{joint_name}_sensor" }}
  ]
  endPoint {shift(child, 2).lstrip()}
}}'''
    return nxt


def generate() -> str:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    specs = config["joints"]
    legs = "\n".join(shift(make_leg(side, specs), 4) for side in ("left", "right"))
    torso = box_shape((.090, .075, .042), (0, .010, 0), "0.86 0.89 0.93")
    head = box_shape((.044, .044, .040), (0, .045, -.004), "0.95 0.96 0.98")
    left_arm = box_shape((.018, .075, .023), (-.065, -.005, 0), "0.38 0.61 0.82")
    right_arm = box_shape((.018, .075, .023), (.065, -.005, 0), "0.38 0.61 0.82")
    # Head/arms are *passive visual shapes* belonging to the rigid Robot body;
    # their mass is lumped into the root body's 0.14 kg.
    passive = "\n".join(shift(n, 4) for n in (torso, head, left_arm, right_arm))
    return f'''#VRML_SIM R2025a utf8
# Robotis Lab RL-H25 v0.1 — generated; edit configs/robot.json and tools/generate_model.py.
# Y-up coordinates (WorldInfo coordinateSystem "NUE"); height at zero joint pose: 0.250 m.
# Physics masses are illustrative only; motor torque is NOT validated against a real servo.
PROTO RLH25 [
  field SFVec3f translation 0 0.183 0
  field SFRotation rotation 0 1 0 0
  field SFString name "RL-H25"
  field SFString controller "rl_h25_controller"
] {{
  Robot {{
    translation IS translation
    rotation IS rotation
    name IS name
    model "Robotis Lab RL-H25 v0.1"
    controller IS controller
    supervisor TRUE
    children [
{passive}
      InertialUnit {{
        name "imu"
        rotation 0 1 0 1.57079632679
      }}
      Gyro {{ name "gyro" }}
      Accelerometer {{ name "accelerometer" }}
      GPS {{ name "root_gps" }}
      Camera {{
        name "head_camera"
        translation 0 0.048 -0.025
        width 128
        height 96
        fieldOfView 0.9
      }}
      DistanceSensor {{
        name "front_distance"
        translation 0 -0.055 -0.040
        rotation 0 1 0 1.57079632679
        type "laser"
        numberOfRays 1
        lookupTable [ 0 0 0, 1.5 1.5 0 ]
      }}
{legs}
    ]
    boundingObject {shift(bounding((.09, .075, .042), (0, .01, 0)), 4).lstrip()}
    physics Physics {{ density -1 mass 0.14 }}
  }}
}}
'''


def main() -> None:
    content = generate()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding="utf-8")
    print(f"generated {TARGET} ({len(content)} bytes)")


if __name__ == "__main__":
    main()

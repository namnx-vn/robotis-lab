"""Run a complete controller loop against deterministic Webots API stand-ins.
This verifies Python integration and logging, NOT simulated gravity or stability.
"""
from __future__ import annotations
import contextlib
import csv
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / "simulation" / "webots" / "controllers" / "rl_h25_controller"
sys.path.insert(0, str(CTRL))


class FakeMotor:
    def __init__(self):
        self.position = 0
        self.torque = 0.8
        self.velocity = 0

    def setPosition(self, v): self.position = v
    def setVelocity(self, v): self.velocity = v
    def setAvailableTorque(self, v): self.torque = v


class FakeSensor:
    def enable(self, timestep): self.timestep = timestep
    def getValue(self): return 0.0
    def getRollPitchYaw(self): return [0.0, 0.0, 0.0]
    def getValues(self): return [0.0, 0.183, 0.0]


class FakeDistance(FakeSensor):
    def getValue(self): return 0.55


class FakeRobot:
    def __init__(self):
        cfg = json.loads((ROOT / "configs" / "robot.json").read_text())
        self.devices = {}
        for name in cfg["joints"]:
            self.devices[name] = FakeMotor()
            self.devices[name + "_sensor"] = FakeSensor()
        for name in ("imu", "gyro", "accelerometer", "root_gps", "head_camera"):
            self.devices[name] = FakeSensor()
        self.devices["front_distance"] = FakeDistance()
        self.t = 0.0

    def getBasicTimeStep(self): return 16
    def getDevice(self, name): return self.devices.get(name)
    def getTime(self): return self.t
    def step(self, ms):
        if self.t >= 0.24:
            return -1
        self.t += ms / 1000
        return 0


class ControllerFakeTests(unittest.TestCase):
    def run_case(self, injection, expected, mode="baseline", nonzero_imu=False):
        module = types.ModuleType("controller")
        module.Robot = FakeRobot
        spec = importlib.util.spec_from_file_location("rl_h25_controller", CTRL / "rl_h25_controller.py")
        ctrl = importlib.util.module_from_spec(spec)
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(sys.modules, {"controller": module}):
                with patch.dict(os.environ, {"RL_H25_LOG_DIR": temp,
                                             "RL_H25_RUN_ID": "fake-case",
                                             "RL_H25_FORCE_FAULT": injection,
                                             "RL_H25_MODE": mode,
                                             "RL_H25_DURATION_S": "0"}):
                    spec.loader.exec_module(ctrl)
                    if nonzero_imu:
                        with patch.object(FakeSensor, "getRollPitchYaw",
                                          return_value=[0.08, -0.06, 0.0]):
                            ctrl.main()
                    else:
                        ctrl.main()
            record = json.loads((Path(temp) / "fake-case.json").read_text())
            with (Path(temp) / "fake-case.csv").open(newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(expected, record["final_state"])
            self.assertEqual(mode, record["mode"])
            self.assertGreaterEqual(len(rows), 1)
            self.assertEqual(expected, rows[-1]["state"])
            self.assertEqual(10, len([k for k in rows[-1] if k.endswith("_target_rad")]))
            if mode == "balance" and expected == "STAND":
                self.assertIn("pitch_correction_rad", rows[-1])
                self.assertIn("root_x_m", rows[-1])
                if nonzero_imu:
                    self.assertNotEqual(0.0, float(rows[-1]["pitch_correction_rad"]))
                    self.assertNotEqual(0.0, float(rows[-1]["roll_correction_rad"]))
                    self.assertNotEqual(0.0, float(rows[-1]["left_ankle_pitch_target_rad"]))
            return record

    def test_normal(self): self.run_case("", "STAND")
    def test_normal_balance(self): self.run_case("", "STAND", mode="balance")
    def test_nonzero_imu_balance_actuates(self):
        self.run_case("", "STAND", mode="balance", nonzero_imu=True)
    def test_invalid_imu_balance(self):
        self.assertEqual("invalid_sensor_value",
                         self.run_case("nan_imu", "FAULT", mode="balance")["stop_reason"])
    def test_estop_balance(self): self.run_case("estop", "E_STOP", mode="balance")
    def test_obstacle(self):
        self.assertEqual("obstacle_nearby", self.run_case("obstacle", "STOP")["stop_reason"])
    def test_bad_imu(self):
        self.assertEqual("invalid_sensor_value", self.run_case("nan_imu", "FAULT")["stop_reason"])
    def test_estop(self): self.run_case("estop", "E_STOP")


if __name__ == "__main__":
    unittest.main()

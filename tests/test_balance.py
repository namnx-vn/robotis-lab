"""Pure-controller and safety fault tests. No Webots runtime needed."""
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation/webots/controllers/rl_h25_controller"))
from motion import AnglePID, BalanceController, JointConfig, PIDConfig, SafetySupervisor, Observation


class BalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT / "configs/robot.json").read_text())
        cls.joints = {n: JointConfig.from_dict(j) for n, j in cls.cfg["joints"].items()}

    def make(self):
        return BalanceController(self.joints, self.cfg["balance"])

    def measured(self):
        return {name: spec.neutral for name, spec in self.joints.items()}

    def test_baseline_no_correction(self):
        c = self.make()
        o = c.update(self.measured(), 0.05, -0.08, 0.016, enabled=True, mode="baseline")
        self.assertTrue(all(v == 0.0 for v in o.values()))
        self.assertEqual(0.0, c.pitch_pid.integral)

    def test_imu_pid_sign_reacts_to_pitch_and_roll(self):
        c = self.make()
        outputs = []
        for _ in range(20):
            outputs.append(c.update(self.measured(), 0.04, 0.07, 0.016,
                                    enabled=True, mode="balance"))
        self.assertLess(outputs[-1]["left_ankle_pitch"], 0.0)
        self.assertLess(outputs[-1]["left_ankle_roll"], 0.0)
        self.assertGreater(outputs[-1]["right_hip_pitch"], 0.0)
        self.assertGreater(outputs[-1]["right_hip_roll"], 0.0)
        self.assertEqual(outputs[-1]["left_knee_pitch"], 0.0)

    def test_per_joint_slew_limit(self):
        c = self.make()
        dt = 0.016
        a = c.update(self.measured(), 0.20, -0.20, dt,
                     enabled=True, mode="balance")
        for name, v in a.items():
            self.assertLessEqual(abs(v), self.joints[name].rate_limit * dt + 1e-10)

    def test_saturation_never_exceeds_joint_limits(self):
        c = self.make()
        for _ in range(1000):
            output = c.update(self.measured(), 0.41, -0.41, 0.016,
                              enabled=True, mode="balance")
        for n, target in output.items():
            self.assertGreaterEqual(target, self.joints[n].minimum)
            self.assertLessEqual(target, self.joints[n].maximum)
        self.assertLessEqual(abs(c.pitch_pid.output), 0.10 + 1e-12)
        self.assertLessEqual(abs(c.roll_pid.output), 0.08 + 1e-12)
        self.assertLessEqual(abs(c.pitch_pid.integral), 0.12 + 1e-12)

    def test_fault_freezes_last_targets_and_resets_pid(self):
        c = self.make()
        before = c.update(self.measured(), 0.07, -0.06, 0.016,
                          enabled=True, mode="balance")
        after = c.update(self.measured(), 0.07, -0.06, 0.016,
                         enabled=False, mode="balance")
        self.assertEqual(before, after)
        self.assertEqual(0., c.roll_pid.integral)
        self.assertEqual(0., c.pitch_pid.integral)
        self.assertEqual(0., c.corrections["roll"])

    def test_timestep_fault_and_reset(self):
        c = self.make()
        c.update(self.measured(), 0.01, 0.02, 0.016, enabled=True, mode="balance")
        with self.assertRaisesRegex(ValueError, "timestep"):
            c.update(self.measured(), 0., 0., 0.2, enabled=True, mode="balance")
        self.assertIsNone(c.pitch_pid.last_measurement)

    def test_nonfinite_sensor_fault(self):
        c = self.make()
        with self.assertRaises(ValueError):
            c.update(self.measured(), math.nan, 0., 0.016, enabled=True, mode="balance")
        bad = self.measured()
        bad["left_ankle_pitch"] = math.inf
        with self.assertRaises(ValueError):
            c.update(bad, 0., 0., 0.016, enabled=True, mode="balance")

    def test_pid_derivative_does_not_kick_on_initial_sample(self):
        pid = AnglePID(PIDConfig(0.4, 0.03, 0.04, 0.1, 0.12, 0.08))
        pid.update(0.1, 0.016)
        self.assertEqual(0., pid.filtered_rate)
        self.assertLess(pid.update(0.1, 0.016), 0.)

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            PIDConfig.from_dict({"kp": -1, "ki": 0, "kd": 0, "integral_limit": 1,
                                 "output_limit_rad": 0.1, "derivative_filter_s": 0.2})
        raw = json.loads(json.dumps(self.cfg["balance"]))
        raw["axis_sign"]["pitch"] = 0
        with self.assertRaises(ValueError):
            BalanceController(self.joints, raw)

    def test_safety_supervisor_latches_tilt(self):
        c = self.make()
        sup = SafetySupervisor(0.45, 0.10, 0.18)
        self.assertEqual("STAND", sup.observe(Observation(0., 0., 0.183, 0.5)))
        self.assertEqual("FAULT", sup.observe(Observation(0., 0.51, 0.18, 0.5)))
        self.assertEqual("FAULT", sup.observe(Observation(0., 0.0, 0.183, 0.5)))
        before = c.targets.copy()
        self.assertEqual(before, c.update(self.measured(), 0., 0., 0.016,
                                          enabled=sup.state == "STAND", mode="balance"))


if __name__ == "__main__":
    unittest.main()

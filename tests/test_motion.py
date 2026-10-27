"""Run: python -m unittest discover -s tests -v"""
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation" / "webots" / "controllers" / "rl_h25_controller"))
from motion import (JointConfig, StandController, Observation, SafetySupervisor,
                    advance, clamp)


class MotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = json.loads((ROOT / "configs" / "robot.json").read_text())
        cls.joints = {name: JointConfig.from_dict(item) for name, item in raw["joints"].items()}

    def test_ten_independent_joint_ids(self):
        self.assertEqual(10, len(self.joints))
        self.assertEqual({"left", "right"}, {k.split("_")[0] for k in self.joints})

    def test_neutral_pose_inside_limits(self):
        for spec in self.joints.values():
            self.assertGreaterEqual(spec.neutral, spec.minimum)
            self.assertLessEqual(spec.neutral, spec.maximum)

    def test_rate_limit_applies(self):
        spec = self.joints["left_hip_pitch"]
        self.assertAlmostEqual(advance(0, 0.5, spec, 0.02), 0.01)
        self.assertAlmostEqual(advance(0, -0.5, spec, 0.02), -0.01)

    def test_joint_limits_apply(self):
        spec = self.joints["left_hip_roll"]
        self.assertEqual(spec.maximum, advance(spec.maximum, 10, spec, 0.5))
        self.assertEqual(spec.minimum, advance(spec.minimum, -10, spec, 0.5))

    def test_invalid_command_is_rejected(self):
        with self.assertRaises(ValueError):
            advance(0, float("nan"), self.joints["left_hip_roll"], 0.01)
        with self.assertRaises(ValueError):
            advance(0, 0, self.joints["left_hip_roll"], -0.01)
        with self.assertRaises(ValueError):
            clamp(float("inf"), -1, 1)

    def test_configuration_rejects_bad_direction(self):
        with self.assertRaises(ValueError):
            JointConfig.from_dict({"neutral": 0, "min": -1, "max": 1,
                                   "direction": 0, "rate_limit": 1})

    def test_stand_controller_neutral(self):
        controller = StandController(self.joints)
        values = controller.update({k: 0.0 for k in self.joints}, 0.016, True)
        self.assertEqual(set(self.joints), set(values))
        self.assertTrue(all(v == 0.0 for v in values.values()))

    def test_sensor_count_must_match(self):
        with self.assertRaises(ValueError):
            StandController(self.joints).update({}, 0.016, True)


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.safe = Observation(0.01, -0.02, 0.182, 0.55)
        self.sup = SafetySupervisor(tilt_fault_rad=0.45,
                                    min_root_height_m=0.1,
                                    obstacle_stop_m=0.18)

    def test_normal_state(self):
        self.assertEqual("STAND", self.sup.observe(self.safe))

    def test_obstacle_latches_stop(self):
        self.assertEqual("STOP", self.sup.observe(Observation(0, 0, 0.18, 0.10)))
        self.assertEqual("STOP", self.sup.observe(self.safe))
        self.assertEqual("obstacle_nearby", self.sup.reason)

    def test_stop_escalates_to_fault_for_later_hazards(self):
        hazards = (
            (Observation(0.46, 0, 0.18, 0.8), "excessive_tilt"),
            (Observation(0, 0, 0.08, 0.8), "root_too_low"),
            (Observation(math.nan, 0, 0.18, 0.8), "invalid_sensor_value"),
        )
        for observation, reason in hazards:
            with self.subTest(reason=reason):
                supervisor = SafetySupervisor(tilt_fault_rad=0.45,
                                              min_root_height_m=0.1,
                                              obstacle_stop_m=0.18)
                self.assertEqual(
                    "STOP", supervisor.observe(Observation(0, 0, 0.18, 0.10))
                )
                self.assertEqual("FAULT", supervisor.observe(observation))
                self.assertEqual(reason, supervisor.reason)

    def test_imu_nonfinite_fault(self):
        self.assertEqual("FAULT", self.sup.observe(Observation(math.nan, 0, 0.18, 0.9)))
        self.assertFalse(self.sup.reset_with_operator_approval(False, self.safe))
        self.assertEqual("FAULT", self.sup.state)
        self.assertTrue(self.sup.reset_with_operator_approval(True, self.safe))
        self.assertEqual("STAND", self.sup.state)

    def test_fall_height_fault(self):
        self.assertEqual("FAULT", self.sup.observe(Observation(0, 0, 0.08, 0.8)))
        self.assertEqual("root_too_low", self.sup.reason)

    def test_tilt_fault(self):
        self.assertEqual("FAULT", self.sup.observe(Observation(0.46, 0, 0.18, 0.8)))
        self.assertEqual("excessive_tilt", self.sup.reason)

    def test_estop_overrides_fault(self):
        self.sup.observe(Observation(math.nan, 0, 0, 0))
        self.assertEqual("E_STOP", self.sup.observe(self.safe, emergency_stop=True))
        self.assertEqual("operator_estop", self.sup.reason)

    def test_reset_not_allowed_while_obstacle_near(self):
        self.sup.observe(Observation(0, 0, 0.18, 0.10))
        self.assertFalse(self.sup.reset_with_operator_approval(True, Observation(0, 0, 0.18, 0.10)))
        self.assertEqual("STOP", self.sup.state)


if __name__ == "__main__":
    unittest.main()

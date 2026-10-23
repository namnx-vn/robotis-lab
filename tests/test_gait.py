"""Offline waveform tests only; cannot certify foot contacts or walking."""
from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from host.robotis.gait import JOINT_NAMES, PHASE_SEQUENCE, OfflineGait

ROOT = Path(__file__).resolve().parents[1]


class OfflineGaitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "configs" / "robot.json").read_text())

    def test_six_phases_and_ten_joint_angles(self):
        gait = OfflineGait(self.config)
        self.assertEqual(len(PHASE_SEQUENCE), 6)
        seen = []
        for tick in range(int(gait.cycle_duration_s / 0.016) + 1):
            frame = gait.frame_at(tick * 0.016)
            if not seen or frame.phase != seen[-1]:
                seen.append(frame.phase)
            self.assertEqual(set(frame.angles_rad), set(JOINT_NAMES))
            self.assertTrue(all(math.isfinite(v) for v in frame.angles_rad.values()))
            for joint, value in frame.angles_rad.items():
                bounds = self.config["joints"][joint]
                self.assertLessEqual(bounds["min"] - 1e-12, value)
                self.assertLessEqual(value, bounds["max"] + 1e-12)
        self.assertEqual(tuple(seen), PHASE_SEQUENCE + (PHASE_SEQUENCE[0],))

    def test_rate_limit_every_sample_including_cycle_seam(self):
        gait = OfflineGait(self.config)
        dt = 0.016
        last = gait.frame_at(0).angles_rad
        for tick in range(1, int(2 * gait.cycle_duration_s / dt) + 2):
            now = gait.frame_at(tick * dt).angles_rad
            for joint in JOINT_NAMES:
                max_delta = self.config["joints"][joint]["rate_limit"] * dt
                self.assertLessEqual(abs(now[joint] - last[joint]), max_delta + 1e-10)
            last = now

    def test_exact_cycle_boundary_is_continuous_and_neutral(self):
        gait = OfflineGait(self.config)
        t = gait.cycle_duration_s
        for sample_t in (0, t, t * 2):
            frame = gait.frame_at(sample_t)
            self.assertEqual(frame.phase, PHASE_SEQUENCE[0])
            for joint in JOINT_NAMES:
                self.assertAlmostEqual(frame.angles_rad[joint],
                                       self.config["joints"][joint]["neutral"])
        for joint in JOINT_NAMES:
            self.assertLess(abs(gait.frame_at(t - 1e-5).angles_rad[joint]
                                - gait.frame_at(t + 1e-5).angles_rad[joint]), 1e-8)

    def test_nonzero_swing_pose_is_only_a_kinematic_proposal(self):
        gait = OfflineGait(self.config)
        right = gait.frame_at(0.4 + 0.8 + 0.3)
        left = gait.frame_at(0.4 + 0.8 + 1.2 + 0.4 + 0.8 + 0.3)
        self.assertEqual("SWING_RIGHT", right.phase)
        self.assertEqual("SWING_LEFT", left.phase)
        self.assertGreater(right.angles_rad["right_knee_pitch"], 0)
        self.assertGreater(left.angles_rad["left_knee_pitch"], 0)
        self.assertEqual(0.0, right.angles_rad["left_knee_pitch"])
        self.assertEqual(0.0, left.angles_rad["right_knee_pitch"])

    def test_rejects_invalid_sensor_like_and_time_inputs(self):
        gait = OfflineGait(self.config)
        for bad in (-1, math.nan, math.inf, "bad", True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                gait.frame_at(bad)

    def test_rejects_invalid_schema_and_nonfinite_config(self):
        for change in ("missing", "extra", "bad_units", "nonfinite", "bad_direction", "bad_rate"):
            config = copy.deepcopy(self.config)
            if change == "missing": del config["joints"]["left_hip_roll"]
            elif change == "extra": config["joints"]["extra_joint"] = config["joints"]["left_hip_roll"]
            elif change == "bad_units": config["units"] = "degree"
            elif change == "nonfinite": config["joints"]["left_hip_roll"]["neutral"] = math.nan
            elif change == "bad_direction": config["joints"]["left_hip_roll"]["direction"] = 0
            else: config["joints"]["left_hip_roll"]["rate_limit"] = 0
            with self.subTest(change=change), self.assertRaises(ValueError):
                OfflineGait(config)

    def test_rejects_out_of_limit_pose_or_unsafe_rate(self):
        for args in ({"knee_lift_rad": 2.0}, {"swing_s": 0.001},
                     {"shift_rad": -0.1}, {"shift_s": math.nan},
                     {"double_support_s": 0}, {"shift_s": 1e308},
                     {"hip_swing_rad": math.inf}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                OfflineGait(self.config, **args)

    def test_frames_are_detached_from_generator_state(self):
        gait = OfflineGait(self.config)
        frame = gait.frame_at(0.2)
        frame.angles_rad["left_hip_roll"] = 1000.0
        self.assertEqual(gait.frame_at(0.2).angles_rad["left_hip_roll"], 0.0)


if __name__ == "__main__":
    unittest.main()

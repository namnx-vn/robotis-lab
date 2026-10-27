"""Fail-closed parser tests (does NOT claim the simulator passed)."""
import json
import math
import sys
import unittest
from pathlib import Path
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from run_force_api_probe import (PREFIX, build_probe_env, parse_probe_log,
                                 run_probe_process)

NAMES = ("pitch_plus", "pitch_minus", "roll_plus", "roll_minus",
         "pitch_zero_offset", "roll_zero_offset",
         "yaw_rotated_world_force", "rotated_local_offset",
         "torque_pitch_plus", "torque_pitch_minus",
         "torque_roll_plus", "torque_roll_minus",
         "torque_zero", "torque_yaw_rotated_world")


def example():
    directions = {
        "pitch_plus": (0, 1), "pitch_minus": (0, -1),
        "roll_plus": (2, -1), "roll_minus": (2, 1),
        "yaw_rotated_world_force": (0, 1), "rotated_local_offset": (1, 1),
        "torque_pitch_plus": (0, 1), "torque_pitch_minus": (0, -1),
        "torque_roll_plus": (2, -1), "torque_roll_minus": (2, 1),
        "torque_yaw_rotated_world": (0, 1),
    }
    results = []
    for name in NAMES:
        omega = [0.0, 0.0, 0.0]
        if name in directions:
            axis, sign = directions[name]
            omega[axis] = sign * 1.0
        results.append({"case": name, "omega_xyz": omega, "pass": True})
    return {"pass": True, "gravity_observed": True,
            "gravity_displacement_m": -0.015,
            "force_api_mode": "r2025a_ctypes_force_with_offset",
            "torque_api_mode": "r2025a_ctypes_torque",
            "build_commit": "a" * 40,
            "source_commit_sha": "b" * 40,
            "test_merge_sha": "a" * 40,
            "webots_version": "Webots R2025a",
            "probe_torque_nm": 0.01, "pulse_steps": 8,
            "results": results}


class ProbeParserTests(unittest.TestCase):
    def test_accepts_complete_native_result_only(self):
        data = example()
        self.assertEqual(data, parse_probe_log("noise\n" + PREFIX + json.dumps(data)))

    def test_rejects_missing_duplicate_or_failed_evidence(self):
        valid = PREFIX + json.dumps(example())
        with self.assertRaises(ValueError): parse_probe_log("noise")
        with self.assertRaises(ValueError): parse_probe_log(valid + "\n" + valid)
        for mutation in (
            {"pass": False},
            {"gravity_observed": False},
            {"force_api_mode": "python_wrapper_unverified"},
            {"torque_api_mode": "python_wrapper_unverified"},
            {"build_commit": "unverified"},
            {"source_commit_sha": "unverified"},
            {"test_merge_sha": "unverified"},
            {"webots_version": "unverified"},
            {"webots_version": "Webots R2025b"},
            {"webots_version": "Webots R2024a"},
            {"results": example()["results"][:-1]},
        ):
            broken = example() | mutation
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                parse_probe_log(PREFIX + json.dumps(broken))
        broken = example()
        broken["results"][0]["pass"] = False
        with self.assertRaises(ValueError):
            parse_probe_log(PREFIX + json.dumps(broken))

    def test_rejects_missing_nonfinite_wrong_sign_or_cross_axis_physics(self):
        mutations = []
        missing = example()
        del missing["results"][0]["omega_xyz"]
        mutations.append(missing)
        nonfinite = example()
        nonfinite["results"][0]["omega_xyz"][0] = math.nan
        mutations.append(nonfinite)
        wrong_sign = example()
        wrong_sign["results"][0]["omega_xyz"][0] = -1.0
        mutations.append(wrong_sign)
        cross_axis = example()
        cross_axis["results"][0]["omega_xyz"][1] = 0.5
        mutations.append(cross_axis)
        wrong_torque = example() | {"probe_torque_nm": 0.02}
        mutations.append(wrong_torque)
        wrong_steps = example() | {"pulse_steps": 7}
        mutations.append(wrong_steps)
        missing_gravity = example()
        del missing_gravity["gravity_displacement_m"]
        mutations.append(missing_gravity)
        mutations.append(example() | {"gravity_displacement_m": math.nan})
        mutations.append(example() | {"gravity_displacement_m": 0.01})

        for index, broken in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(ValueError):
                parse_probe_log(PREFIX + json.dumps(broken))


class ProbeProcessTests(unittest.TestCase):
    def test_probe_env_overwrites_stale_webots_version(self):
        head = "a" * 40
        base = {
            "RL_H25_BUILD_COMMIT": head,
            "RL_H25_SOURCE_COMMIT_SHA": "b" * 40,
            "RL_H25_TEST_MERGE_SHA": head,
            "RL_H25_WEBOTS_VERSION": "Webots R2099z stale",
        }
        with patch("run_force_api_probe.read_webots_version",
                   return_value="Webots R2025a38"):
            env = build_probe_env("webots", base, head, github_actions=True)
        self.assertEqual("Webots R2025a38", env["RL_H25_WEBOTS_VERSION"])

    def test_timeout_kills_webots_process_group_and_returns(self):
        # The child inherits stdout, as Webots' launcher does when it starts
        # the actual simulator. Killing only the launcher leaves communicate()
        # waiting on that inherited pipe.
        command = [sys.executable, "-c",
                   "import subprocess,sys,time; "
                   "subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
                   "time.sleep(30)"]
        started = time.monotonic()
        output, timed_out, returncode = run_probe_process(command, timeout=0.2)
        self.assertTrue(timed_out)
        self.assertNotEqual(0, returncode)
        self.assertLess(time.monotonic() - started, 3.0)
        self.assertIn("TIMEOUT", output)

    def test_nonzero_webots_exit_is_preserved(self):
        output, timed_out, returncode = run_probe_process(
            [sys.executable, "-c", "import sys; print('native error'); sys.exit(7)"],
            timeout=2.0)
        self.assertFalse(timed_out)
        self.assertEqual(7, returncode)
        self.assertIn("native error", output)


if __name__ == "__main__":
    unittest.main()

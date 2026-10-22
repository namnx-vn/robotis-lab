"""Fail-closed parser tests (does NOT claim the simulator passed)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from run_force_api_probe import PREFIX, parse_probe_log

NAMES = ("pitch_plus", "pitch_minus", "roll_plus", "roll_minus",
         "pitch_zero_offset", "roll_zero_offset",
         "yaw_rotated_world_force", "rotated_local_offset")


def example():
    return {"pass": True, "gravity_observed": True,
            "force_api_mode": "r2025a_ctypes_force_with_offset",
            "results": [{"case": name, "pass": True} for name in NAMES]}


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
            {"results": example()["results"][:-1]},
        ):
            broken = example() | mutation
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                parse_probe_log(PREFIX + json.dumps(broken))
        broken = example()
        broken["results"][0]["pass"] = False
        with self.assertRaises(ValueError):
            parse_probe_log(PREFIX + json.dumps(broken))


if __name__ == "__main__":
    unittest.main()

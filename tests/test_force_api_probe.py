"""Fail-closed parser tests (does NOT claim the simulator passed)."""
import json
import sys
import unittest
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from run_force_api_probe import PREFIX, parse_probe_log, run_probe_process

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


class ProbeProcessTests(unittest.TestCase):
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

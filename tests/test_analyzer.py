import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from analyze_runs import summarize


class AnalysisTests(unittest.TestCase):
    def write(self, f, rows):
        with f.open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["t_s", "roll_rad", "pitch_rad", "root_height_m", "state"])
            writer.writeheader()
            writer.writerows(rows)

    def test_synthetic_pass_and_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fake.csv"
            data = [{"t_s": n, "roll_rad": 0.01, "pitch_rad": -0.01,
                     "root_height_m": 0.18, "state": "STAND"} for n in range(32)]
            self.write(path, data)
            self.assertTrue(summarize(path, 30)["pass"])
            data[-1]["state"] = "FAULT"
            self.write(path, data)
            self.assertFalse(summarize(path, 30)["pass"])


if __name__ == "__main__":
    unittest.main()

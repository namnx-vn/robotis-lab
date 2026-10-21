import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from baseline_report import evaluate, evaluate_suite

FIELDS = ("run_id", "t_s", "mode", "state", "reason", "roll_rad", "pitch_rad",
          "root_height_m", "root_x_m", "root_z_m")


class BaselineReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, *, state="STAND", tilt=0.03, drift=0.002,
              gap=False, legacy=False, invalid_metadata=False):
        p = self.root / (name + ".csv")
        fields = list(FIELDS)
        if legacy:
            fields.remove("root_x_m")
            fields.remove("root_z_m")
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for i in range(312):
                if gap and 100 <= i < 110:
                    continue
                row = dict(run_id=name, t_s=round(i * .1, 2), mode="baseline",
                           state=state if i >= 190 else "STAND", reason="",
                           roll_rad=0.0, pitch_rad=tilt, root_height_m=.18,
                           root_x_m=(i / 311) * drift, root_z_m=0.0)
                w.writerow({k: row[k] for k in fields})
        meta = {"run_id": "bad" if invalid_metadata else name, "result": "controller_exited",
                "mode": "baseline", "fault_injection": None}
        p.with_suffix(".json").write_text(json.dumps(meta))
        return p

    def test_valid_baseline(self):
        r = evaluate(self.write("good"))
        self.assertTrue(r["pass"], r)
        self.assertGreater(r["metrics"]["duration_s"], 30)

    def test_tilt_fails(self):
        self.assertIn("tilt_exceeded", evaluate(self.write("tilt", tilt=.25))["reasons"])

    def test_any_fault_fails_even_late_in_run(self):
        self.assertIn("non_stand_state", evaluate(self.write("fault", state="FAULT"))["reasons"])

    def test_foot_sliding_detected_by_gps(self):
        self.assertIn("drift_exceeded", evaluate(self.write("slip", drift=.10))["reasons"])

    def test_gap_fails(self):
        self.assertIn("telemetry_gap", evaluate(self.write("gap", gap=True))["reasons"])

    def test_old_v01_logs_cannot_pass_full_gate(self):
        self.assertIn("missing_columns:root_x_m,root_z_m", evaluate(self.write("legacy", legacy=True))["reasons"])

    def test_metadata_mismatch_fails(self):
        self.assertIn("metadata_run_id_mismatch", evaluate(self.write("badmeta", invalid_metadata=True))["reasons"])

    def test_suite_4_of_5_and_independence(self):
        files = [self.write(f"trial{i}", state="FAULT" if i == 4 else "STAND") for i in range(5)]
        suite = evaluate_suite(files)
        self.assertTrue(suite["pass"], suite)
        self.assertFalse(evaluate_suite(files[:4])["pass"])
        self.assertFalse(evaluate_suite(files[:4] + files[:1])["pass"])


if __name__ == "__main__":
    unittest.main()

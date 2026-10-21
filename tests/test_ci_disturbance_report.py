"""Unit tests for evidence-vs-science distinction in native disturbance CI."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from ci_disturbance_report import analyze_pilot, write_report, ALLOWED_AXES


def fixture(path: Path, status: str = "READY_FOR_FULL", total: int = 4) -> Path:
    cases = []
    for axis, direction in list(sorted(ALLOWED_AXES))[:total]:
        cases.append({
            "axis": axis, "direction": direction, "status": status,
            "report": {
                "pairs": [{
                    "comparable": True,
                    "baseline": {"run_id": f"b-{axis}-{direction}",
                                 "verdict": "RECOVERED", "peak_tilt_change_rad": 0.05},
                    "balance": {"run_id": f"p-{axis}-{direction}",
                                "verdict": "RECOVERED", "peak_tilt_change_rad": 0.03},
                }]
            },
        })
    path.write_text(json.dumps({
        "schema_version": 1, "pilot": True,
        "settings": {"pairs_per_direction": 1},
        "gate": "READY_FOR_FULL" if total == 4 else "REVIEW_REQUIRED",
        "cases": cases,
    }))
    return path


class PilotReportTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.tmp = Path(d.name)

    def analyze(self, source):
        return analyze_pilot(source, commit_sha="abc123", run_url="https://github.test/actions/runs/1")

    def test_pilot_ready_does_not_certify_balance(self):
        report = self.analyze(fixture(self.tmp / "matrix.json"))
        self.assertTrue(report["ci_evidence_ok"])
        self.assertFalse(report["scientific_balance_certified"])
        self.assertEqual("READY_FOR_FULL_EXPERIMENT", report["assessment"])
        write_report(report, self.tmp / "reports")
        self.assertIn("Active balance certified: **NO**",
                      (self.tmp / "reports/balance-pilot-ci-report.md").read_text())

    def test_missing_report_is_invalid(self):
        r = self.analyze(None)
        self.assertFalse(r["ci_evidence_ok"])
        self.assertIn("no_balance_matrix_report", r["errors"])

    def test_corrupt_matrix_is_invalid(self):
        f = self.tmp / "broken.json"
        f.write_text("{oops")
        r = self.analyze(f)
        self.assertFalse(r["ci_evidence_ok"])
        self.assertEqual("INVALID_EVIDENCE", r["assessment"])

    def test_partial_inconclusive_is_reported_not_success(self):
        r = self.analyze(fixture(self.tmp / "partial.json", status="INCONCLUSIVE", total=1))
        self.assertTrue(r["ci_evidence_ok"])
        self.assertEqual("REVIEW_EXPERIMENT", r["assessment"])
        self.assertFalse(r["scientific_balance_certified"])

    def test_fault_does_not_become_balance_success(self):
        f = fixture(self.tmp / "fault.json", status="REVIEW_REQUIRED", total=1)
        data = json.loads(f.read_text())
        data["cases"][0]["report"]["pairs"][0]["balance"] = {
            "verdict": "FAIL", "fault": True, "peak_tilt_change_rad": 0.55}
        f.write_text(json.dumps(data))
        r = self.analyze(f)
        self.assertTrue(r["ci_evidence_ok"])
        self.assertEqual("REVIEW_EXPERIMENT", r["assessment"])
        self.assertEqual("FAIL", r["cases"][0]["runs"]["balance"]["verdict"])

    def test_error_case_fails_infrastructure_gate(self):
        f = fixture(self.tmp / "error.json", total=1)
        data = json.loads(f.read_text())
        data["cases"] = [{"axis": "pitch", "direction": 1,
                          "status": "ERROR", "error": "Webots failed"}]
        f.write_text(json.dumps(data))
        r = self.analyze(f)
        self.assertFalse(r["ci_evidence_ok"])
        self.assertIn("runner_error:pitch:1", r["errors"])

    def test_duplicate_direction_is_invalid(self):
        f = fixture(self.tmp / "duplicate.json", total=2)
        data = json.loads(f.read_text())
        data["cases"][1]["axis"] = data["cases"][0]["axis"]
        data["cases"][1]["direction"] = data["cases"][0]["direction"]
        f.write_text(json.dumps(data))
        r = self.analyze(f)
        self.assertFalse(r["ci_evidence_ok"])


if __name__ == "__main__":
    unittest.main()

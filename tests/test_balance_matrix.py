"""Offline regression tests for the 4-direction experiment gate (no Webots)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run_balance_matrix import CASES, classify_case, overall_gate, validate_experiment


def fake_pair(base="RECOVERED", balance="RECOVERED", comparable=True):
    return {"comparable": comparable,
            "baseline": {"verdict": base}, "balance": {"verdict": balance}}


class MatrixValidationTests(unittest.TestCase):
    def test_four_distinct_directions(self):
        self.assertEqual(set(CASES), {("pitch", 1), ("pitch", -1), ("roll", 1), ("roll", -1)})

    def test_reject_unsafe_or_unproductive_runs(self):
        valid = dict(pairs=1, force=.1, pulse=.112, offset=.04,
                     onset=4., duration=14., timeout=180.)
        for k, value in (("pairs", 2), ("pairs", 20), ("force", float("nan")),
                         ("force", .9), ("pulse", 1.), ("onset", 0.),
                         ("offset", -.01), ("offset", .07),
                         ("duration", 5.), ("timeout", 0.)):
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate_experiment(**(valid | {k: value}))
        validate_experiment(**valid)

    def test_pilot_never_claims_improvement(self):
        r = {"pairs": [fake_pair()], "distinct_run_ids": True, "comparable_pairs": 1,
             "verdict": "INCONCLUSIVE"}
        self.assertEqual("READY_FOR_FULL", classify_case(r, pilot=True))
        self.assertEqual("INCONCLUSIVE", classify_case(r, pilot=False))

    def test_inconclusive_and_fault_stop_review(self):
        for pair, expected in [
            (fake_pair("INCONCLUSIVE"), "INCONCLUSIVE"),
            (fake_pair(balance="INVALID"), "INCONCLUSIVE"),
            (fake_pair(balance="FAIL"), "REVIEW_REQUIRED"),
            (fake_pair(base="FAIL"), "REVIEW_REQUIRED"),
            (fake_pair(comparable=False), "INCONCLUSIVE")
        ]:
            with self.subTest(expected=expected, pair=pair):
                self.assertEqual(expected, classify_case({"pairs": [pair]}, pilot=True))

    def test_full_gate_requires_four_axes_and_real_improvement(self):
        data = [{"axis": a, "direction": d, "status": "IMPROVED"} for a, d in CASES]
        self.assertEqual("PASS", overall_gate(data, pilot=False))
        self.assertEqual("INCOMPLETE", overall_gate(data[:-1], pilot=False))
        data[2]["status"] = "NOT_ESTABLISHED"
        self.assertEqual("NOT_ESTABLISHED", overall_gate(data, pilot=False))

    def test_pilot_gate_never_passes(self):
        rows = [{"axis": a, "direction": d, "status": "READY_FOR_FULL"} for a, d in CASES]
        self.assertEqual("READY_FOR_FULL", overall_gate(rows, pilot=True))
        rows[-1]["status"] = "REVIEW_REQUIRED"
        self.assertEqual("REVIEW_REQUIRED", overall_gate(rows, pilot=True))


if __name__ == "__main__":
    unittest.main()

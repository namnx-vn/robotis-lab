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


def evidenced_case(axis, direction, status="IMPROVED", world="c" * 64):
    evidence = {
        "build_commit": "a" * 40,
        "source_commit_sha": "a" * 40,
        "test_merge_sha": "a" * 40,
        "config_sha256": "b" * 64,
        "world_sha256": world,
        "software_version": "rlh25-v0.2",
        "telemetry_schema_version": 2,
        "log_period_s": .016,
        "webots_version": "Webots R2025a38",
        "force_api_mode": "r2025a_ctypes_force_with_offset",
        "simulation_timestep_s": .016,
        "force_n": .5,
        "pulse_s": .2,
        "onset_s": 4.,
        "offset_m": .06,
        "calibration_mode": False,
        "applied_steps": 13,
    }
    pairs = []
    for index in range(3):
        baseline = dict(evidence, run_id=f"{axis}-{direction}-b-{index}", verdict="RECOVERED")
        balance = dict(evidence, run_id=f"{axis}-{direction}-c-{index}", verdict="RECOVERED")
        pairs.append({"baseline": baseline, "balance": balance, "comparable": True})
    return {
        "axis": axis,
        "direction": direction,
        "status": status,
        "report": {
            "verdict": "IMPROVED",
            "comparable_pairs": 3,
            "distinct_run_ids": True,
            "pairs": pairs,
        },
    }


class MatrixValidationTests(unittest.TestCase):
    def test_four_distinct_directions(self):
        self.assertEqual(set(CASES), {("pitch", 1), ("pitch", -1), ("roll", 1), ("roll", -1)})

    def test_reject_unsafe_or_unproductive_runs(self):
        valid = dict(pairs=1, force=.1, pulse=.112, offset=.04,
                     onset=4., duration=14., timeout=180.)
        for k, value in (("pairs", 2), ("pairs", 20), ("force", float("nan")),
                         ("force", .51), ("pulse", 1.), ("onset", 0.),
                         ("offset", -.01), ("offset", .07),
                         ("duration", 5.), ("timeout", 0.)):
            with self.subTest(k=k), self.assertRaises(ValueError):
                validate_experiment(**(valid | {k: value}))
        validate_experiment(**valid)
        validate_experiment(**(valid | {"force": .5}))

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
        data = [evidenced_case(a, d) for a, d in CASES]
        self.assertEqual("PASS", overall_gate(data, pilot=False))
        self.assertEqual("INCOMPLETE", overall_gate(data[:-1], pilot=False))
        data[2]["status"] = "NOT_ESTABLISHED"
        self.assertEqual("NOT_ESTABLISHED", overall_gate(data, pilot=False))

    def test_full_gate_rejects_cross_case_provenance_mismatch(self):
        data = [evidenced_case(a, d) for a, d in CASES]
        data[-1] = evidenced_case(*CASES[-1], world="d" * 64)
        self.assertEqual("NOT_ESTABLISHED", overall_gate(data, pilot=False))

    def test_full_gate_revalidates_pair_count_verdict_and_run_ids(self):
        for mutation in ("pair_count", "verdict", "duplicate_id"):
            with self.subTest(mutation=mutation):
                data = [evidenced_case(a, d) for a, d in CASES]
                report = data[0]["report"]
                if mutation == "pair_count":
                    report["pairs"] = report["pairs"][:1]
                    report["comparable_pairs"] = 1
                elif mutation == "verdict":
                    report["verdict"] = "NO_DEMONSTRATED_IMPROVEMENT"
                else:
                    duplicate = report["pairs"][0]["baseline"]["run_id"]
                    report["pairs"][0]["balance"]["run_id"] = duplicate
                self.assertEqual("NOT_ESTABLISHED", overall_gate(data, pilot=False))

    def test_pilot_gate_never_passes(self):
        rows = [{"axis": a, "direction": d, "status": "READY_FOR_FULL"} for a, d in CASES]
        self.assertEqual("READY_FOR_FULL", overall_gate(rows, pilot=True))
        rows[-1]["status"] = "REVIEW_REQUIRED"
        self.assertEqual("REVIEW_REQUIRED", overall_gate(rows, pilot=True))


if __name__ == "__main__":
    unittest.main()

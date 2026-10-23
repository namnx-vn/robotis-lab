import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "ci_report.py"
COMMIT_SHA = "a" * 40
SOURCE_COMMIT_SHA = "b" * 40


class CiReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        self.output = self.root / "reports"
        self.logs.mkdir()

    def run_report(self, profile, offline="success", simulation="success"):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--profile",
                profile,
                "--offline-status",
                offline,
                "--simulation-status",
                simulation,
                "--logs-dir",
                str(self.logs),
                "--output-dir",
                str(self.output),
                "--commit-sha",
                COMMIT_SHA,
                "--source-commit-sha",
                SOURCE_COMMIT_SHA,
                "--run-url",
                "https://github.test/actions/runs/7",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def read_json(self):
        return json.loads((self.output / "ci-report.json").read_text(encoding="utf-8"))

    def write_metadata(self, name, **overrides):
        value = {
            "run_id": name,
            "mode": "baseline",
            "result": "controller_exited",
            "final_state": "STAND",
            "sim_time_s": 8.0,
            "build_commit": COMMIT_SHA,
            "source_commit_sha": SOURCE_COMMIT_SHA,
            "test_merge_sha": COMMIT_SHA,
        } | overrides
        (self.logs / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")

    def write_baseline_batch(self, count=5, fault_index=None):
        for index in range(count):
            final_state = "FAULT" if index == fault_index else "STAND"
            self.write_metadata(
                f"baseline-run-{index + 1}",
                final_state=final_state,
                sim_time_s=32.0,
            )

    def test_smoke_success_reports_matching_metadata_and_scope_limit(self):
        (self.logs / "smoke-good.json").write_text(
            json.dumps(
                {
                    "run_id": "smoke-good",
                    "mode": "baseline",
                    "result": "controller_exited",
                    "final_state": "STAND",
                    "sim_time_s": 8.0,
                    "build_commit": COMMIT_SHA,
                    "source_commit_sha": SOURCE_COMMIT_SHA,
                    "test_merge_sha": COMMIT_SHA,
                }
            ),
            encoding="utf-8",
        )
        (self.logs / "baseline-ignore.json").write_text(
            json.dumps({"run_id": "baseline-ignore", "result": "controller_exited"}),
            encoding="utf-8",
        )

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertTrue(report["overall_success"])
        self.assertEqual(report["profile"], "smoke")
        self.assertEqual(report["metadata_summary"]["matched_files"], 1)
        self.assertEqual(report["metadata_summary"]["valid_files"], 1)
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertIn(COMMIT_SHA, markdown)
        self.assertIn("https://github.test/actions/runs/7", markdown)
        self.assertIn("does not certify standing stability", markdown)

    def test_baseline_success_includes_gate_and_visual_check_warning(self):
        self.write_baseline_batch()
        self.output.mkdir()
        (self.output / "standing_baseline_report.json").write_text(
            json.dumps(
                {
                    "pass": True,
                    "passing": 5,
                    "count": 5,
                    "unique_run_ids": True,
                    "same_mode": True,
                }
            ),
            encoding="utf-8",
        )

        completed = self.run_report("baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertTrue(report["overall_success"])
        self.assertEqual(
            report["baseline_gate"],
            {
                "pass": True,
                "passing": 5,
                "count": 5,
                "unique_run_ids": True,
                "same_mode": True,
            },
        )
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertIn("5/5", markdown)
        self.assertIn("visual foot-contact check", markdown)

    def test_baseline_gate_failure_makes_overall_fail(self):
        self.output.mkdir()
        (self.output / "standing_baseline_report.json").write_text(
            json.dumps(
                {
                    "pass": False,
                    "passing": 3,
                    "count": 5,
                    "unique_run_ids": True,
                    "same_mode": True,
                }
            ),
            encoding="utf-8",
        )

        completed = self.run_report("baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(self.read_json()["overall_success"])

    def test_baseline_four_of_five_is_a_valid_passing_gate(self):
        self.write_baseline_batch(fault_index=4)
        self.output.mkdir()
        (self.output / "standing_baseline_report.json").write_text(
            json.dumps(
                {
                    "pass": True,
                    "passing": 4,
                    "count": 5,
                    "unique_run_ids": True,
                    "same_mode": True,
                }
            ),
            encoding="utf-8",
        )

        completed = self.run_report("baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertTrue(report["overall_success"])
        self.assertEqual(report["metadata_summary"]["valid_files"], 5)
        self.assertEqual(report["metadata_summary"]["invalid_files"], 0)

    def test_baseline_missing_gate_makes_overall_fail(self):
        self.write_metadata("baseline-good", sim_time_s=32.0)

        completed = self.run_report("baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertFalse(report["overall_success"])
        self.assertEqual(report["baseline_gate"]["error"], "missing gate report")

    def test_corrupt_baseline_gate_fails_without_aborting(self):
        self.output.mkdir()
        (self.output / "standing_baseline_report.json").write_text(
            "{not-json", encoding="utf-8"
        )

        completed = self.run_report("baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertFalse(report["overall_success"])
        self.assertEqual(report["baseline_gate"]["error"], "JSONDecodeError")
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertNotIn("None/None", markdown)

    def test_baseline_gate_without_counts_does_not_render_none_values(self):
        self.output.mkdir()
        (self.output / "standing_baseline_report.json").write_text(
            json.dumps({"pass": False}), encoding="utf-8"
        )

        completed = self.run_report("baseline")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertNotIn("None/None", markdown)

    def test_baseline_passing_gate_requires_valid_trial_counts(self):
        self.write_metadata("baseline-good", sim_time_s=32.0)
        invalid_gates = (
            {"pass": True},
            {"pass": True, "passing": "5", "count": 5},
            {"pass": True, "passing": 6, "count": 5},
            {"pass": True, "passing": 5, "count": 4},
            {
                "pass": True,
                "passing": 0,
                "count": 5,
                "unique_run_ids": True,
                "same_mode": True,
            },
            {
                "pass": True,
                "passing": 3,
                "count": 5,
                "unique_run_ids": True,
                "same_mode": True,
            },
            {
                "pass": False,
                "passing": 4,
                "count": 5,
                "unique_run_ids": True,
                "same_mode": True,
            },
        )
        for gate in invalid_gates:
            with self.subTest(gate=gate):
                self.output.mkdir(exist_ok=True)
                (self.output / "standing_baseline_report.json").write_text(
                    json.dumps(gate), encoding="utf-8"
                )
                completed = self.run_report("baseline")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = self.read_json()
                self.assertFalse(report["overall_success"])
                self.assertIn("error", report["baseline_gate"])

    def test_failed_status_and_missing_logs_still_create_reports(self):
        completed = self.run_report("smoke", offline="failure", simulation="failure")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((self.output / "ci-report.md").is_file())
        self.assertTrue((self.output / "ci-report.json").is_file())
        report = self.read_json()
        self.assertFalse(report["overall_success"])
        self.assertEqual(report["metadata_summary"]["matched_files"], 0)
        self.assertEqual(report["statuses"]["offline"], "failure")
        self.assertEqual(report["statuses"]["simulation"], "failure")

    def test_success_statuses_with_missing_logs_still_fail_overall(self):
        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(self.read_json()["overall_success"])

    def test_corrupt_metadata_is_reported_without_aborting(self):
        self.write_metadata("smoke-good")
        (self.logs / "smoke-corrupt.json").write_text("{not-json", encoding="utf-8")

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertFalse(report["overall_success"])
        self.assertEqual(report["metadata_summary"]["matched_files"], 2)
        self.assertEqual(report["metadata_summary"]["valid_files"], 1)
        self.assertEqual(report["metadata_summary"]["invalid_files"], 1)
        self.assertIn("smoke-corrupt.json", report["metadata_summary"]["errors"][0])

    def test_incomplete_metadata_does_not_contribute_to_success(self):
        invalid_runs = (
            ("smoke-incomplete", {"result": "incomplete"}),
            ("smoke-no-state", {"final_state": None}),
            ("smoke-no-mode", {"mode": ""}),
            ("smoke-no-time", {"sim_time_s": 0}),
        )
        for name, overrides in invalid_runs:
            with self.subTest(name=name):
                for path in self.logs.glob("*.json"):
                    path.unlink()
                self.write_metadata(name, **overrides)
                completed = self.run_report("smoke")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = self.read_json()
                self.assertFalse(report["overall_success"])
                self.assertEqual(report["metadata_summary"]["valid_files"], 0)

    def test_provenance_must_be_valid_and_match_tested_commit(self):
        invalid_runs = (
            ("missing-source", {"source_commit_sha": "unverified"}),
            ("wrong-source", {"source_commit_sha": "c" * 40}),
            ("wrong-build", {"build_commit": "c" * 40}),
            ("wrong-test-merge", {"test_merge_sha": "c" * 40}),
        )
        for name, overrides in invalid_runs:
            with self.subTest(name=name):
                for path in self.logs.glob("*.json"):
                    path.unlink()
                self.write_metadata(f"smoke-{name}", **overrides)
                completed = self.run_report("smoke")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = self.read_json()
                self.assertFalse(report["overall_success"])
                self.assertEqual(report["metadata_summary"]["valid_files"], 0)
                self.assertIn(name.split("-")[-1], report["metadata_summary"]["errors"][0])

    def test_smoke_fault_is_structurally_valid_but_fails_smoke_evidence(self):
        self.write_metadata("smoke-fault", final_state="FAULT")

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertFalse(report["overall_success"])
        self.assertEqual(report["metadata_summary"]["valid_files"], 1)
        self.assertEqual(report["metadata_summary"]["invalid_files"], 0)

    def test_short_smoke_run_fails_evidence(self):
        self.write_metadata("smoke-short", sim_time_s=0.01)

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(self.read_json()["overall_success"])

    def test_smoke_duration_tolerance_boundary(self):
        for duration, expected in ((7.499, False), (7.5, True)):
            with self.subTest(duration=duration):
                self.write_metadata("smoke-boundary", sim_time_s=duration)
                completed = self.run_report("smoke")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(self.read_json()["overall_success"], expected)

    def test_smoke_extra_metadata_fails_evidence_count(self):
        self.write_metadata("smoke-one")
        self.write_metadata("smoke-two")

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(self.read_json()["overall_success"])

    def test_baseline_missing_or_extra_metadata_fails_evidence_count(self):
        for count in (4, 6):
            with self.subTest(count=count):
                for path in self.logs.glob("*.json"):
                    path.unlink()
                self.write_baseline_batch(count=count)
                self.output.mkdir(exist_ok=True)
                (self.output / "standing_baseline_report.json").write_text(
                    json.dumps(
                        {
                            "pass": True,
                            "passing": 5,
                            "count": 5,
                            "unique_run_ids": True,
                            "same_mode": True,
                        }
                    ),
                    encoding="utf-8",
                )
                completed = self.run_report("baseline")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertFalse(self.read_json()["overall_success"])

    def test_markdown_table_escapes_metadata_values(self):
        self.write_metadata(
            "smoke-safe|id", mode="base|line<script>[docs](https://bad)*_"
        )

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertIn(r"smoke-safe\|id", markdown)
        self.assertNotIn("<script>", markdown)
        self.assertNotIn("[docs](https://bad)", markdown)

    def test_report_documents_zero_exit_policy(self):
        self.write_metadata("smoke-good")

        completed = self.run_report("smoke")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_json()
        self.assertIn("workflow gate", report["cli_exit_policy"])
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertIn("workflow gate", markdown)

    def test_markdown_code_span_values_cannot_inject_backticks(self):
        self.write_metadata("smoke-good")

        completed = self.run_report("smoke", offline="success`**injected**")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        markdown = (self.output / "ci-report.md").read_text(encoding="utf-8")
        self.assertIn("success&#96;\\*\\*injected\\*\\*", markdown)
        self.assertNotIn("success`**injected**", markdown)


if __name__ == "__main__":
    unittest.main()

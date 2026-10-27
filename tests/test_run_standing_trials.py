"""Webots version provenance discovery tests (offline only)."""
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run_standing_trials import (
    build_native_env,
    read_webots_version,
    require_clean_source_commit,
    verified_provenance,
)
from smoke_webots import build_controller_env


class WebotsVersionTests(unittest.TestCase):
    def test_reads_macos_app_bundle_version(self):
        with tempfile.TemporaryDirectory() as temp:
            contents = Path(temp) / "Webots.app" / "Contents"
            executable = contents / "MacOS" / "webots"
            executable.parent.mkdir(parents=True)
            executable.touch()
            resources = contents / "Resources"
            resources.mkdir()
            (resources / "version.txt").write_text("R2025a38\n", encoding="utf-8")
            self.assertEqual("Webots R2025a38", read_webots_version(str(executable), {}))

    def test_reads_webots_home_version_file(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "webots"
            (home / "resources").mkdir(parents=True)
            (home / "resources" / "version.txt").write_text("R2025a38\n", encoding="utf-8")
            self.assertEqual("Webots R2025a38",
                             read_webots_version("/unused/webots", {"WEBOTS_HOME": str(home)}))

    def test_reads_linux_install_version_next_to_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "webots"
            binary = home / "webots"
            binary.parent.mkdir(parents=True)
            binary.touch()
            resources = home / "resources"
            resources.mkdir()
            (resources / "version.txt").write_text("R2025a38\n", encoding="utf-8")
            self.assertEqual("Webots R2025a38", read_webots_version(str(binary), {}))

    def test_smoke_controller_env_records_version_without_mutating_input(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "webots"
            binary = home / "webots"
            binary.parent.mkdir(parents=True)
            binary.touch()
            resources = home / "resources"
            resources.mkdir()
            (resources / "version.txt").write_text("R2025a38\n", encoding="utf-8")
            original = {"EXISTING": "value"}

            result = build_controller_env(str(binary), original)

            self.assertEqual("Webots R2025a38", result["RL_H25_WEBOTS_VERSION"])
            self.assertEqual("1", result["RL_H25_CONTACT_EVIDENCE"])
            self.assertEqual({"EXISTING": "value"}, original)

    def test_native_trial_env_enables_contact_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "webots"
            binary = home / "webots"
            binary.parent.mkdir(parents=True)
            binary.touch()
            resources = home / "resources"
            resources.mkdir()
            (resources / "version.txt").write_text("R2025a38\n", encoding="utf-8")

            result = build_native_env(str(binary), {})

            self.assertEqual("Webots R2025a38", result["RL_H25_WEBOTS_VERSION"])
            self.assertEqual("1", result["RL_H25_CONTACT_EVIDENCE"])


class WorkflowProvenanceTests(unittest.TestCase):
    def test_local_provenance_overwrites_stale_environment(self):
        head = "a" * 40
        result = verified_provenance(
            {
                "RL_H25_BUILD_COMMIT": "b" * 40,
                "RL_H25_SOURCE_COMMIT_SHA": "c" * 40,
                "RL_H25_TEST_MERGE_SHA": "d" * 40,
            },
            head,
            github_actions=False,
        )
        self.assertEqual(head, result["RL_H25_BUILD_COMMIT"])
        self.assertEqual(head, result["RL_H25_SOURCE_COMMIT_SHA"])
        self.assertEqual(head, result["RL_H25_TEST_MERGE_SHA"])

    def test_ci_provenance_requires_tested_head_but_allows_pr_source(self):
        head = "a" * 40
        source = "b" * 40
        env = {
            "RL_H25_BUILD_COMMIT": head,
            "RL_H25_SOURCE_COMMIT_SHA": source,
            "RL_H25_TEST_MERGE_SHA": head,
        }
        self.assertEqual(
            source,
            verified_provenance(env, head, github_actions=True)["RL_H25_SOURCE_COMMIT_SHA"],
        )
        with self.assertRaisesRegex(RuntimeError, "CI provenance"):
            verified_provenance(
                env | {"RL_H25_TEST_MERGE_SHA": "c" * 40},
                head,
                github_actions=True,
            )

    def test_gate_run_refuses_dirty_worktree(self):
        results = [
            CompletedProcess([], 0, stdout="a" * 40 + "\n", stderr=""),
            CompletedProcess([], 0, stdout=" M tools/example.py\n", stderr=""),
        ]
        with patch("run_standing_trials.subprocess.run", side_effect=results):
            with self.assertRaisesRegex(RuntimeError, "dirty working tree"):
                require_clean_source_commit()

    def test_gate_run_uses_clean_head(self):
        results = [
            CompletedProcess([], 0, stdout="a" * 40 + "\n", stderr=""),
            CompletedProcess([], 0, stdout="", stderr=""),
        ]
        with patch("run_standing_trials.subprocess.run", side_effect=results):
            self.assertEqual("a" * 40, require_clean_source_commit())

    def test_simulation_workflow_exports_exact_source_and_test_sha(self):
        workflow = (ROOT / ".github/workflows/simulation.yml").read_text(encoding="utf-8")
        self.assertIn("RL_H25_BUILD_COMMIT: ${{ github.sha }}", workflow)
        self.assertIn(
            "RL_H25_SOURCE_COMMIT_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
            workflow,
        )
        self.assertIn("RL_H25_TEST_MERGE_SHA: ${{ github.sha }}", workflow)
        self.assertIn(
            '--source-commit-sha "${{ github.event.pull_request.head.sha || github.sha }}"',
            workflow,
        )

    def test_disturbance_workflow_exports_build_source_and_test_sha(self):
        workflow = (ROOT / ".github/workflows/disturbance-pilot.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("RL_H25_BUILD_COMMIT: ${{ github.sha }}", workflow)
        self.assertIn(
            "RL_H25_SOURCE_COMMIT_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
            workflow,
        )
        self.assertIn("RL_H25_TEST_MERGE_SHA: ${{ github.sha }}", workflow)


if __name__ == "__main__":
    unittest.main()

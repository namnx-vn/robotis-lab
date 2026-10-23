"""Webots version provenance discovery tests (offline only)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run_standing_trials import read_webots_version


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


class WorkflowProvenanceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

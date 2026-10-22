"""Check docs organization and guard against broken links (offline)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_docs_links import broken_links


class DocsLinksTests(unittest.TestCase):
    def test_repo_local_markdown_links_resolve(self):
        self.assertEqual([], broken_links(ROOT))

    def test_reports_missing_file_but_skips_external_and_code_fences(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "ok.md").write_text("fine\n", encoding="utf-8")
            (root / "guide.md").write_text(
                "[good](ok.md) [remote](https://example.com) [anchor](#here)\n"
                "```markdown\n[fenced](ignored.md)\n```\n"
                "[broken](missing.md)\n", encoding="utf-8"
            )
            errors = broken_links(root)
            self.assertEqual(1, len(errors))
            self.assertIn("missing.md", errors[0])

    def test_rejects_escape_outside_repo(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "guide.md").write_text("[escape](../elsewhere.md)\n", encoding="utf-8")
            self.assertIn("escapes repo", broken_links(root)[0])


if __name__ == "__main__":
    unittest.main()

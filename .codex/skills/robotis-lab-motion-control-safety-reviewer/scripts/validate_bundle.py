#!/usr/bin/env python3
"""Small, dependency-free check for skill bundle structure (not robotics tests)."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
skill = root / "SKILL.md"
assert skill.exists(), "missing SKILL.md"
text = skill.read_text(encoding="utf-8")
assert text.startswith("---\n"), "missing frontmatter"
parts = text.split("---\n", 2)
assert len(parts) == 3, "unclosed frontmatter"
fm = parts[1]
assert re.search(r"^name: robotis-lab-motion-control-safety-reviewer$", fm, re.M)
assert re.search(r"^description: ", fm, re.M)
assert len(fm.strip()) > 180
for term in ["E_STOP", "watchdog", "AI Intent Adapter", "NOT RUN", "INCONCLUSIVE", "CRITICAL", "NEEDS EVIDENCE", "APPROVE", "BLOCK", "operator", "radians"]:
    assert term.lower() in text.lower(), f"missing invariant: {term}"
for link in re.findall(r"\]\(([^)]+)\)", text):
    if not link.startswith(("https://", "http://", "#")):
        assert (root / link).is_file(), f"broken local link: {link}"
for p in (root / "references").glob("*.md"):
    assert p.read_text(encoding="utf-8").strip(), f"empty: {p}"
assert (root / "assets" / "review-report-template.md").exists()
print("Skill bundle structure: PASS (not a robot or Webots test)")

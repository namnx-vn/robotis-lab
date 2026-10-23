#!/usr/bin/env python3
"""Offline packaging checks for RL-H25 Hardware/BOM/Torque skill; no sim/hardware runs."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
files = [
    "SKILL.md", "references/torque-sizing.md", "references/power-and-safety.md",
    "references/bom-procurement.md", "references/bench-test-gates.md",
    "references/repository-baseline.md", "assets/bom-template.md",
    "assets/task-report-template.md", "scripts/validate_bundle.py",
]
missing = [x for x in files if not (root / x).is_file()]
assert not missing, f"Required missing files: {missing}"
skill = (root / "SKILL.md").read_text(encoding="utf-8")
assert skill.startswith("---\n"), "YAML frontmatter missing"
frontmatter = skill.split("---\n", 2)[1]
assert re.search(r"^name: robotis-lab-hardware-bom-torque-engineer$", frontmatter, re.M)
assert re.search(r"^description:", frontmatter, re.M)
for heading in (
    "Role and intent", "Required repository-first workflow", "Mandatory torque engineering rules",
    "Mandatory electrical and safety rules", "Evidence and BOM status discipline",
    "Required output", "Non-negotiable completion criteria",
):
    assert heading.lower() in skill.lower(), f"Missing core section: {heading}"
for required in ("OWNED", "PLANNED", "VERIFIED", "UNVERIFIED", "BLOCKED", "NOT RUN"):
    assert required in skill
cols = ["Component", "Model", "Quantity", "Voltage", "Torque/Current", "Estimated Cost (VND)", "Source", "Verification Status", "Priority"]
expected = "| " + " | ".join(cols) + " |"
for p in ("assets/bom-template.md", "assets/task-report-template.md"):
    assert expected in (root / p).read_text(encoding="utf-8"), f"Missing/altered BOM columns: {p}"
for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", skill):
    if "://" not in link and not link.startswith("mailto:"):
        assert (root / link).is_file(), f"Broken relative reference: {link}"
for p in root.rglob("*"):
    if p.is_file() and p.suffix in (".md", ".py"):
        p.read_text(encoding="utf-8")
print(f"PASS: validated {len(files)} required files, metadata, BOM headers and internal links")
print("Scope: static skill/package checks only; Webots, servo, PSU and physical tests NOT RUN")

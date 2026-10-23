#!/usr/bin/env python3
"""Standard-library-only validation of this portable Agent Skill bundle."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md", "references/repository-checkpoint.md", "references/acceptance-gates.md",
    "references/test-fault-matrix.md", "references/experiment-methodology.md",
    "references/ci-evidence-playbook.md", "assets/experiment-report-template.md",
    "assets/experiment-metadata.template.json", "assets/experiment-metadata.schema.json",
    "scripts/analyze_telemetry.py", "tests/test_analyze_telemetry.py"
]
for name in REQUIRED:
    path = ROOT / name
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise SystemExit(f"MISSING or EMPTY: {name}")
skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
assert skill.startswith("---\nname: robotis-lab-test-experiment-analysis-engineer\n")
for label in ("PASS", "FAIL", "INCONCLUSIVE", "NOT RUN", "BLOCKED"):
    assert label in skill, label
for link in re.findall(r"\]\((references/[^)]+|assets/[^)]+|scripts/[^)]+)\)", skill):
    assert (ROOT / link).is_file(), f"bad internal reference: {link}"
metadata = json.loads((ROOT / "assets/experiment-metadata.template.json").read_text(encoding="utf-8"))
schema = json.loads((ROOT / "assets/experiment-metadata.schema.json").read_text(encoding="utf-8"))
assert set(schema["required"]) <= set(metadata)
assert metadata["pass_fail_status"] == "NOT RUN"
assert metadata["run_id"] is None and metadata["metrics"] == {}
assert metadata["pass_fail_status"] in schema["properties"]["pass_fail_status"]["enum"]
print(f"PASS: {len(REQUIRED)} required skill files, links and JSON template/schema structure")
try:
    import jsonschema
except ImportError:
    print("NOT RUN: JSON Schema Draft 2020-12 validation (jsonschema dependency unavailable)")
else:
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(metadata)
    print("PASS: JSON Schema draft 2020-12 and metadata template")
print("NOT RUN: Webots/hardware tests (bundle validation only)")

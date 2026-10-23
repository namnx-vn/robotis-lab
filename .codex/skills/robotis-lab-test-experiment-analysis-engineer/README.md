# Robotis Lab — Test & Experiment Analysis Engineer

Portable Agent Skill for evidence-driven validation of RL-H25 in `namnx-vn/robotis-lab`.

## Included

- `SKILL.md` — activation contract, repository-first workflow, scientific/evidence rules, required reports.
- `references/` — phase gates, existing CI/artifact contracts, experimental statistics, 26 normal/fault/regression cases, dated repo checkpoint.
- `assets/` — experiment metadata JSON Schema and null-preserving template; Markdown report template.
- `scripts/analyze_telemetry.py` — conservative offline raw CSV/JSON inspection and metrics. **It cannot certify standing, active balance, gait, native physics or hardware.**
- `tests/test_analyze_telemetry.py` — 11 pytest checks using synthetic temporary fixtures, never physics evidence.
- `scripts/validate_bundle.py` — standard-library bundle structure/link checks.

## Validate this skill bundle

```bash
python3 scripts/validate_bundle.py
python3 -m compileall -q scripts tests
python3 -m pytest -q tests/test_analyze_telemetry.py
```

`pytest` is required only for this bundle's example test suite. The RL-H25 repository currently uses `python3 -m unittest discover -s tests -v`; **do not replace it implicitly**. The bundle itself is not installed into the Robotis Lab repository.

## Offline artifact inspection (illustration, not Webots execution)

```bash
python3 scripts/analyze_telemetry.py \
  --csv /path/to/real-webots-run.csv \
  --metadata /path/to/real-webots-run.json \
  --output /path/to/summary.json
```

The script validates finite samples, timing, run identity, source/version provenance, faults and computes bounded metrics. It intentionally **does not emit a scientific PASS**; the project's own `tools/baseline_report.py` or `tools/disturbance_report.py` plus native contact evidence determine those gates.

No simulator or physical hardware is started by bundle validation. For ongoing CI review, use the connected GitHub tool to retrieve run/artifacts at the **exact** SHA, and read the current `AGENTS.md`, CI workflows and acceptance protocols first.

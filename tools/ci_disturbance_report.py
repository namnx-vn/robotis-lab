#!/usr/bin/env python3
"""Summarize a native Webots disturbance pilot without claiming active balance.

This is CI evidence, not a walking/balance acceptance gate.  A pilot has
one paired baseline/balance trial per direction; the >=3-pair scientific
acceptance gate is intentionally impossible in this workflow.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

ALLOWED_AXES = {("pitch", 1), ("pitch", -1), ("roll", 1), ("roll", -1)}
ALLOWED_RESULTS = {"READY_FOR_FULL", "REVIEW_REQUIRED", "INCONCLUSIVE", "ERROR"}
ALLOWED_RUN_VERDICTS = {"RECOVERED", "FAIL", "INCONCLUSIVE", "INVALID"}
REPORT_NAME = "balance-pilot-ci-report"


def analyze_pilot(source: Path | None, *, commit_sha: str, run_url: str) -> dict[str, Any]:
    problems: list[str] = []
    cases: list[dict[str, Any]] = []
    matrix_gate = "NOT_RUN"
    if source is None:
        problems.append("no_balance_matrix_report")
    else:
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("matrix_root_not_object")
            matrix_gate = str(raw.get("gate", "MISSING"))
            if raw.get("schema_version") != 1 or raw.get("pilot") is not True:
                problems.append("invalid_matrix_schema_or_not_pilot")
            settings = raw.get("settings")
            if not isinstance(settings, dict) or settings.get("pairs_per_direction") != 1:
                problems.append("invalid_pilot_pair_count")
            rows = raw.get("cases")
            if not isinstance(rows, list) or len(rows) > 4:
                raise ValueError("invalid_matrix_cases")
            seen: set[tuple[str, int]] = set()
            for item in rows:
                if not isinstance(item, dict):
                    raise ValueError("invalid_case")
                axis, direction = item.get("axis"), item.get("direction")
                if axis not in ("pitch", "roll") or direction not in (-1, 1):
                    raise ValueError("invalid_case_axis")
                key = (axis, direction)
                if key in seen:
                    raise ValueError("duplicate_case")
                seen.add(key)
                status = item.get("status")
                if status not in ALLOWED_RESULTS:
                    problems.append(f"invalid_case_status:{axis}:{direction}")
                entry: dict[str, Any] = {
                    "axis": axis, "direction": direction, "status": status,
                    "runs": {},
                }
                report = item.get("report")
                if status == "ERROR":
                    entry["error"] = str(item.get("error", "unspecified_error"))
                    problems.append(f"runner_error:{axis}:{direction}")
                elif not isinstance(report, dict):
                    problems.append(f"missing_case_report:{axis}:{direction}")
                else:
                    pairs = report.get("pairs")
                    if not isinstance(pairs, list) or len(pairs) != 1:
                        problems.append(f"invalid_case_pairs:{axis}:{direction}")
                    else:
                        pair = pairs[0]
                        if not isinstance(pair, dict) or not pair.get("comparable", False):
                            problems.append(f"noncomparable_pair:{axis}:{direction}")
                        for mode in ("baseline", "balance"):
                            run = pair.get(mode, {}) if isinstance(pair, dict) else {}
                            if not isinstance(run, dict):
                                run = {}
                            verdict = run.get("verdict")
                            if verdict not in ALLOWED_RUN_VERDICTS:
                                problems.append(f"invalid_run_verdict:{axis}:{direction}:{mode}")
                            entry["runs"][mode] = {
                                "verdict": verdict,
                                "peak_tilt_change_rad": run.get("peak_tilt_change_rad"),
                                "fault": run.get("fault"),
                                "applied_steps": run.get("applied_steps"),
                                "run_id": run.get("run_id"),
                            }
                cases.append(entry)
            if len(rows) == 4 and seen != ALLOWED_AXES:
                problems.append("incomplete_direction_set")
            if not rows:
                problems.append("no_completed_cases")
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            problems.append(f"unreadable_matrix:{type(exc).__name__}:{exc}")
    # A fault/inconclusive pilot is valuable evidence, not certification.
    # Only missing/broken runner evidence fails the CI infrastructure gate.
    pipeline_ok = bool(cases) and not problems
    all_ready = len(cases) == 4 and all(c["status"] == "READY_FOR_FULL" for c in cases)
    assessment = "READY_FOR_FULL_EXPERIMENT" if all_ready else "REVIEW_EXPERIMENT"
    return {
        "schema_version": 1,
        "kind": "webots-disturbance-pilot",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha, "workflow_run_url": run_url,
        "source_matrix": None if source is None else source.name,
        "experiment_gate": matrix_gate,
        "assessment": assessment if pipeline_ok else "INVALID_EVIDENCE",
        "scientific_balance_certified": False,
        "ci_evidence_ok": pipeline_ok,
        "errors": problems, "cases": cases,
        "caveat": "ONE pair per direction. No certified active balancing or walking. "
                  "A FAULT/INCONCLUSIVE result must be investigated, not silently retried at higher force.",
    }


def write_report(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / (REPORT_NAME + ".json")).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# RL-H25 Webots Controlled Disturbance Pilot",
        "", f"- Commit: `{report['commit_sha']}`",
        f"- Native Webots experiment: **{report['assessment']}**",
        f"- Simulation protocol gate: `{report['experiment_gate']}`",
        f"- Artifact validity: `{'OK' if report['ci_evidence_ok'] else 'INVALID'}`",
        "- Active balance certified: **NO** (pilot cannot qualify)",
        "", "| Direction | Pilot result | Baseline | PID |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        run = row["runs"]
        base = run.get("baseline", {})
        balance = run.get("balance", {})
        lines.append(
            f"| {row['axis']} {row['direction']:+d} | {row['status']} | "
            f"{base.get('verdict', 'n/a')} (peak {base.get('peak_tilt_change_rad', 'n/a')}) | "
            f"{balance.get('verdict', 'n/a')} (peak {balance.get('peak_tilt_change_rad', 'n/a')}) |"
        )
    if report["errors"]:
        lines += ["", "## Evidence errors", *("- " + e for e in report["errors"])]
    lines += ["", "**Interpretation:** " + report["caveat"], ""]
    (output_dir / (REPORT_NAME + ".md")).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", type=Path, default=Path("experiments/logs"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args()
    candidates = sorted(args.logs_dir.glob("balance-matrix-*.json"))
    report = analyze_pilot(candidates[-1] if candidates else None,
                           commit_sha=args.commit_sha, run_url=args.run_url)
    write_report(report, args.output_dir)
    print("PILOT REPORT:", report["assessment"], "evidence_ok=", report["ci_evidence_ok"])
    print("SCIENTIFIC CERTIFICATION: NO")
    # Only fail when the report cannot be relied upon at all. Runner's own
    # expected exit status 1 for a one-pair pilot is handled in GitHub Actions.
    return 0 if report["ci_evidence_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

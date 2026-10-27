#!/usr/bin/env python3
"""Create durable CI summaries from offline checks and Webots artifacts.

After both report files are written, this command intentionally exits zero so
GitHub can upload failure evidence. The workflow's final gate enforces the
recorded overall result.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path
from typing import Any


EXIT_POLICY = (
    "Report generation exits 0 after artifacts are written; the workflow gate "
    "enforces overall success."
)
SMOKE_TARGET_DURATION_S = 8.0
SMOKE_DURATION_TOLERANCE_S = 0.5
SMOKE_MIN_DURATION_S = SMOKE_TARGET_DURATION_S - SMOKE_DURATION_TOLERANCE_S
CONTACT_API = "Node.getContactPoints(includeDescendants=True)"


def _contact_evidence_error(value: Any) -> str | None:
    if not isinstance(value, dict):
        return "missing contact evidence"
    if value.get("api") != CONTACT_API:
        return "unexpected contact evidence API"

    integer_fields = (
        "sample_count",
        "samples_with_contacts",
        "min_contact_count",
        "max_contact_count",
    )
    if any(type(value.get(field)) is not int for field in integer_fields):
        return "invalid contact evidence counts"
    sample_count = value["sample_count"]
    if sample_count < 1 or value["samples_with_contacts"] != sample_count:
        return "contact missing from one or more samples"
    if (
        value["min_contact_count"] < 2
        or value["max_contact_count"] < value["min_contact_count"]
    ):
        return "invalid contact point range"

    node_ids = value.get("contact_solid_node_ids")
    if (
        not isinstance(node_ids, list)
        or len(node_ids) != 2
        or len(set(node_ids)) != 2
        or any(type(node_id) is not int or node_id <= 0 for node_id in node_ids)
    ):
        return "expected exactly two contact solids"
    expected_keys = {str(node_id) for node_id in node_ids}
    observations = value.get("contact_observations_by_solid_node_id")
    samples_by_solid = value.get("samples_by_solid_node_id")
    if not isinstance(observations, dict) or set(observations) != expected_keys:
        return "invalid contact observations by solid"
    if any(type(count) is not int or count < 1 for count in observations.values()):
        return "invalid contact observations by solid"
    if not isinstance(samples_by_solid, dict) or set(samples_by_solid) != expected_keys:
        return "invalid contact samples by solid"
    if any(
        type(count) is not int or count != sample_count
        for count in samples_by_solid.values()
    ):
        return "both contact solids must be present in every sample"
    if any(
        observations[node_id] < samples_by_solid[node_id]
        for node_id in expected_keys
    ):
        return "contact observations conflict with samples by solid"
    total_observations = sum(observations.values())
    if not (
        sample_count * value["min_contact_count"]
        <= total_observations
        <= sample_count * value["max_contact_count"]
    ):
        return "contact observations conflict with point range"

    foot_mapping = value.get("foot_mapping")
    if foot_mapping is not None:
        samples_by_foot = value.get("samples_by_foot")
        if (
            not isinstance(samples_by_foot, dict)
            or set(samples_by_foot) != {"left", "right"}
            or any(type(count) is not int or count != sample_count
                   for count in samples_by_foot.values())
        ):
            return "invalid foot mapping sample counts"
        if foot_mapping == "solid_node_id":
            foot_node_ids = value.get("foot_node_ids")
            if (
                not isinstance(foot_node_ids, dict)
                or set(foot_node_ids) != {"left", "right"}
                or any(type(node_id) is not int or node_id <= 0
                       for node_id in foot_node_ids.values())
                or set(foot_node_ids.values()) != set(node_ids)
            ):
                return "invalid foot mapping"
        elif foot_mapping != "world_x_sign":
            return "invalid foot mapping"

    min_y = value.get("min_world_y_m")
    max_y = value.get("max_world_y_m")
    if (
        isinstance(min_y, bool)
        or not isinstance(min_y, (int, float))
        or isinstance(max_y, bool)
        or not isinstance(max_y, (int, float))
        or not math.isfinite(min_y)
        or not math.isfinite(max_y)
        or min_y > max_y
    ):
        return "invalid contact world-y range"
    return None


def _read_metadata(
    path: Path, profile: str, commit_sha: str, source_commit_sha: str
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{path.name}: {type(error).__name__}"
    if not isinstance(value, dict):
        return None, f"{path.name}: metadata root must be an object"
    run_id = value.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        return None, f"{path.name}: missing run_id"
    if not run_id.startswith(f"{profile}-"):
        return None, f"{path.name}: run_id does not match profile"
    if value.get("result") != "controller_exited":
        return None, f"{path.name}: controller did not exit successfully"
    for field in ("build_commit", "source_commit_sha", "test_merge_sha"):
        sha = value.get(field)
        if not isinstance(sha, str) or re.fullmatch(r"[a-fA-F0-9]{40}", sha) is None:
            return None, f"{path.name}: invalid {field.replace('_', '-')} provenance"
    if value["build_commit"] != commit_sha:
        return None, f"{path.name}: build commit does not match tested commit"
    if value["source_commit_sha"] != source_commit_sha:
        return None, f"{path.name}: source commit does not match expected source"
    if value["test_merge_sha"] != commit_sha:
        return None, f"{path.name}: test-merge commit does not match tested commit"
    final_state = value.get("final_state")
    if not isinstance(final_state, str) or not final_state.strip():
        return None, f"{path.name}: missing final_state"
    mode = value.get("mode")
    if not isinstance(mode, str) or not mode.strip():
        return None, f"{path.name}: missing mode"
    sim_time = value.get("sim_time_s")
    if (
        isinstance(sim_time, bool)
        or not isinstance(sim_time, (int, float))
        or not math.isfinite(sim_time)
        or sim_time <= 0
    ):
        return None, f"{path.name}: invalid sim_time_s"
    contact_error = _contact_evidence_error(value.get("contact_evidence"))
    if contact_error is not None:
        return None, f"{path.name}: {contact_error}"
    return value, None


def _metadata_summary(
    logs_dir: Path, profile: str, commit_sha: str, source_commit_sha: str
) -> dict[str, Any]:
    paths = tuple(sorted(logs_dir.glob(f"{profile}-*.json")))
    parsed = tuple(
        _read_metadata(path, profile, commit_sha, source_commit_sha) for path in paths
    )
    metadata = tuple(value for value, error in parsed if value is not None and error is None)
    errors = tuple(error for _, error in parsed if error is not None)
    runs = [
        {
            "run_id": value.get("run_id"),
            "mode": value.get("mode"),
            "result": value.get("result"),
            "final_state": value.get("final_state"),
            "sim_time_s": value.get("sim_time_s"),
            "build_commit": value.get("build_commit"),
            "source_commit_sha": value.get("source_commit_sha"),
            "test_merge_sha": value.get("test_merge_sha"),
            "contact_sample_count": value["contact_evidence"]["sample_count"],
            "contact_samples_with_contacts": value["contact_evidence"][
                "samples_with_contacts"
            ],
            "contact_solid_node_ids": value["contact_evidence"][
                "contact_solid_node_ids"
            ],
            "contact_min_count": value["contact_evidence"]["min_contact_count"],
            "contact_max_count": value["contact_evidence"]["max_contact_count"],
        }
        for value in metadata
    ]
    return {
        "matched_files": len(paths),
        "valid_files": len(metadata),
        "invalid_files": len(errors),
        "runs": runs,
        "errors": list(errors),
    }


def _baseline_gate(output_dir: Path, profile: str) -> dict[str, Any] | None:
    path = output_dir / "standing_baseline_report.json"
    if profile != "baseline":
        return None
    if not path.exists():
        return {"pass": False, "error": "missing gate report"}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"pass": False, "error": type(error).__name__}
    if not isinstance(value, dict) or not isinstance(value.get("pass"), bool):
        return {"pass": False, "error": "invalid gate summary"}
    passing = value.get("passing")
    count = value.get("count")
    if (
        isinstance(passing, bool)
        or not isinstance(passing, int)
        or isinstance(count, bool)
        or not isinstance(count, int)
        or count != 5
        or not 0 <= passing <= 5
    ):
        return {"pass": False, "error": "invalid gate counts"}
    unique_run_ids = value.get("unique_run_ids")
    same_mode = value.get("same_mode")
    if not isinstance(unique_run_ids, bool) or not isinstance(same_mode, bool):
        return {"pass": False, "error": "invalid gate independence fields"}
    expected_pass = passing >= 4 and unique_run_ids and same_mode
    if value["pass"] is not expected_pass:
        return {"pass": False, "error": "inconsistent gate result"}
    return {
        "pass": value["pass"],
        "passing": passing,
        "count": count,
        "unique_run_ids": unique_run_ids,
        "same_mode": same_mode,
    }


def _metadata_evidence_ok(metadata: dict[str, Any], profile: str) -> bool:
    expected_files = 1 if profile == "smoke" else 5
    correct_count = (
        metadata["matched_files"] == expected_files
        and metadata["valid_files"] == expected_files
        and metadata["invalid_files"] == 0
    )
    if not correct_count:
        return False
    if profile != "smoke":
        return True
    run = metadata["runs"][0]
    return run["final_state"] == "STAND" and run["sim_time_s"] >= SMOKE_MIN_DURATION_S


def _markdown_value(value: Any) -> str:
    markdown_escaped = ("" if value is None else str(value)).replace("\\", "\\\\")
    for character in "|*_[]()":
        markdown_escaped = markdown_escaped.replace(character, f"\\{character}")
    escaped = html.escape(markdown_escaped, quote=True).replace("`", "&#96;")
    return (
        escaped.replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
    )


def _markdown(report: dict[str, Any]) -> str:
    success = "PASS" if report["overall_success"] else "FAIL"
    metadata = report["metadata_summary"]
    lines = [
        "# Robotis Lab CI Report",
        "",
        f"- Overall: **{success}**",
        f"- Profile: `{_markdown_value(report['profile'])}`",
        f"- Commit: `{_markdown_value(report['commit_sha'])}`",
        f"- Workflow run: {_markdown_value(report['run_url'])}",
        f"- Offline checks: `{_markdown_value(report['statuses']['offline'])}`",
        f"- Webots simulation: `{_markdown_value(report['statuses']['simulation'])}`",
        f"- Exit policy: {_markdown_value(report['cli_exit_policy'])}",
        "",
        "## Simulation metadata",
        "",
        f"Matched {metadata['matched_files']} file(s): "
        f"{metadata['valid_files']} valid, {metadata['invalid_files']} invalid.",
    ]
    if metadata["runs"]:
        lines += [
            "",
            "| Run ID | Mode | Result | Final state | Sim time (s) | Source SHA | Tested SHA |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
            *(
                f"| {_markdown_value(run['run_id'])} | {_markdown_value(run['mode'])} | "
                f"{_markdown_value(run['result'])} | {_markdown_value(run['final_state'])} | "
                f"{_markdown_value(run['sim_time_s'])} | "
                f"{_markdown_value(run['source_commit_sha'])} | "
                f"{_markdown_value(run['test_merge_sha'])} |"
                for run in metadata["runs"]
            ),
        ]
        lines += [
            "",
            "## Native contact telemetry",
            "",
            "| Run ID | Contact samples | Contact points/sample | Contact solid IDs |",
            "| --- | ---: | ---: | --- |",
            *(
                f"| {_markdown_value(run['run_id'])} | "
                f"{_markdown_value(run['contact_samples_with_contacts'])}/"
                f"{_markdown_value(run['contact_sample_count'])} | "
                f"{_markdown_value(run['contact_min_count'])}-"
                f"{_markdown_value(run['contact_max_count'])} | "
                f"{_markdown_value(', '.join(str(node_id) for node_id in run['contact_solid_node_ids']))} |"
                for run in metadata["runs"]
            ),
            "",
            "**Scope limitation:** Headless contact telemetry does not prove absence of "
            "artificial anchoring, visual interpenetration or slip; the operator GUI check "
            "remains required.",
        ]
    if metadata["errors"]:
        lines += [
            "",
            "Metadata errors:",
            *(f"- {_markdown_value(error)}" for error in metadata["errors"]),
        ]
    gate = report["baseline_gate"]
    if gate is not None:
        gate_status = "PASS" if gate["pass"] else "FAIL"
        count = (
            f" ({_markdown_value(gate['passing'])}/{_markdown_value(gate['count'])})"
            if gate.get("passing") is not None and gate.get("count") is not None
            else ""
        )
        lines += ["", "## Standing baseline gate", "", f"Gate: **{gate_status}**{count}"]
        if gate.get("error"):
            lines.append(f"Gate report error: {_markdown_value(gate['error'])}")
    if report["profile"] == "smoke":
        lines += ["", "**Scope limitation:** This smoke run does not certify standing stability."]
    else:
        lines += [
            "",
            "**Manual check required:** Baseline telemetry still requires a visual "
            "foot-contact check for slipping and floor penetration.",
        ]
    return "\n".join(lines) + "\n"


def create_report(
    *,
    profile: str,
    offline_status: str,
    simulation_status: str,
    logs_dir: Path,
    output_dir: Path,
    commit_sha: str,
    source_commit_sha: str,
    run_url: str,
) -> dict[str, Any]:
    metadata = _metadata_summary(logs_dir, profile, commit_sha, source_commit_sha)
    gate = _baseline_gate(output_dir, profile)
    metadata_ok = _metadata_evidence_ok(metadata, profile)
    overall = (
        offline_status == "success"
        and simulation_status == "success"
        and metadata_ok
        and (gate is None or gate.get("pass") is True)
    )
    report = {
        "profile": profile,
        "overall_success": overall,
        "statuses": {"offline": offline_status, "simulation": simulation_status},
        "commit_sha": commit_sha,
        "source_commit_sha": source_commit_sha,
        "run_url": run_url,
        "metadata_summary": metadata,
        "baseline_gate": gate,
        "cli_exit_policy": EXIT_POLICY,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ci-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "ci-report.md").write_text(_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=("smoke", "baseline"))
    parser.add_argument("--offline-status", required=True)
    parser.add_argument("--simulation-status", required=True)
    parser.add_argument("--logs-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--source-commit-sha", required=True)
    parser.add_argument("--run-url", required=True)
    args = parser.parse_args()
    report = create_report(
        profile=args.profile,
        offline_status=args.offline_status,
        simulation_status=args.simulation_status,
        logs_dir=args.logs_dir,
        output_dir=args.output_dir,
        commit_sha=args.commit_sha,
        source_commit_sha=args.source_commit_sha,
        run_url=args.run_url,
    )
    print(f"CI report written: {'PASS' if report['overall_success'] else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

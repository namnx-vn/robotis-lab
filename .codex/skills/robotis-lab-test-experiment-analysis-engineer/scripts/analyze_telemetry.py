#!/usr/bin/env python3
"""Conservative offline CSV/JSON telemetry summary, NOT a Webots phase-gate validator.

Does not execute Webots or hardware. Does not assert native physics/contact or
active balance. Always defer scientific PASS to the current project's accepted
native experiment-specific validators and independent contact evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

REQUIRED_COLUMNS = {"run_id", "t_s", "roll_rad", "pitch_rad", "state"}
FAULT_STATES = {"FAULT", "E_STOP", "FALL_DETECTED"}


def _finite_float(raw: str, name: str, index: int) -> float:
    try:
        value = float(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"row {index}: invalid {name}") from exc
    if not math.isfinite(value):
        raise ValueError(f"row {index}: nonfinite {name}")
    return value


def summarize(csv_path: Path, metadata_path: Path | None = None, *, max_gap_s: float = 0.45) -> dict:
    """Read measurements and emit an audit, never an unsupported PASS.

    A valid FAULT/E_STOP is reportable as FAIL for safe-state/standing requirements;
    absence of fault is NOT proof of standing or contact dynamics.
    """
    report: dict = {
        "input_csv": str(csv_path),
        "input_metadata": str(metadata_path) if metadata_path else None,
        "execution_class": "offline_artifact_analysis",
        "metrics": {},
        "data_integrity": "INCONCLUSIVE",
        "pass_fail_status": "INCONCLUSIVE",
        "scientific_acceptance": "INCONCLUSIVE",
        "native_contact_verified": None,
        "warnings": ["This summary does not certify native Webots physics, foot contact, COM, balance or hardware."],
        "errors": [],
    }
    errors: list[str] = report["errors"]
    if not math.isfinite(max_gap_s) or max_gap_s <= 0:
        errors.append("invalid_max_gap_s")
        return report
    try:
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - cols
            if missing:
                errors.append("missing_columns:" + ",".join(sorted(missing)))
                return report
            raw_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append("cannot_read_csv:" + str(exc))
        return report
    if len(raw_rows) < 2:
        errors.append("too_few_rows")
        return report

    rows: list[dict] = []
    try:
        for i, raw in enumerate(raw_rows, start=2):
            run_id, state = raw.get("run_id"), raw.get("state")
            if not run_id or not state:
                raise ValueError(f"row {i}: empty run_id/state")
            row = {"run_id": run_id, "state": state,
                   "t_s": _finite_float(raw.get("t_s"), "t_s", i),
                   "roll_rad": _finite_float(raw.get("roll_rad"), "roll_rad", i),
                   "pitch_rad": _finite_float(raw.get("pitch_rad"), "pitch_rad", i)}
            for optional in ("root_x_m", "root_z_m", "root_height_m"):
                if optional in cols:
                    row[optional] = _finite_float(raw.get(optional), optional, i)
            rows.append(row)
    except ValueError as exc:
        errors.append(str(exc))
        return report

    ids = {r["run_id"] for r in rows}
    if len(ids) != 1:
        errors.append("mixed_run_ids")
    gaps = [b["t_s"] - a["t_s"] for a, b in zip(rows, rows[1:])]
    if any(g <= 0 for g in gaps):
        errors.append("non_monotonic_or_duplicate_timestamps")
    if any(g > max_gap_s for g in gaps):
        errors.append("telemetry_sample_gap_exceeded")

    if metadata_path is None:
        errors.append("missing_run_metadata")
        metadata = None
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if not isinstance(metadata, dict):
                raise ValueError("metadata_must_be_json_object")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            errors.append("invalid_run_metadata:" + str(exc))
            metadata = None
    if metadata is not None:
        if metadata.get("run_id") not in ids:
            errors.append("metadata_run_id_mismatch")
        sha = metadata.get("source_commit_sha") or metadata.get("git_commit")
        if not isinstance(sha, str) or re.fullmatch(r"[a-fA-F0-9]{40}", sha) is None:
            errors.append("missing_verified_git_commit")
        if not isinstance(metadata.get("webots_version"), str) or "R20" not in metadata["webots_version"]:
            errors.append("missing_webots_version")
        if metadata.get("result") not in (None, "controller_exited"):
            errors.append("run_not_completed")
        if metadata.get("result") is None:
            errors.append("run_completion_unverified")
        if not metadata.get("config_sha256") or not metadata.get("world_sha256"):
            errors.append("missing_config_world_hashes")

    if not errors:
        faults = [(r["t_s"], r["state"]) for r in rows if r["state"] in FAULT_STATES]
        metrics: dict = {
            "run_id": rows[0]["run_id"],
            "rows": len(rows),
            "observed_duration_s": round(rows[-1]["t_s"] - rows[0]["t_s"], 6),
            "max_sample_gap_s": round(max(gaps), 6),
            "max_abs_roll_rad": max(abs(r["roll_rad"]) for r in rows),
            "max_abs_pitch_rad": max(abs(r["pitch_rad"]) for r in rows),
            "max_abs_euler_tilt_rad": max(max(abs(r["roll_rad"]), abs(r["pitch_rad"])) for r in rows),
            "fault_event_samples": len(faults),
            "first_fault_t_s": faults[0][0] if faults else None,
            "first_fault_state": faults[0][1] if faults else None,
        }
        if "root_x_m" in rows[0] and "root_z_m" in rows[0]:
            x0, z0 = rows[0]["root_x_m"], rows[0]["root_z_m"]
            metrics["max_root_planar_drift_m"] = max(
                math.hypot(r["root_x_m"] - x0, r["root_z_m"] - z0) for r in rows)
        if "root_height_m" in rows[0]:
            metrics["min_root_height_m"] = min(r["root_height_m"] for r in rows)
        report["metrics"] = metrics
        report["data_integrity"] = "PASS"
        if faults:
            report["pass_fail_status"] = "FAIL"
            report["warnings"].append("FAULT/E_STOP observed; investigate first fault before rerunning.")
        else:
            report["warnings"].append("No FAULT in this telemetry is NOT proof of standing or balance.")
    else:
        report["warnings"].append("Metric acceptance withheld because input data/provenance failed validation.")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--metadata", type=Path)
    ap.add_argument("--max-gap-s", type=float, default=0.45)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    report = summarize(args.csv, args.metadata, max_gap_s=args.max_gap_s)
    encoded = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    print(encoded, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    return 0 if report["data_integrity"] == "PASS" and report["pass_fail_status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

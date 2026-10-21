#!/usr/bin/env python3
"""Standing baseline gate from real Webots CSV, never from a screenshot.

Compatible with Sprint 01 CSV for *diagnosis*, but deliberately refuses a full
PASS if lateral root position is absent. No claims about foot contact or motors.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
from typing import Sequence


def evaluate(path: Path, *, min_s: float = 30., max_tilt: float = 0.20,
             min_height: float = 0.10, max_drift: float = 0.030,
             max_gap_s: float = 0.45) -> dict:
    result = {"file": str(path), "pass": False, "reasons": [], "metrics": {}}
    errors: list[str] = result["reasons"]
    try:
        with path.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except (OSError, UnicodeError, csv.Error) as e:
        errors.append("unreadable_csv:" + type(e).__name__)
        return result
    if len(rows) < 2:
        errors.append("too_few_samples")
        return result
    expected = {"t_s", "state", "roll_rad", "pitch_rad", "root_height_m",
                "root_x_m", "root_z_m", "run_id"}
    missing = sorted(expected - set(rows[0]))
    if missing:
        errors.append("missing_columns:" + ",".join(missing))
        # Sprint01 can be inspected in old analyzer; here no claimed drift PASS.
        if any(col not in rows[0] for col in ("t_s", "state", "roll_rad", "pitch_rad", "root_height_m")):
            return result
    keys = ["t_s", "roll_rad", "pitch_rad", "root_height_m"]
    has_position = all(k in rows[0] for k in ("root_x_m", "root_z_m"))
    if has_position:
        keys += ["root_x_m", "root_z_m"]
    try:
        numeric = {k: [float(r[k]) for r in rows] for k in keys}
    except (ValueError, TypeError, KeyError):
        errors.append("non_numeric_csv")
        return result
    if any(not math.isfinite(v) for a in numeric.values() for v in a):
        errors.append("nonfinite_telemetry")
        return result
    times = numeric["t_s"]
    if any(b <= a for a, b in zip(times, times[1:])):
        errors.append("non_monotonic_time")
    max_gap = max((b - a for a, b in zip(times, times[1:])), default=0.)
    if max_gap > max_gap_s:
        errors.append("telemetry_gap")
    duration = times[-1] - times[0]
    if duration < min_s:
        errors.append("insufficient_duration")
    states = sorted(set(r["state"] for r in rows))
    if states != ["STAND"]:
        errors.append("non_stand_state")
    max_abs_roll = max(abs(v) for v in numeric["roll_rad"])
    max_abs_pitch = max(abs(v) for v in numeric["pitch_rad"])
    if max(max_abs_roll, max_abs_pitch) >= max_tilt:
        errors.append("tilt_exceeded")
    min_root = min(numeric["root_height_m"])
    if min_root < min_height:
        errors.append("root_height_too_low")
    drift = None
    if has_position:
        x, z = numeric["root_x_m"], numeric["root_z_m"]
        drift = max(math.hypot(a-x[0], b-z[0]) for a, b in zip(x, z))
        if drift >= max_drift:
            errors.append("drift_exceeded")
    run_ids = sorted(set(r.get("run_id", "") for r in rows))
    run_id = run_ids[0] if len(run_ids) == 1 else None
    if not run_id:
        errors.append("run_id_missing_or_inconsistent")
    mode = sorted(set(r.get("mode", "legacy") for r in rows))
    if len(mode) != 1:
        errors.append("mode_inconsistent")
    meta_path = path.with_suffix(".json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("run_id") != run_id:
                errors.append("metadata_run_id_mismatch")
            if meta.get("result") != "controller_exited":
                errors.append("controller_run_incomplete")
            if meta.get("fault_injection"):
                errors.append("fault_injected")
            if mode != ["legacy"] and meta.get("mode") != mode[0]:
                errors.append("metadata_mode_mismatch")
        except (ValueError, OSError):
            errors.append("metadata_invalid")
    else:
        errors.append("metadata_missing")
    result.update(run_id=run_id, mode=mode[0] if len(mode) == 1 else None,
                  metrics={"duration_s": round(duration, 3),
                           "max_gap_s": round(max_gap, 4),
                           "max_abs_roll_rad": round(max_abs_roll, 4),
                           "max_abs_pitch_rad": round(max_abs_pitch, 4),
                           "min_height_m": round(min_root, 4),
                           "max_planar_drift_m": None if drift is None else round(drift, 4),
                           "states": states, "samples": len(rows)})
    result["pass"] = not errors
    return result


def evaluate_suite(paths: Sequence[Path], *, min_trials: int = 5, min_passing: int = 4,
                   **kwargs) -> dict:
    trials = [evaluate(path, **kwargs) for path in paths]
    ids = [trial.get("run_id") for trial in trials]
    unique = len(set(ids)) == len(ids) and all(ids)
    modes = [trial.get("mode") for trial in trials]
    same_mode = len(set(modes)) == 1 and all(modes)
    passes = sum(t["pass"] for t in trials)
    return {"pass": len(trials) >= min_trials and passes >= min_passing and unique and same_mode,
            "trials": trials, "count": len(trials), "passing": passes,
            "unique_run_ids": unique, "same_mode": same_mode,
            "requires_visual_foot_contact_check": True,
            "note": "CSV is not proof of contacts, center-of-pressure, external disturbances or hardware balance"}


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze Webots static standing baseline or active balance trials")
    p.add_argument("csv", nargs="+", type=Path)
    p.add_argument("--min-trials", type=int, default=5)
    p.add_argument("--min-passing", type=int, default=4)
    p.add_argument("--min-seconds", type=float, default=30.)
    p.add_argument("--max-tilt", type=float, default=0.20)
    p.add_argument("--max-drift", type=float, default=0.030)
    p.add_argument("--min-height", type=float, default=0.10)
    p.add_argument("--json-output", type=Path)
    a = p.parse_args()
    if not 0 < a.min_passing <= a.min_trials or not 0 < a.min_seconds:
        p.error("invalid acceptance thresholds")
    res = evaluate_suite(a.csv, min_trials=a.min_trials, min_passing=a.min_passing,
                         min_s=a.min_seconds, max_tilt=a.max_tilt,
                         max_drift=a.max_drift, min_height=a.min_height)
    for trial in res["trials"]:
        print(("PASS" if trial["pass"] else "FAIL"), trial["file"],
              trial["metrics"], ",".join(trial["reasons"]))
    print(f"GATE: {'PASS' if res['pass'] else 'FAIL'} | {res['passing']}/{res['count']} "
          f"| distinct run_ids={res['unique_run_ids']} | one mode={res['same_mode']}")
    print("NOTE: visual confirmation of contacts/slipping still required.")
    if a.json_output:
        a.json_output.parent.mkdir(parents=True, exist_ok=True)
        a.json_output.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

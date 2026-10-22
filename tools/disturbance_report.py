#!/usr/bin/env python3
"""Evidence-oriented paired baseline vs PID disturbance analysis.

Do not label PID 'working' if robot never got measurably perturbed.
Requires CSV and matching completed JSON metadata from a real Webots run.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import re
from pathlib import Path


def inspect_run(path: Path, *, intended_mode: str | None = None) -> dict:
    failures: list[str] = []
    out: dict = {"file": str(path), "verdict": "INVALID", "reasons": failures}
    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = set(reader.fieldnames or [])
            required = {"run_id", "t_s", "state", "roll_rad", "pitch_rad", "root_height_m",
                        "root_x_m", "root_z_m", "mode"}
            if not required <= columns:
                raise ValueError("missing_csv_columns: " + ",".join(sorted(required - columns)))
            rows = list(reader)
        meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        dist = meta.get("disturbance")
        if not isinstance(dist, dict):
            raise ValueError("no_disturbance_metadata")
        # A source/matrix without force-method provenance cannot certify P2.2.
        for field in ("source_commit_sha", "config_sha256", "world_sha256"):
            value = meta.get(field, "")
            if not isinstance(value, str) or re.fullmatch(r"[a-fA-F0-9]{40,64}", value) is None:
                raise ValueError("missing_or_invalid_provenance:" + field)
        if (not str(meta.get("webots_version", "")).startswith("Webots R20") or
                dist.get("force_api_mode") != "r2025a_ctypes_force_with_offset"):
            raise ValueError("unverified_webots_build_or_force_api")
        if not 0 < float(meta.get("simulation_timestep_s", 0)) <= 0.05:
            raise ValueError("invalid_simulation_timestep")
        if meta.get("result") != "controller_exited":
            raise ValueError("controller_not_completed")
        if meta.get("fault_injection"):
            raise ValueError("other_fault_injection_enabled")
        if len(rows) < 20:
            raise ValueError("too_few_samples")
        mode = meta.get("mode")
        if mode not in ("baseline", "balance") or (intended_mode and mode != intended_mode):
            raise ValueError("invalid_mode")
        if {r["run_id"] for r in rows} != {meta["run_id"]} or {r["mode"] for r in rows} != {mode}:
            raise ValueError("run_id_or_mode_mismatch")
        numeric_cols = ("t_s", "roll_rad", "pitch_rad", "root_height_m", "root_x_m", "root_z_m")
        data = [{k: float(r[k]) for k in numeric_cols} | {"state": r["state"]} for r in rows]
        if not all(math.isfinite(r[k]) for r in data for k in numeric_cols):
            raise ValueError("nonfinite_telemetry")
        times = [r["t_s"] for r in data]
        if any(b <= a or b-a > 0.15 for a,b in zip(times, times[1:])):
            raise ValueError("telemetry_gap_or_out_of_order")
        onset = float(dist["onset_s"])
        duration = float(dist["pulse_s"])
        force = float(dist["force_n"])
        offset = float(dist["offset_m"])
        applied = int(dist["applied_steps"])
        axis = dist["axis"]
        if (axis not in ("pitch", "roll") or not 0.01 <= force <= 0.35 or
                not 0.016 <= duration <= 0.20 or not 0 <= offset <= 0.06 or
                not 2 <= onset <= 15 or applied < 1 or
                dist["first_application_s"] is None or
                abs(float(dist["first_application_s"])-onset) > 0.05):
            raise ValueError("invalid_or_unapplied_force")
        if times[-1] < onset + duration + 5.0:
            raise ValueError("insufficient_post_pulse_log")
        before = [r for r in data if onset - 1.0 <= r["t_s"] < onset - 0.1]
        after = [r for r in data if onset <= r["t_s"] <= onset + duration + 5.0]
        if len(before) < 5 or len(after) < 15:
            raise ValueError("missing_pre_post_samples")
        if any(abs(r[axis + "_rad"]) >= 0.08 for r in before):
            raise ValueError("nonupright_pre_pulse")
        if any(r["root_height_m"] < 0.10 for r in before):
            raise ValueError("root_too_low_before_pulse")
        initial_angle = sum(r[axis + "_rad"] for r in before) / len(before)
        amp = [abs(r[axis + "_rad"] - initial_angle) for r in after]
        other_axis = "roll" if axis == "pitch" else "pitch"
        other_initial = sum(r[other_axis + "_rad"] for r in before) / len(before)
        cross_peak = max(abs(r[other_axis + "_rad"] - other_initial) for r in after)
        peak = max(amp)
        peak_idx = max(range(len(amp)), key=amp.__getitem__)
        fault_rows = [r for r in data if r["state"] != "STAND"]
        fault = bool(fault_rows)
        first_fault_s = fault_rows[0]["t_s"] if fault_rows else None
        min_height = min(r["root_height_m"] for r in data)
        x0, z0 = before[0]["root_x_m"], before[0]["root_z_m"]
        drift = max(math.hypot(r["root_x_m"]-x0, r["root_z_m"]-z0) for r in data)
        settle = None
        # The return must stay inside 0.025 rad for at least 0.8s after peak.
        for i in range(peak_idx+1, len(after)):
            if amp[i] > 0.025:
                continue
            until = after[i]["t_s"] + 0.8
            tail = [j for j in range(i,len(after)) if after[j]["t_s"] <= until]
            if tail and after[tail[-1]]["t_s"] >= until-0.07 and all(amp[j] <= 0.025 for j in tail):
                settle = round(after[i]["t_s"] - onset, 3)
                break
        observed = peak >= 0.008
        out.update(run_id=meta["run_id"], mode=mode, axis=axis, direction=int(dist["direction"]),
                   force_n=force, pulse_s=duration, onset_s=onset, offset_m=offset,
                   applied_steps=applied, peak_tilt_change_rad=round(peak, 5),
                   max_planar_drift_m=round(drift, 5), min_root_height_m=round(min_height, 5),
                   settled_after_onset_s=settle, fault=fault,
                   first_fault_s=first_fault_s,
                   cross_axis_peak_change_rad=round(cross_peak, 6),
                   peak_signed_tilt_change_rad=round(
                       after[peak_idx][axis + "_rad"] - initial_angle, 6),
                   source_commit_sha=meta["source_commit_sha"],
                   test_merge_sha=meta.get("test_merge_sha", "unverified"),
                   config_sha256=meta["config_sha256"], world_sha256=meta["world_sha256"],
                   webots_version=meta["webots_version"],
                   force_api_mode=dist["force_api_mode"],
                   simulation_timestep_s=meta["simulation_timestep_s"],
                   duration_s=round(times[-1]-times[0],3))
        if fault or min_height < 0.10 or drift >= 0.10:
            out["verdict"] = "FAIL"
            failures.append("fault_fall_or_large_drift")
        elif not observed:
            out["verdict"] = "INCONCLUSIVE"
            failures.append("no_measurable_excitation")
        elif settle is None:
            out["verdict"] = "FAIL"
            failures.append("did_not_settle_in_5s")
        else:
            out["verdict"] = "RECOVERED"
    except (OSError, KeyError, ValueError, TypeError, csv.Error, json.JSONDecodeError) as exc:
        failures.append(str(exc))
    return out


def compare_pairs(pairs: list[tuple[Path, Path]]) -> dict:
    reports = []
    for b, c in pairs:
        base = inspect_run(b, intended_mode="baseline")
        balance = inspect_run(c, intended_mode="balance")
        compatible = (all(k in base and k in balance and base[k] == balance[k]
                          for k in ("axis", "direction", "force_n", "pulse_s", "onset_s", "offset_m",
                                    "source_commit_sha", "config_sha256", "world_sha256",
                                    "webots_version", "force_api_mode", "simulation_timestep_s"))
                      and abs(base.get("applied_steps", -999)-balance.get("applied_steps", 999)) <= 1)
        reports.append({"baseline": base, "balance": balance, "comparable": compatible})
    ids = [v[mode].get("run_id") for v in reports for mode in ("baseline", "balance")]
    distinct = len(ids) == len(set(ids)) and all(ids)
    valid = [p for p in reports if p["comparable"] and
             p["baseline"]["verdict"] in ("RECOVERED", "FAIL") and
             p["balance"]["verdict"] in ("RECOVERED", "FAIL")]
    # Success requires at least 3 pairs (5 preferred), all balance recover,
    # and a measurable improvement in peak response, not merely STAND once.
    if len(valid) < 3 or len(valid) != len(pairs) or not distinct:
        verdict = "INCONCLUSIVE"
    elif any(p[mode]["verdict"] != "RECOVERED" for p in valid
             for mode in ("baseline", "balance")):
        verdict = "FAIL"
    else:
        base_mean = sum(p["baseline"]["peak_tilt_change_rad"] for p in valid) / len(valid)
        balance_mean = sum(p["balance"]["peak_tilt_change_rad"] for p in valid) / len(valid)
        verdict = "IMPROVED" if balance_mean <= 0.9 * base_mean else "NO_DEMONSTRATED_IMPROVEMENT"
    return {"verdict": verdict, "comparable_pairs": len(valid), "total_pairs": len(pairs), "distinct_run_ids": bool(distinct), "pairs": reports,
            "note": "Quantitative sim-only result; real hardware balance and foot contacts not proven."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pair", nargs=2, metavar=("BASELINE.csv", "BALANCE.csv"), action="append", required=True)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    result = compare_pairs([(Path(a), Path(b)) for a,b in args.pair])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return 0 if result["verdict"] == "IMPROVED" else 1

if __name__ == "__main__":
    raise SystemExit(main())

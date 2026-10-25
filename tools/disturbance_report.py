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
                        "root_x_m", "root_z_m", "mode",
                        "root_angular_velocity_x_rad_s", "root_angular_velocity_y_rad_s",
                        "root_angular_velocity_z_rad_s", "root_com_x_m", "root_com_y_m",
                        "root_com_z_m", "static_balance", "gyro_x_rad_s",
                        "gyro_y_rad_s", "gyro_z_rad_s", "root_velocity_x_m_s",
                        "root_velocity_y_m_s", "root_velocity_z_m_s",
                        "pitch_correction_rad", "roll_correction_rad"}
            if not required <= columns:
                raise ValueError("missing_csv_columns: " + ",".join(sorted(required - columns)))
            target_bases = {name.removesuffix("_target_rad") for name in columns
                            if name.endswith("_target_rad")}
            measured_bases = {name.removesuffix("_measured_rad") for name in columns
                              if name.endswith("_measured_rad")}
            torque_bases = {name.removesuffix("_torque_feedback_nm") for name in columns
                            if name.endswith("_torque_feedback_nm")}
            if (len(target_bases) != 10 or target_bases != measured_bases or
                    target_bases != torque_bases):
                raise ValueError("missing_or_mismatched_actuator_observability")
            actuator_columns = tuple(
                f"{name}_{suffix}" for name in sorted(target_bases)
                for suffix in ("target_rad", "measured_rad", "torque_feedback_nm")
            )
            rows = list(reader)
        meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        dist = meta.get("disturbance")
        if not isinstance(dist, dict):
            raise ValueError("no_disturbance_metadata")
        # A source/matrix without force-method provenance cannot certify P2.2.
        for field in ("build_commit", "source_commit_sha", "test_merge_sha",
                      "config_sha256", "world_sha256"):
            value = meta.get(field, "")
            if not isinstance(value, str) or re.fullmatch(r"[a-fA-F0-9]{40,64}", value) is None:
                raise ValueError("missing_or_invalid_provenance:" + field)
        if (meta.get("software_version") != "rlh25-v0.2" or
                meta.get("telemetry_schema_version") != 2 or
                not math.isclose(float(meta.get("log_period_s", 0)), 0.016,
                                 rel_tol=0.0, abs_tol=1e-9)):
            raise ValueError("invalid_controller_version_or_log_period")
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
        contact = meta.get("contact_evidence")
        if not isinstance(contact, dict):
            raise ValueError("missing_contact_evidence")
        try:
            contact_samples = int(contact["sample_count"])
            samples_with_contacts = int(contact["samples_with_contacts"])
            min_contact_count = int(contact["min_contact_count"])
            max_contact_count = int(contact["max_contact_count"])
            contact_ids = contact["contact_solid_node_ids"]
            samples_by_solid = contact["samples_by_solid_node_id"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_contact_evidence") from exc
        if (contact_samples != len(rows) or contact_samples <= 0 or
                not isinstance(contact_ids, list) or
                not all(type(node_id) is int for node_id in contact_ids) or
                not isinstance(samples_by_solid, dict) or
                min_contact_count < 0 or max_contact_count < min_contact_count):
            raise ValueError("invalid_contact_evidence")
        foot_mapping = contact.get("foot_mapping")
        samples_by_foot = contact.get("samples_by_foot")
        if (foot_mapping != "world_x_sign"
                or not isinstance(samples_by_foot, dict)):
            raise ValueError("missing_explicit_foot_mapping")
        continuous_two_foot_contact = (
            samples_with_contacts == contact_samples
            and min_contact_count > 0
            and len(contact_ids) == 2
            and len(set(contact_ids)) == 2
            and all(samples_by_solid.get(str(node_id)) == contact_samples
                    for node_id in contact_ids)
            and all(samples_by_foot.get(name) == contact_samples
                    for name in ("left", "right"))
        )
        mode = meta.get("mode")
        if mode not in ("baseline", "balance") or (intended_mode and mode != intended_mode):
            raise ValueError("invalid_mode")
        if {r["run_id"] for r in rows} != {meta["run_id"]} or {r["mode"] for r in rows} != {mode}:
            raise ValueError("run_id_or_mode_mismatch")
        numeric_cols = ("t_s", "roll_rad", "pitch_rad", "root_height_m", "root_x_m",
                        "root_z_m", "root_angular_velocity_x_rad_s",
                        "root_angular_velocity_y_rad_s", "root_angular_velocity_z_rad_s",
                        "root_com_x_m", "root_com_y_m", "root_com_z_m",
                        "gyro_x_rad_s", "gyro_y_rad_s", "gyro_z_rad_s",
                        "root_velocity_x_m_s", "root_velocity_y_m_s",
                        "root_velocity_z_m_s", "pitch_correction_rad",
                        "roll_correction_rad") + actuator_columns
        data = []
        for row in rows:
            if row["static_balance"] not in ("True", "False"):
                raise ValueError("invalid_static_balance_value")
            data.append({k: float(row[k]) for k in numeric_cols} |
                        {"state": row["state"],
                         "static_balance": row["static_balance"] == "True"})
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
        direction = dist["direction"]
        direction_valid = type(direction) is int and direction in (-1, 1)
        expected_force = (
            [direction * force, 0.0, 0.0] if axis == "roll"
            else [0.0, 0.0, direction * force]
        ) if direction_valid else None
        world_force = dist.get("world_force_n")
        force_vector_valid = (
            expected_force is not None
            and isinstance(world_force, list)
            and len(world_force) == 3
            and all(
                math.isfinite(float(actual))
                and math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-9)
                for actual, expected in zip(world_force, expected_force)
            )
        )
        if (axis not in ("pitch", "roll") or
                not direction_valid or not force_vector_valid or
                not 0.01 <= force <= 0.35 or
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
        signed_peak = after[peak_idx][axis + "_rad"] - initial_angle
        first_measurable_signed = next(
            (r[axis + "_rad"] - initial_angle for r in after
             if abs(r[axis + "_rad"] - initial_angle) >= 0.008),
            None,
        )
        fault_rows = [r for r in data if r["state"] != "STAND"]
        fault = bool(fault_rows)
        first_fault_s = fault_rows[0]["t_s"] if fault_rows else None
        min_height = min(r["root_height_m"] for r in data)
        x0, z0 = before[0]["root_x_m"], before[0]["root_z_m"]
        drift = max(math.hypot(r["root_x_m"]-x0, r["root_z_m"]-z0) for r in data)
        settle = None
        # The return must stay inside both the absolute 0.025 rad band and
        # 50% of this run's observed peak for at least 0.8 s after the peak.
        # The relative predicate prevents a 0.008..0.025 rad excitation from
        # being called recovered without any meaningful decay.
        recovery_limit = min(0.025, 0.5 * peak)
        for i in range(peak_idx+1, len(after)):
            if amp[i] > recovery_limit:
                continue
            until = after[i]["t_s"] + 0.8
            tail = [j for j in range(i,len(after)) if after[j]["t_s"] <= until]
            if (tail and after[tail[-1]]["t_s"] >= until-0.07 and
                    all(amp[j] <= recovery_limit for j in tail)):
                settle = round(after[i]["t_s"] - onset, 3)
                break
        observed = first_measurable_signed is not None
        axis_actuators = [name for name in target_bases
                          if axis in name and ("hip" in name or "ankle" in name)]
        correction_peak = max(abs(r[axis + "_correction_rad"]) for r in after)
        pre_target = {name: sum(r[f"{name}_target_rad"] for r in before) / len(before)
                      for name in target_bases}
        target_excursion = max(
            (abs(r[f"{name}_target_rad"] - pre_target[name]) for r in after
             for name in axis_actuators), default=0.0)
        measured_excursion = max(
            (abs(r[f"{name}_measured_rad"] - pre_target[name]) for r in after
             for name in axis_actuators), default=0.0)
        actuation_evidence = (mode == "baseline" or
                              (correction_peak >= 1e-7 and
                               target_excursion >= 1e-7 and
                               measured_excursion >= 1e-9))
        out.update(run_id=meta["run_id"], mode=mode, axis=axis, direction=direction,
                   force_n=force, pulse_s=duration, onset_s=onset, offset_m=offset,
                   applied_steps=applied, peak_tilt_change_rad=round(peak, 5),
                   max_planar_drift_m=round(drift, 5), min_root_height_m=round(min_height, 5),
                   settled_after_onset_s=settle, fault=fault,
                   first_fault_s=first_fault_s,
                   cross_axis_peak_change_rad=round(cross_peak, 6),
                   peak_signed_tilt_change_rad=round(signed_peak, 6),
                   first_measurable_signed_tilt_change_rad=(
                       round(first_measurable_signed, 6) if observed else None),
                   build_commit=meta["build_commit"],
                   source_commit_sha=meta["source_commit_sha"],
                   test_merge_sha=meta["test_merge_sha"],
                   config_sha256=meta["config_sha256"], world_sha256=meta["world_sha256"],
                   software_version=meta["software_version"],
                   telemetry_schema_version=meta["telemetry_schema_version"],
                   log_period_s=meta["log_period_s"],
                   webots_version=meta["webots_version"],
                   force_api_mode=dist["force_api_mode"],
                   simulation_timestep_s=meta["simulation_timestep_s"],
                   contact_sample_count=contact_samples,
                   continuous_two_foot_contact=continuous_two_foot_contact,
                   actuation_evidence=actuation_evidence,
                   static_balance_all_samples=all(r["static_balance"] for r in data),
                   duration_s=round(times[-1]-times[0],3))
        if fault or min_height < 0.10 or drift >= 0.10:
            out["verdict"] = "FAIL"
            failures.append("fault_fall_or_large_drift")
        elif not continuous_two_foot_contact:
            out["verdict"] = "FAIL"
            failures.append("contact_or_support_loss")
        elif not actuation_evidence:
            out["verdict"] = "INCONCLUSIVE"
            failures.append("no_balance_actuation_evidence")
        elif not observed:
            out["verdict"] = "INCONCLUSIVE"
            failures.append("no_measurable_excitation")
        elif direction * first_measurable_signed <= 0:
            out["verdict"] = "FAIL"
            failures.append("wrong_signed_response")
        elif settle is None:
            out["verdict"] = "FAIL"
            failures.append("did_not_recover_from_peak")
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
                                    "build_commit", "source_commit_sha", "test_merge_sha",
                                    "config_sha256", "world_sha256", "software_version",
                                    "telemetry_schema_version",
                                    "log_period_s", "webots_version", "force_api_mode",
                                    "simulation_timestep_s"))
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

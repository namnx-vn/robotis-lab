#!/usr/bin/env python3
"""Four-direction, paired Webots balance verification. Never controls real hardware.

The pilot uses exactly one pair per direction and cannot pass a recovery gate.
A full gate requires >=3 comparable pairs for *every* pitch/roll direction.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import shutil
import sys

from disturbance_report import compare_pairs
from run_standing_trials import LOGDIR, trial

CASES = (("pitch", 1), ("pitch", -1), ("roll", 1), ("roll", -1))


def validate_experiment(*, pairs: int, force: float, pulse: float,
                        onset: float, duration: float, timeout: float) -> None:
    if pairs not in (1, 3, 4, 5):
        raise ValueError("--pairs must be 1 (pilot) or 3..5 (full gate)")
    if not all(math.isfinite(v) for v in (force, pulse, onset, duration, timeout)):
        raise ValueError("all numeric settings must be finite")
    if not (0.01 <= force <= 0.35 and 0.016 <= pulse <= 0.20):
        raise ValueError("force/pulse outside bounded simulation limits")
    if not (2.0 <= onset <= 15.0 and onset + pulse + 6 <= duration <= 60.0):
        raise ValueError("run duration must provide >=6s post-pulse observation, <=60s")
    if timeout <= 0:
        raise ValueError("--timeout must be positive")


def classify_case(report: dict, *, pilot: bool) -> str:
    """No optimistic pass for absent excitation or missing/invalid trials."""
    pair_rows = report.get("pairs", [])
    if not pair_rows:
        return "INCONCLUSIVE"
    for row in pair_rows:
        if not row.get("comparable", False):
            return "INCONCLUSIVE"
        b, c = row.get("baseline", {}), row.get("balance", {})
        if b.get("verdict") in ("INVALID", "INCONCLUSIVE") or c.get("verdict") in ("INVALID", "INCONCLUSIVE"):
            return "INCONCLUSIVE"
        if b.get("verdict") == "FAIL" or c.get("verdict") == "FAIL":
            return "REVIEW_REQUIRED"
    if pilot:
        return "READY_FOR_FULL" if len(pair_rows) == 1 else "INCONCLUSIVE"
    if not report.get("distinct_run_ids", False) or report.get("comparable_pairs", 0) < 3:
        return "INCONCLUSIVE"
    return report["verdict"] if report.get("verdict") == "IMPROVED" else "NOT_ESTABLISHED"


def overall_gate(cases: list[dict], *, pilot: bool) -> str:
    if len(cases) != len(CASES) or {(r["axis"], r["direction"]) for r in cases} != set(CASES):
        return "INCOMPLETE"
    outcomes = {r["status"] for r in cases}
    if pilot:
        return "READY_FOR_FULL" if outcomes == {"READY_FOR_FULL"} else "REVIEW_REQUIRED"
    return "PASS" if outcomes == {"IMPROVED"} else "NOT_ESTABLISHED"


def run_matrix(*, executable: str, pairs: int, force: float, pulse: float,
               onset: float, duration: float, timeout: float, graphics: bool = False,
               stop_on_concern: bool = True) -> dict:
    validate_experiment(pairs=pairs, force=force, pulse=pulse, onset=onset,
                        duration=duration, timeout=timeout)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    for axis, direction in CASES:
        env = {
            "RL_H25_DISTURBANCE": "1", "RL_H25_DIST_AXIS": axis,
            "RL_H25_DIST_DIRECTION": str(direction),
            "RL_H25_DIST_FORCE_N": str(force),
            "RL_H25_DIST_PULSE_S": str(pulse),
            "RL_H25_DIST_ONSET_S": str(onset),
            "RL_H25_DIST_OFFSET_M": "0.04",
            "RL_H25_LOG_PERIOD_S": "0.016",
        }
        files = []
        try:
            for i in range(pairs):
                base = trial(executable, mode="baseline", sim_duration_s=duration,
                             timeout_s=timeout, number=i + 1, graphics=graphics, extra_env=env)
                balanced = trial(executable, mode="balance", sim_duration_s=duration,
                                 timeout_s=timeout, number=i + 1, graphics=graphics, extra_env=env)
                files.append((base, balanced))
        except Exception as exc:
            entries.append({"axis": axis, "direction": direction, "status": "ERROR",
                            "error": str(exc), "completed_pairs": len(files)})
            break
        report = compare_pairs(files)
        status = classify_case(report, pilot=pairs == 1)
        entries.append({"axis": axis, "direction": direction,
                        "status": status, "report": report})
        print(f"MATRIX {axis:5} {direction:+d}: {status}", flush=True)
        if stop_on_concern and status in ("REVIEW_REQUIRED", "INCONCLUSIVE", "ERROR"):
            print("Stopping before next axis: inspect individual CSV/JSON telemetry.", flush=True)
            break
    result = {
        "schema_version": 1, "protocol": "rlh25-v0.2.2-paired-disturbance-matrix",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "pilot": pairs == 1,
        "settings": {"pairs_per_direction": pairs, "force_n": force,
                     "pulse_s": pulse, "onset_s": onset,
                     "duration_s": duration, "offset_m": 0.04},
        "cases": entries, "gate": overall_gate(entries, pilot=pairs == 1),
        "caveat": "Webots simulation only. Contact, torque, sensor noise and hardware not certified."
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--webots", default="webots", help="e.g. /Applications/Webots.app/Contents/MacOS/webots")
    ap.add_argument("--pairs", type=int, default=1, help="1=pilot; 3..5=full gate")
    ap.add_argument("--force", type=float, default=0.10)
    ap.add_argument("--pulse", type=float, default=0.112)
    ap.add_argument("--onset", type=float, default=4.0)
    ap.add_argument("--duration", type=float, default=14.0)
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--graphics", action="store_true")
    ap.add_argument("--continue-on-concern", action="store_true",
                    help="Continue remaining axes after unexpected fault/inconclusive result")
    ap.add_argument("--dry-run", action="store_true", help="Validate/print protocol; no Webots subprocesses")
    args = ap.parse_args()
    try:
        validate_experiment(pairs=args.pairs, force=args.force, pulse=args.pulse,
                            onset=args.onset, duration=args.duration, timeout=args.timeout)
    except ValueError as exc:
        ap.error(str(exc))
    if args.dry_run:
        print(json.dumps({"cases": CASES, "pairs": args.pairs, "force_n": args.force,
                          "pulse_s": args.pulse, "onset_s": args.onset,
                          "duration_s": args.duration, "native_webots": "NOT_RUN"}, indent=2))
        return 0
    binary = shutil.which(args.webots)
    if not binary:
        print("ERROR: Webots executable missing; use --webots absolute macOS binary path", file=sys.stderr)
        return 2
    result = run_matrix(executable=binary, pairs=args.pairs, force=args.force,
                        pulse=args.pulse, onset=args.onset, duration=args.duration,
                        timeout=args.timeout, graphics=args.graphics,
                        stop_on_concern=not args.continue_on_concern)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = LOGDIR / f"balance-matrix-{stamp}.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("MATRIX GATE:", result["gate"])
    print("REPORT:", destination)
    # Pilot is intentionally NOT certification; do not exit 0 for only one pair.
    return 0 if result["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

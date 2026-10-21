#!/usr/bin/env python3
"""Evaluate logged *simulated* neutral stance using only observed CSV samples.

Exit 0 only if all supplied trials pass. Run 5 independent reset trials for the
P2 gate; Sprint 01 doesn't claim this acceptance gate.
"""
from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path


def summarize(path: Path, min_seconds: float = 30.0) -> dict:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    if len(rows) < 2:
        return {"file": path.name, "pass": False, "reason": "too_few_samples"}
    try:
        time_s = [float(row["t_s"]) for row in rows]
        roll = [float(row["roll_rad"]) for row in rows]
        pitch = [float(row["pitch_rad"]) for row in rows]
        heights = [float(row["root_height_m"]) for row in rows]
    except (KeyError, ValueError) as error:
        return {"file": path.name, "pass": False, "reason": str(error)}
    finite = all(math.isfinite(value) for arr in (time_s, roll, pitch, heights) for value in arr)
    if not finite:
        return {"file": path.name, "pass": False, "reason": "nonfinite_telemetry"}
    duration = time_s[-1] - time_s[0]
    max_tilt = max(abs(value) for value in roll + pitch)
    min_height = min(heights)
    states = sorted(set(row["state"] for row in rows))
    passed = duration >= min_seconds and max_tilt < 0.45 and min_height >= 0.10 and states == ["STAND"]
    return {"file": path.name, "pass": passed, "duration_s": round(duration, 3),
            "max_abs_tilt_rad": round(max_tilt, 4), "min_height_m": round(min_height, 4),
            "observed_states": states}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="+", type=Path)
    parser.add_argument("--min-seconds", default=30.0, type=float)
    args = parser.parse_args()
    results = [summarize(file, args.min_seconds) for file in args.csv]
    for res in results:
        print("PASS" if res["pass"] else "FAIL", res)
    if len(args.csv) < 5:
        print("NOTE: P2 reliability gate needs at least five independent Webots reset trials.")
    return 0 if all(x["pass"] for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

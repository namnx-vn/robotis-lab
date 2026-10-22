#!/usr/bin/env python3
"""Run native Webots free-body force probe; write fail-closed JSON and simulator log."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "simulation/webots/worlds/force_api_probe.wbt"
PREFIX = "FORCE_API_PROBE_RESULT="


def parse_probe_log(text: str) -> dict:
    lines = [line.partition(PREFIX)[2].strip() for line in text.splitlines() if PREFIX in line]
    if len(lines) != 1:
        raise ValueError("expected exactly one native probe result")
    result = json.loads(lines[0])
    expected = {"pitch_plus", "pitch_minus", "roll_plus", "roll_minus",
                "pitch_zero_offset", "roll_zero_offset",
                "yaw_rotated_world_force", "rotated_local_offset"}
    cases = result.get("results", [])
    if (result.get("pass") is not True or result.get("gravity_observed") is not True or
            result.get("force_api_mode") != "r2025a_ctypes_force_with_offset" or
            len(cases) != len(expected) or {r.get("case") for r in cases} != expected or
            any(r.get("pass") is not True for r in cases)):
        raise ValueError("native force ABI or frame/physics check failed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--webots", default="webots")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    binary = shutil.which(args.webots)
    if not binary or args.timeout <= 0:
        parser.error("valid Webots executable and positive timeout required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    command = [binary, "--stdout", "--stderr", "--batch", "--mode=fast",
               "--no-rendering", str(WORLD)]
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        xvfb = shutil.which("xvfb-run")
        if not xvfb:
            raise RuntimeError("headless Linux needs xvfb-run")
        command = [xvfb, "-a"] + command
    timed_out = False
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
        stdout = proc.stdout + "\n" + proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or b"").decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stdout += "\nTIMEOUT"
    (args.output_dir / "force-api-probe.log").write_text(stdout, encoding="utf-8")
    try:
        outcome = parse_probe_log(stdout)
        if timed_out:
            raise ValueError("native Webots process timed out even though it emitted a result")
        if proc.returncode != 0:
            raise ValueError("native Webots returned nonzero status: " + str(proc.returncode))
        (args.output_dir / "force-api-probe.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    except (ValueError, json.JSONDecodeError) as exc:
        print("FORCE API PROBE NOT ACCEPTED:", exc, file=sys.stderr)
        return 1
    print("Native free-body force API probe PASS:", len(outcome["results"]), "cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

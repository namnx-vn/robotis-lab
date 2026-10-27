#!/usr/bin/env python3
"""Run native Webots free-body force/torque probe with fail-closed evidence."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys

from run_standing_trials import (read_webots_version, require_clean_source_commit,
                                 verified_provenance)

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "simulation/webots/worlds/force_api_probe.wbt"
PREFIX = "FORCE_API_PROBE_RESULT="


def build_probe_env(binary: str, base_env: dict[str, str], head: str, *,
                    github_actions: bool) -> dict[str, str]:
    env = verified_provenance(base_env, head, github_actions=github_actions)
    # Never trust a stale caller export for gate evidence.
    env["RL_H25_WEBOTS_VERSION"] = read_webots_version(binary, env)
    return env


def parse_probe_log(text: str) -> dict:
    lines = [line.partition(PREFIX)[2].strip() for line in text.splitlines() if PREFIX in line]
    if len(lines) != 1:
        raise ValueError("expected exactly one native probe result")
    result = json.loads(lines[0])
    if not isinstance(result, dict):
        raise ValueError("native probe result must be an object")
    expected = {"pitch_plus", "pitch_minus", "roll_plus", "roll_minus",
                "pitch_zero_offset", "roll_zero_offset",
                "yaw_rotated_world_force", "rotated_local_offset",
                "torque_pitch_plus", "torque_pitch_minus",
                "torque_roll_plus", "torque_roll_minus",
                "torque_zero", "torque_yaw_rotated_world"}
    cases = result.get("results", [])
    torque_nm = result.get("probe_torque_nm")
    gravity_displacement = result.get("gravity_displacement_m")
    shas = [result.get(field) for field in (
        "build_commit", "source_commit_sha", "test_merge_sha")]
    if (result.get("pass") is not True or result.get("gravity_observed") is not True or
            result.get("force_api_mode") != "r2025a_ctypes_force_with_offset" or
            result.get("torque_api_mode") != "r2025a_ctypes_torque" or
            result.get("pulse_steps") != 8 or isinstance(torque_nm, bool) or
            not isinstance(torque_nm, (int, float)) or
            not math.isfinite(torque_nm) or
            not math.isclose(torque_nm, 0.01, rel_tol=0.0, abs_tol=1e-12) or
            isinstance(gravity_displacement, bool) or
            not isinstance(gravity_displacement, (int, float)) or
            not math.isfinite(gravity_displacement) or gravity_displacement >= -0.002 or
            any(not isinstance(sha, str) or
                re.fullmatch(r"[a-fA-F0-9]{40}", sha) is None for sha in shas) or
            shas[0] != shas[2] or
            not str(result.get("webots_version", "")).startswith("Webots R2025a") or
            not isinstance(cases, list) or len(cases) != len(expected) or
            any(not isinstance(case, dict) for case in cases) or
            {case.get("case") for case in cases} != expected or
            any(case.get("pass") is not True for case in cases)):
        raise ValueError("native disturbance ABI or frame/physics check failed")

    directions = {
        "pitch_plus": (0, 1), "pitch_minus": (0, -1),
        "roll_plus": (2, -1), "roll_minus": (2, 1),
        "yaw_rotated_world_force": (0, 1), "rotated_local_offset": (1, 1),
        "torque_pitch_plus": (0, 1), "torque_pitch_minus": (0, -1),
        "torque_roll_plus": (2, -1), "torque_roll_minus": (2, 1),
        "torque_yaw_rotated_world": (0, 1),
    }
    zero_cases = {"pitch_zero_offset", "roll_zero_offset", "torque_zero"}
    for case in cases:
        omega = case.get("omega_xyz")
        if (not isinstance(omega, list) or len(omega) != 3 or
                any(isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) for value in omega)):
            raise ValueError("native probe has invalid angular velocity")
        name = case["case"]
        if name in zero_cases:
            if max(abs(value) for value in omega) >= 0.08:
                raise ValueError("zero-input probe rotated")
            continue
        axis, sign = directions[name]
        primary = sign * omega[axis]
        cross = max(abs(omega[index]) for index in range(3) if index != axis)
        if primary <= 0.10 or cross >= max(0.08, 0.3 * primary):
            raise ValueError("native probe direction or cross-axis response failed")
    return result


def run_probe_process(command: list[str], *, timeout: float,
                      env: dict[str, str] | None = None) -> tuple[str, bool, int]:
    """Run Webots in its own process group and reap the group on timeout.

    Webots' macOS/Linux launchers can start a simulator child that inherits
    stdout/stderr. Killing only the launcher leaves ``communicate`` waiting
    for the child's pipe, so a timeout must terminate the whole group.
    """
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env, start_new_session=(os.name == "posix"))
    try:
        output, _ = proc.communicate(timeout=timeout)
        return output, False, proc.returncode
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()
        output, _ = proc.communicate()
        return output + "\nTIMEOUT", True, proc.returncode


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
    raw_path = (args.output_dir / "force-api-probe-raw.json").resolve()
    raw_path.unlink(missing_ok=True)  # never consume evidence from an older run
    head = require_clean_source_commit()
    env = build_probe_env(
        binary, os.environ.copy(), head,
        github_actions=os.environ.get("GITHUB_ACTIONS") == "true",
    )
    env["RL_H25_FORCE_PROBE_OUT"] = str(raw_path)
    timed_out = False
    stdout, timed_out, returncode = run_probe_process(command, timeout=args.timeout, env=env)
    (args.output_dir / "force-api-probe.log").write_text(stdout, encoding="utf-8")
    try:
        if timed_out:
            raise ValueError("native Webots process timed out")
        if not raw_path.is_file():
            raise ValueError("native controller did not persist result JSON")
        outcome = parse_probe_log(PREFIX + raw_path.read_text(encoding="utf-8"))
        if returncode != 0:
            raise ValueError("native Webots returned nonzero status: " + str(returncode))
        (args.output_dir / "force-api-probe.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    except (ValueError, json.JSONDecodeError) as exc:
        print("DISTURBANCE API PROBE NOT ACCEPTED:", exc, file=sys.stderr)
        return 1
    print("Native free-body disturbance API probe PASS:",
          len(outcome["results"]), "cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

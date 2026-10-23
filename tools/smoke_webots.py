#!/usr/bin/env python3
"""Optional actual-Webots smoke test. Exits 2 when Webots is not installed.

Works on Linux with Xvfb or a graphical desktop, or macOS/Windows with native
Webots. Stops the simulator once the controller has written its run metadata.
Verifies launch/logging; it does NOT certify upright stability.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from run_standing_trials import read_webots_version

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "simulation/webots/worlds/rl_h25_lab.wbt"


def build_controller_env(binary: str, base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    env.setdefault("RL_H25_WEBOTS_VERSION", read_webots_version(binary, env))
    env.setdefault("RL_H25_CONTACT_EVIDENCE", "1")
    return env


def main():
    exe = shutil.which("webots")
    if not exe:
        print("SKIP: Webots executable not available on PATH.", file=sys.stderr)
        return 2
    prefix = []
    if sys.platform.startswith("linux") and not os.getenv("DISPLAY"):
        xvfb = shutil.which("xvfb-run")
        if not xvfb:
            print("SKIP: install xvfb-run or run with DISPLAY set.", file=sys.stderr)
            return 2
        prefix = [xvfb, "-a"]
    run_id = "smoke-" + uuid.uuid4().hex[:10]
    log_dir = ROOT / "experiments/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    cmd = prefix + [exe, "--stdout", "--stderr", "--batch", "--mode=fast", "--no-rendering", str(WORLD)]
    env = build_controller_env(exe, os.environ)
    env.update(RL_H25_RUN_ID=run_id, RL_H25_DURATION_S="8", RL_H25_LOG_DIR=str(log_dir))
    print("CMD:", " ".join(cmd), flush=True)
    meta_file = log_dir / (run_id + ".json")
    result = None
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as output:
        process = subprocess.Popen(cmd, env=env, stdout=output,
                                   stderr=subprocess.STDOUT,
                                   start_new_session=(os.name != "nt"))
        deadline = time.monotonic() + 100
        try:
            while time.monotonic() < deadline:
                if meta_file.is_file():
                    try:
                        meta = json.loads(meta_file.read_text(encoding="utf-8"))
                        if meta.get("result") == "controller_exited":
                            result = meta
                            break
                    except (json.JSONDecodeError, OSError):
                        pass
                if process.poll() is not None:
                    break
                time.sleep(0.4)
        finally:
            if process.poll() is None:
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            output.seek(0)
            stdout = output.read()
            print("WEBOTS OUTPUT (last 100 lines):\n" + "\n".join(stdout.splitlines()[-100:]))
    if result is None:
        print("FAIL: controller did not finish; inspect Webots messages above.")
        return 1
    contact = result.get("contact_evidence")
    if not isinstance(contact, dict) or contact.get("sample_count", 0) < 1:
        print("FAIL: native contact-point evidence is missing")
        return 1
    csv_path = log_dir / (run_id + ".csv")
    if not csv_path.exists() or csv_path.stat().st_size <= 80:
        print("FAIL: telemetry CSV missing/empty")
        return 1
    print("PASS: Real Webots ran the controller and wrote telemetry.")
    print("FINAL STATE:", result["final_state"], "REASON:", result["stop_reason"])
    print("CSV:", csv_path)
    print("IMPORTANT: This is not a 30-second standing stability certification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

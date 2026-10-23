#!/usr/bin/env python3
"""Optional 5 independent fresh-process Webots trials on an installed host.

Never runs hardware; no E-STOP hardware claim. Close other Webots windows first.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import subprocess
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / 'simulation/webots/worlds/rl_h25_lab.wbt'
LOGDIR = ROOT / 'experiments/logs'


def read_webots_version(binary: str, env: dict[str, str]) -> str:
    """Read exact version metadata from Webots home or a macOS app bundle."""
    roots = []
    if env.get('WEBOTS_HOME'):
        roots.append(Path(env['WEBOTS_HOME']))
    try:
        executable = Path(binary).resolve()
        roots.append(executable.parent)
        if len(executable.parents) > 1 and executable.parents[1].name == 'Contents':
            roots.append(executable.parents[1])
    except OSError:
        pass
    for root in roots:
        for relative in ('resources/version.txt', 'Resources/version.txt'):
            version_file = root / relative
            try:
                value = version_file.read_text(encoding='utf-8').strip()
            except OSError:
                continue
            if value.startswith('R20'):
                return 'Webots ' + value
    try:
        version = subprocess.run([binary, '--version'], capture_output=True,
                                  text=True, timeout=10, check=False)
        output = (version.stdout + ' ' + version.stderr).strip().replace('\\n', ' ')
    except (subprocess.SubprocessError, OSError):
        output = ''
    return ('Webots ' + output if output.startswith('R20') else
            output if output.startswith('Webots R20') else 'unverified')


def build_native_env(binary: str, base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)
    env.setdefault('RL_H25_WEBOTS_VERSION', read_webots_version(binary, env))
    env.setdefault('RL_H25_CONTACT_EVIDENCE', '1')
    return env


def trial(binary: str, *, mode: str, sim_duration_s: float, timeout_s: float,
          number: int, graphics: bool = False, extra_env: dict | None = None) -> Path:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_id = f'{mode}-{stamp}-{number:02d}-{uuid.uuid4().hex[:6]}'
    log_csv = LOGDIR / (run_id + '.csv')
    meta_file = LOGDIR / (run_id + '.json')
    cmd = [binary, '--stdout', '--stderr', '--batch', '--mode=fast']
    if not graphics:
        cmd.append('--no-rendering')
    cmd.append(str(WORLD))
    prefix = []
    if sys.platform.startswith('linux') and not os.getenv('DISPLAY'):
        if not shutil.which('xvfb-run'):
            raise RuntimeError('No DISPLAY; xvfb-run is required on headless Linux')
        prefix = ['xvfb-run', '-a']
    env = build_native_env(binary, os.environ)
    env.update(RL_H25_MODE=mode, RL_H25_RUN_ID=run_id,
               RL_H25_DURATION_S=str(sim_duration_s), RL_H25_LOG_DIR=str(LOGDIR))
    # Keep provenance of the exact checked-out source and PR test merge.
    # CI can provide the original PR head independently of GITHUB_SHA.
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        head = "unverified"
    env.setdefault("RL_H25_BUILD_COMMIT", head)
    env.setdefault("RL_H25_SOURCE_COMMIT_SHA", head)
    env.setdefault("RL_H25_TEST_MERGE_SHA", os.getenv("GITHUB_SHA", head))
    env.pop('RL_H25_FORCE_FAULT', None)
    for key in list(env):
        if key.startswith('RL_H25_DIST_') or key == 'RL_H25_DISTURBANCE':
            env.pop(key)  # normal standing run must never inherit an experiment
    if extra_env:
        env.update(extra_env)
    print('Trial', number, 'run_id=', run_id, 'mode=', mode, flush=True)
    with tempfile.TemporaryFile(mode='w+t', encoding='utf-8') as capture:
        p = subprocess.Popen(prefix + cmd, env=env, stdout=capture,
                             stderr=subprocess.STDOUT, start_new_session=(os.name != 'nt'))
        ok = False
        try:
            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                if meta_file.exists():
                    try:
                        m = json.loads(meta_file.read_text())
                        if m.get('result') == 'controller_exited' and m.get('run_id') == run_id:
                            ok = True
                            break
                    except (OSError, ValueError):
                        pass
                if p.poll() is not None:
                    break
                time.sleep(0.3)
        finally:
            if p.poll() is None:
                try:
                    if os.name == 'nt':
                        p.terminate()
                    else:
                        os.killpg(p.pid, signal.SIGTERM)
                    p.wait(timeout=8)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    p.kill()
                    p.wait()
            capture.seek(0)
            output = capture.read()
            print('Webots tail:\n' + '\n'.join(output.splitlines()[-15:]), flush=True)
    if not ok or not log_csv.exists():
        raise RuntimeError(f'Webots did not produce completed CSV+JSON for {run_id}')
    return log_csv


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=('baseline', 'balance'), default='baseline')
    p.add_argument('--trials', type=int, default=5)
    p.add_argument('--duration', type=float, default=32.)
    p.add_argument('--timeout', type=float, default=180.)
    p.add_argument('--webots', default='webots')
    p.add_argument('--graphics', action='store_true', help='disable --no-rendering')
    args = p.parse_args()
    if args.trials < 1 or args.duration < 30.5 or args.timeout <= 0:
        p.error('trials >= 1, duration >= 30.5s, timeout > 0 required')
    exe = shutil.which(args.webots)
    if not exe:
        print('ERROR: Webots not found on PATH; open manually or set --webots path.', file=sys.stderr)
        return 2
    LOGDIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(args.trials):
        try:
            paths.append(trial(exe, mode=args.mode, sim_duration_s=args.duration,
                               timeout_s=args.timeout, number=i + 1, graphics=args.graphics))
        except Exception as e:
            print('TRIAL FAILED:', type(e).__name__, str(e), file=sys.stderr)
            return 1
    print('\nGENERATED FILES FOR GATE:')
    for csv_path in paths:
        print(csv_path)
    from baseline_report import evaluate_suite
    out = evaluate_suite(paths, min_trials=args.trials,
                         min_passing=max(1, args.trials - 1))
    for res in out['trials']:
        print('PASS' if res['pass'] else 'FAIL', res['file'], res['metrics'], res['reasons'])
    print('RESULT:', out['passing'], '/', out['count'], 'gate=', out['pass'])
    print('NOTE: Real Webots results; visual contact/no slipping must be checked separately.')
    print('COMPARE: run same procedure in --mode balance ONLY after baseline review.')
    return 0 if out['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

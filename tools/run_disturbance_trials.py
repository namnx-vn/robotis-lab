#!/usr/bin/env python3
"""Real-Webots, fresh-process, paired, reproducible bounded-disturbance runs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

from run_standing_trials import trial, LOGDIR
from disturbance_report import compare_pairs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--webots', default='webots', help='Absolute path on macOS: /Applications/Webots.app/Contents/MacOS/webots')
    ap.add_argument('--pairs', type=int, default=3, help='3 for pilot, 5 for final decision')
    ap.add_argument('--axis', choices=('pitch', 'roll'), default='pitch')
    ap.add_argument('--direction', type=int, choices=(-1, 1), default=1)
    ap.add_argument('--force', type=float, default=0.10, help='Newtons; 0.01 .. 0.35')
    ap.add_argument('--pulse', type=float, default=0.112, help='Seconds; 0.016 .. 0.20')
    ap.add_argument('--onset', type=float, default=4.0, help='Seconds; 2 .. 15')
    ap.add_argument('--duration', type=float, default=14.0, help='Simulated total seconds')
    ap.add_argument('--timeout', type=float, default=180.0)
    ap.add_argument('--graphics', action='store_true')
    args = ap.parse_args()
    if args.pairs < 1 or args.pairs > 10 or args.timeout <= 0 or not (args.onset + args.pulse + 6 <= args.duration <= 60):
        ap.error('pairs 1..10, timeout positive, duration 6s after end of pulse and <=60s')
    if not (0.01 <= args.force <= .35 and .016 <= args.pulse <= .20 and 2 <= args.onset <= 15):
        ap.error('disturbance outside bounded envelope')
    exe = shutil.which(args.webots)
    if not exe:
        print('ERROR: Cannot find Webots; pass --webots /Applications/Webots.app/Contents/MacOS/webots', file=sys.stderr)
        return 2
    env = {'RL_H25_DISTURBANCE': '1',
           'RL_H25_DIST_AXIS': args.axis,
           'RL_H25_DIST_DIRECTION': str(args.direction),
           'RL_H25_DIST_FORCE_N': str(args.force),
           'RL_H25_DIST_PULSE_S': str(args.pulse),
           'RL_H25_DIST_ONSET_S': str(args.onset),
           'RL_H25_DIST_OFFSET_M': '0.04',
           'RL_H25_LOG_PERIOD_S': '0.016'}
    LOGDIR.mkdir(parents=True, exist_ok=True)
    pairs = []
    try:
        for i in range(args.pairs):
            b = trial(exe, mode='baseline', sim_duration_s=args.duration,
                      timeout_s=args.timeout, number=i+1, graphics=args.graphics, extra_env=env)
            c = trial(exe, mode='balance', sim_duration_s=args.duration,
                      timeout_s=args.timeout, number=i+1, graphics=args.graphics, extra_env=env)
            pairs.append((b,c))
    except Exception as exc:
        print('TRIAL ABORT:', str(exc), file=sys.stderr)
        return 2
    result = compare_pairs(pairs)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    filename = LOGDIR / f'disturbance-{args.axis}-{stamp}.json'
    filename.write_text(json.dumps(result, indent=2)+'\n')
    for pair in result['pairs']:
        b, c = pair['baseline'],pair['balance']
        print(f"BASELINE: {b['verdict']}, peak={b.get('peak_tilt_change_rad')}, file={b['file']}")
        print(f" BALANCE: {c['verdict']}, peak={c.get('peak_tilt_change_rad')}, file={c['file']}")
    print('COMPARISON:', result['verdict'], 'comparable=',result['comparable_pairs'], '/', len(pairs))
    print('JSON REPORT:', filename)
    print('WARNING: improvement needs verified perturbation; no gait admission unless evidenced.')
    return 0 if result['verdict'] == 'IMPROVED' else 1

if __name__ == '__main__':
    raise SystemExit(main())

# Verification commands, test matrix, telemetry and evidence

All commands below are examples from the current repository as of 2026-10-22; verify paths and CLI flags in live code. Executing them in a response is never implied by quoting them.

## Offline checks (when source is available)

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q simulation/webots/controllers tools tests
```

## Native Webots (only on a configured operator/CI environment)

```bash
# macOS example; check install location first
RL_H25_MODE=baseline /Applications/Webots.app/Contents/MacOS/webots \
  simulation/webots/worlds/rl_h25_lab.wbt

python3 tools/run_standing_trials.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --mode baseline --trials 5 --duration 32

# Protocol-only inspection; does NOT launch Webots
python3 tools/run_balance_matrix.py --dry-run --pairs 1

# Single bounded pilot: STOP and analyze if data inconclusive or faulted
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14

# Only after pilot review/approval and valid evidence
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 5 --force 0.10 --pulse 0.112 --duration 14
```

The `--pairs 1` pilot may intentionally exit nonzero because it cannot satisfy the three-pair gate. This does not alone establish controller failure; interpret its report status and faults.

## Test matrix

| Layer | Normal | Error/edge | Fault injection |
|---|---|---|---|
| Config and source | Syntax/parser, 10 joint names, bounds, neutral, units | Missing config, invalid limits, unexpected device name | NaN/nonfinite position, out-of-range request |
| Controller offline | Neutral ramp, interpolation smoothness, rate limit, reset | Timing jitter, stale sensor, empty input | Excess tilt, watchdog expiration, STOP/E_STOP priority |
| Webots static | Independent standing restarts, tilt/contact/time series | Vary reset order, initial pose within safe envelope | Joint saturation, modest sensor noise/latency under controlled setup |
| Webots balance | pitch+/pitch-/roll+/roll- matching baseline/active | Missing/weak injected force, drift/slip | Excessive tilt/first-fault, sensor missing, transient contact loss |
| Webots gait (only after gate) | Valid support transfer and consecutive grounded steps | Edge of foot support polygon, planned transition interruption | Unexpected contact loss, obstacle STOP, fall transition |

## Evidence fields

Use existing repo schemas where available. Report these fields or equivalent mappings (mark `NOT AVAILABLE` rather than fabricate):

```json
{
  "run_id": "example-only",
  "commit_sha": "UNVERIFIED",
  "simulator_version": "NOT RUN",
  "scenario": "pitch_plus",
  "mode": "baseline_or_balance",
  "platform": "macos_or_ci_ubuntu",
  "config_hash": "UNVERIFIED",
  "time_step_ms": null,
  "force_applied": null,
  "peak_tilt_rad": null,
  "settling_time_s": null,
  "left_contact": null,
  "right_contact": null,
  "fault_reason": null,
  "outcome": "NOT RUN"
}
```

CSV time-series when supported: `run_id`, monotonic/time simulated, `state`, target/actual joint positions (rad), joint velocity/rate, roll/pitch (rad), angular rates, foot-contact evidence, injected force and direction, position/COM estimate when available, `fault_reason`, safety transitions. Include version/units in metadata. Do **not** invent sensors or mark inferred contact as measured contact.

## Scientific comparison

For every trial, report scenario, target excitation vs observed response, max tilt, time to recover, foot slip/stance, fall/FAULT, number of qualified trials, and the baseline-vs-active comparison with uncertainty. Inspect `simulation.log`, raw CSV, JSON and matching SHA before claiming a gate. A screenshot/video is supplementary evidence only.

If simulator is unavailable, provide the exact user command and expected artifact paths; mark **native Webots tests: `NOT RUN`**. A `compileall` success only means Python syntax compiles; it does not establish Webots parser validity, physics, contact or controller correctness.

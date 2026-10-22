# RL-H25 0.2 — Standing baseline protocol

## Requirement / measurement before tuning

**Known observation:** Webots R2025a on user macOS displayed RL-H25 upright in one image. A prior run reported `FAULT excessive_tilt` at `t=332.46s`, `pitch=0.522rad`. No actual CSV logs supplied, so no full trial metrics were calculated.

**Baseline = position hold (PID disabled)**. Run five new independent Webots resets, **32 simulated seconds** per run, without injected faults. The data are in `experiments/logs/<run_id>.csv` and `.json`. The metadata includes `mode=baseline`, `config_sha256`, `build_commit`, `run_id`, `final_state`, `sim_time_s` and `result`. Each trial has fresh reset/initial placement and an unmodified `.wbt` world. Keep screenshot/video for manual foot contacts.

## Metrics and rationale

| Signal | Metric | Initial gate (ASSUMPTION) | Failure |
|---|---|---|---|
| `state` | all recorded `STAND` | 100% | any STOP, FAULT, E_STOP |
| `t_s` | last-first + no gaps | >=30s and gaps <=0.45s | short or missing data |
| `roll_rad`, `pitch_rad` | max absolute sample | <0.20 rad (~11.5 deg) | more tilt |
| `root_height_m` | min height | >=0.10 m | torso collapsed |
| `root_x_m`, `root_z_m` | peak planar deviation from first sample | <0.030 m | too much drift/sliding |
| `run_id`/`.json` | distinct + completed | unique and valid | repeated or incomplete trial |
| Foot-ground contact | visual video/scene inspection | no slip/penetration | cannot be proven by GPS alone |

>=4 of 5 distinct independent trials must pass, same control mode, then do an operator visual review of contact and foot placement. This is a **reproducible static-stance gate**, not a gait/balance proof. Even 5/5 pass without disturbance does not prove active balance. The configured thresholds are provisional: baseline results should be used to revisit them before publication.

## Tooling

```bash
python3 tools/run_standing_trials.py --mode baseline --trials 5 --duration 32
python3 tools/baseline_report.py --json-output experiments/standing_baseline_report.json <five-explicit-CSV-paths>
```

Compare with `--mode balance` only after initial baseline analysis. If the auto-runner cannot launch the macOS Webots app, run from terminal manually five times, reset world each time and ensure distinct IDs. A run with `RL_H25_FORCE_FAULT` is an intentional negative test and MUST NOT be included in pass trials.

Legacy Sprint01 logs lack `root_x_m` and `root_z_m`; strict acceptance must therefore FAIL with `missing_columns`, rather than silently ignoring drift. `tools/analyze_runs.py` can still report partial legacy metrics.

Logs contain no measured foot contact forces or motor torque. A visually upright pose and `state=STAND` are not sufficient evidence of stable balance.

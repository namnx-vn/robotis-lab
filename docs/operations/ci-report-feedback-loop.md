# Robotis Lab — Continuous Webots Experiment & Report Loop

## Goal

Create a reproducible engineering cycle:
**code commit → GitHub Actions Webots R2025a simulation → version-linked CSV/JSON report → report review → next short PR**.
A passing smoke/standing report is *not* proof of balance under force or successful walking.

## What already runs automatically

| Trigger | Workflow | Experiment | Artifact |
|---|---|---|---|
| Pull request targeting `master` | `python-tests.yml` | Python unit/fake-Webots tests (3.10, 3.12) | Logs in job |
| Pull request targeting `master` | `simulation.yml` | Native Webots smoke, ~8s | `ci-report.json`, `ci-report.md`, `simulation.log`, CSV/JSON |
| Push/merge to `master` | `simulation.yml` | 5 separate 32s static baseline runs | Same plus `standing_baseline_report.json` |
| Manual workflow dispatch | `simulation.yml` | Selected `smoke` or `baseline` | Same |

Webots runs on a **GitHub-hosted Ubuntu runner** using `cyberbotics/webots:R2025a-ubuntu22.04`. This is a real Webots engine, not a fake Python controller; it is **not** the operator's Mac, and may differ in rendering, contact dynamics and platform behavior. The artifact is kept for 30 days by default.

## Artifact contract

The simulation job uploads artifact
`robotis-lab-report-<commit-sha>-<run-id>-<attempt>`.

Expected contents:

```text
reports/
  ci-report.json                 # profile, commit SHA, run URL, statuses and gate
  ci-report.md                   # human-readable summary and caveats
  offline.log                    # unit/structural tests
  simulation.log                 # actual simulator/runner output
  standing_baseline_report.json  # baseline only, detailed per-trial metrics
experiments/logs/
  <run_id>.csv
  <run_id>.json                  # telemetry + paired run metadata
```

Not all files exist in every profile. If Webots fails to start, the report uploader still runs when possible and the final CI gate fails. Missing, corrupt, or incomplete evidence must be reported as **FAIL/INCONCLUSIVE**, never synthesized.

## How the AI reviewer reads the report

For each new finished workflow run:

1. Read repository `master` and the **specific branch/commit SHA** tested; never confuse the current head with a historical run.
2. Through the connected GitHub capability: list Actions runs for `namnx-vn/robotis-lab`; inspect the most relevant `Webots simulation` run; list and download its artifact.
3. Read `ci-report.json` and profile-specific report before interpreting CSV. Verify `commit_sha`, unique run IDs, complete samples, no FAULT and any declared gate.
4. Inspect `simulation.log` and actual CSV near FIRST FAULT (if any). Quantify tilt, height, X/Z drift, fault timestamp, and motor target vs measurement where present.
5. Label separately: **offline tests**, **native Webots smoke**, **static standing**, **controlled disturbance**, **physical hardware**. Never infer one from another.
6. Write a short assessment: observed result, first failure/root-cause hypothesis, safety implications, test to falsify it, proposed minimal PR.
7. Change code on a feature/fix branch; rerun the same CI conditions; review the new artifacts. **Do not auto-merge safety-critical changes.**

Example user prompt: “Kiểm tra GitHub Actions Webots simulation mới nhất của `namnx-vn/robotis-lab`, tải artifact và phân tích trước khi đề xuất PR tiếp theo.”

## Command-line access (operator)

From an authenticated GitHub CLI installation:

```bash
gh run list --repo namnx-vn/robotis-lab --workflow simulation.yml --limit 10
gh run view <run-id> --repo namnx-vn/robotis-lab
gh run download <run-id> --repo namnx-vn/robotis-lab --dir reports-from-ci
```

In GitHub UI: **Actions → Webots simulation → completed run → Artifacts**.

Local macOS disturbance test (NOT automatic in the current GitHub CI):

```bash
python3 tools/run_balance_matrix.py --dry-run --pairs 1
python3 tools/run_balance_matrix.py \
  --webots /Applications/Webots.app/Contents/MacOS/webots \
  --pairs 1 --force 0.10 --pulse 0.112 --duration 14
```

A one-pair pilot is deliberately inconclusive as a full acceptance gate, even when its individual results are useful. Upload its **sanitized** CSV/JSON report or attach it in chat for review; do not commit raw private camera footage or secrets.

## Acceptance and scope

- Pull-request smoke PASS means Webots booted/controller wrote enough clean telemetry for ~8 s.
- Master baseline PASS means at least 4/5 *undisturbed* 30 s standing trials passed its explicitly defined threshold; **visual foot contact is still unverified**.
- Active balance needs measured force excitation, comparable baseline/PID pairs, roll/pitch both signs, settled response and no FAULT. The current CI workflow does **not** run the full disturbance matrix on each PR.
- Physical walking needs a separate human-approved test; a CI-green simulation cannot certify torque, peak current, servo thermal margin or E-STOP wiring.

## Automation limits

GitHub Actions automatically runs without the owner keeping the Mac powered. A ChatGPT conversation does **not** wake up on GitHub pushes on its own. To request ongoing report analysis, use an explicitly enabled scheduled/conditional watch (e.g. hourly), or ask ChatGPT to review the latest run. If the artifact has expired, rerun the workflow on the specific commit or supply the local output. Automatic report review is not permission to merge PRs or command hardware.

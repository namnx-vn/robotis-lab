# CI and evidence review playbook

1. Record exact target (`master`, branch, PR) and SHA being evaluated; PR source/head SHA may differ from GitHub Actions **test merge** SHA. Treat old artifacts as historical only.
2. Review repository Actions definitions and output contract before interpreting labels: `python-tests.yml` (offline tests), `simulation.yml` (native smoke/baseline), `disturbance-pilot.yml` (free-body force API + one-pair pilot on PR). The last workflow validates report integrity, **not P2.2 active balance acceptance**.
3. Locate completed run URL, run attempt, conclusion and artifact, e.g. `robotis-lab-disturbance-<sha>-<run-id>-<attempt>` or `robotis-lab-report-<sha>-<run-id>-<attempt>`; confirm artifact retains expected files before reading metrics.
4. Match `ci-report.json` or `balance-pilot-ci-report.json` to raw `simulation.log`, per-trial `*.csv` and `*.json`, source/test SHA, controller config and world hash. Determine which tests were **native Webots** vs Python-only. A green step running `python -m unittest` does not prove physics.
5. Identify `scientific_balance_certified`, `assessment`, native probe status, actual injected force/steps and excitation threshold where present. `ci_evidence_ok: true` merely means evidence structurally valid. If the native pilot is marked INCONCLUSIVE, report precisely that.
6. If artifact expired, absent, corrupted, mismatched or can't be downloaded: explicitly `BLOCKED` or `INCONCLUSIVE`; ask for rerun on exact commit or sanitized local output. **Do not manufacture CSV or cite a screenshot as run telemetry.**
7. Build report with exact run/commit links, methods and first failure. Recommend smallest justified reviewed PR or next test; never auto-merge safety changes.

Operator commands (on an authenticated machine):

```bash
gh run list --repo namnx-vn/robotis-lab --limit 10
gh run view <run-id> --repo namnx-vn/robotis-lab
gh run download <run-id> --repo namnx-vn/robotis-lab --dir reports-from-ci
```

Keep source, test-merge, and environment distinctions visible. Current repo artifacts may have **30-day retention**; verify current workflow. Never promise proactive event-triggered ChatGPT review without a configured automation.

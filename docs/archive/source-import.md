# Historical migration guide — completed

The owner imported the RL-H25 v0.2.1 source files onto `master` after the first bootstrap pull request was merged. This document is retained only to explain prior migration from the local ZIP.

**Do not re-import the old ZIP into the repository.** New development must branch from the latest `master`, because it now contains the Webots world/PROTO, controller, motor limits, disturbance runner, and tests.

For current commands and acceptance criteria, read [README](../../README.md), [backlog](../../tasks/backlog.md), and [Sprint 02.2 protocol](../experiments/balance-matrix.md).

Evidence is not automatically migrated with source code: the reported 5/5 baseline is backed by the operator's console output; physical foot-contact verification and paired disturbance CSV/JSON tests are still pending. Do not commit raw footage or private sensor logs.

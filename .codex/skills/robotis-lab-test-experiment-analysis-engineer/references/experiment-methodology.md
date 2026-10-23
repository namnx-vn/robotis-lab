# Experiment design & analysis protocol

## Pre-register

Define hypothesis; observable effect; primary metric and unit; minimum excitation/signal-to-noise; success/failure thresholds; duration, number of resets/pairs, stopping rules and safety supervisor; exact source/config/world/physics hashes; random seed; platform; external influences; and who verifies foot contact. Fix these **before** results. Do not revise a gate after viewing the results without explicitly declaring a new exploratory protocol/version.

## Artifact integrity

- Keep **per-trial** CSV and JSON metadata, simulator console, run log, timestamps, exact source SHA vs PR test-merge SHA, world/config hash and true Webots engine version. Commit histories and artifact run IDs are evidence; filename labels alone are not.
- Reject nonfinite roll/pitch, out-of-order/duplicate timestamps, excessive sample gaps, mismatched run IDs, unexpectedly shortened runs and an invalid/unknown source of force. If one sample is corrupt, do not silently interpolate it into acceptance data.
- Retain all failures, faults and aborts in denominators and provide first-failure timestamp. Do not cherry-pick trials or report success after excluding failed attempts unless exclusion was predeclared and objectively applied to both arms.
- Document camera/force/contact provenance and privacy. If native telemetry lacks foot-ground contact, status should say **contact UNVERIFIED**.

## Baseline vs PID

Use **paired** trials with identical initial conditions per pair and independent simulator resets between pairs. Control only one variable (baseline vs PID), keeping force magnitude, offset, direction, pulse timing and sample window comparable; verify actual excitation. Analyze each sign and axis separately. Report:

- `n_total`, `n_valid`, `n_fault`, `n_inconclusive`, `n_recovered`, per-criterion success rates with valid denominator stated.
- Peak absolute tilt and peak **change** from pre-pulse baseline (`rad`), cross-axis peak; roll and pitch individually.
- Settling time/recovery: threshold, dwell time and window definition; label undefined when no valid recovery.
- Root/COM motion: root x-z drift if available; COM relative to support polygon only when actual geometry/contact is available.
- Joint target-vs-measured errors, saturation/rate limit hit frequency and relevant power/contact metrics when instrumented.
- Mean/median/spread and per-trial points; 95% CI only when method/sample size reasonable and stated. Do not treat small-N deterministic simulation mean as physical uncertainty.

Calculate a per-direction improvement only for valid and comparable pairs: `improvement_pct = 100 * (mean_baseline_peak - mean_PID_peak) / mean_baseline_peak` with nonzero verified baseline excitation. If denominator is tiny/unmeasurable, mark `INCONCLUSIVE`, not 100% improvement.

## Root cause and regression

Split observation vs hypothesis. Review first fault +/- relevant time window, controller output and clamping, IMU/gyro sign, feet/ground collision and resets. Design **one controlled falsification experiment** to distinguish competing hypotheses. When comparing commits, rerun identical scenarios and label software versions explicitly; do not compare different physics or revisions without caveat. Document observed regression severity and whether the phase release stays BLOCKED.

## Safe iteration

An inconclusive pilot is valuable evidence about instrumentation/excitation; it is **not** an invitation to blindly increase force, torque, mass or relax thresholds. Inspect source of inertial force and joint/contact frame first. Do not run physical bench without explicit operator authorization, a fixture and emergency stop plan. A single test cannot establish reproducibility or safety certification.

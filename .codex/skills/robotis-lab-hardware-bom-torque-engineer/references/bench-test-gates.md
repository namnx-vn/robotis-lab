# Supervised hardware bench-test gates (planning only)

No stage below authorizes energization, command transmission, firmware upload, actuation or expenditure. Each requires explicit operator approval, correct bench equipment, no nearby children/animals/fragile objects, and a physical support jig appropriate to the potential load. A full independent technical safety check and PSU/servo datasheet compatibility must precede first power. `NOT RUN` until actually executed.

## Pre-energization checklist

- [ ] Part numbers, allowed operating voltage, pin/polarity and connector layout **physically verified**.
- [ ] Servo power does **not** come from Arduino Uno 5 V or USB; PSU/current-limit setup is validated.
- [ ] Common ground reference is correct; wiring handles high-current motor return separately from logic ground path.
- [ ] Fuse, E-STOP/disable switch, isolation, cable gauge/connector rated current and polarity are reviewed by an appropriate operator.
- [ ] Mechanical travel bounds, physical stops, no pinch zone, harness/tether and servo fixture fasteners inspected.
- [ ] Real-time measured current and supply voltage instruments available; temperature monitoring and stop thresholds established from part ratings.
- [ ] Local watchdog/command validity, manual-stop and physical E-STOP behavior reviewed; operator is present and can cut motor power.
- [ ] No unprotected batteries or improvised mains wiring; provide appropriate regulated supply rather than unreviewed electronics.

## Stage A — one servo, no mechanical load

**Aim:** confirm controllability and supply stability for a *known compatible* servo.
**Method concept:** with protective jig, permit a narrow verified angular sweep at low rate and current-limited supply under supervision; compare requested to observed position and signal loss/recovery. Validate physical E-STOP on the protected rig.
**Evidence:** SKU/datasheet, voltage/current/temperature trace, command/timestamp, response speed, controller resets, physical stop observation. **Abort:** unexpectedly high current/heat, jitter, runaway or unexpected movement, fuse operation, brownout, unknown polarity or failed stop.
**Gate:** no abnormality in agreed load/speed/duration and reproducible logs; must not claim working torque capacity from unloaded motion.

## Stage B — one constrained joint

**Aim:** compare predicted `mgd` and dynamic margins to measured current, displacement, sustained load and temperature in the actual linkage, never by hand-held free movement.
**Evidence:** real lever-arm measurement, calibrated load/torque apparatus, effective link mass, angle-versus-target, current and temperature trajectory, no gear slip/jam, recoverable E-STOP under jig support.
**Gate:** verified sustained-duty capability for proposed loads, travel/speed bounds and thermal margin; blocked if only stall torque or no usable data.

## Stage C — one fully supported leg

**Aim:** characterize coupled servos, wiring distribution, pose rate, support loading and safe intervention while the leg is constrained so it cannot fall or strike people.
**Evidence:** measured combined current peaks/sag, sequence/position errors, friction/backlash, thermal rise, heartbeat-loss behavior, individual joint calibration and reproducibility across multiple trials.
**Gate:** all Stage B joint margins still adequate under interactions, no brownout, repeatable STOP and physical power cut.

## Stage D — two legs on a rig/tether

**Aim:** compare Webots masses/COM, foot reaction, passive structure and current/transient limits with the protected physical assembly, without declaring unsupported self-standing/walking.
**Evidence:** per-link measured masses, contact/force/tilt/height, applied commands, PSU and motor telemetry, root drift, first-fault reason and repeat trials with documented environment. Validate stop while supported.
**Gate:** no progression to unsupported standing or steps without review and explicit operator permission, prior phase evidence and robust support/STOP behavior.

## Test outcomes

- `PASS`: specified measured test executed, all predeclared conditions met, artifacts retained.
- `FAIL`: recorded evidence violates a limit; halt progress.
- `INCONCLUSIVE`: bad sampling, missing sensor/source, incomplete repeat count or ambiguous contact; no acceptance.
- `NOT RUN`: test not performed (a plan, calculation, animation or compiled code is not an executed test).

Each report records operator approval, protocol version, timestamp, device and power source IDs, firmware/host/software revision, current/voltage/temperature instrument details, log location, duration, acceptance thresholds, anomalies and first fault.

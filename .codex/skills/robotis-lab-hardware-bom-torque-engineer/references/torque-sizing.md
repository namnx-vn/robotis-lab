# Mechanical load and servo torque sizing

## Inputs and provenance

Collect explicit units and evidence for every input: dimensions of thigh/shin/foot, target standing pose, joint axes/signs, payload placement, center of mass (COM), physical mass per link including servo/cables/brackets, bearing positions, ground contact points and ground friction. Webots mass and torque values are **simulation assumptions until measured**. For the current RL-H25 Webots config, approximate `height_m = 0.25`, `hip_to_knee_m = 0.07`, `knee_to_ankle_m = 0.07`, `total_mass_kg = 0.38`; do **not** claim these are physical values.

## Calculation order

1. **Define the pose and support mode.** Neutral stand in double support, crouch/forward reach, roll-shift and single support at minimum. Identify which foot(s) contact the ground, load distribution and whether a joint moves slowly or quickly.
2. **Draw a free-body diagram per segment/joint.** Choose local coordinate frames. For each mass supported or distal mass attached to the joint, determine perpendicular distance from joint axis to line of gravity or contact reaction. Record COM uncertainty intervals and unsupported links.
3. **Compute gravitational moment.** In 3D, `tau_gravity_axis = axis_unit ⋅ Σ (r_i × m_i*g_vec)` (signed N·m). Scalar screening magnitude `|tau| ≈ m_supported*9.80665*d_perpendicular`. In double-support, foot-reaction distribution is a dynamic/contact unknown, not automatically 50:50. In single-support, supported ankle may experience most or all bodyweight reaction moment depending on center of pressure.
4. **Worst-case screening.** Enumerate hip roll/pitch, knee pitch and ankle roll/pitch separately for left and right. Determine maximum across states and posture constraints; flag collision/mechanical stops.
5. **Dynamic addition.** Estimate angular acceleration `alpha`, segment inertias and gravitational load changes; add friction, backlash, compliant deflection and unplanned impact/transient. Use inverse dynamics if kinematics/IMU/contact forces permit; otherwise report dynamic term as bounded unknown with explicit assumption.
6. **Actuator and transmission.** Evaluate motor/gear output *usable continuous torque*, peak torque rating/duration, speed at given torque, efficiency, heat, gear fatigue, stall exposure, voltage variation, travel and backlash. A quoted stall torque is **never** the target continuous value. Even with nominal 2–3× screening margin, missing thermal curves leave `UNVERIFIED`.
7. **Motion and controls.** Confirm speed under load meets commanded angular rate and that acceleration/jerk and hardware rate limits align with Webots. Gait energy and peak mechanical load may differ strongly from static posture.
8. **Record a range.** Compute lower/best/upper plausible values for mass and `d` when dimensions are uncertain. Do not report false one-digit precision. Store equation/pose/units and input source next to each output.

## Calculation table for a real task

| Joint | Scenario | Supported mass (kg) | Moment arm d⊥ (m) | τ_static (N·m) | Dynamic / uncertainty | τ_design (N·m) | Evidence |
|---|---|---:|---:|---:|---|---:|---|
| left_hip_pitch | crouch | TBD | TBD | TBD | TBD | TBD | UNVERIFIED |
| left_knee_pitch | crouch | TBD | TBD | TBD | TBD | TBD | UNVERIFIED |
| left_ankle_pitch | forward COM, one support | TBD | TBD | TBD | TBD | TBD | UNVERIFIED |
| left_hip_roll | support shift | TBD | TBD | TBD | TBD | TBD | UNVERIFIED |
| left_ankle_roll | one support | TBD | TBD | TBD | TBD | TBD | UNVERIFIED |

Repeat for right side, or justify symmetry and explicitly test the asymmetric worst case.

## Purely illustrative arithmetic — **NOT RL-H25 rated torque**

If one *hypothetically* uses the Webots **assumed** total mass `0.38 kg` and an invented example COM moment arm `0.03 m`, then the simplified gravitational moment is `0.38 × 9.80665 × 0.03 ≈ 0.112 N·m ≈ 1.14 kgf·cm`. This is **not** a proven knee/hip/ankle loading case, not a servo recommendation and not a hardware measurement; real moment arm, support forces and servo temperatures are unknown.

## Model limitations and sim-to-real comparison

Compare actual vs Webots link masses, inertia tensors, joint location/axis, foot contact patch/friction, COM location, actuator max velocity, speed under load, saturation, joint backlash, deadband, thermal behavior, voltage drop and sensor noise. Do not tune Webots torque/mass unrealistically just to make the simulation stand. Preserve physical safety if a simulation benchmark fails.

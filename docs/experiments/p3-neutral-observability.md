# P3-A — Neutral support observability

**Status:** source and mock tests implemented; native Webots evidence **NOT RUN**. P2.2 remains `INCONCLUSIVE`, so weight shift, foot lift, gait trajectories and `WALK` remain **BLOCKED**.

## Goal and scope

Prepare the non-actuating evidence path required before P3 motion. When contact evidence is enabled, the controller now resolves the `LEFT_FOOT` and `RIGHT_FOOT` PROTO nodes and records:

- left/right contact state and contact-point count by exact solid node ID;
- left/right foot world position;
- the convex support polygon from native Webots contact points in the world XZ plane;
- the signed distance from the model-derived COM projection to the closest polygon edge;
- unexpected non-foot contact solid IDs, retained so a fall/body contact cannot be hidden.

The implementation does not change joint targets, PID gains, motor limits, world physics, safety thresholds or controller states. The COM is Webots `Node.getCenterOfMass()` output, not a measured physical COM. Contact-point count is not load or force.

## Verification

```bash
python3 tools/verify_project.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q simulation/webots/controllers tools tests
```

The unit and fake-controller tests cover explicit foot identity, inside/outside COM margin, malformed/non-finite observations, non-foot contact retention and CSV integration. They do not exercise Webots contact physics.

Native validation still requires Webots R2025a on a compatible runner with `RL_H25_CONTACT_EVIDENCE=1`. Accept only if both PROTO feet resolve, the polygon is non-degenerate, the COM margin is finite and positive during neutral double support, GUI contact agrees, and no penetration, hidden anchoring or unexplained slip is observed. Preserve CSV/JSON and exact source/test SHA.

## Gate

This work is a partial P3-A prerequisite only. It does not satisfy P2.2 or the P3 acceptance criterion of at least five physically simulated steps. Per-foot load/force sensing, freshness/watchdog rules and native support-polygon evidence remain outstanding before any motion phase is enabled.

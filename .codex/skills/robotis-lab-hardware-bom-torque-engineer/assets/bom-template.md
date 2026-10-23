# RL-H25 staged BOM template

**Snapshot date:** YYYY-MM-DD  
**Hardware stage:** G0 Inventory / G1 Sizing / G2 Single-servo / G3 Bench / G4 One-leg / G5 Assembly  
**Budget target:** 3,000,000 VND, including necessary wiring, protection, fabrication and external services.  
**Cost convention:** each numeric value in `Estimated Cost (VND)` is a **line total** for the given quantity. `TBD` is not zero.  
**Ownership evidence:** operator statement / photograph / physical inspection / bench-tested.  
**Specification and price evidence:** manufacturer doc ID+revision / source link+date / measured log ID.

| Component | Model | Quantity | Voltage | Torque/Current | Estimated Cost (VND) | Source | Verification Status | Priority |
|---|---|---:|---|---|---:|---|---|---|
| Arduino host MCU | Uno (revision TBD) | 1 | TBD from board | Board supply draw TBD | TBD (owned; cash outlay 0 if confirmed) | Owner-reported, inspect label | OWNED (owner-reported); UNVERIFIED model | P0 required |
| PWM servo controller | PCA9685 breakout TBD | 1 planned | Logic VCC TBD, servo V+ TBD | Board current/traces TBD | TBD | Manufacturer board schematic TBD | PLANNED; UNVERIFIED | P1 candidate |
| Bench actuator | Servo SKU TBD | 1 initially | Datasheet TBD | Continuous/peak/stall distinction TBD | TBD | Manufacturer datasheet + vendor quote TBD | PLANNED; BLOCKED sizing | P1 required for bench |
| Final actuator set | Servo SKU TBD | 10 target (not approved) | TBD | Per-joint capability TBD | TBD | No purchase source yet | PLANNED; BLOCKED | Later |
| Independent regulated servo power | PSU model TBD | 1 planned | Exact rated servo voltage TBD | Verified continuous/surge A TBD | TBD | PSU datasheet TBD | PLANNED; BLOCKED | Safety essential |
| Fuse and safe power switch / physical E-STOP | Compatible models TBD | TBD | DC ratings TBD | Interrupt/rated current TBD | TBD | Safety components datasheets TBD | PLANNED; BLOCKED | Safety essential |
| Wiring, connectors, servo distribution | TBD | TBD | As designed | Ampacity/length/ΔV TBD | TBD | Supplier/spec sheets TBD | PLANNED; UNVERIFIED | Safety essential |
| Jig/tether and mechanical brackets | TBD | TBD | N/A | Load rating TBD | TBD | CAD/prototype shop TBD | PLANNED; UNVERIFIED | P1 required |
| Measuring equipment / rental (if not owned) | TBD | TBD | N/A | Meter/current capture/temp TBD | TBD | Inventory/source TBD | UNVERIFIED | P1 required |

**Risk of double counting:** final servo set is a **future alternative stage**, not cumulative procurement of 1+10 without accounting for the pilot actuator. State total target count, units reusable and replaceable spares explicitly.

### Budget summary

- Verified new-gear line subtotal: `UNVERIFIED` until all required lines have documented price and counts.
- Verified owned cash cost now: `0 VND` only for confirmed owned items, excluding replacement cost, consumables and missing accessories.
- Taxes/shipping/assembly/3D printing/spares: `UNVERIFIED` until sourced.
- **Complete physical prototype cash budget:** `BLOCKED / UNVERIFIED` until all scope and costs are resolved.
- Difference to target 3,000,000 VND: `UNVERIFIED`, not a false positive headroom.

Never use a historical planning-range estimate as a verified price or infer a shopping link.

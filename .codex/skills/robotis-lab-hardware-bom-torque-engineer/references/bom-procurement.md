# Inventory, BOM sourcing and cost optimization

## Inventory intake

For each image, box, datasheet, seller listing or operator description:

- Record exact readable model/variant/voltage, manufacturer vs reseller branding, channel count, connector orientation, number owned, photo timestamp when known and whether the item actually works. Keep unresolved identity as `UNVERIFIED`; similar appearance is insufficient for an official part number.
- Confirm intended function and compatibility: Arduino Uno board revision/clone, PCA9685 VCC/V+ breakout limits, servo electrical connector/horn/spline travel, needed IMU/camera, DC supply voltage/polarity, fuses, wiring, fastening and mechanical fabrication capacity.
- Prefer actual label photos from two sides, package/manual and measurements over inferred SKU names. `OWNED` based on user statement is legitimate with an annotation `owner-reported`; do not confuse possession with electrical readiness.

## Source hierarchy

1. Manufacturer datasheet/manual for voltage, speed/torque/current, operating duty, stall/thermal limits and dimensions. Record exact variant and revision.
2. Trusted distributor/manufacturer store for current regional price and stock. Record date, listed currency, link, price units, VAT, shipping and return terms.
3. Reseller catalog/community measurements as secondary data: label uncertain unless cross-checked.
4. User physical measurements (with equipment/method/time) are primary **for that specimen**, not a manufacturer guarantee for every item.
5. Treat unattributed AI-generated prices, historical project estimates, visually similar models and undated forum claims as `UNVERIFIED`.

When user requests actual product selection or market prices, retrieve current manufacturer technical sources and shopping listings **at execution time**; never invent products, merchants, links, inventory availability, discounts or quotes. Mark insufficient access `UNVERIFIED` and stop before a purchase recommendation that requires it.

## Budget accounting

Use the exact nine BOM columns; put supplementary `unit_cost`, availability, note and evidence date outside the mandatory table or in a linked appendix. Define whether `Estimated Cost (VND)` is per line (quantity × unit price) or per unit; default it to **line total** and state this convention.

Calculate separately:

- `known_new_outlay = Σ known line prices for PLANNED purchases`
- `owned_items_spend_now = 0` **only** as incremental cash spend (not replacement cost), after verifying possession; unknown accessory spend remains unknown.
- `shipping + taxes + outsourced printing/machining + spares + contingency` when sourced; if missing mark full budget `UNVERIFIED`.
- `headroom = 3,000,000 − verified_commitments` is only partial headroom if other costs are unknown.
- `BOM_full_total = unknown` while any mandatory quantity/component or required charge is unpriced. Avoid a falsely exact green budget claim.

## Procurement gate stages

| Gate | Objective | Dependency |
|---|---|---|
| G0 | Identify actual Uno and inventory; update weights/geometry | Owner photos, counts, model numbers and support | 
| G1 | Complete worst-case torque and speed envelope; filter candidate servo models | Accurate link masses and manufacturer curves | 
| G2 | Select **one** servo + protective PSU/jig (if not already owned) for an approved bench | Verified voltage/current, electronics review and operator approval |
| G3 | Measure one-servo continuous duty, temperature, speed, currents, load/position error | Executed approved test and calibration logs |
| G4 | Single constrained joint and supported leg | No overload, valid protective response, budget reserve |
| G5 | Remaining servo quantity and full build | Proven actuator adequacy and complete power/thermal budget |

A staged approach can expose infeasibility before committing to ten motors. Never trade away appropriate current capacity, insulation, grounding, fusing, accessible E-STOP or mechanical support just to meet 3,000,000 VND. If safe parts exceed the cap, recommend reducing scope/delaying the purchase instead.

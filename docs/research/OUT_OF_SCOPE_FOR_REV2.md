# OUT_OF_SCOPE_FOR_REV2 — research / history only

**None of this is implemented, supported or claimed by Rev.2.** It is kept only so
the decision is traceable. Rev.2 is a lithium-ion (~10S, ~30–42 V) characterization
platform built around the SFSU equipment in `docs/rev2/SFSU_EQUIPMENT_MATRIX.md`.

Removed from the active project:
- NiMH (and other non-lithium-ion) chemistry support; sub-3 V profiles and low-voltage custom-load plans
- Dat Bike (~72 V class) and anything above the OSBAMS 44 V ceiling / 6060B 60 V window
- Medium-/high-voltage architectures, EV modules and EV packs
- The OWON electronic load (archived code: `legacy/rev1/`)
- Regenerative or commercial cycler drivers (any vendor) and generic future-cycler abstractions
- "60 A at all voltages" or "90 A" testing claims (the 6060B is limited to `min(60 A, 300 W / V)`; an XT90 plug is not a test current)
- Full smart-BMS support (only normal, read-only communication with documented packs is ever in scope; unsupported packs report `SMART_PACK_UNSUPPORTED`; no BMS bypass)

OptiMate 12.8 V LiFePO4 chargers are separate lab equipment: documented in the
equipment matrix, never integrated into the test path and never used on the 36–42 V packs.

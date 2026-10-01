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

Lab equipment that exists at SFSU but is NOT part of the Rev.2 stack or validation workflow (future research notes only):
Analog Discovery 2, waveform generators (Keysight EDU33212A, HP 33120A), extra bench supplies (Keysight EDU36311A, HP E3630A),
secondary instruments (HP 34401A DMM, HP 54601B oscilloscope), a handheld multimeter, and OptiMate 12.8 V LiFePO4 chargers
(separate lab equipment; never used on the 36–42 V packs). Using them would restore pre-battery commissioning
sources, protocol debugging and signal injection — see "Limits of this workflow" in `docs/rev2/LV_HARDWARE_VALIDATION_PLAN.md`.
Connectors: XT60 is the supported Rev.2 interface. A future adapter (e.g. XT90) is easy, but connector type does not determine test capability — the validated power path does — so no adapter implies a higher test current.

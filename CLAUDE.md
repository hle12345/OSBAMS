# OSBAMS — project memory for Claude Code sessions

**Rev.2 = lithium-ion, SFSU lab-optimized.** Supported: lithium-ion packs (NMC/NCA/LFP), ~10S, ~30–42 V
(Ninebot/Segway 36 V, Shenzhen Elite 37 V). Built ONLY around the equipment in `docs/rev2/SFSU_EQUIPMENT_MATRIX.md`
(12 roles: 6060B load; EDU34450A + HP 34401A reference DMMs; EDU36311A + HP E3630A sources; EDUX1052G + HP 54601B scopes;
EDU33212A + HP 33120A generators; AD2; handheld DMM; OptiMate LFP chargers = separate lab equipment, never in the test path,
never on the 36–42 V packs). Start with `docs/rev2/ARCHITECTURE.md`, `HARDWARE_FREEZE_CANDIDATE.md`, `BENCH_CHECKLIST.md`.

## Claim (keep narrow)
"OSBAMS Rev.2 is an open lithium-ion battery characterization platform for supported battery packs within the validated
OSBAMS hardware envelope and the Agilent 6060B electronic-load envelope." Never claim NiMH/other chemistries, Dat Bike/72 V,
EV packs, 60 A at all voltages, full smart-BMS support, BENCH_TESTED or HARDWARE_VALIDATED without recorded data.

## Hard rules
- Permitted current = min(profile, OSBAMS ceiling 10 A, 60 A, 300 W / conservative pack voltage, fuse, disconnect, relay, shunt, wiring, connector). 42 V → 7.14 A; 36 V → 8.33 A. The 60 A rating never overrides 300 W. System ceiling **≤ 44 V, ≤ 10 A (provisional)** until the power path is physically validated.
- Invariant: commanded current × conservative pack voltage ≤ 300 W; the conservative voltage = max(OCV, highest seen) and never decreases (sag can't raise current). Every load command goes through `equipment/capability.py`.
- Layers: firmware hard trip (18.5 A / 60 °C) = protection boundary; desktop/profile limits = operating boundary. Don't force them equal.
- No global minimum battery voltage; cutoff is per profile. Chemistry must be lithium-ion or the profile is refused.
- Pipeline: profile → OCV screen → hardware safety check → capability calc → controlled load test → logging → Ah/Wh → DCIR (separate test) → automatic cutoff → verified load-off → recovery → SOH/report/passport.
- 6060B remote control is BLOCKED (no confirmed GPIB path; no command VERIFIED against the official Keysight manuals — `docs/rev2/6060B_DRIVER_EVIDENCE.md`). An operation enables only when every command it needs is VERIFIED. Manual6060B is the working mode.
- Removed from the active project (history only in `docs/research/`, `legacy/rev1/`): NiMH/non-lithium chemistries, sub-3 V and low-voltage load plans, the Rev.1 OWON load, Dat Bike, MV/HV, EV packs, any cycler drivers. A test fails if they reappear in active code. Smart BMS: normal read-only communication only; unsupported → `SMART_PACK_UNSUPPORTED`; no bypass.
- Current-sensing redesign is not planned (existing ~20 A shunt + INA228 suffices for 36–42 V packs).
- Instrument serial / asset ID / calibration status stay UNKNOWN until read off the instrument.

## Open items
Exact DG57CM suffix, shunt P/N, 12→5 V converter, fuse + holder P/N; the 15 A fuse is below the 18.5 A firmware trip — decide ordering; shunt high/low-side vs PCB; TC74 bring-up (thermal protection unvalidated, safety check refuses to start without a temperature); read the two official 6060B manuals (www.keysight.com was blocked in the cloud environment).

## Commands
`python3 -m pytest tests` (needs pytest numpy scikit-learn pyserial PySide6 pyqtgraph; `QT_QPA_PLATFORM=offscreen`) · `make -C Firmware/Tests run` · `python3 tools/gen_rev2_docs.py` after editing `commands.py`, `validation.py` or `inventory.py` (tests fail if the generated docs are stale).

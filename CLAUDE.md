# OSBAMS — project memory for Claude Code sessions

**Rev.2 = standalone lithium-ion characterization platform around the SFSU Agilent 6060B.** Supported: lithium-ion
(NMC/NCA/LFP), ~30–42 V, 10S-class, XT60. The active stack is exactly: 6060B (only external load), EDU34450A (reference
measurement), Raspberry Pi 5 + touchscreen (UI), STM32L476RG (safety controller), the power path, and the EDUX1052G
(validation only). See `docs/rev2/SFSU_EQUIPMENT_MATRIX.md`, `ARCHITECTURE.md`, `HARDWARE_FREEZE_CANDIDATE.md`, `BENCH_CHECKLIST.md`.
Keep the active project and docs to that stack; removed scope lives only in `docs/research/OUT_OF_SCOPE_FOR_REV2.md` and
`legacy/rev1/` — do not reintroduce it, and do not list other lab equipment in Rev.2 docs.

## Claim (keep narrow)
Use `config.REV2_CLAIM`. Never claim BENCH_TESTED / HARDWARE_VALIDATED without recorded data, 60 A at all voltages, or full smart-BMS support.
XT60 = supported; connector type does not determine test capability — the validated power path does.

## Hard rules
- Allowed current = min(profile, OSBAMS hardware limit (10 A ceiling; fuse, disconnect, relay, shunt, wiring, connector), 6060B 60 A, 300 W / conservative pack voltage). 42 V → 7.14 A; 36 V → 8.33 A. The 60 A rating never overrides 300 W. System ceiling **≤ 44 V, ≤ 10 A (provisional)** until the power path is physically validated.
- Invariant: commanded current × conservative pack voltage ≤ 300 W; the conservative voltage = max(OCV, highest seen) and never decreases (sag can't raise current). Every load command goes through `equipment/capability.py`.
- Layers: firmware hard trip (18.5 A / 60 °C) = protection boundary; desktop/profile limits = operating boundary. Don't force them equal.
- No global minimum battery voltage; cutoff is per profile. Chemistry must be lithium-ion or the profile is refused.
- Pipeline: profile → OCV screen → hardware safety check → capability calc → controlled load test → logging → Ah/Wh → DCIR (separate test) → automatic cutoff → verified load-off → recovery → SOH/report/passport.
- 6060B remote control is BLOCKED (no confirmed GPIB path; no command VERIFIED against the official Keysight manuals — `docs/rev2/6060B_DRIVER_EVIDENCE.md`). An operation enables only when every command it needs is VERIFIED. Manual6060B is the working mode.
- Removed scope (see the research note) is guarded by `TestRev2ScopeCleanup`. Smart BMS: normal read-only communication only; unsupported → `SMART_PACK_UNSUPPORTED`; no bypass.
- Current-sensing redesign is not planned (existing ~20 A shunt + INA228 suffices for 36–42 V packs).
- Instrument serial / asset ID / calibration status stay UNKNOWN until read off the instrument. No variable source is in the stack: voltage/current are verified at the pack's own operating points.

## Open items
Read the installed part numbers off the hardware and record them in `docs/rev2/HARDWARE_ACCEPTANCE_RECORD.md` (relay — firmware records DG57CM-5021-76-1012-R; shunt — firmware RSA-20-50; fuse + holder; 12→5 V converter + Pi 5 supply; XT60 supplier); identify the 6060B interface; ADC divider and TVS unfinished; shunt high/low-side vs PCB; TC74 bring-up (thermal protection unvalidated, safety check refuses to start without a temperature); read the two official 6060B manuals (www.keysight.com was blocked in the cloud environment). The 15 A fuse vs 10 A software limit vs 18.5 A firmware trip is a documented layered design, not a defect.

Next milestone: **physical validation** — `docs/rev2/FIRST_BATTERY_TEST_PROCEDURE.md`. Do not add features until real measurements exist.

## Controller PCB manufacturing package
**No fabrication package exists** (the earlier script-generated candidate was removed; `docs/rev2/pcb/MANUFACTURING_STATE.md`). `docs/rev2/pcb/RELEASE_GATES.json` has six gates, all false; `tools.mfg.build_package` refuses without `--candidate`, and `tests/test_pcb_release_gates.py` fails if fab files appear. The KiCad board is a through-hole carrier (NOT STM32/INA228-on-board) with a known diode-polarity defect (symbol pin 1 = anode, footprint pad 1 = cathode on D1–D3) and no PA0/PC9/PA1 circuits. Plan only, board unmodified: `docs/rev2/pcb/REV2_SCHEMATIC_PCB_PLAN.md`. Audit inputs and the authoritative V1–V10 bench list are in `docs/rev2/pcb/` (`BENCH_V1_V10_ONE_PAGE.pdf`). Rules: keep the Durakool relay unless its verified DC rating is inadequate; Pi 5 V power is a separate decision (not on the PCB by default); no TC74 interface redesign until the four V1 discriminators are recorded.

## Commands
`python3 -m pytest tests` (needs pytest numpy scikit-learn pyserial PySide6 pyqtgraph; `QT_QPA_PLATFORM=offscreen`) · `make -C Firmware/Tests run` · `python3 tools/gen_rev2_docs.py` after editing `commands.py`, `validation.py` or `inventory.py` (tests fail if the generated docs are stale).

# OSBAMS — Rev.2

> ## Status
> **Release candidate, not bench-validated.** The controller PCB (`Hardware/Rev2_Controller/OSBAMS_Rev2_RELEASE_CANDIDATE_1/`, RC1.2e) is a
> *review* package: ERC/DRC/netlist/schematic-parity checks are clean, but **no physical validation has been run**, the board is
> **not released for fabrication**, and nothing here is BENCH_TESTED or HARDWARE_VALIDATED. Gerbers are intentionally not shipped:
> export them yourself from the KiCad 10 project after re-running ERC/DRC. First-article tests and open items are listed in
> `Hardware/Rev2_Controller/CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`. Do not connect a real battery pack to hardware built from
> these files without completing `docs/rev2/FIRST_BATTERY_TEST_PROCEDURE.md`.

> **AI assistance.** Developed with AI-assisted engineering tools (including Claude) for code generation, documentation, and design
> review. Final design decisions, hardware validation, and release responsibility remain with the project author/team.

## Licences
* **Software and firmware** (`desktop/`, `Firmware/`, `tools/`, `tests/`, build/calculation scripts): **MIT** — see `LICENSE`.
* **Hardware and hardware documentation** (`Hardware/`, `manufacturing/`, `docs/`, `Documentation/`, KiCad sources): **CERN-OHL-S-2.0** — see `LICENSE-HARDWARE.md`.
* Manufacturer datasheets and CAD models are **not** included; see `docs/rev2/pcb/evidence/SOURCES.md` for where to get them.

**OSBAMS Rev.2 is a standalone lithium-ion battery characterization platform optimized
around the SFSU Agilent 6060B electronic load. It uses an STM32L476RG safety controller,
Raspberry Pi 5 interface, INA228-based measurement, independent voltage verification, and
Keysight reference instrumentation to validate capacity, energy, DCIR, thermal behavior, and
battery health metrics of compatible lithium-ion battery packs within the verified hardware envelope.**

Supported: lithium-ion packs, approximately 30–42 V (10S-class; Ninebot/Segway, Shenzhen Elite), XT60 (connector type does not determine test capability — the validated power path does).
Status: **2.0.0-dev1 — host- and simulator-tested; no physical validation has been run**
(nothing is BENCH_TESTED or HARDWARE_VALIDATED).

## The one rule
`allowed current = min(battery profile, OSBAMS hardware limit, 6060B current limit, 300 W / battery voltage)`
at the conservative (never-sagging) pack voltage. 42 V → **7.14 A**; 36 V → **8.33 A**. The 60 A rating never
overrides 300 W. Operating ceiling: ≤ 44 V and ≤ 10 A until the power path is physically validated.

## The Rev.2 stack (`docs/rev2/SFSU_EQUIPMENT_MATRIX.md`)
Agilent/Keysight **6060B** (primary and only external load) · Keysight **EDU34450A** (reference measurement) ·
**Raspberry Pi 5 + 10.1" touchscreen** (UI, database, passport, reports) · **STM32L476RG** (safety controller) ·
**power path** (battery → XT60 → fuse → disconnect → relay → shunt → 6060B) · Keysight **EDUX1052G** (validation-only observation).

## Test orchestrator and dashboard
`services/test_orchestrator.py`: Capacity (`PROFILE → OCV screen → hardware safety check → capability calculation → READY → CC discharge → cutoff → load OFF verified → recovery → results`) and a separate DCIR current-step test. The dashboard shows the live permitted-current breakdown and drives a *manual* 6060B (operator sets/enables the load; OSBAMS verifies from measurements). Hard invariant: commanded current × conservative pack voltage ≤ 300 W; sag never raises current.

## Open at multiple levels
**Current status of the calibration / validation / AI work (under development)**
- The Rev.2 PCB remains frozen at RC1.2e (release candidate, not bench-validated until first article); the validation/AI work makes no PCB or schematic geometry change.
- Protocol v2 firmware is still under development: only a host-side reference parser, golden vectors and design exist; the STM32 firmware still speaks protocol v1.
- Calibration, measurement-quality and agreement thresholds (and the rule-baseline thresholds) are provisional until real bench/reference-instrument measurements exist.
- The AI/data work is experimental/research-stage; no ML-based battery-health result is production-valid yet, and capacity retention vs rated is not a validated cell-level SOH.

OSBAMS is a platform for assessing unknown and second-life batteries, not just a low-cost cycler: **open hardware** (Rev.2 controller PCB review package), **open firmware and software**, **open battery profiles and test protocols**, **open standardized data** (`docs/rev2/DATASET_SCHEMA.md`, Battery Passport) and **open health models** (`ai/`). Chain: Rev.2 hardware → calibration/validation layer → real battery dataset → explainable AI health assessment. The calibration/validation and AI work is **under development**: thresholds are provisional until reference-instrument validation, Rev.2 remains unbench-validated until first article, AI health estimation is experimental/research-stage, and capacity retention is not a validated cell-level SOH. See `docs/rev2/WORKSTREAMS.md`, `docs/rev2/VALIDATION_AND_CALIBRATION_PLAN.md`, `ai/README.md`.

## Next milestone: first real battery test
`docs/rev2/FIRST_BATTERY_TEST_PROCEDURE.md`, with `CALIBRATION_RECORD_TEMPLATE.md` and `HARDWARE_ACCEPTANCE_RECORD.md`. Software is ahead of hardware; no more features until measurements exist.

## Bench work
`docs/rev2/BENCH_CHECKLIST.md` — the exact physical tests, in order (workflow: `LV_HARDWARE_VALIDATION_PLAN.md`; verification: `INSTRUMENT_CALIBRATION_PLAN.md`). `docs/rev2/6060B_DRIVER_EVIDENCE.md` — remote-control command evidence (nothing VERIFIED yet).

## Controller PCB manufacturing package
`manufacturing/PCBWay_OSBAMS_Rev2_PCBA/` — candidate Gerber/BOM/CPL/PDFs for the KiCad controller PCB, with a design review and checklist. **Not production-ready** (see its README and checklist).

## Layout
- `desktop/` — Python application (`equipment/`, `services/`, `db/`, `gui/`)
- `Firmware/` — STM32 firmware + host C tests
- `docs/rev2/` — architecture, power-path matrix, current-sensing redesign, GPIB checklist, validation plan, baseline
- `legacy/rev1/` — archived Rev.1 code (nothing may import it)
- `tests/`, `tools/` — Python tests; simulator and demo-data tools

## Run the tests
```
pip install pytest numpy scikit-learn
python3 -m pytest tests          # also: pyserial PySide6 pyqtgraph; QT_QPA_PLATFORM=offscreen
make -C Firmware/Tests run
```
Learning Mode demo: `cd desktop && python3 -m services.learning_mode`.
Simulator: `python3 tools/simulate_serial.py --list`.

## 6060B remote control
`6060B_REMOTE_CONTROL = BLOCKED_BY_INTERFACE_CONFIRMATION` until the lab's GPIB
path is confirmed (`docs/rev2/GPIB_INTERFACE_CONFIRMATION.md`). Use `Manual6060B`
or `Simulator6060B` meanwhile.

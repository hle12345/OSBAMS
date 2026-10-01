# OSBAMS — Rev.2

**OSBAMS Rev.2 is an open lithium-ion battery characterization platform for
supported battery packs within the validated OSBAMS hardware envelope and the
Agilent 6060B electronic-load envelope.**

Supported: lithium-ion packs, approximately 10S, ~30–42 V (Ninebot/Segway 36 V,
Shenzhen Elite 37 V). Status: **2.0.0-dev1 — host- and simulator-tested; no
physical validation has been run** (nothing is BENCH_TESTED or HARDWARE_VALIDATED).

## The one rule
`permitted current = min(profile, OSBAMS 10 A, 60 A, 300 W / conservative pack voltage, fuse, disconnect, relay, shunt, wiring, connector)`

42 V → **7.14 A**; 36 V → **8.33 A**. The 60 A rating never overrides 300 W. Operating
ceiling: ≤ 44 V and ≤ 10 A until the power path is physically validated.

## Not claimed
NiMH or other chemistries, Dat Bike / 72 V, EV packs, 60 A at all voltages, full
smart-BMS support (only normal read-only communication with documented packs; unsupported
packs report `SMART_PACK_UNSUPPORTED`; no BMS bypass). History only: `docs/research/`, `legacy/rev1/`.

## Equipment (12 roles — `docs/rev2/SFSU_EQUIPMENT_MATRIX.md`)
6060B (primary load) · EDU34450A (primary reference DMM) · HP 34401A (secondary) ·
EDU36311A / HP E3630A (commissioning sources, not loads) · EDUX1052G / HP 54601B (scopes) ·
EDU33212A / HP 33120A (signal injection) · Analog Discovery 2 · handheld DMM. OptiMate
12.8 V LiFePO4 chargers are separate lab equipment: never in the test path, never on the 36–42 V packs.

## Test orchestrator and dashboard
`services/test_orchestrator.py`: Capacity (`PROFILE → OCV screen → hardware safety check → capability calculation → READY → CC discharge → cutoff → load OFF verified → recovery → results`) and a separate DCIR current-step test. The dashboard shows the live permitted-current breakdown and drives a *manual* 6060B (operator sets/enables the load; OSBAMS verifies from measurements). Hard invariant: commanded current × conservative pack voltage ≤ 300 W; sag never raises current.

## Bench work
`docs/rev2/BENCH_CHECKLIST.md` — the exact physical tests, in order (workflow: `LV_HARDWARE_VALIDATION_PLAN.md`; calibration: `INSTRUMENT_CALIBRATION_PLAN.md`). `docs/rev2/6060B_DRIVER_EVIDENCE.md` — remote-control command evidence (nothing VERIFIED yet).

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

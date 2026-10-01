# OSBAMS — Rev.2 (SFSU lab-optimized rebuild)

**OSBAMS Rev.2 is an open battery characterization and health-assessment
platform designed around the available SFSU laboratory instrumentation. It
supports battery packs within a validated subset of the Agilent 6060B's
3–60 V, 60 A, 300 W operating envelope and performs automated capacity,
energy, DCIR, voltage-sag, thermal, SOH and battery-history analysis.**

Status: **2.0.0-dev1 — design and host-tested software; no physical validation
has been run.** The 60 V / 60 A / 300 W figures are the *instrument's* rating,
not an OSBAMS capability: the OSBAMS envelope is the intersection of the 6060B,
the battery profile and the validated power path (10 A today).

## The one rule
`permitted current = min(profile, OSBAMS hardware, connector, fuse, wiring, contactor, shunt, 60 A, 300 W / V)`

42 V pack → 300 / 42 = **7.14 A**. 60 A exists only at ≤ 5 V; an XT90 plug is
not a 90 A test. Every load command is checked by `desktop/equipment/capability.py`.

## Not supported (OUT_OF_SCOPE_FOR_REV2)
Dat Bike / 72 V, 100 V, 150 V, 500 V, EV modules/packs, regenerative cyclers.
Removed: OWON load (archived under `legacy/rev1/`), ITECH, Bitrode, Arbin, Chroma, Digatron.

## Test orchestrator and dashboard
`services/test_orchestrator.py`: Capacity (`PROFILE → OCV → READY → CC discharge → cutoff → load OFF verified → recovery → results`) and a separate DCIR current-step test. The dashboard shows the live permitted-current breakdown and drives a *manual* 6060B (operator sets/enables the load; OSBAMS verifies from measurements). Hard invariant: commanded current × conservative pack voltage ≤ 300 W; sag never raises current.

## Bench work
`docs/rev2/BENCH_CHECKLIST.md` — the exact physical tests, in order. `docs/rev2/6060B_COMMAND_EVIDENCE.md` — remote-control command evidence (nothing VERIFIED yet).

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

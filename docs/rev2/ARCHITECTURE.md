# OSBAMS Rev.2 architecture — SFSU lab-optimized

Direction change: Rev.2 is designed **only** around equipment physically
available at SFSU. The earlier MV/HV/Dat Bike/EV-pack roadmap is removed from
the active system (nothing of it existed in code; the concepts live only as
`OUT_OF_SCOPE_FOR_REV2` notes).

## Claim
> OSBAMS Rev.2 is an open battery characterization and health-assessment
> platform designed around the available SFSU laboratory instrumentation. It
> supports battery packs within a validated subset of the Agilent 6060B's
> 3–60 V, 60 A, 300 W operating envelope and performs automated capacity,
> energy, DCIR, voltage-sag, thermal, SOH and battery-history analysis.

Not claimed: Dat Bike, 72 V, 100 V, EV-pack compatibility, or a "90 A tester".
The 60 V / 60 A figures are the **instrument's** rating; the OSBAMS envelope
is the intersection with the profile and the validated power path (currently
10 A, see `LV_POWER_PATH_CAPABILITY.md`).

## Layers
```
desktop/equipment/
  capability.py        60 V / 60 A / 300 W + OSBAMS limits -> permitted current
  inventory.py         SFSU instruments (asset IDs/cal status UNKNOWN until read)
  drivers/
    base.py            ElectronicLoad interface; every setpoint is envelope-guarded
    keysight_6060b/    SCPI driver (commands.py carries per-command verification status)
    manual_6060b.py    operator drives the panel; software validates instructions
    simulator_6060b.py same envelope + battery model; 51 scenarios, all <= 60 V
  reference/           EDU34450A calibration records (-> calibration_records table)
desktop/services/  battery_profiles.py  bms.py  learning_mode.py  (+ existing)
desktop/gui/limit_panel.py   the permitted-current panel (PySide6)
legacy/rev1/         archived Rev.1 load code (nothing may import it)
```

## Test orchestrator (`services/test_orchestrator.py`)
```
Capacity: PROFILE -> OCV -> READY -> CC DISCHARGE (V/I/P/T, Ah/Wh) -> profile CUTOFF
          -> LOAD OFF (verified from measured current) -> RECOVERY -> COMPLETE
DCIR:     PROFILE -> OCV -> READY -> STEP I1 -> STEP I2 ... -> LOAD OFF -> RECOVERY -> COMPLETE
```
Push-based (`on_sample`), fed by the STM32/INA228 stream, the simulator or a bench;
timing comes from sample timestamps. FAULT paths always turn the load off and
verify it. Dashboard: permitted-current panel + phase/confirm controls
(`gui/tabs/dashboard_tab.py`), results saved with `services/run_persistence.py`.

## Layered limit model
Firmware hard trip 18.5 A (absolute protection) > OSBAMS operating ceiling 10 A
(provisional) > 6060B `min(60 A, 300 W/V)` > battery profile. Commanded maximum =
min of the *operating* layers; the firmware trip is deliberately not an input.
Hard invariant: `commanded current x conservative pack voltage <= 300 W`, where the
conservative voltage is `max(OCV, highest seen)` and never decreases — sag cannot
raise current mid-test. `tests/test_protocol.py` checks the firmware trip mirrors
`config.FIRMWARE_HARD_TRIP_*` exactly and that the operating limits sit below it.

## Rules enforced in code (tests: `tests/test_rev2_equipment.py`)
- Every load command passes `check_load_command` (V ≤ 60, ≥ 3; I ≤ 60; V·I ≤ 300 W; profile/OSBAMS/component limits) **before** any write.
- Power check uses the highest known pack voltage (OCV vs live) — a sagged reading cannot relax the limit.
- CV mode requires a stated maximum expected current; CR is checked at I = V/R.
- `Keysight6060B.connect()` raises `InterfaceBlocked` unless `interface_confirmed=True`; an operation runs only if every command it needs is VERIFIED against the official manuals (`6060B_COMMAND_EVIDENCE.md`) — none are today, so remote control is blocked twice over.
- No global minimum battery voltage: cutoff is per profile.
- Active loads: Keysight6060B, Manual6060B, Simulator6060B only. OWON/ITECH/Bitrode/Arbin/Chroma/Digatron are absent and tested absent.

## Unchanged and kept
Registry, QR IDs, photos, lifecycle, measurements, DCIR/thermal/BMS data,
grading, reports, battery passport, Learning Mode, Simulation Mode, software
BMS abstraction (`SMART_PACK_UNSUPPORTED` for unknown packs; never bypass BMS
protection).

## Known gaps (honest status)
- 6060B remote control: no confirmed GPIB path, and no command is VERIFIED
  (www.keysight.com is blocked from the build environment; the two official manuals were not readable).
- Orchestrator and dashboard are host/simulator-tested only (offscreen Qt); **no physical validation has been run** — see `BENCH_CHECKLIST.md`.
- The dashboard drives a *manual* 6060B: the operator sets/enables/disables the load; the orchestrator verifies from measurements.
- Firmware limits (18.5 A trip, 60 °C, 30/44 V defaults) are Rev.1 defaults, unchanged.
- Current-sensing redesign deliberately deferred (`CURRENT_SENSING_REDESIGN.md`).

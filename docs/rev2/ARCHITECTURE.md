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

## Rules enforced in code (tests: `tests/test_rev2_equipment.py`)
- Every load command passes `check_load_command` (V ≤ 60, ≥ 3; I ≤ 60; V·I ≤ 300 W; profile/OSBAMS/component limits) **before** any write.
- Power check uses the highest known pack voltage (OCV vs live) — a sagged reading cannot relax the limit.
- CV mode requires a stated maximum expected current; CR is checked at I = V/R.
- `Keysight6060B.connect()` raises `InterfaceBlocked` unless `interface_confirmed=True`; unverified SCPI is blocked by default.
- No global minimum battery voltage: cutoff is per profile.
- Active loads: Keysight6060B, Manual6060B, Simulator6060B only. OWON/ITECH/Bitrode/Arbin/Chroma/Digatron are absent and tested absent.

## Unchanged and kept
Registry, QR IDs, photos, lifecycle, measurements, DCIR/thermal/BMS data,
grading, reports, battery passport, Learning Mode, Simulation Mode, software
BMS abstraction (`SMART_PACK_UNSUPPORTED` for unknown packs; never bypass BMS
protection).

## Known gaps (honest status)
- 6060B remote control blocked: no confirmed GPIB path; official programming
  manual not retrievable at build time ⇒ only a subset of commands enabled.
- Test modes OCV/CC capacity/DCIR/sag/recovery/thermal/transient have
  simulator and data-model support; **no physical validation has been run.**
- A DCIR-step / SOH test orchestrator using the new drivers is not yet wired into the dashboard.
- `limit_panel.py` is not yet embedded in the dashboard and was not run
  (no display libraries in the build container).
- Firmware limits (18.5 A trip, 60 °C, 30/44 V defaults) are Rev.1 defaults, unchanged.

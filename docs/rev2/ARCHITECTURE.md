# OSBAMS Rev.2 architecture

## Identity
> OSBAMS Rev.2 is a standalone lithium-ion battery characterization platform
> optimized around the SFSU Agilent 6060B electronic load. It uses an
> STM32L476RG safety controller, Raspberry Pi 5 interface, INA228-based
> measurement, independent voltage verification, and Keysight reference
> instrumentation to validate capacity, energy, DCIR, thermal behavior, and
> battery health metrics of compatible lithium-ion battery packs within the
> verified hardware envelope.

Supported batteries: lithium-ion (NMC/NCA/LFP), approximately 30–42 V, 10S-class
(Ninebot/Segway, Shenzhen Elite). Connector: XT60, adapter only if needed.
Removed scope is recorded only in `docs/research/OUT_OF_SCOPE_FOR_REV2.md`.

## The Rev.2 equipment stack
1. **Agilent/Keysight 6060B** — the only external load; primary test load (CC/CV/CR; capacity, energy, DCIR steps).
2. **Keysight EDU34450A** — reference measurement for calibration/verification; not in the automated loop.
3. **Raspberry Pi 5 + 10.1" touchscreen** — UI: test control, live dashboard, SQLite database, battery passport, reports, analysis.
4. **STM32L476RG** — real-time safety controller: acquisition, relay control, fault handling, watchdog, E-stop monitoring.
5. **Power path** — battery → XT60 → fuse → disconnect → relay → current shunt → 6060B.
6. **Keysight EDUX1052G** — validation only: relay switching, shutdown timing, transients, load-enable behavior.

*The Pi requests actions. The STM32 authorizes them.* (Design principle; today the orchestrator supervises a manual 6060B and verifies load-off from measurements — it does not command the STM32.)

## Envelope
`allowed current = min(battery profile, OSBAMS hardware limit, 6060B current limit, 300 W / battery voltage)`
using the **conservative pack voltage** (max of OCV and highest seen, never lowered by sag) and including the
fuse, disconnect, relay, shunt, wiring and connector limits inside "OSBAMS hardware". 42 V → 7.14 A; 36 V → 8.33 A.
The 60 A rating never overrides 300 W. Operating ceiling: **≤ 44 V, ≤ 10 A (provisional)** until the power path is
physically validated. The firmware hard trip (18.5 A / 60 °C) is a separate protection boundary, not an input to the minimum.

## Test pipeline
```
battery profile → OCV screen → hardware safety check → 6060B capability calculation
→ controlled load test → live logging → Ah/Wh integration → DCIR step
→ automatic cutoff → recovery → SOH / report / passport
```
`services/test_orchestrator.py`: `CapacityTest` (OCV, constant-current discharge, Ah, Wh, voltage sag, thermal
monitoring, automatic profile cutoff, verified load-off, recovery) and a separate `DcirTest` (current steps). The
hardware safety check logs each check (registry status, temperature present and in limits, voltage envelope, positive
permitted current, ceiling below firmware trip, load idle) and blocks before any load command. FAULT paths always turn the
load off and verify it from measured current. Results: `services/run_persistence.py`; history, grading, report and
passport use the existing registry/DB/PDF modules. The dashboard shows pack voltage, profile limit, OSBAMS limit, 6060B
rating, power-derived limit, FINAL PERMITTED and the limiting factor.

## Code map (`desktop/equipment/`)
`capability.py` (envelope + invariant) · `inventory.py` (stack) · `drivers/` (`Keysight6060B` — blocked; `Manual6060B` — working mode; `Simulator6060B`) ·
`reference/` (EDU34450A calibration records) · `validation.py` (ordered bench workflow → `BENCH_CHECKLIST.md`).
Driver evidence: `6060B_DRIVER_EVIDENCE.md`.

## Smart BMS
Supported, documented low-voltage lithium-ion packs, normal read-only communication only. Nothing is implemented or verified,
so every pack reports `SMART_PACK_UNSUPPORTED`. No BMS bypass.

## Known gaps (honest status)
- 6060B remote control: no confirmed GPIB path and no command VERIFIED (the official manuals were not readable from the build environment).
- Orchestrator/dashboard are host- and simulator-tested only; the Pi 5 deployment is untested; **no physical validation has been run** — nothing is BENCH_TESTED or HARDWARE_VALIDATED.
- Power-path parts not yet read off the hardware; the 15 A fuse sits below the 18.5 A firmware trip (decision open).
- TC74 not brought up: thermal protection unvalidated; the safety check refuses to start without a temperature reading.
- No variable source is part of the stack, so voltage/current are verified at the pack's own operating points (`INSTRUMENT_CALIBRATION_PLAN.md`).

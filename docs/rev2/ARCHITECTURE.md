# OSBAMS Rev.2 architecture — lithium-ion, SFSU lab-optimized

## Claim (narrow)
> OSBAMS Rev.2 is an open lithium-ion battery characterization platform for
> supported battery packs within the validated OSBAMS hardware envelope and the
> Agilent 6060B electronic-load envelope.

Supported class: lithium-ion (NMC/NCA/LFP), approximately 10S, ~30–42 V
(Ninebot/Segway 36 V, Shenzhen Elite 37 V). Not claimed: NiMH or any other
chemistry, Dat Bike or 72 V, EV packs, 60 A testing at all voltages, full smart-BMS
support. Out-of-scope history lives only in `docs/research/OUT_OF_SCOPE_FOR_REV2.md`
and `legacy/rev1/`.

## Envelope (three different things)
| Layer | Value |
|---|---|
| 6060B instrument rating | 3–60 V, 60 A, **300 W** → `I = min(60 A, 300 W / V)` (the 60 A rating never overrides 300 W) |
| OSBAMS operating limits (provisional, until the power path is validated) | **≤ 44 V, ≤ 10 A** |
| Firmware hard trip (protection boundary, not an input to the minimum) | 18.5 A / 60 °C |

`final permitted = min(profile, OSBAMS 10 A, 60 A, 300 W / conservative pack voltage,
fuse, disconnect, relay/contactor, shunt/sensor, wiring, connector)`. The conservative
pack voltage is max(OCV, highest seen) and never decreases, so sag cannot raise current.
42 V → 7.14 A; 36 V → 8.33 A.

## Test pipeline
```
battery profile → OCV screen → hardware safety check → 6060B capability calculation
→ controlled load test → live logging → Ah/Wh integration → DCIR step
→ automatic cutoff → recovery → SOH / report / passport
```
`services/test_orchestrator.py` — `CapacityTest` (OCV, constant-current discharge,
Ah, Wh, voltage sag, thermal monitoring, automatic profile cutoff, verified
load-off, recovery) and a separate `DcirTest` (controlled current steps).
The hardware safety check logs each check (registry status, temperature present and in
profile limits, voltage inside the OSBAMS/6060B envelope, a positive permitted current,
ceiling below firmware trip, load idle). Push-based (`on_sample`); FAULT paths always
turn the load off and verify it from measured current. Results saved by
`services/run_persistence.py`; history, grading, report and battery passport use the
existing registry/DB/PDF modules. Dashboard: live limit panel (pack voltage,
profile limit, OSBAMS limit, 6060B rating, power-derived limit, FINAL PERMITTED,
limiting factor) plus phase/confirm controls.

## Equipment layer (`desktop/equipment/`)
- `capability.py` — the envelope model and the hard invariant `I × V_conservative ≤ 300 W`.
- `inventory.py` — 12 roles (matrix in `SFSU_EQUIPMENT_MATRIX.md`): 6060B primary load; EDU34450A / HP 34401A references; EDU36311A / HP E3630A sources; EDUX1052G / HP 54601B scopes; EDU33212A / HP 33120A generators; AD2; handheld DMM; OptiMate chargers = separate lab equipment, never in the test path.
- `drivers/` — `Keysight6060B` (blocked: no confirmed GPIB path and no command VERIFIED), `Manual6060B` (working mode), `Simulator6060B` (same envelope, 10S lithium-ion scenarios). Evidence: `6060B_DRIVER_EVIDENCE.md`.
- `reference/` — calibration records (EDU34450A primary, HP 34401A cross-check).
- `validation.py` — ordered bench workflow → `BENCH_CHECKLIST.md`.

## Smart BMS
Limited to supported, documented low-voltage lithium-ion packs, normal read-only
communication. Nothing is implemented or verified, so every pack reports
`SMART_PACK_UNSUPPORTED`. No BMS bypass.

## Known gaps (honest status)
- 6060B remote control: no confirmed GPIB path, and no command is VERIFIED (the two official manuals were not readable from the build environment).
- Orchestrator/dashboard are host- and simulator-tested only; **no physical validation has been run** — nothing is BENCH_TESTED or HARDWARE_VALIDATED.
- The dashboard drives a *manual* 6060B: the operator sets/enables/disables the load; the orchestrator verifies from measurements.
- Power-path parts are not yet read off the hardware (DG57CM suffix, shunt, fuse + holder, DC/DC); the 15 A fuse sits below the 18.5 A firmware trip (decision open).
- TC74 not brought up: thermal protection is unvalidated; the hardware safety check refuses to start without a temperature reading.

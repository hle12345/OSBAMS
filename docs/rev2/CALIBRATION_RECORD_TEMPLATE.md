# Calibration / verification record — TEMPLATE

Copy this file per session (e.g. `records/2026-xx-xx_NEB1002-H_C1.md`) and fill it in. Each measured point also goes
into the database with `equipment.reference.make_record(...)` + `save_record(conn, rec)` (table `calibration_records`).
**Write the acceptance tolerance BEFORE measuring.** No accuracy is claimed until a record is complete.

## 1. Session
| Field | Value |
|---|---|
| Date / time | |
| Operator | |
| Second person | |
| Software commit (`git rev-parse --short HEAD`) | |
| Bench-checklist step(s) (e.g. C1, C2, D1, E1) | |
| Battery (registry ID / serial) | |
| Ambient temperature | |
| Notes | |

## 2. Instruments used
| Instrument | Model | Serial | Asset ID | Calibration status / due date | Range / settings used |
|---|---|---|---|---|---|
| Reference DMM | Keysight EDU34450A | | | | |
| Load | Agilent/Keysight 6060B | | | | mode CC; settings: |
| Scope (if used) | Keysight EDUX1052G | | | | |
| OSBAMS | commit / firmware / INA228 shunt cal | | n/a | last OSBAMS verification: | |

Asset ID and calibration status stay **UNKNOWN** until read off the instrument — do not guess.

## 3. Acceptance tolerance (written before the run)
| Quantity | Tolerance (absolute and/or %) | Basis (why this value) |
|---|---|---|
| Voltage | | |
| Current | | |
| Power | | |
| Temperature | | |

## 4. Measurements
One row per point. `abs error = |OSBAMS − reference|`, `% error = 100 × abs error / reference`.

| # | Quantity | Channel | Condition / setpoint | EDU34450A (reference) | OSBAMS | 6060B readback | Abs error | % error | Within tolerance? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | voltage | INA228 bus | OCV, relay open | | | n/a | | | | |
| 2 | voltage | ADC divider | OCV, relay open | | | n/a | | | | |
| 3 | temperature | TC74 | ambient | | | n/a | | | | |
| 4 | current | INA228 / shunt | 0.1 A | | | | | | | |
| 5 | current | INA228 / shunt | 0.25 A | | | | | | | |
| 6 | current | INA228 / shunt | 0.5 A | | | | | | | |
| 7 | voltage | INA228 bus | under 0.5 A | | | | | | | |
| 8 | voltage | INA228 bus | run start | | | | | | | |
| 9 | voltage | INA228 bus | run middle | | | | | | | |
| 10 | voltage | INA228 bus | run end (near cutoff) | | | | | | | |
| 11 | power | INA228 | 1.0 A run | (V×I from references) | | | | | | |

Burden check when the EDU34450A is in series in current mode: DMM burden voltage ____ V; effect on the pack current considered? ☐

## 5. Result (fill in after the run; do not pre-fill)
- Largest voltage error: ____  at ____ V  |  Largest current error: ____ at ____ A
- ADC vs INA228 vs reference agreement: ____
- Is the existing shunt adequate at the 1–3 A test currents (tolerance from §3)? ☐ yes ☐ no ☐ undecided
- Records saved to the database (record IDs): ____
- Step status for `ValidationLog` (PASS needs operator + data location): ☐ PASS ☐ FAIL — data location: ____
- Anything unexpected: ____

Operator signature / date: ____________

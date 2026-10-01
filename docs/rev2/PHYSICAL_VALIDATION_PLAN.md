# Rev.2 physical validation plan (SFSU equipment only)

Every row is **NOT RUN**. A row becomes PASS only with recorded data (operator,
date, instrument asset IDs, software commit). Equipment: 6060B, EDU34450A,
EDU36311A, EDUX1052G, EDU33212A, Analog Discovery 2, handheld DMM
(`desktop/equipment/inventory.py`). Never command the 6060B outside
V ≤ 60, I ≤ 60, V×I ≤ 300 W and the permitted current from `capability.py`.

## Phase 0 — interface and instruments
| ID | Test | Equipment | Pass criterion | Status |
|---|---|---|---|---|
| REV2-00 | Record asset ID / calibration status of every instrument | all | all fields filled in `inventory.py`/records | NOT RUN |
| REMOTE-01 | Confirm GPIB path (`GPIB_INTERFACE_CONFIRMATION.md`) | 6060B + adapter | `*IDN?` returns 6060B | NOT RUN (blocked) |
| REMOTE-02 | Confirm each UNVERIFIED command against the manual | manual + 6060B | table updated | NOT RUN |

## Phase 1 — low-energy commissioning (no battery)
| ID | Test | Equipment | Pass criterion | Status |
|---|---|---|---|---|
| REV2-10 | INA228 voltage calibration, 3–30 V steps | EDU36311A vs EDU34450A | records in `calibration_records`; error reported (no tolerance assumed) | NOT RUN |
| REV2-11 | Current verification 0.1–1 A | EDU36311A CH1/2/3 + EDU34450A | error recorded | NOT RUN |
| REV2-12 | ADC divider cross-check vs INA228 | EDU36311A (CH2+CH3 series ≤ 60 V per manufacturer docs) | disagreement flag fires at injected error | NOT RUN |
| REV2-13 | Threshold/state-machine tests (UV/OV/OT) | EDU36311A, EDU33212A | firmware faults at set thresholds | NOT RUN |
| REV2-14 | Sensor fault injection (TC74/INA228 loss) | bench | sensor-fault state reached | NOT RUN |
| REV2-15 | UART/I²C/PWM protocol checks | AD2 / EDUX1052G | frames decode; CRC valid | NOT RUN |

## Phase 2 — switching and safety timing
| ID | Test | Equipment | Pass criterion | Status |
|---|---|---|---|---|
| REV2-20 | E-stop → contactor open, independent of firmware | EDUX1052G | time recorded; opens with MCU held in reset | NOT RUN |
| REV2-21 | Contactor close/open timing, precharge/inrush | EDUX1052G, EDU36311A | times recorded | NOT RUN |
| REV2-22 | Fault shutdown timing, supply startup | EDUX1052G | recorded | NOT RUN |
Scope probing only on appropriately rated probes/grounding; high-energy nodes are not probed casually.

## Phase 3 — 6060B envelope (resistor/supply first, then battery)
| ID | Test | Equipment | Pass criterion | Status |
|---|---|---|---|---|
| REV2-30 | Manual CC points at 5/12/24 V: verify permitted current vs front panel | 6060B + supply source, EDU34450A | 6060B readback vs reference error recorded | NOT RUN |
| REV2-31 | Power-limit behaviour: confirm the instrument's 300 W limit at 42 V | 6060B | software never reaches it; documented | NOT RUN |
| REV2-32 | Three-way comparison OSBAMS vs 6060B vs EDU34450A (V, I) | all | records saved | NOT RUN |
| REV2-33 | Current-sense accuracy 0.1–10 A (and up to the new range if Option A is built) | EDU34450A | error vs range documented; decide on `CURRENT_SENSING_REDESIGN.md` Option C | NOT RUN |

## Phase 4 — battery characterization (real packs, supervised)
Order: lowest-risk pack first (NEB1002, 5.2 Ah, ≤ 1 A).
| ID | Test | Pass criterion | Status |
|---|---|---|---|
| REV2-40 | OCV + safety checks + permitted-current display | permitted = min(...) shown, ≤ 7.14 A at 42 V | NOT RUN |
| REV2-41 | CC capacity to profile cutoff; Ah = ∫I dt, Wh = ∫VI dt | automatic cutoff; Ah/Wh vs 6060B and EDU34450A | NOT RUN |
| REV2-42 | DCIR current step, R = ΔV/ΔI | repeatable across ≥ 3 steps | NOT RUN |
| REV2-43 | Voltage sag and recovery after load removal | curves stored | NOT RUN |
| REV2-44 | Thermal: pack/shunt temperature during discharge | stops at profile limit | NOT RUN |
| REV2-45 | 6060B transient (needs REMOTE-02 for the transient commands) | current-step on scope matches setpoint | NOT RUN |
| REV2-46 | SOH_capacity vs reference capacity; passport + report saved | report reproducible | NOT RUN |
| REV2-47 | Repeat on Shenzhen Elite, then NEE1006-M (units with BMS issues flagged in intake notes are tested only after inspection) | per above | NOT RUN |

## End-to-end demonstration (target)
select battery → identify/profile → OCV → safety checks → compute 6060B
envelope → controlled discharge → V/I/P/T → compare OSBAMS vs 6060B vs
EDU34450A → Ah/Wh → DCIR step → automatic cutoff → recovery → SOH → battery
passport → report. Until REV2-4x are PASS this is a **design target, not a claim**.

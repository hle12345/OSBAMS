# Serial protocol v2 — design, host reference and firmware encoder (not wired in)

**Status: design, a host reference implementation (`desktop/services/protocol_v2.py`) and a host-tested C encoder (`Protocol_EncodeDataV2` in `Firmware/App/Src/protocol.c`, tests in `Firmware/Tests/test_protocol_v2.c`). The firmware still SENDS protocol v1: `OSBAMS_PROTOCOL_VERSION` is 1 and `main.c` does not call the v2 encoder. The INA228 CHARGE/ENERGY support, the STM32 integrator and the accumulator session exist as host-tested modules but are NOT called from main.c, so the v2 fields are not filled on hardware. Nothing here has run on hardware.** v1 (`services/protocol.py`, CRC-16/CCITT-FALSE) stays authoritative for the existing firmware and is
still accepted by `parse_any`.

## Why
The three-way capacity cross-check (`VALIDATION_AND_CALIBRATION_PLAN.md` §4) needs three things v1 does not carry: the independent STM32
ADC voltage, the INA228's own charge/energy accumulators, and the STM32's own timestamp-based integration, plus counters and a
sensor-status word so the Pi can tell "unavailable" from "zero" and "lost frame" from "lost acquisition".

## Frame
`OSBAMS,2,<seq>,<tick_ms>,<V_mV>,<I_mA>,<P_mW>,<T_C10>,<flags>,<state>,<V_adc_mV>,<Q_ina_uAh>,<Q_mcu_uAh>,<E_ina_uWh>,<E_mcu_uWh>,<acq_count>,<sensor_status>,<CRC16>`
(18 fields). Fields 0–9 mean exactly what they mean in v1. Fields 10–14 are integers or the literal `NA`; `NA` is never replaced by 0.
Field table, accumulator rules and `sensor_status` bits: module docstring of `protocol_v2.py` (SS_INA_FAULT, SS_ADC_FAULT, SS_TEMP_FAULT,
SS_ACCUM_INVALID, SS_TIME_JUMP).

## Rules
1. v1 backward compatibility: a v2 reader accepts v1 frames (new fields unavailable); a v1 reader never sees a v2 frame unless the
   firmware is upgraded.
2. All four accumulators reset together at an explicit test-start command. A decrease between frames, or `SS_ACCUM_INVALID`, makes the
   Pi flag `CAPACITY_VALIDATION_WARNING`; it never silently re-baselines.
3. INA228 accumulators are valid only when ADCRANGE/SHUNT_CAL match the active calibration profile (firmware sets `SS_ACCUM_INVALID` otherwise).
4. Like-for-like: the device integrates its own uncalibrated readings, so the agreement check uses the RAW Pi samples; the calibrated Pi
   result is reported separately and is the one used for capacity retention.
5. Nothing in the protocol can change relay, E-stop or load-control behaviour.

## Test-first firmware plan (steps 1–2 done)
Golden frames: `docs/rev2/protocol_v2_test_vectors.json` (valid, NA fields, v1 still accepted, bad CRC, wrong field count). Host tests:
`tests/test_protocol_v2_and_data.py`. Firmware order of work: (1) DONE: C tests in `Firmware/Tests/test_protocol_v2.c` encode these vectors byte for byte, and `tests/test_protocol_v2_and_data.py` checks the C literals against the JSON and parses the C output with the Python parser; (2) DONE: encoder implemented (pure formatting, v1 untouched); (3) expose the INA228 CHARGE/ENERGY registers; (4) add STM32 timestamp integration; (5) bench-compare on the
first-article rig. The Pi side and the AI/data work do not wait for any of this.

## Pi-side comparison at test completion
`services/capacity_validation.py`: `AccumulatorTracker` consumes samples, `validate()` returns Ah and Wh per method, % disagreement,
sample and missing-sample counts, calibration id, firmware version, PCB revision, and status `OK` / `CAPACITY_VALIDATION_WARNING` /
`INSUFFICIENT` (fewer than two totals available — never reported as agreement). The warning threshold is **PROVISIONAL** (default 1 %,
configurable) until bench data set it. Persisted by `run_persistence.save_capacity_validation`.

## Firmware modules (host-tested, not wired into live telemetry)
| Module | Files | What it does |
|---|---|---|
| INA228 CHARGE/ENERGY | `Drivers/Src/ina228.c` (`INA228_ReadAccumulators`, `INA228_ResetAccumulators`, decode and scaling helpers), `Tests/test_ina228_accum.c` | 40-bit decode; `Charge[C] = CURRENT_LSB x CHARGE` (signed), `Energy[J] = 16 x 3.2 x CURRENT_LSB x ENERGY` (unsigned), both from the TI datasheet SLYS021A (eq. 6, 7; `docs/rev2/pcb/evidence/`); uses the truncated CURRENT_LSB (38146 nA at the 20 A scale) that `INA228_Init` actually programs. ENERGY decrease latches `INA228_ACCUM_F_DECREASE` (rollover/reset): never unwrapped. RSTACC (CONFIG bit 14) is written 1 then 0 (not self-clearing); a reset whose read-back energy is not below the pre-reset value is reported as a failure. |
| STM32 integrator | `App/Src/integrator.c`, `Tests/test_integrator.c` | integrates |I| and |P| with the actual elapsed time (trapezoid, mA*us and mW*us, no per-interval truncation; the older `measurement.c` path truncates each interval to whole milliseconds and is left untouched). Explicit reset. Gap longer than the limit, non-advancing timestamp, invalid sample and 64-bit overflow each have defined, latched behaviour (never zero-filled, never wrapped). Totals are unavailable until the first interval exists. |
| Accumulator session | `App/Src/accum_session.c`, `Tests/test_accum_session.c` | `AccumSession_Start` resets the INA228 and STM32 accumulators together and refuses outside IDLE/PACK_DETECTED/PRECHECK/READY/COMPLETE (so no command can zero totals during RESTING/DISCHARGING/PAUSED/CUTOFF/RECOVERY/FAULT/E_STOP). Line command `ACCUM_START` -> `OSBAMS,ACCUM,STARTED` / `STARTED_HW_RESET_FAILED` / `REFUSED,STATE`. `AccumSession_BuildExtra` assembles the v2 fields (ADC voltage, INA228 charge/energy, STM32 charge/energy, acquisition count, status bits; `NA` where unavailable, a measured zero stays 0). A failed INA228 reset still resets the STM32 side, sends the INA228 fields as `NA` and sets ACCUM_INVALID until the next clean start. |

Sign convention: Q_ina follows the shunt polarity (signed); Q_mcu, E_mcu and E_ina are magnitudes. The Pi compares magnitudes and treats a decrease of |total| as a reset (`capacity_validation.py`).
Status bits added beyond the original five: `SS_INTEG_GAP` (1<<5) and `SS_SAMPLE_INVALID` (1<<6). Nothing here touches relay, E-stop, load-enable or the safety state machine; `OSBAMS_PROTOCOL_VERSION` stays 1.

Cross-checks in `tests/test_protocol_v2_and_data.py`: the C integrator and `services/charge_integration.py` agree on an irregular negative-polarity stream (Ah within 1e-4 relative, Wh within 2e-3); the C encoder output parses with the Python parser.

## BENCH_REQUIRED (not asserted by any host test; no constants invented)
- INA228 ENERGY/CHARGE against the EDU34450A integrated Ah on a real discharge; accumulator accuracy with the real RSA-20-50 shunt and ADC averaging settings (accumulation runs per conversion cycle, before averaging).
- Shunt polarity (sign of CHARGE) and high-side/low-side question (open item in CLAUDE.md).
- ENERGY register range: at the 20 A scale (38146 nA LSB) the 40-bit ENERGY register rolls over at about 600 Wh; confirm and decide whether larger tests need a firmware unwrap policy (today: flag only).
- CHARGE and ENERGY are read in two separate I2C transactions: measure the skew between them.
- RSTACC timing: delay needed between the reset write and a valid read-back; reset read-back tolerance (today only "below the pre-reset energy").
- `INTEG_DEFAULT_MAX_GAP_US` (10 s) is provisional: set from measured acquisition-timer jitter.
- Wiring `AccumSession_*` and `INA228_ReadAccumulators` into `main.c` (target build, UART command line handling, telemetry period) and a dev-only opt-in switch for the v2 frame.
- Agreement threshold between the three methods (Pi default 1 %, provisional).

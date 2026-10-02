# Serial protocol v2 — design, host reference and firmware encoder (not wired in)

**Status: design, a host reference implementation (`desktop/services/protocol_v2.py`) and a host-tested C encoder (`Protocol_EncodeDataV2` in `Firmware/App/Src/protocol.c`, tests in `Firmware/Tests/test_protocol_v2.c`). The firmware still SENDS protocol v1: `OSBAMS_PROTOCOL_VERSION` is 1 and `main.c` does not call the v2 encoder. The INA228 CHARGE/ENERGY registers and the STM32 timestamp integration are not yet exposed, so the v2 fields cannot be filled on hardware. Nothing here has run on hardware.** v1 (`services/protocol.py`, CRC-16/CCITT-FALSE) stays authoritative for the existing firmware and is
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

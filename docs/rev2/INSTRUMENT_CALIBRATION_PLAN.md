# Instrument calibration plan

Purpose: establish the **actual** error of each OSBAMS channel against independent
references before any battery is connected. No tolerance is claimed anywhere until
these records exist. Records use `equipment.reference.make_record` and the
`calibration_records` table (model, asset ID, calibration status, reference
reading, OSBAMS reading, absolute and percent error, timestamp, software commit,
operator, optional 6060B readback, optional HP 34401A cross-check).

| Quantity | OSBAMS channel | Primary reference | Cross-check | Source | Points (minimum) | Step |
|---|---|---|---|---|---|---|
| Voltage | INA228 bus | EDU34450A | HP 34401A | EDU36311A (CH2; CH2+CH3 series per manual), HP E3630A | 3, 5, 10, 20, 30 V, then series points toward 44 V | C1, D2 |
| Voltage | STM32 ADC divider | EDU34450A | HP 34401A | EDU36311A | 5–30 V + injected divider error | C2 |
| Current | INA228 / shunt | EDU34450A (current range/fuse checked first) | HP 34401A; 6060B panel readback | EDU36311A CH1 into a resistor; later 6060B on a supply | 0.1, 0.25, 0.5, 1.0 A (supply limit); battery currents at the I-steps | E1, E2 |
| Power | INA228 | computed V×I from the two references | 6060B readback | as above | same points | E2 |
| Resistance | (DCIR check) | EDU34450A | HP 34401A | known resistor | 2–3 values bracketing the pack DCIR | D1 |
| Continuity / polarity | wiring | handheld DMM | EDU34450A | — | all power-path joints | A2 |
| Temperature | TC74 | EDU34450A temperature function | — | ambient + warmed point | 2 points | C3 |

Procedure per point: settle, read all instruments together, `make_record(...)`,
`save_record(conn, rec)`. Compare EDU34450A vs HP 34401A first (D1); if they
disagree beyond the tolerance set beforehand, resolve that before trusting either.

Intervals: `config.CALIBRATION_INTERVAL_DAYS` (90) for OSBAMS channels; reference
DMM calibration status is read off each instrument (A1) and stays UNKNOWN until then.

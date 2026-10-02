# Instrument verification / calibration plan

Purpose: establish the **actual** error of each OSBAMS channel against the EDU34450A
before relying on any number. No tolerance is claimed anywhere until records exist.
Records: `equipment.reference.make_record` and the `calibration_records` table
(reference model, asset ID, calibration status, reference reading, OSBAMS reading,
absolute and percent error, timestamp, software commit, operator, optional 6060B readback).

| Quantity | OSBAMS channel | Reference | Where the points come from | Step |
|---|---|---|---|---|
| Pack voltage | INA228 bus | EDU34450A | pack OCV with the relay open; spot checks at start, mid and end of runs | C1, E1 |
| Pack voltage | independent ADC divider | EDU34450A (and the INA228) | same moment as C1; disagreement-fault threshold exercised by configuration | C2 |
| Current | INA228 / shunt | EDU34450A in series (current range/fuse checked first); 6060B panel readback | 0.1, 0.25, 0.5 A low-current run, then profile currents | D1, E1 |
| Power | INA228 | V × I from the references; 6060B readback | same points | D1, E1 |
| Resistance / continuity / polarity | wiring | EDU34450A | all power-path joints, power off | A2 |
| Temperature | TC74 | EDU34450A temperature function | ambient, then during runs | C3, E3 |

Procedure per point: settle, read the instruments together, `make_record(...)`,
`save_record(conn, rec)`. The acceptance tolerance is written beforehand by the operator.

Limitation: there is no swept source in the stack, so voltage is verified at the pack's
own operating points rather than over a 3–44 V sweep, and nothing is adjusted — the
result is a characterized error. Reference calibration status is read off the
EDU34450A (A1) and stays UNKNOWN until then. OSBAMS channel interval:
`config.CALIBRATION_INTERVAL_DAYS` (90).

# Rev.2 hardware validation plan (36–42 V lithium-ion packs)

Equipment: only what `SFSU_EQUIPMENT_MATRIX.md` lists. Every step starts
**NOT_RUN**; nothing is BENCH_TESTED or HARDWARE_VALIDATED. The exact step list
is `BENCH_CHECKLIST.md` (generated from `desktop/equipment/validation.py`;
track results with `ValidationLog`).

## The workflow, in the required order
| # | Goal | Instruments | Checklist steps |
|---|---|---|---|
| 0 | Record identities, inspect and record the power-path parts | all, handheld DMM | A1, A2 |
| 1 | Safe low-energy commissioning | EDU36311A (primary), HP E3630A (manual) | B1, B2 |
| 2 | Calibrate OSBAMS voltage against the EDU34450A (INA228 + ADC channel, temperature) | EDU36311A, EDU34450A | C1, C2, C3 |
| 3 | Cross-check with the HP 34401A | HP 34401A, EDU34450A | D1, D2 |
| 4 | Validate current measurement against 6060B readback and DMM where practical | 6060B (manual), EDU34450A, HP 34401A | E0–E3 |
| 5 | Capture contactor / load-enable and fault-shutdown timing | EDUX1052G (HP 54601B optional) | F1–F3 |
| 6 | UART / I²C debugging and capture | Analog Discovery 2 (EDU33212A / HP 33120A for injection) | G1 |
| 7 | Orchestrator dry run on a supply, no battery | EDU36311A, 6060B (manual) | H1, H2 |
| 8 | **Only then** connect a real 36–42 V pack | 6060B, references, EDUX1052G | I1–I6 |
| — | Remote control (blocked: no confirmed GPIB path; no command VERIFIED) | — | J1–J4 |

Rules for every step
- The operator writes the acceptance tolerance into the record **before** the run; no accuracy figure is claimed until then.
- A step is PASS only with an operator, recorded data and every prerequisite PASS (`ValidationLog`).
- Never deliberately exceed 300 W on the 6060B. The dashboard's FINAL PERMITTED value is the setpoint ceiling.
- Probe only with rated probes and good grounding; the scope's input rating is not permission to probe high-energy nodes.
- OptiMate chargers are never connected to a 36–42 V pack or to OSBAMS.
- Packs with BMS anomalies in the intake notes are inspected and judged safe before any connection.

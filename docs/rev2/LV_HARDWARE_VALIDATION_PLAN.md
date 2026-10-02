# Rev.2 hardware validation plan (36–42 V lithium-ion packs)

Equipment: the 6060B (the actual battery load), the EDU34450A (reference
measurement) and the EDUX1052G (validation-only observation), plus the OSBAMS stack
itself — see `SFSU_EQUIPMENT_MATRIX.md`. Every step starts **NOT_RUN**; nothing is
BENCH_TESTED or HARDWARE_VALIDATED. The exact step list is `BENCH_CHECKLIST.md`
(generated from `desktop/equipment/validation.py`; track results with `ValidationLog`).

## The workflow
| Phase | Goal | Instruments | Steps |
|---|---|---|---|
| A | Record identities; inspect and record the power-path parts | EDU34450A | A1, A2 |
| B | Bench bring-up with **no battery**: sensors, frames, fault handling, relay coil-side timing | EDUX1052G | B1–B3 |
| C | Pack connected, **relay open, no load**: OCV verification, ADC cross-check, temperature, dashboard envelope check | EDU34450A | C1–C4 |
| D | First supervised **low-current** load (≤ 0.5 A): current comparison, E-stop/shutdown timing under load | 6060B (manual), EDU34450A, EDUX1052G | D1, D2 |
| E | Full characterization of the 36–42 V packs: capacity, DCIR, thermal, other packs, report/passport | 6060B (manual), EDU34450A | E1–E5 |
| F | Remote control — blocked (no confirmed GPIB path; no command VERIFIED) | — | F1–F4 |

## Rules for every step
- The operator writes the acceptance tolerance into the record **before** the run; no accuracy figure is claimed until then.
- A step is PASS only with an operator, recorded data and every prerequisite PASS (`ValidationLog`).
- The first loaded run (D1) is gated on every earlier non-optional step.
- Never deliberately exceed 300 W on the 6060B. The dashboard's FINAL PERMITTED value is the setpoint ceiling.
- Probe only with rated probes and good grounding; the scope's input rating is not permission to probe high-energy nodes.
- Packs with BMS anomalies in the intake notes are inspected and judged safe before any connection.

## Limits of this workflow (read before relying on it)
There is no variable bench source in the Rev.2 stack, so voltage and current are
**verified** against the EDU34450A at the pack's own operating points (OCV with the
relay open, then spot checks during low-current and full runs). The error of each
channel is characterized and recorded; it is not "calibrated" over a swept range.
Fault thresholds that would need an injected voltage are exercised only through
configuration (profile limits) and host/firmware tests.

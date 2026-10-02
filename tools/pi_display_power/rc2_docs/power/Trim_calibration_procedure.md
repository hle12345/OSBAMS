# Per-unit trim calibration — RSDW40F-05 (Rev.A first articles)

Decision: each unit is calibrated on the **assembled system**; the calculated Rt is **not** universal (RSDW accuracy ±1 % + line/load/temperature terms, plus the unit's real connector/socket/harness drops). **R3 (TRIM → −Vout, PI_GND) is the trim-up resistor, fitted only by this procedure from the E96 kit (61.9k / 71.5k / 84.5k, Yageo RC0603FR-07…L). R2 has no part (trim-down is never used).** The calibration setpoint window and its width are in `Power_budget_report.md` (typical-resistance window ≈ 5.10–5.20 V; worst-path window is closed by design - which is why the contact resistances are measured in `First_article_checklist.md` Part A6).

Target: **≥ 4.85 V at the Pi header pins at the intended worst-case load (5 A)** and **≤ 5.25 V no-load**. Keep the 4.85 V target; do not relax it toward the Pi floor.

## Equipment
Bench supply for the 12 V bus (current-limited 5 A), electronic load rated ≥ 8 A at 5 V with 4-wire sense, DMM (≥ 5½ digit preferred), thermocouple, the real harness + interposer (or a calibration fixture with the same connectors), 0603 resistors from the E96 series (1 % or better).

## Steps
1. **Assemble** the power board with R3 **unfitted** (R2 has no part). No Pi connected.
2. **Polarity/continuity (power off):** confirm `+5V_PI` ≠ `PI_GND` (no short), J_OUT pins 1,2 = +5 V, 3,4 = GND, and ≥ 1 MΩ between `12V_GND` and `PI_GND` (isolation).
3. **Power on, no load:** apply 12 V (current-limit 1 A); measure `5V_ISO_RAW` (TP3), `5V_PI` (TP4) and **at the interposer/Pi-end connector**. Record **V_unt,no-load** (expected 5.00 V ±1.7 %). Confirm PG LED lit.
4. **Load at the Pi end:** connect the electronic load at the Pi-end connector (through the harness and interposer). Draw **5.0 A** at the Pi pins (and log 3 A). With the display fed from J_DISP, add its measured current (≈1 A) as a second load at J_DISP, or add its drop through the shared PCB/F2 path (≈ 1 A × 12 mΩ ≈ 12 mV) when the display is not connected. Let it thermally settle 10 min; record **V_pi,loaded** measured *at the Pi-end connector/header*, not at the DC/DC output, plus module case and ambient temperature.
5. **Calculate:** `python3 tools/pi_display_power/trim_calibration.py V_unt,no-load V_pi,loaded 5.0` → prints the required R3 and predicted no-load/loaded voltages (uses this unit's measured reference and the Mean Well formula `Rt = aR2/(R2−a) − R3`).
6. **Fit R3** (nearest E96). Re-measure no-load and 5 A loaded at the Pi-end connector. Accept only if **loaded ≥ 4.85 V** and **no-load ≤ 5.25 V** (also check at 3 A and during a load step 0→5 A for droop/ripple, spec ripple 100 mVp-p at 20 MHz).
7. If it cannot satisfy both limits, **reject the unit** and investigate path resistance (connector crimps, solder fill) — do not trade away the 4.85 V target.
8. **Record** in the acceptance record in `First_article_checklist.md`. Keep the same harness/interposer for the measurement and for the final unit; repeat if either changes. Ambient temperature drift (0.05 %/°C) is part of first-article validation, not recalibration.

## Acceptance record (one per unit)
| Field | Value |
|---|---|
| Board serial / RSDW lot-date code | |
| Harness + interposer ID, length | |
| Ambient / module case temp (°C) | |
| V_unt,no-load (R3 unfitted) | |
| V_pi,loaded @ 5 A (R3 unfitted) | |
| Effective path R (mΩ) from script | |
| R3 calculated / fitted (kΩ, E96) | |
| No-load after trim at Pi-end (V) — limit ≤ 5.25 | |
| 3 A loaded at Pi-end (V) | |
| 5 A loaded at Pi-end (V) — limit ≥ 4.85 | |
| Ripple at Pi-end (mVp-p, 20 MHz) — limit ≤ 100 | |
| Harness/connector max temp rise at 5 A, 30 min (°C) | |
| Pass / Fail, operator, date | |

Safety: R3 must never be fitted on the basis of the nominal calculation alone; an incorrect value could over-voltage the Pi. Verify polarity and the no-load limit before ever connecting a Pi.

**Correction (RevB review):** one E96 step of R3 (71.5 k → 73.2 k) changes the module output by only about **3 mV**, and a 1 % resistor by about 1 mV. The earlier statement of "~20 mV per E96 step" was wrong (20 mV is the spread between the three kit values 61.9 k / 71.5 k / 84.5 k). The calibration therefore resolves the setpoint finely; the limiting factor is the window width, not the resistor step. See `Voltage_drop_report.md` of RevB RC1.

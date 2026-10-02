# Per-unit trim calibration — RSDW40F-05 (Rev.A first articles)

Decision (carrier RevB): each unit is calibrated on the **assembled board**; the calculated Rt is **not** universal (RSDW accuracy ±1 % + line/load/temperature terms, plus the unit's real connector/socket/harness drops). **R3 (TRIM → −Vout, PI_GND) is the trim-up resistor, fitted only by this procedure from the E96 kit (61.9k / 71.5k / 84.5k, Yageo RC0603FR-07…L). R2 has no part (trim-down is never used).** The calibration setpoint window and its width are in `Power_budget_report.md` (carrier: worst-path window for the 4.85 V target ≈ 5.07–5.20 V, typical ≈ 5.03–5.20 V; one E96 step of R3 changes the output by ~3 mV, a 1 % resistor by ~1 mV — `Voltage_drop_report.md` §3).

Target: **≥ 4.85 V at the Pi header pins at the intended worst-case load (5 A)** and **≤ 5.25 V no-load**. Keep the 4.85 V target; do not relax it toward the Pi floor.

## Equipment
Bench supply for the 12 V bus (current-limited 5 A), electronic load rated ≥ 8 A at 5 V with 4-wire sense, DMM (≥ 5½ digit preferred), thermocouple, the carrier, and a **Pi-header test adapter** (a 2 × 20 male header board that brings Pi pins 2 and 4 together and pins 6, 9, 14, 20 together to 4-wire terminals; it plugs into the carrier's SSW socket exactly as the Pi does), 0603 resistors from the E96 series (1 % or better).

## Steps
1. **Assemble** the power board with R3 **unfitted** (R2 has no part). No Pi connected.
2. **Polarity/continuity (power off):** confirm `+5V_PI` ≠ `PI_GND` (no short), J_OUT pins 1,2 = +5 V, 3,4 = GND, and ≥ 1 MΩ between `12V_GND` and `PI_GND` (isolation).
3. **Power on, no load:** apply 12 V (current-limit 1 A); measure `5V_ISO_RAW` (TP3), `5V_PI` (TP4) and **at the Pi-header test adapter**. Record **V_unt,no-load** (expected 5.00 V ±1.7 %). Confirm PG LED lit.
4. **Load at the Pi end:** connect the electronic load at the Pi-header test adapter. Draw **5.0 A** at the Pi pins (and log 3 A). With the display fed from J_DISP, add its measured current (0.8 A typical, 1.0 A design scenario) as a second load at J_DISP, or add its drop through the shared PCB/F2/module-pin path (≈ 1 A × 12 mΩ ≈ 12 mV) when the display is not connected. Let it thermally settle 10 min; record **V_pi,loaded** measured *at the Pi-end connector/header*, not at the DC/DC output, plus module case and ambient temperature.
5. **Calculate:** `python3 tools/pi_display_power/trim_calibration.py V_unt,no-load V_pi,loaded 5.0` → prints the required R3 and predicted no-load/loaded voltages (uses this unit's measured reference and the Mean Well formula `Rt = aR2/(R2−a) − R3`).
6. **Fit R3** (nearest E96). Re-measure no-load and 5 A loaded at the Pi-end connector. Accept only if **loaded ≥ 4.85 V** and **no-load ≤ 5.25 V** (also check at 3 A and during a load step 0→5 A for droop/ripple, spec ripple 100 mVp-p at 20 MHz).
7. If it cannot satisfy both limits, **reject the unit** and investigate path resistance (connector crimps, solder fill) — do not trade away the 4.85 V target.
8. **Record** in the acceptance record in `First_article_checklist.md`. Keep the same adapter and measurement points; repeat if R3, F2 or the Pi socket changes. Ambient temperature drift (0.05 %/°C) is part of first-article validation, not recalibration.

## Acceptance record
See `First_article_checklist.md` (one record per unit).

# 5 V power-budget report (RC2)

Topology (RC2): `RSDW40F-05 +VOUT -> PCB copper -> F2 -> [5V_PI node]`; from the node two branches: (a) **Pi branch**: J_OUT -> 16 AWG harness -> interposer J1 -> interposer copper -> SSW-120 socket -> Pi pins 2/4 (+5 V) and 6/9/14/20 (GND); (b) **display branch**: J_DISP (Micro-Fit 430450200) -> display lead. The display is fed directly from the board because the interposer covers the Pi header (see `Waveshare_integration.md`), so display current does not pass through the harness, the interposer or the socket. Both loads share only the PCB copper and F2.

Inputs: `datasheet_inputs.json` (source/status per value, see `Parts_and_sources.md`). Targets: **Pi pins >= 4.85 V at the maximum intended Pi load, worst case**; **<= 5.25 V at no load / high line**; Pi under-voltage region begins near 4.75 V or lower (design floor 4.75 V). Calibrated unit: module setpoint **5.185 V** (25 C, no load); line 0.2 %, load 0.5 % over 0-8 A, temperature 0.05 %/C x 15 C = 0.75 %.

## 1. Element drops

| Element | carries | R typ (mOhm) | R worst (mOhm) | drop @3 A typ / worst (mV) | drop @5 A typ / worst (mV) |
|---|---|---|---|---|---|
| PCB copper (2 oz, +5 V and GND paths, from layout squares) | Pi + display | 2.2 | 2.2 | 7 / 7 | 11 / 11 |
| F2 output fuse 0451008.MRL (7.7 mOhm cold; 1.3x hot) | Pi + display | 7.7 | 10.0 | 23 / 30 | 38 / 50 |
| J_OUT Micro-Fit 430450400 (2 contacts/rail, 5.24 typ / 10 max mOhm per contact) | Pi only | 5.2 | 10.0 | 16 / 30 | 26 / 50 |
| Harness 16 AWG, 150 mm, 2 wires/rail (hot 1.2x) | Pi only | 2.0 | 2.4 | 6 / 7 | 10 / 12 |
| Interposer J1 Micro-Fit (2 contacts/rail) | Pi only | 5.2 | 10.0 | 16 / 30 | 26 / 50 |
| Interposer copper (estimate 2 mOhm/rail) | Pi only | 4.0 | 4.0 | 12 / 12 | 20 / 20 |
| SSW-120 socket contacts (20 mOhm/contact max; 2 on +5 V, 4 on GND; typ = 0.6x) | Pi only | 9.0 | 15.0 | 27 / 45 | 45 / 75 |
| **Shared (PCB + fuse)** | | **9.9** | **12.2** | **30 / 37** | **49 / 61** |
| **Pi branch (connectors, harness, interposer, socket)** | | **25.5** | **41.4** | **76 / 124** | **127 / 207** |
| **Total to the Pi pins** | | **35.4** | **53.6** | **106 / 161** | **177 / 268** |

Fuse drop (F2) and connector/contact drop (J_OUT + J1 + SSW socket) are separate rows. F1 (input side, 0407008.WR, 9 mOhm / 12.1 mOhm hot) is upstream of the module (under-voltage lock-out 8 V, bus 12 V) and does not enter the 5 V budget. The display branch (J_DISP contact + lead) depends on the display connector/lead, which is chosen with the display data (`Waveshare_integration.md`): allow <= 50 mV for it.

## 2. Voltage at the Pi pins, by scenario (calibrated unit)

| Pi load (A) | Display load (A) | Total through F2 (A) | Pi pins typical (V) | Pi pins worst path (V) | Margin to 4.85 V (worst) | Display terminal J_DISP worst (V, before its lead) |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 5.185 | 5.136 | +0.286 | 5.136 |
| 1 | 0 | 1 | 5.146 | 5.079 | +0.229 | 5.120 |
| 3 | 0 | 3 | 5.069 | 4.965 | +0.115 | 5.089 |
| 5 | 0 | 5 | 4.992 | 4.851 | +0.001 | 5.059 |
| 3 | 1 | 4 | 5.056 | 4.950 | +0.100 | 5.074 |
| 4 | 1 | 5 | 5.017 | 4.893 | +0.043 | 5.059 |
| 5 | 1 | 6 | 4.979 | 4.836 | -0.014 | 5.043 |

Lowest voltage anywhere in the table (every resistance at its maximum, F2 hot, +15 C, 5 A Pi + 1 A display): **4.836 V**: MISSES the 4.85 V owner target by -14 mV and clears the 4.75 V design floor by +86 mV. The 4.85 V target is the conservative owner target; the 4.75 V floor is the under-voltage design limit.

The 5 A + 1 A row is the maximum intended load (Pi 5 at its 5 A supply rating plus ~1 A display; owner note in `docs/rev2/pcb/PI_POWER_ARCHITECTURE.md`: Pi 5 5 V / up to 5 A, display ~0.8-1 A - the actual Waveshare model rating must still be confirmed).

**Setpoint window (calibrated unit, worst path, hot F2, 5 A Pi + 1 A display):** the module output measured at 25 C, no load, must lie in **5.199 V ... 5.201 V** (lower bound: 4.85 V at the Pi pins; upper bound: 5.25 V at no load / high line / +15 C): width 1 mV (effectively closed: narrower than one E96 trim step, ~20 mV). With **typical** resistances the window is 5.104 V ... 5.201 V (96 mV wide). The worst-path window stacks every contact at its maximum with F2 hot at once; it shows the limit, not the expected case. **Calibration is therefore done on the assembled system** (measure the real drop, then choose the trim resistor; `Trim_calibration_procedure.md`, `First_article_checklist.md`); worst-path closure is checked by measuring the socket and connector contact resistances on the first articles.

No-load worst case: **5.234 V** (setpoint 5.185 V x (1 + line 0.2 % + temperature 0.75 %)) -> below the 5.25 V Pi maximum.

## 3. Scenarios and acceptance (measured at first article)

The Pi 5 and display currents are not taken from datasheets in this build; they are measured. The hardware limit is **5.0 A into the Pi pins** (2 x 5 V pins, J_OUT/J1 contacts, harness) and **6.0 A total through F2 / the module (8 A)**.

| Scenario | What is loaded | Required measurement | Pass if |
|---|---|---|---|
| Pi only, idle / boot | Pi 5 alone | I_5V at pins, V at pins | V >= 4.85 V at the measured current |
| Pi only, stress | CPU+GPU+RAM stress, Active Cooler if fitted | I_5V peak/continuous, V at pins, throttling flag | V >= 4.85 V; no under-voltage / throttle flag |
| Pi + Waveshare display | stress + display at full brightness + touch | I_Pi, I_display, V at Pi pins and at the display input | I_Pi <= 5.0 A, total <= 6.0 A, V_Pi >= 4.85 V, display input >= its minimum |
| Pi + display + USB peripherals | the above + intended USB load | I_Pi (incl. USB) | I_Pi <= 5.0 A; otherwise reduce the USB load - the Pi branch is not rated beyond 5 A |

Contact loading at 5 A Pi load: 2.5 A per Pi 5 V pin (2 pins), 1.25 A per GND pin (4 pins); Samtec SSW 4.7 A per pin with two pins powered (53 % on +5 V). Micro-Fit 8.5 A per contact (owner-cited): J_OUT and J1 carry 2.5 A per +5 V contact (29 %); J_DISP carries 1 A.

## 4. Sensitivities (Pi pins at 5 A Pi + 1 A display, worst path)

| Case | Pi pins (V) |
|---|---|
| Baseline | 4.836 |
| Only 2 GND socket pins used (no pins 14/20) | 4.811 |
| Socket contact 25 mOhm instead of 20 | 4.817 |
| Module 5 C hotter (dT 20 C) | 4.823 |
| Uncalibrated unit (accuracy +-1 % included, same setpoint) | 4.784 |

The uncalibrated row shows why **per-unit trim calibration is required**: without it the 5 A worst case falls below 4.85 V and no fixed setpoint can satisfy both the 4.85 V and 5.25 V limits.

# Voltage-drop report — Pi Power Carrier RevB (combined board)

Recomputed from scratch for the combined board: no J_OUT, no 4-wire harness, no interposer J1. Path: `RSDW40F-05 pins 4/5 -> F2 -> 5V_PI pour -> SSW-120-01-L-D -> Pi header pins 2,4 (+5 V) and 6,9,14,20 (GND)`; display branch `5V_PI node -> band -> J_DISP -> display lead`. Copper lengths/widths are measured on this layout (2 oz, 0.246 mOhm/square, x1.2 hot). Inputs: `datasheet_inputs.json` (source and status per value; user-relayed Samtec/Waveshare data marked there).

Targets: Pi pins >= 4.85 V (preferred) with the 4.75 V design floor, no-load <= 5.25 V; Waveshare input 4.75-5.3 V (4.75 / 5.00 / 5.30, **0.8 A typical, maximum not published**; 1.0 A is a design scenario, not a manufacturer maximum). Calibrated unit: setpoint 5.185 V (25 C, no load); line 0.2 %, load 0.5 % over 0-8 A, temperature 0.05 %/C x 15 C = 0.75 %.

## 1. Element drops

| Element | carries | R typ (mOhm) | R worst (mOhm) | drop @5 A typ / worst (mV) |
|---|---|---|---|---|
| PCB: U1 pin 4 -> F2 (2.5 mm track, 3.7 squares) | Pi + display | 0.90 | 1.08 | 5 / 6 (at 6 A) |
| U1 pins 4 + 5 solder joints / PTH barrels (estimate) | Pi + display | 1.00 | 1.00 | 6 / 6 (at 6 A) |
| F2 0451008.MRL (7.7 mOhm cold; 1.3x hot) | Pi + display | 7.70 | 10.01 | 46 / 60 (at 6 A) |
| PCB: F2 -> Pi pins 2,4 (5V_PI pour, 1.9 squares) | Pi only | 0.46 | 0.55 | 2 / 3 (at 5 A) |
| PCB: Pi GND pins 6,9,14,20 -> U1 pin 5 (PI_GND pour, 0.35 squares) | Pi only | 0.09 | 0.10 | 0 / 1 (at 5 A) |
| SSW-120-01-L-D socket contacts (20 mOhm/contact max, typ 0.6x; 2 on +5 V, 4 on GND) | Pi only | 9.00 | 15.00 | 45 / 75 (at 5 A) |
| Pi header pins + solder joints (1 mOhm/contact estimate; 2 on +5 V, 4 on GND) | Pi only | 0.75 | 0.75 | 4 / 4 (at 5 A) |
| PCB: 5V_PI band + track to J_DISP (19.2 squares) | display only | 4.72 | 5.67 | 5 / 6 (at 1 A) |
| PCB: J_DISP GND -> U1 pin 5 (0.70 squares) | display only | 0.17 | 0.21 | 0 / 0 (at 1 A) |
| J_DISP Micro-Fit contacts (1 on +5 V, 1 on GND; 5.24 typ / 10 max per contact) | display only | 10.48 | 20.00 | 10 / 20 (at 1 A) |
| Display lead 20 AWG, 200 mm, both wires (hot 1.2x) | display only | 11.00 | 13.20 | 11 / 13 (at 1 A) |
| **Shared (module pins, track, F2)** | | **9.6** | **12.1** | |
| **Pi branch (pour, socket, header)** | | **10.3** | **16.4** | |
| **Total to the Pi pins** | | **19.9** | **28.5** | **99 / 142** |
| **Display branch (after the shared part)** | | **26.4** | **39.1** | |

**Versus RC2** (separate power board + interposer + 18 AWG harness): total to the Pi pins 36.5 / 55.0 mOhm typ/worst -> carrier 19.9 / 28.5 mOhm: **26.5 mOhm less in the worst case (133 mV at 5 A)** (removed: J_OUT and J1 Micro-Fit contacts 4 x 10 mOhm, 4 x 18 AWG wires, interposer copper). The J_IN and the contact-resistance items that remain are the SSW socket and the Pi header pins (the only mating interface to the Pi).

## 2. Cases (calibrated unit)

| Case | Pi load (A) | Display (A) | Total through F2 (A) | Pi pins typ (V) | Pi pins worst (V) | margin to 4.85 V (worst) | margin to 4.75 V (worst) | J_DISP typ / worst (V) |
|---|---|---|---|---|---|---|---|---|
| no load | 0 | 0 | 0 | 5.185 | 5.136 | +0.286 | +0.386 | 5.185 / 5.136 |
| 1 A | 1 | 0 | 1 | 5.162 | 5.104 | +0.254 | +0.354 | 5.172 / 5.120 |
| 3 A | 3 | 0 | 3 | 5.116 | 5.041 | +0.191 | +0.291 | 5.146 / 5.090 |
| 5 A Pi | 5 | 0 | 5 | 5.069 | 4.977 | +0.127 | +0.227 | 5.121 / 5.059 |
| 5 A Pi + 0.8 A display (typical) | 5 | 0.8 | 5.8 | 5.059 | 4.965 | +0.115 | +0.215 | 5.089 / 5.016 |
| 5 A Pi + 1.0 A display (design scenario) | 5 | 1 | 6 | 5.056 | 4.962 | +0.112 | +0.212 | 5.082 / 5.005 |

**No-load maximum:** 5.234 V (setpoint x (1 + line + temperature)) -> below the 5.25 V Pi maximum and below the Waveshare 5.3 V limit by 66 mV.
**Worst case, 5 A Pi + 1.0 A display:** 4.962 V at the Pi pins (+112 mV vs the 4.85 V preferred target, +212 mV vs the 4.75 V floor); RC2 with the same load and setpoint: 4.829 V -> **carrier improves the worst case by 133 mV**.

## 3. Setpoint (trim) window, calibrated unit, 5 A Pi + 1.0 A display

| Window | lower (V) | upper (V) | width (mV) |
|---|---|---|---|
| worst path, 4.85 V preferred target | 5.072 | 5.201 | 129 |
| worst path, 4.75 V design floor | 4.970 | 5.201 | 230 |
| typical path, 4.85 V target | 5.026 | 5.201 | 175 |

RC2 worst-path window for comparison: 5.206 V ... 5.201 V (CLOSED, negative width). Carrier: **open** against the preferred target in the stacked worst case.

Trim tolerance: a 1 % resistor on the trim-up pad (71.5 k nominal) moves the output by **1.2 mV**; one E96 step (71.5 k -> 73.2 k) is **3 mV**. The calibration therefore resolves the setpoint to about ±1 mV plus the 1.2 mV tolerance: usable window for the worst-path target = 123 mV after quantisation and tolerance (workable).

## 4. Waveshare display input

| Case | Display connector (V) | Range 4.75-5.30 V |
|---|---|---|
| lowest: worst path, 5 A Pi + 1.0 A display | 5.005 | inside (+255 mV to the lower limit) |
| 5 A Pi + 0.8 A display (typical current) | 5.016 | inside (+266 mV to the lower limit) |
| highest: no load, high line, +15 C | 5.234 | inside (+66 mV to the upper limit) |

## 5. Current per contact (SSW-120-01-L-D: 4.7 A per contact with two pins powered, Samtec basis)

| Contact group | Pi current | per contact | rating | utilisation |
|---|---|---|---|---|
| +5 V: Pi pins 2, 4 | 5.0 A | 2.50 A | 4.7 A | 53 % |
| GND: Pi pins 6, 9, 14, 20 | 5.0 A | 1.25 A | 4.7 A | 27 % |
| J_DISP Micro-Fit contact | 1.0 A | 1.00 A | 8.5 A (owner-cited) | 12 % |
| J_IN Micro-Fit contact (12 V, full module load ~3.9 A over 1 contact per rail) | 3.9 A | 3.9 A | 8.5 A (owner-cited) | 46 % |

Power dissipation at 5 A + 1 A (worst): F2 360 mW; SSW +5 V pin 125 mW each; SSW GND pin 31 mW each; J_DISP contact 10 mW; copper negligible. The module (~3.5 W) dominates. First article measures the real temperatures.

## 6. What is estimated (all BENCH_REQUIRED — see `BENCH_REQUIRED.md`)

Copper squares are measured on this layout but the plated-through-hole barrels, solder joints and the Pi-side pin resistance are estimates (0.5 mOhm per module pin, 1 mOhm per Pi header contact). The SSW contact resistance (20 mOhm max) is a conservative limit — Samtec publishes no initial value for this code — and is **BENCH_REQUIRED** (measure the actual drop across the socket at high load), as are the module solder-joint resistance, the real Waveshare current (0.8 A typical, maximum unpublished; 1.0 A is a design scenario), the no-load maximum (5.234 V, only 16 mV below the 5.25 V ceiling) and the mechanical fit.

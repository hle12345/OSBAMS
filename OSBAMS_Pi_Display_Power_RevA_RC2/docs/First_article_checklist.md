# Pi power board — first-article bench plan (RC2)

Purpose: validate the first built units before they power a real Pi 5. Not a fabrication gate: RC2 may be ordered first, and this plan is run on the first articles. Record every value in the acceptance record at the end. Stop and do not connect a Pi if any step fails.

## Equipment
Bench 12 V supply (current limit 1 A -> 5 A), electronic load 0-10 A with 4-wire sense, 2 DMMs (>= 5.5 digit), oscilloscope (20 MHz bandwidth limit, 10x probe, short ground spring), thermocouples or IR camera (+ a thermocouple logger for the fuse/connector/module), the real harness + interposer, a Pi 5 (with Active Cooler if used), the Waveshare 10.1" DSI display and a USB load for the peripheral case.

## Part A - bare board (no Pi, no display)
| # | Step | Pass if | Result |
|---|---|---|---|
| A1 | Visual: polarity of TVS1, D1, C2, C4; U1 orientation; J_IN/J_OUT/J_DISP seated; R2 absent, R3 absent | per assembly notes | |
| A2 | Power off: continuity 12V_GND-PI_GND (isolation), 5V_PI-PI_GND, +12V_IN-12V_GND | >= 1 MOhm between 12V_GND and PI_GND; no shorts | |
| A3 | Input 12.0 V, no load: input current | < 0.2 A | |
| A4 | No-load 5 V: V(TP3) module output, V(TP4) after F2, V at J_OUT pins | 5.00 V +-1.7 %; TP4 = TP3 within 5 mV; PG LED lit | |
| A5 | Isolation resistance 500 V (or the highest safe test voltage) between 12V_GND and PI_GND | >= 100 MOhm (module spec 1000 MOhm at 500 VDC) | |
| A5b | Harness crimp inspection (43030-0038 on 18 AWG): conductor crimp height 1.00–1.10 mm, strip 2.54–2.92 mm, pull ≥ 89 N on a sample, insulation OD ≤ 1.85 mm | per Molex ATS-638280200 | |
| A6 | Contact resistances (4-wire, 5 A DC): J_OUT contact pair, J1 pair, SSW socket per pin (interposer on a spare Pi header or a test header), F2 | each <= its budget row in `Power_budget_report.md` (J 10 mOhm/contact, socket 20 mOhm/contact, F2 <= 10 mOhm hot, 18 AWG wire <= 3.8 mOhm per 150 mm) | |

## Part B - loaded, no Pi (electronic load at the interposer / Pi-end connector)
| # | Step | Pass if | Result |
|---|---|---|---|
| B1 | 1 A / 3 A / 5 A loads, 10 min each: V at module output (TP3), at board output (TP4/J_OUT), at the Pi-end socket pins | drops match `Power_budget_report.md` within 20 % | |
| B2 | 5 A, 30 min: temperature of J_OUT, J1, SSW socket pins, F2, F1, TVS1, U1 case, harness (hot spot), ambient | rises <= 30 K (connectors/fuses), module case within its derating curve; no discoloration | |
| B3 | Load step 0 -> 5 A -> 0 | ripple <= 100 mVp-p (20 MHz), no droop below 4.75 V at the Pi pins | |
| B4 | Short-circuit the output through the load (current-limited) | module hiccups/recovers (spec: continuous protection), F2 intact | |
| B5 | Input at 9 V, 12 V, 14.4 V | 5 V outputs stable; no-load output moves < 0.2 % | |

## Part C - trim calibration (per unit; see `Trim_calibration_procedure.md`)
| # | Step | Pass if | Result |
|---|---|---|---|
| C1 | Untrimmed no-load V_unt (R3 absent) at the Pi-end connector | 5.00 V +-1.7 % | |
| C2 | Untrimmed 5 A loaded at the Pi-end connector (through harness + interposer), after 10 min | recorded | |
| C3 | `trim_calibration.py V_unt V_5A 5.0` -> R3 (E96, kit 61.9k / 71.5k / 84.5k) | RESULT: ACCEPT | |
| C4 | Fit R3, re-measure no-load, 1/3/5 A at the Pi-end connector, then 5 A + 1 A display-current equivalent at TP4 | no-load <= 5.25 V; 5 A at the Pi pins >= 4.85 V (owner target; design floor 4.75 V) | |

## Part D - with the Pi 5 (USB-C power input NOT connected)
| # | Step | Pass if | Result |
|---|---|---|---|
| D1 | Interposer fit on the Pi, key standoffs fitted; **reverse-fit attempt on a dummy/spare Pi board with power off** | reversed board cannot seat; pins cannot enter the socket | |
| D2 | Pi boot to desktop; measure V at the Pi pins (idle) and I_5V | V >= 4.85 V | |
| D3 | `vcgencmd get_throttled` and `dmesg | grep -i volt` after boot and after the tests below | `0x0`, no under-voltage lines | |
| D4 | Pi stress (CPU + GPU + memory), 30 min: I_5V, V at pins, module/connector/fuse/harness temperatures | V >= 4.85 V; throttled flag clear; temperature rises per B2 | |
| D5 | Pi + Waveshare display (J_DISP fed): full brightness + touch + stress, 30 min; measure I_Pi and I_display separately | I_Pi <= 5.0 A, total <= 6.0 A; V_Pi >= 4.85 V; display input within Waveshare's supply range | |
| D6 | Pi + display + intended USB peripherals | I_Pi <= 5.0 A; otherwise reduce the USB load | |
| D7 | Power-cycle 10x (cold boots), and a 12 V brown-out to 9 V and back | clean boots, no latch-up | |
| D8 | Only after D1-D7 pass: set `PSU_MAX_CURRENT=5000` (see `Raspberry_Pi_configuration_note.md`) | | |

## Acceptance record (one per unit)
| Field | Value |
|---|---|
| Board serial / RSDW lot-date code / harness+interposer ID | |
| Ambient / module case temperature (C) | |
| Contact resistances (J_OUT, J1, SSW per pin, F2) mOhm | |
| V_unt no-load; V_5A untrimmed at the Pi end | |
| R3 calculated / fitted (kOhm, E96) | |
| No-load after trim (V) - limit <= 5.25 | |
| 1 A / 3 A / 5 A at the Pi pins (V) - limit >= 4.85 at 5 A | |
| I_Pi, I_display, V at Pi pins and at the display input (D5) | |
| Temperatures at 5 A, 30 min: J_OUT / J1 / socket / F1 / F2 / U1 / harness (C) | |
| get_throttled after D4/D5 | |
| Pass / Fail, operator, date | |

# Carrier RevB — first-article bench plan

Run on the first built units before they power a real Pi 5 or the display. Not a fabrication gate. Record every value in the acceptance record. Stop if any step fails. **The power path is not validated until every row below has been measured.**

Equipment: 12 V bench supply (1 A → 5 A limit), electronic load 0–10 A with 4-wire sense, 2 DMMs (≥ 5.5 digit), scope (20 MHz BW limit, short ground), thermocouple logger / IR camera, a **Pi-header test adapter** (2 × 20 male header board: pins 2 + 4 → +5 V terminal, pins 6, 9, 14, 20 → GND terminal, 4-wire), a Pi 5 (+ Active Cooler if used), the Waveshare 10.1-DSI-TOUCH-A, a USB load, a spare/dummy Pi board for D1.

## A — bare board (no Pi, no display)
| # | Step | Pass if | Result |
|---|---|---|---|
| A1 | Visual: TVS1, D1, C2, C4 polarity; U1 orientation (primary end at the top, J_IN side); J_IN / J_DISP seated; R3 absent; M3 standoffs K1/K2 fitted | per assembly notes | |
| A2 | Power off: 12V_GND–PI_GND, 5V_PI–PI_GND, +12V_IN–12V_GND | ≥ 1 MΩ between 12V_GND and PI_GND; no shorts | |
| A3 | 12.0 V in, no load: input current | < 0.2 A | |
| A4 | No-load 5 V: V(TP3) at the module, V(TP4) after F2, V at the socket pins 2/4 | 5.00 V ±1.7 %; TP4 = TP3 within 5 mV; PG LED lit | |
| A5 | Isolation resistance, 500 V between 12V_GND and PI_GND | ≥ 100 MΩ (module spec 1000 MΩ) | |
| A5b | Crimp inspection of the 43030-0038 terminals on 18 AWG: crimp height 1.00–1.10 mm, strip 2.54–2.92 mm, insulation OD ≤ 1.85 mm, pull ≥ 89 N on a sample | Molex ATS-638280200 | |
| A6 | Contact resistances (4-wire, 5 A DC): SSW socket per pin (via the test adapter), J_DISP contact pair, F2 | socket ≤ 20 mΩ/contact, J_DISP ≤ 10 mΩ/contact, F2 ≤ 10 mΩ hot | |

## B — loaded, no Pi (electronic load on the test adapter, then on J_DISP)
| # | Step | Pass if | Result |
|---|---|---|---|
| B1 | 1 / 3 / 5 A Pi load, 10 min each: **converter output (TP3), board output (TP4), socket pins (adapter terminals)** | drops within 20 % of `Voltage_drop_report.md` | |
| B2 | 5 A, 30 min, plus 1 A on J_DISP: temperature of SSW pins, J_DISP, F1, F2, U1 case, TVS1, 5V pour, ambient | rises ≤ 30 K; module case within its derating; no discoloration | |
| B3 | Load step 0 → 5 A → 0 | ripple ≤ 100 mVp-p (20 MHz); no droop below 4.75 V at the socket | |
| B4 | Output short through the load (current-limited) | module hiccups/recovers, F2 intact | |
| B5 | Input 9 V / 12 V / 14.4 V | 5 V stable; no-load shift < 0.2 % | |
| B6 | Display current: J_DISP loaded with the real display (or 0.8 A / 1.0 A load), 5 V at J_DISP | ≥ 4.75 V and ≤ 5.30 V at the display connector | |

## C — trim calibration (per unit; `Trim_calibration_procedure.md`)
| # | Step | Pass if | Result |
|---|---|---|---|
| C1 | Untrimmed no-load V at the socket (R3 absent) | 5.00 V ±1.7 % | |
| C2 | Untrimmed 5 A loaded at the socket | recorded | |
| C3 | `trim_calibration.py V_unt V_5A 5.0` → R3 (E96 kit 61.9k / 71.5k / 84.5k) | RESULT: ACCEPT | |
| C4 | Fit R3; no-load, 1/3/5 A at the socket, then 5 A + display load | no-load ≤ 5.25 V; 5 A at the Pi pins ≥ 4.85 V (design floor 4.75 V) | |

## D — with the Pi 5 (USB-C power NOT connected)
| # | Step | Pass if | Result |
|---|---|---|---|
| D1 | Standoffs K1/K2 (M3 × 20) + Pi standoffs 7.4 mm: **reverse-fit attempt on a spare Pi board with power off**; then correct fit, check the real clearances (Active Cooler, USB/Ethernet, small connector F, DSI ribbon, enclosure wall) | reversed board cannot seat, pins cannot enter; correct fit clears everything ≥ 2 mm | |
| D2 | Pi boot; V at the Pi pins (idle), I_5V | V ≥ 4.85 V | |
| D3 | `vcgencmd get_throttled`, `dmesg \| grep -i volt` after boot and after the tests | `0x0`, no under-voltage lines | |
| D4 | Pi stress (CPU+GPU+memory) 30 min: I_5V, V at pins, temperatures | V ≥ 4.85 V; throttle flag clear | |
| D5 | Pi + Waveshare simultaneously (J_DISP fed), full brightness + touch + stress, 30 min; I_Pi and I_display separately | I_Pi ≤ 5.0 A, total ≤ 6.0 A, V_Pi ≥ 4.85 V, display input 4.75–5.30 V | |
| D6 | + intended USB peripherals | I_Pi ≤ 5.0 A | |
| D7 | 10 cold boots; 12 V brown-out to 9 V and back | clean boots | |
| D8 | After D1–D7: `PSU_MAX_CURRENT=5000` (`Raspberry_Pi_configuration_note.md`) | | |

## Acceptance record (one per unit)
Board serial / RSDW lot-date code; ambient and module case temperature; contact resistances (SSW per pin, J_DISP, F2); V_unt no-load and at 5 A; R3 calculated / fitted; no-load after trim (≤ 5.25 V); 1/3/5 A at the Pi pins (≥ 4.85 V at 5 A); I_Pi, I_display, V at the Pi pins and at J_DISP (D5); temperatures at 5 A + 1 A, 30 min (SSW / J_DISP / F1 / F2 / U1 / TVS1); get_throttled; isolation resistance; pass/fail, operator, date.

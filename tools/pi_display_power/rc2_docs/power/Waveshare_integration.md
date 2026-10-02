# Waveshare 10.1" DSI display — power integration (RC2 decision)

## Decision
**The display's 5 V / GND are taken directly from the isolated 5 V distribution board, through a dedicated 2-circuit connector `J_DISP` (Molex Micro-Fit 430450200, pin 1 = +5V_PI, pin 2 = PI_GND, downstream of F2).** The Pi does not power the display, and the display current does not pass through the harness, the interposer or the Pi header pins.

Why:
1. **The interposer covers the Pi header.** The Waveshare power leads are normally landed on Pi header pins (5 V / GND). The RC2 interposer is a 2x20 socket (Samtec SSW-120-01-x-D, 2.64 mm tails) that plugs over all 40 pins; its top side has no pin header, so those pins are not reachable. (RC1 left this open: "Waveshare 5 V/GND leads: confirm which Pi pins they use" and suggested a taller stacking socket; the -04 stacking variant was rejected earlier as mechanically unnecessary and unavailable.)
2. **The display load is not negligible** (owner note, `docs/rev2/pcb/PI_POWER_ARCHITECTURE.md`: display ~0.8-1 A, Pi 5 up to 5 A). Fed from the board it reduces the Pi-branch current: the Pi header pins (2 x 5 V, ~4.7 A each) carry only the Pi (+USB) current; the display shares only the PCB copper and F2 (`Power_budget_report.md`).
3. **One isolated domain.** Display ground = PI_GND = Pi ground (the DSI ribbon also carries ground). There is no second ground reference and nothing connects to 12V_GND.

Cost: one more connector on the power board (J_DISP, same part as J_IN, placed beside J_OUT), 2 extra Micro-Fit terminals (43030-0038) and a 2-wire display lead (display end: MX1.25 2-pin, confirm the housing).

## Manufacturer data (user-relayed from the Waveshare page; not read locally)
Waveshare **10.1-DSI-TOUCH-A** (SKU 30052): 10.1" IPS capacitive touch, 800 × 1280, MIPI DSI, Pi 5 supported.
| Item | Value |
|---|---|
| Input voltage | **4.75 V min / 5.00 V nominal / 5.30 V max** |
| Input current | **0.8 A typical; maximum not published** (supply should deliver ≥ ~0.8 A or start-up/display abnormalities may occur) |
| Temperature | operating 0–60 °C, storage −10–70 °C |
| Pi 5 connection | 22-pin DSI/FFC cable to the Pi DSI connector (data) + a **separate GPIO-style power cable to 5 V + GND** |
| Package cables | `MX1.25 2PIN to 2.54 3PIN` and `MX1.25 2PIN to MX1.25 4PIN` |

Consequences: (1) the same 5 V rail is electrically appropriate (budget: 5.01 V lowest, 5.234 V highest at the display, inside 4.75–5.30 V — `Power_budget_report.md` §5); (2) the documented power cable lands on Pi header pins, which the interposer covers, so `J_DISP` is the right adaptation; (3) the display power is **not** routed through the interposer, only the DSI ribbon goes Pi → display; (4) 1.0 A is a design scenario, not a manufacturer maximum — the first article measures the real current (D5).

## Wiring rules
- J_DISP pin 1 (+5V_PI, red) and pin 2 (PI_GND, black), 20 AWG or heavier, <= 200 mm, twisted; display-end connector per the Waveshare data.
- Do not connect the display's USB or any other 5 V input to a second supply. Do not connect the display's ground to anything except PI_GND.
- DSI ribbon: Pi-to-display only (video/data), unchanged.

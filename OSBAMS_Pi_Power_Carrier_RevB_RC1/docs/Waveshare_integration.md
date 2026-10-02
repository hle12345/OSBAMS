# Waveshare 10.1" DSI display — power integration (RC2 decision)

## Decision
**The display's 5 V / GND come from `J_DISP` on the carrier (Molex Micro-Fit 430450200, pin 1 = +5V_PI, pin 2 = PI_GND), tapped from the post-F2 5 V node.** The Pi powers neither the display nor itself through the display wiring; display power never passes through the Pi header. The documented Waveshare connection (separate power cable to Pi 5 V + GND) is replaced by this feed because the carrier occupies the 2×20 header; the DSI/FFC data cable goes directly Pi → display.

Why: (1) the SSW socket covers all 40 header pins; (2) the display load (0.8 A typical, 1.0 A design scenario) stays off the Pi pins and socket contacts; (3) one isolated domain: display ground = PI_GND.

## Manufacturer data (user-relayed from the Waveshare page; not read locally)
Waveshare **10.1-DSI-TOUCH-A** (SKU 30052): 10.1" IPS capacitive touch, 800 × 1280, MIPI DSI, Pi 5 supported.
| Item | Value |
|---|---|
| Input voltage | **4.75 V min / 5.00 V nominal / 5.30 V max** |
| Input current | **0.8 A typical; maximum not published** (supply should deliver ≥ ~0.8 A or start-up/display abnormalities may occur) |
| Temperature | operating 0–60 °C, storage −10–70 °C |
| Pi 5 connection | 22-pin DSI/FFC cable to the Pi DSI connector (data) + a **separate GPIO-style power cable to 5 V + GND** |
| Package cables | `MX1.25 2PIN to 2.54 3PIN` and `MX1.25 2PIN to MX1.25 4PIN` |

Consequences: (1) the same 5 V rail is electrically appropriate (carrier budget: 5.005 V lowest at the display connector, 5.234 V highest, inside 4.75–5.30 V — `Voltage_drop_report.md` §4); (2) the documented power cable lands on Pi header pins, which the carrier covers, so `J_DISP` is the right adaptation; (3) only the DSI ribbon goes Pi → display; (4) 1.0 A is a design scenario, not a manufacturer maximum — the first article measures the real current (D5).

## Wiring rules
- J_DISP pin 1 (+5V_PI, red) and pin 2 (PI_GND, black), 18 AWG with 43030-0038 terminals (or 20 AWG with 43030-0007 for ≈ 1 A; 24–20 AWG range user-relayed), ≤ 200 mm, twisted; display end: the MX1.25 2-pin cable supplied with the display (user-relayed: `MX1.25 2PIN to 2.54 3PIN` and `MX1.25 2PIN to MX1.25 4PIN`), confirm the housing.
- Do not connect the display's USB or any other 5 V input to a second supply. Do not connect the display's ground to anything except PI_GND.
- DSI ribbon: Pi-to-display only (video/data).

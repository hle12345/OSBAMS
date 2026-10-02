# Waveshare 10.1" DSI display — power integration (RC2 decision)

## Decision
**The display's 5 V / GND are taken directly from the isolated 5 V distribution board, through a dedicated 2-circuit connector `J_DISP` (Molex Micro-Fit 430450200, pin 1 = +5V_PI, pin 2 = PI_GND, downstream of F2).** The Pi does not power the display, and the display current does not pass through the harness, the interposer or the Pi header pins.

Why:
1. **The interposer covers the Pi header.** The Waveshare power leads are normally landed on Pi header pins (5 V / GND). The RC2 interposer is a 2x20 socket (Samtec SSW-120-01-x-D, 2.64 mm tails) that plugs over all 40 pins; its top side has no pin header, so those pins are not reachable. (RC1 left this open: "Waveshare 5 V/GND leads: confirm which Pi pins they use" and suggested a taller stacking socket; the -04 stacking variant was rejected earlier as mechanically unnecessary and unavailable.)
2. **The display load is not negligible** (owner note, `docs/rev2/pcb/PI_POWER_ARCHITECTURE.md`: display ~0.8-1 A, Pi 5 up to 5 A). Fed from the board it reduces the Pi-branch current: the Pi header pins (2 x 5 V, ~4.7 A each) carry only the Pi (+USB) current; the display shares only the PCB copper and F2 (`Power_budget_report.md`).
3. **One isolated domain.** Display ground = PI_GND = Pi ground (the DSI ribbon also carries ground). There is no second ground reference and nothing connects to 12V_GND.

Cost: one more connector on the power board (J_DISP, same part as J_IN, placed beside J_OUT), 2 extra Micro-Fit terminals and a 2-wire display lead.

## Requirements still to be confirmed from Waveshare (not available to this build)
| Item | Needed | Why |
|---|---|---|
| Exact model (10.1" DSI touch variant) and revision | Waveshare product page / wiki | power connector and cable differ between variants |
| Supply voltage range and **maximum current** (full brightness, touch active, backlight at 100 %) | datasheet or measured | sets the display wire gauge and the 6 A total budget |
| Power connector type on the display side (pitch, housing, pin order) | datasheet | the display-end of the 2-wire lead; the board end is Micro-Fit |
| Whether the display must also be powered over the DSI ribbon / USB | datasheet | avoid a second 5 V source back-feeding |

The owner's working figure (~0.8-1 A) is used only for the scenario table in `Power_budget_report.md` (Pi 5 A + display 1 A); the display current is **measured at first article** (`First_article_checklist.md`) and the acceptance limits are stated for the measured value. The design limits are fixed regardless: 5.0 A into the Pi pins, 6.0 A total through F2 / the module (8 A rated), J_DISP 1 A at 8.5 A contact rating.

## Wiring rules
- J_DISP pin 1 (+5V_PI, red) and pin 2 (PI_GND, black), 20 AWG or heavier, <= 200 mm, twisted; display-end connector per the Waveshare data.
- Do not connect the display's USB or any other 5 V input to a second supply. Do not connect the display's ground to anything except PI_GND.
- DSI ribbon: Pi-to-display only (video/data), unchanged.

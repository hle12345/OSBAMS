# Harness definition — RC1 (candidates, verify before ordering)

## Pi 5 V harness (J_OUT → Pi GPIO)
| Item | Selection | Status |
|---|---|---|
| Board header | Molex 430450400, Micro-Fit 3.0, RA, dual row, 4 ckt | locked |
| Mating housing | Molex **43025-0400** (receptacle, 4 ckt, dual row) | candidate — verify |
| Terminals | Molex **43030** family crimp terminal; candidate 43030-0007 for 18 AWG | verify AWG range & current rating |
| Wire | 18 AWG stranded silicone (16 AWG if available), red (+5 V) / black (GND), ≤ 250 mm, twist pairs | |
| Circuits | 1,2 = +5V_PI (red); 3,4 = PI_GND (black) | per brief |
| Pi end | 2.54 mm 2×5 crimp housing on GPIO pins 1–10, populate only cavities 2 (5V), 4 (5V), 6 (GND), 9 (GND) | part numbers OPEN — choose a housing/terminal rated ≥ 3 A per contact |
| Key / orientation | Micro-Fit housing is polarised/latched; mark pin 1 on label. Pi end: pin 1 (3V3) cavity left empty, align with the square pad/pin 1 marking. | |

No Dupont jumpers. Each rail uses two parallel wires → two Pi header contacts.

## 12 V input harness (XDR-75-12 → J_IN)
Molex 43025-0200 housing + 2 terminals, 18 AWG, red = +12 V (pin 1), black = GND (pin 2). Fused at F1 (5 A) on board; fit a second in-line fuse at the XDR/bus if the 12 V bus has no per-branch protection.

## Waveshare display
Unchanged: 22-pin DSI ribbon to the Pi; display 5 V/GND leads to Pi GPIO 5 V/GND per Waveshare. Check which GPIO pins the Waveshare leads use and avoid cavity conflicts with this harness (share pins 2/4/6 housing positions or move to separate GND pins such as 14/20). Display current also flows through the Pi's 5 V pins — include it in the current budget.
Drawing: `Harness_drawing.pdf`, `Pi_power_wiring_diagram.pdf`.

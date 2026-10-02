# Harness definition — RC2

Housings are the standard Molex mates of the 43045 headers; **terminal and wire part numbers are not verified** (no Molex 43030 drawing in the project) and are the owner's to select before the harness is ordered. None of this is on the PCB.

## Pi 5 V harness (J_OUT → interposer J1)
| Item | Selection | Status |
|---|---|---|
| Board header | Molex 430450400, Micro-Fit 3.0, RA, 4 circuits | locked (owner-cited ratings) |
| Mating housings | Molex **43025-0400** at both ends | standard mate; owner confirms |
| Terminals | Molex 43030 family, crimp range must cover **16 AWG** | **owner to select exact MPN** |
| Wire | **16 AWG** stranded silicone, red (+5 V) / black (GND), **≤ 150 mm**, twisted pairs | design value used in the budget |
| Circuits | 1,2 = +5V_PI (red, outer row); 3,4 = PI_GND (black, inner row), 1:1 to interposer J1 | per netlist |
| Pi end | keyed interposer J1 → Pi pins 2,4 (+5 V), 6,9,14,20 (GND) | `OSBAMS_Pi_Power_Interposer_RevA_RC2` |

## Display feed (J_DISP → display)
2 wires, 20 AWG or heavier, ≤ 200 mm, red = +5V_PI (pin 1), black = PI_GND (pin 2); Micro-Fit 43025-0200 housing at the board end, the display-end connector per the Waveshare data (open). Current ≈ 0.8–1 A (owner figure; measured at first article).

## 12 V input harness (XDR-75-12 → J_IN)
Molex 43025-0200 + 2 terminals, 18 AWG, red = +12 V (pin 1), black = GND (pin 2); 4 A at full module load. Fused at F1 (8 A time-lag) on the board; add a branch fuse at the XDR-75-12 bus if it has none.

## Rules
No Dupont jumpers, no splices; strain relief (tie/clip) at both ends; measure each assembled harness (4-wire resistance, 5 A temperature rise) before use. Drawings: `Harness_drawing.pdf`, `Pi_power_wiring_diagram.pdf`.

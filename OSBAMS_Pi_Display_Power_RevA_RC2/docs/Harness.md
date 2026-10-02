# Harness definition — RC2

**Correction vs RC1/RC2-draft:** no Molex 43030 terminal accepts 16 AWG. Micro-Fit 3.0 is retained with **18 AWG wire and Molex 43030-0038 terminals** (Molex ATS-638280200). None of this is on the PCB.

## Pi 5 V harness (J_OUT → interposer J1)
| Item | Selection | Status |
|---|---|---|
| Board header | Molex 430450400, Micro-Fit 3.0, RA, 4 circuits | locked (owner-cited ratings) |
| Mating housings | Molex **43025-0400** at both ends | standard mate; owner confirms |
| Terminals | Molex **43030-0038** (18 AWG / 0.75 mm², tin; -0039/-0040 selective gold only if gold is wanted) | verified (Molex ATS-638280200); hand tool 63828-0200 with locator 63828-0275 |
| Wire | **18 AWG** UL1061-type stranded, **insulation OD ≤ 1.85 mm** (1.60–1.85 mm for an optimum crimp; silicone wire is usually thicker — check the OD), red (+5 V) / black (GND), **≤ 150 mm**, twisted pairs | design value used in the budget (21 mΩ/m, ×1.2 hot) |
| Circuits | 1,2 = +5V_PI (red, outer row); 3,4 = PI_GND (black, inner row), 1:1 to interposer J1 | per netlist |
| Pi end | keyed interposer J1 → Pi pins 2,4 (+5 V), 6,9,14,20 (GND) | `OSBAMS_Pi_Power_Interposer_RevA_RC2` |

## Display feed (J_DISP → display)
2 wires, 18 AWG with 43030-0038 terminals (or 20 AWG with 43030-0007 if the display current stays ≈ 1 A — 24–20 AWG range user-relayed), ≤ 200 mm, red = +5V_PI (pin 1), black = PI_GND (pin 2); Micro-Fit 43025-0200 housing at the board end, the display-end connector per the Waveshare data (open). Current ≈ 0.8–1 A (owner figure; measured at first article).

## 12 V input harness (XDR-75-12 → J_IN)
Molex 43025-0200 + 2 × 43030-0038, 18 AWG, red = +12 V (pin 1), black = GND (pin 2); 4 A at full module load. Fused at F1 (8 A time-lag) on the board; add a branch fuse at the XDR-75-12 bus if it has none.

## Rules
No Dupont jumpers, no splices; strain relief (tie/clip) at both ends; crimp per Molex ATS-638280200 (conductor crimp height 1.00–1.10 mm for 18 AWG, strip 2.54–2.92 mm, pull ≥ 89 N); measure each assembled harness (4-wire resistance, 5 A temperature rise) before use. Drawings: `Harness_drawing.pdf`, `Pi_power_wiring_diagram.pdf`.

# Isolation report — carrier RevB

**Single boundary:** `12V_GND` (XDR-75-12 return, shared with the controller) and `PI_GND` (Pi + display) are joined only inside U1 (RSDW40F-05: 1.6 kVDC, 1000 MΩ at 500 VDC, 1500 pF typ, Mean Well spec). No Y capacitor, ferrite, resistor, jumper, stitching or bond.

| Primary (12 V) | Isolated (5 V) |
|---|---|
| +12V_IN, +12V_F, 12V_GND: J_IN, F1, TVS1, C1, C2, TP1, TP2, U1 pins 1–3 (module top end, y ≤ 20) | 5V_ISO_RAW, 5V_PI, PI_GND, PG_LED_A, TRIM: U1 pins 4–6, F2, R3, C4–C6, R1, D1, J_DISP, J2 (Pi header), TP3–TP5 (y ≥ 33) |

## Results (KiCad 10.0.6; `reports/Isolation_check.txt`)
- Custom DRC rule (`.kicad_dru`, net classes PRIMARY / ISOLATED): ≥ **10 mm** copper-to-copper on every layer — **0 violations**. This is at least the RC2 physical gap (10 mm; RC2 rule 8 mm). Negative control: the same board with the rule tightened to 30 mm reports violations, so KiCad applies the rule.
- Layout: copper-free lane **13.5 mm** (y 19.5 … 33.0) across the full board width on both layers; 12V_GND B.Cu pour y ≤ 19.5, PI_GND B.Cu pour y ≥ 33; the module's primary and secondary pin rows are 45.7 mm apart; its body is the only thing crossing the lane.
- Parts with pads on both sides: **U1 only**; no net joins a 12 V net to a 5 V / PI_GND net.
- Mounting: the 4 M3 holes (K1, K2, S3, S4) and the 2 M2.5 holes (M1, M2) are **NPTH, no copper pad, no net**: the enclosure standoffs do not tie any ground to the board; J_IN / J_DISP have no shell; there is no shield.

## System-level cautions (hidden second ground paths)
- Metal standoffs from the Pi's mounting holes (ground-connected on the Pi) to an enclosure that is bonded to earth / 12V_GND bypass the barrier: use plastic standoffs for the Pi, or keep the enclosure unbonded; the carrier's M3 standoffs touch no copper but must not bridge a bonded metal enclosure to Pi ground through the Pi's own hardware.
- Pi USB / Ethernet / HDMI shields and the display frame can reference PI_GND to earth: keep one documented bond point.
- Display ground = PI_GND (J_DISP pin 2). The Pi USB-C power input must not be fed while the carrier powers the Pi.
- Bench: isolation resistance ≥ 100 MΩ at 500 V between 12V_GND and PI_GND on the assembled board (first-article A5). The 13.5 mm gap is an engineering margin, not a certified safety design.

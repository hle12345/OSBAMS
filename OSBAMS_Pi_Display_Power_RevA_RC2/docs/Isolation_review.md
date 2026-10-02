# Isolation review (RC2)

## The single isolation boundary
`12V_GND` (XDR-75-12 return, shared with the Rev.2 controller) and `PI_GND` (Pi + display) are separate and are joined only **inside U1 (RSDW40F-05)**: isolation 1.6 kVDC I/P-O/P, isolation resistance 1000 MOhm / 500 VDC, isolation capacitance 1500 pF typ (Mean Well spec). No Y capacitor, ferrite, resistor, jumper or stitching is fitted between the domains. The Pi/display side floats; the only other coupling to the controller is the ISO7721 data isolator on the controller board.

| Primary (12 V) side | Isolated (5 V) side |
|---|---|
| +12V_IN, +12V_F, 12V_GND; J_IN, F1, TVS1, C1, C2, TP1, TP2; U1 pins 1-3 | 5V_ISO_RAW, 5V_PI, PI_GND, PG_LED_A, TRIM; U1 pins 4-6, F2, C4-C6, R1, D1, R2, R3, J_OUT, J_DISP, TP3-TP5 |

## Checks (KiCad 10.0.6, `reports/Isolation_check.txt`)
- Custom DRC rule (`.kicad_dru`, net classes PRIMARY / ISOLATED): >= 8 mm copper-to-copper between the classes on every layer: **0 violations**. Negative control: the same board with the rule tightened to 24 mm reports violations, proving KiCad applies the rule. Actual gap: a 10 mm copper-free lane (x = 45...55 mm), full board height, both layers; dashed silk line at x = 50.
- Parts with pads on both sides: **U1 only**. No net joins a 12 V net and a 5 V / PI_GND net.
- Two separate ground pours (`/12V_GND` x <= 45 mm, `/PI_GND` x >= 55 mm), no stitching vias across.
- **Mounting holes** H1-H4 are NPTH with no copper pad and no net: the board has no chassis/shield connection. J_IN/J_OUT/J_DISP have no metal shell. Interposer M1/M2 and K1/K2 holes are NPTH.

## Manufacturer layout requirements
The Mean Well RSDW40/RDDW40 spec (uploaded) gives the 1.6 kVDC withstand and the pin drawing but **no creepage/clearance or under-module copper rule**. The layout therefore (a) keeps the module's own primary/secondary pin separation (pins 1-3 and 4-6 are 45.72 mm apart), (b) keeps the 10 mm lane free of copper on both layers, including under the module body (primary copper stops at x = 45, secondary copper starts at x = 55), and (c) uses no copper that bridges the pin rows. For a 1.6 kV test voltage across air/FR-4 a 10 mm gap is well above the creepage expected for pollution degree 2 (order of 5-6 mm at 1.6 kV); the working voltage across the barrier is <= a few tens of volts. This is an engineering margin, **not** a certified safety design (no creepage standard is claimed). If Mean Well publishes an under-module layout rule, re-check it.

## Hidden second ground paths to avoid in the system (not on the board)
- Pi mounting screws / metal standoffs tie Pi ground (the Pi's mounting holes are normally ground-connected - verify on the real board) to the enclosure: do not bond a metal enclosure that is also tied to 12V_GND/earth to the Pi mounting hardware, or the barrier is bypassed. Use plastic standoffs for the Pi or float the Pi mounting.
- Pi USB / Ethernet / HDMI shields connected to other earthed equipment, and the display's metal frame, create a PI_GND path to earth; keep a single documented bond point (G-13 in the controller documents).
- The display's own ground is PI_GND (fed from J_DISP); never connect the display ground to 12V_GND.
- Pi USB-C power input must not be fed while the 5 V harness is fitted.

## Bench verification (first article)
A5 in `First_article_checklist.md`: isolation resistance >= 100 MOhm at 500 V between 12V_GND and PI_GND on the assembled board.

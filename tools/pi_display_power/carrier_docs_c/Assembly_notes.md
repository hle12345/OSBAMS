# Assembly notes — carrier RevC

1. **SMD (top):** F1, F2, TVS1, C1, C5, C6, R1, D1, TP1–TP5. Reflow, lead-free. TVS1 cathode (band) to `+12V_F` (pad 1); D1 cathode to `PI_GND` (pad 1).
2. **THT:** U1 (RSDW40F-05, encapsulated; no ultrasonic wash), J_IN, J_DISP, C2, C4 (polarised: `+` is pad 1, square pad), **J2 (SSW-120-01-L-D) inserted from the UNDERSIDE and soldered from the top** (2.64 mm tails through the 1.6 mm board; pin 1 square pad at the lower-left corner of the header row). Check full hole fill on J_IN / J_DISP / U1.
3. R3 is **not fitted** at assembly (select-on-test at calibration). The module runs at nominal 5.00 V until calibrated.
4. Consigned U1 if PCBWay cannot source it; no substitution.
5. No jumper / ferrite / Y capacitor between `PI_GND` and `12V_GND` exists.
6. Mounting: **M3 × 20 mm female-female standoffs at K1, K2, S3, S4 (all four; K1 and K2 are the key posts)**; M2.5 × 11 mm spacers at M1, M2 (to the Pi's header-end holes); Pi on M2.5 × 7.4 mm standoffs so that the 20 mm posts reach the enclosure floor. **Do not power or fit a Pi without K1/K2** (reversed fit would put +5 V on Pi pin 39 = GND and pin 37 = GPIO26).
7. First power-up before any Pi or display: 12 V current-limited 1 A; TP3 and TP4 = 5.00 V ±2 %, PG LED lit, ≥ 100 MΩ between TP2 and TP5.
8. Pinout: J_IN pin 1 = +12 V, pin 2 = GND; J_DISP pin 1 = +5V_PI, pin 2 = PI_GND (verify the pin-1 end against the Molex part). J_IN mates toward the top edge, J_DISP toward the left edge (both away from the Pi).
9. Silkscreen: front: isolation-lane marker and `RC1 NOT FOR FAB` (replace at release), connector and part designators; back: board name `OSBAMS Pi Power Carrier Rev.C`, `9-36 V IN > ISOLATED 5 V 8 A > Pi + DISPLAY`, `ISOLATED 5 V SIDE`, `PRIMARY 12 V SIDE`, `RSDW40F-05 1.6 kVDC`.

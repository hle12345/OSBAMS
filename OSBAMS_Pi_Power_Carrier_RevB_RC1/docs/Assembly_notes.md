# Assembly notes — carrier RevB

1. **SMD (top):** F1, F2, TVS1, C1, C5, C6, R1, D1, TP1–TP5. Reflow, lead-free. TVS1 cathode (band) to `+12V_F` (pad 1); D1 cathode to `PI_GND` (pad 1).
2. **THT:** U1 (RSDW40F-05, encapsulated; no ultrasonic wash), J_IN, J_DISP, C2, C4 (polarised: `+` is pad 1, square pad), **J2 (SSW-120-01-L-D) inserted from the UNDERSIDE and soldered from the top** (2.64 mm tails through the 1.6 mm board; pin 1 square pad at the plug-tab corner marked `PI PIN 1`). Check full hole fill on J_IN / J_DISP / U1.
3. R3 is **not fitted** at assembly (select-on-test at calibration). The module runs at nominal 5.00 V until calibrated.
4. Consigned U1 if PCBWay cannot source it; no substitution.
5. No jumper / ferrite / Y capacitor between `PI_GND` and `12V_GND` exists.
6. Mounting: **M3 × 20 mm female-female standoffs at K1, K2, S3, S4 (all four; K1 and K2 are the key posts)**; M2.5 × 11 mm spacers at M1, M2 (to the Pi's header-end holes); Pi on M2.5 × 7.4 mm standoffs so that the 20 mm posts reach the enclosure floor. **Do not power or fit a Pi without K1/K2** (reversed fit would put +5 V on Pi pin 39 = GND and pin 37 = GPIO26).
7. First power-up before any Pi or display: 12 V current-limited 1 A; TP3 and TP4 = 5.00 V ±2 %, PG LED lit, ≥ 100 MΩ between TP2 and TP5.
8. Pinout: J_IN pin 1 = +12 V, pin 2 = GND; J_DISP pin 1 = +5V_PI, pin 2 = PI_GND (verify the pin-1 end against the Molex part). Both connectors mate toward the right board edge, away from the Pi.
9. Silkscreen: board name, `PRIMARY 12V SIDE`, `PI SIDE - ISOLATED`, dashed isolation lane, `12V IN`, `DISPLAY 5V OUT`, `Pi pins: +5V 2,4 GND 6,9,14,20`, `R3: SELECT-ON-TEST TRIM`, `K1/K2` key-post note, `RC1 - NOT FOR FAB` (replace at release).

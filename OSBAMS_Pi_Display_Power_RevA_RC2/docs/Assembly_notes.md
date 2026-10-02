# Assembly notes — RC2

1. **SMD (top side only):** F1, F2, TVS1, C1, C5, C6, R1, D1, TP1–TP5. Reflow, lead-free.
   - TVS1: cathode (marked band) to `+12V_F` (pad 1). D1: cathode to `PI_GND` (pad 1). R1 = 1.5 kΩ (~2 mA from 5 V).
2. **THT:** U1 (RSDW40F-05), J_IN, J_OUT, **J_DISP**, C2, C4. Hand/selective solder; follow the Mean Well soldering guidance (not in the spec supplied).
   - C2/C4 polarised: `+` is pad 1 (square pad, `+` on silk). U1 is encapsulated: no ultrasonic wash.
   - J_OUT pads carry up to 5 A: verify full hole fill (also J_DISP).
3. If PCBWay cannot source RSDW40F-05, ship it **consigned**; do not substitute.
4. **R2: not fitted, no part. R3: not fitted at assembly** — fitted per unit during calibration from the E96 kit (61.9k / 71.5k / 84.5k) by the procedure in `Trim_calibration_procedure.md`.
5. No jumper / ferrite / Y capacitor between `PI_GND` and `12V_GND` exists; do not add one.
6. First power-up (before any Pi or display): current-limited 12 V (1 A), check TP3 and TP4 = 5.00 V ±2 %, PG LED lit, ≥ 100 MΩ between TP2 and TP5 (see `First_article_checklist.md`, Part A).
7. Silkscreen: board name, `12V IN`, `ISOLATED 5V OUT`, `DISPLAY 5V` area, `5V / 5A MAX` (Pi branch; 1 A on J_DISP), `PI SIDE — ISOLATED`, dashed isolation barrier, `RC2 – NOT FOR FAB` (replace with the revision string when releasing).
8. Pinout: J_IN pin 1 = +12 V (outer), pin 2 = GND. J_OUT: 1,2 = +5V_PI (outer row), 3,4 = PI_GND (inner row). **J_DISP: pin 1 = +5V_PI, pin 2 = PI_GND** (verify the pin-1 end against the Molex drawing/part). Right-angle headers mate toward the board edge.

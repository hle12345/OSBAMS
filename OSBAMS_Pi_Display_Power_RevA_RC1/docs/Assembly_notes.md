# Assembly notes — RC1.1

1. **SMD (top side only):** F1, F2, TVS1, C1, C5, C6, R1, D1, TP1–TP5. Reflow, lead-free.
   - TVS1: cathode (marked band) to `+12V_F` (pad 1, silk bar on the left).
   - D1: cathode to `PI_GND` (pad 1, silk bar on the left). R1 = 1.5 kΩ, ≈2 mA from 5 V.
2. **THT:** U1 (RSDW40F-05), J_IN, J_OUT, C2, C4. Hand/selective solder.
   - C2/C4 are polarised: `+` is pad 1 (square pad, `+` mark on silk). C2 `+` at the left pad; C4 `+` at the top pad (toward the 5 V bar).
   - Use 2 oz heavy-copper-capable soldering; J_OUT pads carry up to 8 A — verify full hole fill.
3. **U1 is encapsulated**: no wash-in-place with ultrasonic; follow Mean Well soldering profile (not verified here).
4. If PCBWay cannot source RSDW40F-05, ship it as **consigned** and note "do not substitute".
5. Do not populate any jumper/ferrite/Y-capacitor between `PI_GND` and `12V_GND` (none exist).
6. After assembly, before connecting the Pi: apply 12 V from a current-limited bench supply (1 A), check `5V_ISO_RAW` and `5V_PI` at TP3/TP4 = 5.0 V ±2 %, PG LED lit, and measure ≥1 MΩ between TP2 and TP5 (isolation).
7. Silkscreen: `OSBAMS Pi/Display Power Rev.A`, `12V IN`, `ISOLATED 5V OUT`, `5V / 8A MAX`, `PI SIDE — ISOLATED`, dashed isolation barrier, `RC1.1 - NOT FOR FAB` (remove for final).
8. J_IN pinout: pin 1 (outer) = +12V, pin 2 (inner) = GND. J_OUT: 1,2 = +5V_PI (outer row); 3,4 = PI_GND (inner row). Right-angle headers mate toward the board edge (J_IN toward −X, J_OUT toward +Y); housing flush with edge, peg holes per library footprint.
9. R2/R3 are **DNP** trim-network pads. Do not fit unless the Mean Well trim formula has been confirmed.

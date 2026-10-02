# Proposals — NOT implemented in RC1 (need your decision)

1. **Ideal-diode input stage** (e.g. a controller + N-FET) for reverse-polarity protection without a Schottky loss. Adds ~4 parts and a bit of layout; the keyed connector + F1 + harness labelling are the stated protection. Recommend adding only if the harness may be user-mated.
2. **Y-capacitor:** not proposed. Isolation stays clean unless EMC testing gives a specific reason (then choose safety class/value deliberately).
3. **Remote ON/OFF** is left open (assumed enabled). Confirm default polarity on the datasheet; a 0 Ω/jumper option can be added.
4. **F2 replacement:** pick the lowest-resistance 8 A Nano2 once the Littelfuse datasheet values are available; removal needs a documented protection analysis (Voltage_drop_budget.md).
5. **Trim:** R2/R3 DNP pads are on the board; fitting needs Mean Well's trim formula/range and your approval.

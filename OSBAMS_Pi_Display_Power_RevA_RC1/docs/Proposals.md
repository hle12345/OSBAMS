# Proposals — NOT implemented in RC1 (need your decision)

1. **Ideal-diode input stage** (e.g. a controller + N-FET) for reverse-polarity protection without a Schottky loss. Adds ~4 parts and a bit of layout; the keyed connector + F1 + harness labelling are the stated protection. Recommend adding only if the harness may be user-mated.
2. **Y-capacitor / bleed between PI_GND and chassis** (e.g. 1 nF 2 kV + 1 MΩ) to bleed common-mode charge on the floating 5 V domain and reduce EMI. Not fitted because the brief demands no connection between the grounds; this would be to chassis, not to controller ground — your call.
3. **Remote ON/OFF** is left open (assumed enabled). Confirm default polarity on the datasheet; a 0 Ω/jumper option can be added.
4. **F2 removal / replacement** if the bench voltage budget requires (see Isolation_review.md).

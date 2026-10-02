# Proposals — NOT implemented in RC2 (need an owner decision)

1. **Ideal-diode / reverse-polarity input stage:** not added; the keyed Micro-Fit connector + F1 + harness labelling are the protection. Add only if the 12 V harness can be user-mated.
2. **Y capacitor:** not proposed; isolation stays clean unless EMC testing gives a specific reason.
3. **Remote ON/OFF:** left open (enabled, per the spec: open = ON). A 0 Ω/jumper option can be added if a controlled enable is wanted.
4. **F2 replacement:** F2 (0451008.MRL, 7.7 mΩ) is the largest single drop after the socket; a lower-resistance 8 A fuse only after a documented protection analysis.
5. **Second Pi-branch return (more GND contacts):** not possible beyond pins 6/9/14/20 without enlarging the interposer's no-connect set; not needed (4 GND contacts).
6. **Lower-resistance Pi-end socket:** only if first-article contact measurements exceed 20 mΩ per contact.

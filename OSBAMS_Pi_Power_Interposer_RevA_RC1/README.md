# OSBAMS_Pi_Power_Interposer_RevA — RC1

**NOT FOR FABRICATION (release candidate).** Small keyed interposer that plugs onto the Raspberry Pi 5 40-pin header and exposes the isolated 5 V rail through a keyed Micro-Fit connector. Replaces the unpolarised Harwin M20 housing at the Pi end of the power harness.

`... Power PCB J_OUT (430450400) → short 16 AWG harness → J1 (430450400) on this board → Pi pins 2,4 (+5 V) and 6,9,14,20 (GND)`

| Item | Detail |
|---|---|
| Size | 65 × 22 mm (HAT+ width, header centred), 2-layer, 1.6 mm, 2 oz Cu (stackup in PCB file) |
| J1 | Molex 430450400, right-angle, mating face off the board edge; pins 1,2 = +5 V, 3,4 = GND (same as the power board J_OUT) |
| J2 | **Samtec SSW-120-01-S-D** (owner-selected): 2×20, 2.54 mm, through-hole, 30 µin gold, body 8.51 mm, tail 2.64 mm; mounted from the underside. All 40 positions socketed → no offset; long-tail option SSW-120-04-G-D rejected. Body 8.51 mm / tail 2.64 mm confirmed by catalog F-226; **plating letter `-S` is not a catalog plating code (use/confirm -L or -G)** |
| Power pins | +5 V: pins 2 and 4 (2 contacts); GND: pins 6, 9, 14, 20 (4 contacts); all other pins NC (no-connects) |
| Mounting | M1/M2: M2.5 holes at the Pi's header-end mounting holes (spacers = socket seated height) |
| Key | two M2.5 holes (K1 x=18.5, K2 x=43.25) 14.5 mm outward of the header axis — plan-view check vs the official Pi 5 drawing PASSES (`reports/Pi5_keying_check.txt`); see `docs/Keying_analysis.md` |
| Isolation | `PI_GND` here is the isolated Pi-side ground only; it never touches the controller ground. No Y-capacitor |

Files: `kicad/` (project, schematic, PCB), `gerbers/` + `drill/`, `bom/`, `reports/` (DRC; custom connectivity check — KiCad ERC not run here), `docs/`.
Spacers M2.5 × 11 mm (M1/M2), key posts M2.5 × 20 mm (K1/K2). Open: KiCad 10 ERC; first article: measured socket contact resistance, reversed-fit test, voltage/temperature. Regenerate with `tools/pi_display_power/build_interposer.py`.

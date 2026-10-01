# OSBAMS_Pi_Power_Interposer_RevA — RC1

**NOT FOR FABRICATION (release candidate).** Small keyed interposer that plugs onto the Raspberry Pi 5 40-pin header and exposes the isolated 5 V rail through a keyed Micro-Fit connector. Replaces the unpolarised Harwin M20 housing at the Pi end of the power harness.

`... Power PCB J_OUT (430450400) → short 16 AWG harness → J1 (430450400) on this board → Pi pins 2,4 (+5 V) and 6,9,14,20 (GND)`

| Item | Detail |
|---|---|
| Size | 57 × 22 mm, 2-layer, 1.6 mm, 2 oz Cu (stackup in PCB file) |
| J1 | Molex 430450400, right-angle, mating face off the board edge; pins 1,2 = +5 V, 3,4 = GND (same as the power board J_OUT) |
| J2 | **2×20** gold stacking female header: all 40 positions socketed → cannot be offset along or across the header; long tails keep the Pi pins reachable for the Waveshare 5 V/GND leads. **MPN not yet chosen** |
| Power pins | +5 V: pins 2 and 4 (2 contacts); GND: pins 6, 9, 14, 20 (4 contacts); all other pins NC (no-connects) |
| Key | two M2.5 holes (K1, K2) on the *outward* side — see `docs/Keying_analysis.md` |
| Isolation | `PI_GND` here is the isolated Pi-side ground only; it never touches the controller ground. No Y-capacitor |

Files: `kicad/` (project, schematic, PCB), `gerbers/` + `drill/`, `bom/`, `reports/` (DRC; custom connectivity check — KiCad ERC not run here), `docs/`.
Open: J2 MPN with published ratings, key-standoff 3D check, KiCad 10 ERC. Regenerate with `tools/pi_display_power/build_interposer.py`.

# Pi-end connection — keyed interposer (RC2)

`J_OUT (Micro-Fit 430450400) → ≤150 mm 16 AWG harness (43025-0400 both ends) → interposer J1 (430450400) → SSW-120-01 2×20 socket → Pi pins`

- +5 V on Pi pins **2 and 4**; GND on **6, 9, 14, 20**; **no other pin is connected** (34 pins are no-connect in the schematic; the netlist check confirms the pin map).
- Keying: Micro-Fit keys harness↔interposer; the full 2×20 socket prevents an offset fit; **two M2.5 × 20 mm key standoffs** prevent the 180° fit (the reversed fit would put +5 V on Pi pin 39 = GND and pin 37 = GPIO26, the GND pins on GPIOs). Evidence: `OSBAMS_Pi_Power_Interposer_RevA_RC2/docs/Mechanical_verification.md`.
- **The display no longer needs Pi header pins**: its 5 V / GND come from `J_DISP` on the power board (`Waveshare_integration.md`). The earlier "stacking socket so the pins stay reachable" question is therefore closed; the short-tail SSW-120-01 (tail 2.64 mm) is used.
- Socket: Samtec SSW-120-01 (body 8.51 mm, tail 2.64 mm, 4.7 A per pin with 2 pins powered; catalog F-226). The plating letter of the owner's code (`-S-D`) is not a catalog plating option: confirm at purchase (geometry is identical). **Contact resistance is a first-article measured parameter (acceptance ≤ 20 mΩ per contact).**
- Loading at 5 A: 2.5 A per +5 V pin (53 % of 4.7 A), 1.25 A per GND pin; the Pi header pin (~3 A class) is the practical limit — hence the hard 5.0 A limit on the Pi branch.
- Enclosure: the interposer overhangs the Pi edge by ~14 mm and the key posts by ~11 mm; the official Pi 5 case (98.5 × 70.3 × 33 mm) does not take it with the lid on — custom enclosure or open case. Bumper (89.6 × 60.6 mm) wraps 4.6 mm: check against the posts.
- Strain relief: tie/clip the harness at both ends; the Micro-Fit latch retains the connectors.

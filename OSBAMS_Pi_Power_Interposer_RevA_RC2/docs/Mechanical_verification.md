# Interposer mechanical verification (RC2)

Evidence: `reports/Pi5_keying_check.txt` (plan view digitised from the official Raspberry Pi 5 mechanical drawing RP-008347-DS-1, ±0.3 mm), `reports/Stack_height_check.txt`, `reports/ERC_equivalent_connectivity_report.txt`, KiCad 10 ERC/DRC reports. HAT+ geometry from RP-008281-DS-1. Socket dimensions from Samtec catalog F-226; orderable code `SSW-120-01-L-D` (user-relayed from the Samtec product page).

| Requirement | Result | Evidence |
|---|---|---|
| 2×20 header alignment | Pad pattern generated from the Pi pin numbers (pin 1 square pad, odd pins inner row, even pins outer row), 2.54 mm pitch; pin 1 silk marker; full 40-position socket (no offset fit possible) | footprint `SSW-120-01-L-D_RPi_TopView` (`OSBAMS_PiPwr.pretty`), HAT+ Fig. 2 |
| +5 V only on Pi pins 2 and 4 | PASS | netlist: `5V_PI` = J1.1, J1.2, J2.2, J2.4 |
| GND on the intended pins | PASS: Pi pins 6, 9, 14, 20 | netlist: `PI_GND` = J1.3, J1.4, J2.6, J2.9, J2.14, J2.20 |
| No accidental power on GPIO | PASS: the other 34 header pins are no-connect (no net, no copper) | `check_interposer.py`: 34 unconnected positions |
| 180° insertion prevention | PASS (mechanical): two M2.5 × 20 mm key standoffs on the outward side. Correct orientation: posts hang in free air 11 mm beyond the Pi edge. Reversed (pin n → 41 − n: +5 V would land on pin 39 = GND and 37 = GPIO26): posts land on bare Pi PCB (3.3 mm and 1.6 mm clear of the nearest component edge for a 5 mm post) and stop the socket face 11.5 mm above the Pi PCB vs pin tips at 9.0 mm (+2.5 mm margin, minimum post length 19.0 mm) | `Pi5_keying_check.txt`, `Stack_height_check.txt`, `Keying_analysis.md` |
| Pi 5 mechanical drawing | PASS: M1/M2 (3.5, 3.5) and (61.5, 3.5) coincide with the Pi header-end mounting holes (Ø2.7, 58 mm pitch) | `Pi5_keying_check.txt` |
| Active Cooler | PASS: SoC/Active-Cooler area 17.1 mm away in plan; board floats 11 mm above the header-side chips | `Pi5_keying_check.txt` |
| USB / Ethernet | PASS in plan: 5.8 mm gap to the USB/Ethernet stack (the interposer is above the header edge, the ports are on the opposite edge) | `Pi5_keying_check.txt` |
| DSI / CSI flex connectors | PASS: left-edge FFC connectors (y ≥ 20 mm) and the PoE 2×2 header are > 12 mm away | `Pi5_keying_check.txt` |
| Small connector by the right mounting hole | WATCH: 0.2 mm from the interposer edge in plan, the board floats 11 mm above it — **confirm its height when fitting** | `Pi5_keying_check.txt` |
| Enclosure | The interposer overhangs the Pi edge by ~14 mm and the posts by ~11 mm: not compatible with the official Pi 5 case with the lid on; custom enclosure/open case. Interposer top surface 12.6 mm above the Pi PCB, plus J1's height | `Stack_height_check.txt` |

## Is the mechanical key physically reliable?
It is reliable **if both key standoffs are fitted**: with them the reversed fit is blocked with a 2.5 mm margin and the posts rest on bare PCB. It is not an electrical interlock — without the posts the interposer can be fitted reversed and would put +5 V on a GND pin and GPIOs. Mitigations: silk `KEY` / `FIT KEY STANDOFFS`, the assembly step in `README.md`, and the **first-article reversed-fit test** (`First_article_checklist.md` D1) with power off on a spare/dummy Pi board. No change to the key geometry is needed for RC2; a physical fit check with a real Pi 5 (and the real 20 mm posts) closes the 3D question that the plan-view/height arithmetic cannot (no STEP model of the Pi 5 or the SSW socket was available).

## Socket data used
Samtec SSW-120-01: body 8.51 mm, tail 2.64 mm, mating insertion depth 3.68–6.35 mm (Pi pins protrude ~6.5 mm above the plastic: a pin up to 0.15 mm beyond the 6.35 mm maximum would bottom out, which the 11 mm spacer tolerates). Seated gap G = 8.51 + ~2.5 mm Pi header plastic = 11.0 mm → M2.5 × 11 mm spacers (standard HAT length). Hole 1.0 mm / pad 1.7 mm carried over; check against Samtec's recommended hole at first fit.

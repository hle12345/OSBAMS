# Keying analysis — why the interposer needs its own key

The Micro-Fit connector keys the **harness ↔ interposer** joint (a Micro-Fit 43025 housing mates a 43045 header one way only). The **interposer ↔ Pi header** joint is separate, and the Pi's 2×20 header is unshrouded and symmetric, so a socket board can be fitted rotated 180°.

Fitted 180° (pin *n* → 41−*n*), contacts land as follows:

| Interposer contact | Intended Pi pin | 180° lands on |
|---|---|---|
| +5 V (2, 4) | 5 V | pin 39 = **GND**, pin 37 = GPIO26 |
| GND (6, 9, 14, 20) | GND | pins 35, 32, 27, 21 = GPIOs |

→ the isolated +5 V would be shorted to Pi GND and driven into GPIOs. No choice of populated pins avoids this (the 5 V pins are only in the outer row; reversal sends them to the inner row, which has no 5 V pins). The fix must be mechanical.

## What the interposer does
1. **Full 2×20 socket (all 40 positions):** the only position the socket can seat is aligned with the header, so offset by one column/row is impossible. (A short 2×5 socket could be fitted 8 columns off and put 5 V on a GND pin — that is why it is not used.)
2. **Key standoffs K1/K2 on the outward side.** In the correct orientation the board's outward edge hangs past the Pi's edge, so posts fitted in K1/K2 point down into free air. If the board is fitted rotated 180°, the same posts land *over the Pi PCB* and stop the socket before the contacts engage. The post must be longer than the seated gap plus the contact-engagement depth so a reversed board cannot reach the pins.
3. Silk "KEY / FIT KEY STANDOFFS", pin-1 marker.

## Geometry now taken from the HAT+ specification (Fig. 2)
Pi mounting holes are 3.5 mm from the board edges on a 58 × 49 mm pattern, and the 40-pin header is centred between the end holes **on the hole-row axis**. Consequently the Pi's top edge is **3.5 mm outward of the header axis** and the interposer is laid out on that basis: 65 mm wide (header centred at 32.5 mm), M2.5 holes M1/M2 at 3.5 and 61.5 mm on the header axis (spacers to the Pi's end holes — mechanical retention/strain relief and the HAT+ "at least one hole aligned" practice), key-standoff holes K1/K2 at 14.5 mm outward, i.e. ~11 mm beyond the Pi edge in the correct orientation. The two end holes are symmetric about the header centre, so **the spacers alone do not key the board** — the posts do.
Reversed, K1/K2 land ~14.5 mm inboard of the header axis (18 mm from the Pi edge) — over the Pi PCB area next to the header. The HAT+ spec also says not to foul the PoE header and the camera/display/PCIe flex connectors; the interposer only extends 4 mm inboard, so it clears the SoC/Active Cooler area, and the 15–16 mm board-to-board rule matters only if the board is enlarged over the cooler.

## Result — checked against the official Pi 5 mechanical drawing (RP-008347-DS-1)
Script: `tools/pi_display_power/check_pi5_keying.py` → `reports/Pi5_keying_check.txt` (plan view, component boxes digitised from the drawing at 300 dpi, ±0.3 mm).
- **Correct orientation:** key posts K1/K2 at x = 18.5 and 43.25 mm, 14.5 mm outward of the header axis → Pi y = −11 mm, i.e. 11 mm beyond the Pi edge, in free air. **PASS.**
- **Reversed 180°:** the posts land at Pi (46.5, 18.0) and (21.8, 18.0) — **on bare PCB**, 3.3 mm and 1.6 mm clear of the nearest component edge for a 5 mm post. **PASS.** (The first post positions I used landed on or at the edge of chips; they were moved so a failed reversed attempt presses on bare PCB, not on a component.)
- **Hole alignment:** interposer M1/M2 (3.5, 3.5) and (61.5, 3.5) coincide with the Pi's header-end mounting holes (Ø2.7, 58 mm pitch). **PASS.**
- **Clearances in plan (correct orientation):** SoC/Active-Cooler area 17.1 mm; chip B 4.4 mm; USB/Ethernet stack 5.8 mm; DSI/CSI FFCs (left edge, y ≥ 20 mm) and the PoE 2×2 header (bottom right) > 12 mm. **Watch:** the small connector by the right mounting hole is only 0.2 mm from the interposer's right edge in plan (and another 0.9 mm away) — the board floats well above it at the seated gap, but confirm its height.
- The spacers alone still do not key the board (end holes are symmetric); the posts do.

## Heights — with Samtec SSW-120-01 (owner code -S-D; plating letter to be confirmed at purchase) (see `reports/Stack_height_check.txt`)
Seated gap G = 8.51 mm body + ~2.5 mm Pi header plastic (assumed) = 11.0 mm → **M1/M2: M2.5 × 11 mm** spacers (standard HAT length). Pi pins protrude ~6.5 mm above the plastic (tip ~9 mm, Pi drawing) and enter the 8.51 mm body. **K1/K2: M2.5 × 20 mm standoffs** — reversed, the socket face stops at 20 − 8.51 = 11.5 mm above the Pi PCB, 2.5 mm above the pin tips, so the pins cannot enter (minimum post length for 1.5 mm margin: 19.0 mm). In the correct orientation the posts hang ~9 mm below the Pi PCB plane, 11 mm beyond its edge. No Active-Cooler collision (17 mm away in plan). A physical reversed-fit test with a real Pi 5 is still a first-article check; a STEP confirmation is optional.

## Waveshare display
Closed in RC2: the display is powered from `J_DISP` on the power board, so it does not need Pi header pins and the short-tail SSW-120-01 socket is sufficient (`Waveshare_integration.md` in the power board docs).

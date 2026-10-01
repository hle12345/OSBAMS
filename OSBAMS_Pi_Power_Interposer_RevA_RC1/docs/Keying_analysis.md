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

## Not yet proven (needs your 3D/mechanical check)
- Distance from the header axis to the Pi 5 board edge and what sits inboard of the header at K1/K2 positions (14.5 mm from the axis) — a component or hole there changes the outcome.
- Post length vs stacking-socket seated height; interaction with the Pi 5 active cooler, the Waveshare DSI flex and the enclosure.
- The posts overhang the Pi edge in the correct orientation; confirm clearance in the enclosure.
Treat this as **mechanically keyed in design, unverified in 3D** until a printed/physical test confirms a reversed fit cannot seat. Also test a second, independent safeguard on the bench: with the isolated supply current-limited, plug in reversed and confirm it cannot make contact.

## Waveshare display
The Waveshare 5 V/GND leads stay on Pi GPIO 5 V/GND per Waveshare. Use **stacking (long-tail) sockets** so the Pi pins remain reachable above J2, or land the Waveshare leads on spare 5 V/GND positions via a second keyed outlet if you prefer — decision for you. Display current also flows through Pi pins 2/4, so the 3 A-per-contact consideration applies to the sum.

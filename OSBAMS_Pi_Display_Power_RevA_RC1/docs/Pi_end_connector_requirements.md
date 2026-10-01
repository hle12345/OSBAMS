# Pi-end connector — Harwin M20 crimp system (owner-selected; pin map + keying still OPEN)

## Selection (owner-cited, re-check vs Harwin PDFs)
- Housing: Harwin **M20-1070500** (2×N 2.54 mm cable housing; confirm pin count/layout on the drawing). Contacts: Harwin **M20-1160042** gold crimp, 22–30 AWG, **3 A per contact, 20 mΩ max initial**. Wire: **22 AWG** per contact. Harwin M20 housings are **not polarised**.
- Two contacts in parallel for +5 V (Pi pins 2, 4) and at least two for GND (e.g. pins 6, 9). 16 AWG trunk (≤150 mm) from J_OUT splits/splices to 22 AWG branch leads (~50 mm) near the Pi. No 16 AWG into the Pi-end contacts.

## Pin map (proposal) — Pi GPIO pins 1–10, 2×5 housing
| Pi pin | Role | Harness |
|---|---|---|
| 2, 4 | +5 V | populated (22 AWG red) |
| 6, 9 | GND | populated (22 AWG black); pins 14/20 can add GND contacts with a larger housing |
| 1,3,5,7,8,10 | 3V3 / GPIO | cavities left **empty** |

Loading at 5 A: **2.5 A per 5 V contact vs the 3 A rating (83 %)** — no derating headroom, and the Pi has only two 5 V pins. Keep real load ≤ ~5 A; do not use this for 8 A. (3 GND contacts help only the return.) Check the Waveshare power leads: they also need Pi 5 V/GND pins; if they use pins 2/4/6/9 they must share this housing, not a second Dupont plug.

## Hazard found: reversed insertion is destructive
The housing is unpolarised and the Pi header is unkeyed. Inserting the 2×5 housing rotated 180° maps pin *n* → 11−*n*:

| Harness contact | Intended pin | Reversed lands on |
|---|---|---|
| +5 V | 2 | pin 9 = **GND** |
| +5 V | 4 | pin 7 = GPIO4 (5 V into a 3.3 V pin) |
| GND | 6 | pin 5 = GPIO3 |
| GND | 9 | pin 2 = **+5 V** |

No population pattern is safe against reversal (any 5 V contact lands on a GPIO or GND pin). Anti-reversal must be **mechanical**. Options (your decision):
1. **Keyed interposer (recommended):** small board with a female 2×5 socket for the Pi pins and a keyed Micro-Fit receptacle/header toward the harness, so the whole path stays polarised and high-current. Adds one part.
2. A moulded/printed polarising shroud or clip that collides with the Pi/board features if reversed — needs 3D verification on the Pi 5 + Waveshare mounting, not just labeling.
3. Colour/label only — **not acceptable** for a permanent harness.

## Still open
Confirm housing pin count/orientation and keying choice; then update `datasheet_inputs.json` (`pi_end_pin_map_confirmed`). A bench temperature-rise and pull-out test of the assembled harness at 5 A remains a release gate.

# 5 V distribution voltage-drop budget (RC1.1)

Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT contacts -> harness -> Pi-end contacts -> Pi 5V pins` and the matching return.
**Every resistance below is an assumption** (Littelfuse, Molex and Mean Well datasheets were not reachable from the build environment). Replace the values in `tools/pi_display_power/voltage_budget.py` with datasheet/measured numbers and re-run.

## Assumptions

- Source: 5.00 V nominal; worst-case low 4.90 V (+-2 % setpoint+regulation, not verified).
- F2 hot resistance typ/max 8/15 mOhm; J_OUT mated contact 5/10 mOhm; Pi-end 2.54 mm crimp+header 8/20 mOhm per contact.
- Two contacts in parallel per rail (as specified); wire resistance derated x1.2 for ~50 C.
- PCB copper (2 oz, 0.246 mOhm/sq): 5 V path ~8.5 squares, GND return ~0.4 squares measured from the RC1.1 layout (RC1 assumed 6+6 mOhm-equivalent).
- Raspberry Pi 5 input: 5 V nominal; spec floor 4.75 V; low-voltage warning ~4.63 V (verify against Raspberry Pi documentation). Raspberry Pi recommends 5 V/5 A and says to allow for cable/connector loss.

## Results (voltage at the Pi 5V pins)

| Case | R typ (mOhm) | R max (mOhm) | V@Pi 3 A typ / worst | V@Pi 5 A typ / worst |
|---|---|---|---|---|
| RC1: 18 AWG 250 mm, 2+2 Pi pins | 30.4 | 54.4 | 4.91 / 4.74 | 4.85 / 4.63 |
| RC1.1: 16 AWG 150 mm, 2+2 Pi pins, wide copper | 25.6 | 49.6 | 4.92 / 4.75 | 4.87 / 4.65 |
| RC1.1 + 4 Pi GND pins (6,9,14,20 via splice) | 23.6 | 44.6 | 4.93 / 4.77 | 4.88 / 4.68 |
| RC1.1, F2 deleted (NOT recommended w/o protection analysis) | 17.6 | 34.6 | 4.95 / 4.80 | 4.91 / 4.73 |
| RC1.1 + trim to 5.10 V (only if Mean Well confirms) | 25.6 | 49.6 | 5.02 / 4.85 | 4.97 / 4.75 |

Typ = nominal source and typical resistances. Worst = low source and maximum resistances stacked (deliberately pessimistic corner).

## What each lever buys (RC1.1 baseline, 5 A, worst case)

| Change | Saves |
|---|---|
| F2 max 15 -> 8 mOhm | 35 mV |
| J_OUT contact max 10 -> 5 mOhm | 25 mV |
| Pi-end contact max 20 -> 10 mOhm | 50 mV |
| Harness 18 AWG/250 mm -> 16 AWG/150 mm | 20 mV |
| PCB copper RC1 -> RC1.1 | 4 mV |

## Reading the numbers
- **Typical case clears 4.85 V at 5 A (4.87 V); the stacked worst case does not (4.65 V, below the 4.75 V floor).** No single lever closes that corner: it needs low-resistance Pi-end contacts (-50 mV), a lower-resistance F2 (-35 mV) and trim together. Treat the worst-case corner as unproven until measured.
- The two largest terms are the *Pi-end* and J_OUT contacts, not copper or wire.
- Done in RC1.1, in your order: (1) fuse - kept F2 (see below); (2) 2+2 parallel contacts (unchanged); (3) harness changed to 16 AWG, <=150 mm; (4) PCB copper re-laid with wide pours (~5 mm bars, GND return through a full-width plane) - small gain; (5) trim *not* applied, but DNP pads R2/R3 added so a trim network can be fitted without a respin once Mean Well's trim formula and range are confirmed.
- **F2:** no lower-resistance 8 A Nano2 alternative can be selected without the Littelfuse datasheet. F2 is *not* removed. Its job is to protect the harness/connector if U1 fails short or its overload limit is higher than assumed; an 18 AWG or 16 AWG short run tolerates 8 A, so the fuse is protecting against >8 A fault current that U1's own limiting should already cap. Removal is a protection-analysis decision for you, not a voltage-margin shortcut.
- **Biggest lever that needs no new board:** choose Pi-end terminals/housing with low contact resistance (measure them), and keep +5 V on both Pi 5V pins (2,4). Adding GND pins (6,9,14,20) via a splice is shown as an option; it helps the return only.
- **Trim:** if Mean Well confirms the RSDW trim range, +2 % (5.10 V) gives ~4.97 V typical and ~4.75 V stacked-worst-case at 5 A (still marginal); no-load worst-case source is ~5.00 x 1.02 x 1.02 = ~5.20 V (< 5.25 V). Do not fit R2/R3 until the formula is confirmed - a wrong value could over-volt the Pi.
- **Gate:** a bench measurement *at the Pi header pins* under real Pi 5 + Waveshare load (and a stress test at 5 A) is still required before release.

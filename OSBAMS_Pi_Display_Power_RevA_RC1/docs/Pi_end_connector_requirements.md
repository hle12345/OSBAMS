# Pi-end connection — keyed interposer (decision)

**Superseded:** the unpolarised Harwin M20 housing is no longer the Pi connection. The Pi end is the keyed interposer `OSBAMS_Pi_Power_Interposer_RevA_RC1/`:

`Power PCB J_OUT (Micro-Fit 430450400) → ≤150 mm 16 AWG crimped harness (43025-0400 at both ends) → interposer J1 (430450400) → 2×20 gold stacking socket → Pi pins`

- +5 V on Pi pins **2 and 4** (two contacts in parallel); GND on **6, 9, 14, 20** (four contacts); no Dupont wires, no splices.
- Keying: Micro-Fit keys harness↔interposer; the full 2×20 socket prevents offset; **key standoffs** prevent the 180° fitting that would otherwise swap +5 V and GND (see the interposer's `docs/Keying_analysis.md`; 3D check still to do).
- Harwin M20-1160042 (3 A, 22–30 AWG, 0.64 mm pin) is verified from the uploaded datasheet but is not in the power path any more.
- Strain relief: harness tie/clip at the interposer and the power board; Micro-Fit latch provides retention.

## Still open
1. Stacking-socket **exact MPN** with a published per-contact current and contact resistance (the budget needs ≤ ~14 mΩ per contact for an uncalibrated fixed setpoint, ≤ ~21 mΩ for calibrated units; 3 A per contact rating is a floor — 2.5 A per 5 V contact at 5 A).
2. Key-standoff 3D check against the Raspberry Pi 5 drawing, active cooler and enclosure; physical reversed-fit test.
3. Waveshare 5 V/GND leads: confirm which Pi pins they use and keep them reachable above the stacking socket.

## Socket — Samtec SSW-120-01-S-D (owner-selected baseline) — dimensions confirmed by catalog F-226; plating letter needs confirming
40 positions, 2 rows, 2.54 mm, through-hole vertical receptacle, 30 µin gold mating / tin tails, **body 8.51 mm, tail 2.64 mm**, −55…+125 °C, 4.7 A (Samtec SSW/TSW spec: **one pin powered per row** — not 4.7 A per contact with all adjacent power contacts loaded). **Catalog page F-226 (uploaded) confirms:** body 8.51 mm, lead style -01 tail 2.64 mm, 40 positions (20 per row), 4.7 A per pin with 2 pins powered (the same one-per-row basis as the spec), 465 VAC/655 VDC, mating insertion depth 3.68–6.35 mm, max 100 cycles with 10 µin gold.
- **⚠ Ordering-code mismatch:** the catalog's plating options are **-F** (gold flash), **-L** (10 µin Au), **-G** (20 µin Au) and **-T** (tin); **-S is a *row* option (single row)** and no 30 µin gold option is listed. `SSW-120-01-S-D` is therefore not a code I can match to the catalog (it may be a legacy/distributor code). Confirm the exact orderable code with the distributor/Samtec, or use a catalog-valid equivalent: **`SSW-120-01-L-D`** (10 µin Au, matte-tin tails) or **`SSW-120-01-G-D`** (20 µin Au). The BOM keeps your code, flagged. `SSW-120-04-G-D` (14.83 mm tail, no stock) is rejected — nothing mechanical requires it.
- **Use:** 2 contacts for +5 V (Pi pins 2, 4 → 2.5 A each at 5 A, 53 % of 4.7 A) and 4 for GND (6, 9, 14, 20). The Pi header pin (~3 A class) is the practical limit.
- **Mounting:** from the interposer underside, soldered on top; 2.64 mm tails through the 1.6 mm board leave 1.04 mm for soldering. Hole size 1.0 mm is carried over — confirm against Samtec's footprint.
- **Heights** (`OSBAMS_Pi_Power_Interposer_RevA_RC1/reports/Stack_height_check.txt`): seated gap G = 8.51 + ~2.5 mm Pi header plastic = **11.0 mm** → M2.5 × 11 mm spacers; Pi pins protrude 6.5 mm above the plastic and enter the 8.51 mm body; key posts **M2.5 × 20 mm** keep the reversed socket face 11.5 mm above the Pi PCB vs pin tips at ~9 mm (+2.5 mm margin). Posts hang ~9 mm below the Pi PCB plane, 11 mm beyond its edge — an enclosure consideration.
- **No collision** with the Active Cooler (17 mm away in plan, board 11 mm above the header-side chips). The official Pi 5 case does not accommodate the overhang with the lid on.
- **Contact resistance:** none published for this ordering code (only ΔLLCR 15 mΩ after tests). The budget keeps a **conservative 20 mΩ placeholder, treated as a first-article measured parameter** (measure on the assembled interposer; do not substitute a lower value on paper).

## Enclosure interactions (from the Raspberry Pi case and bumper briefs, uploaded)
- Official Pi 5 case (98.5 × 70.3 × 33 mm, approximate): HATs mount **on top of the case with standoffs and GPIO header extenders**, cables leave through a breakout slot. The interposer's outward overhang (~14 mm beyond the Pi edge, key posts ~11 mm) will not fit inside this case with the lid on — use your own enclosure or the open case.
- Bumper (89.6 × 60.6 mm) wraps ~4.6 mm around the board edge — check against the posts and the overhanging board.
- PCIe FFC power pins are 500 mA each (1 A total): not an alternative path.

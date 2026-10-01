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

## Socket family — Samtec SSW (through-hole), per the uploaded SSW/TSW specification
The SMT SSM strip is dropped in favour of the **SSW** vertical through-hole socket family (fits the existing THT interposer footprint; the socket is inserted from the underside, soldered from the top).
Verified from the spec (rev C, 2023): 4.7 A **with one pin powered per row**, 465 VAC, gold −55…+125 °C, 1000 cycles, normal force ≥ 30 g (gold), standoffs recommended for a robust board-to-board joint (our M2.5 spacers).
**Gaps (not in this spec):**
1. The exact **2×20 ordering code** (lead style / tail length, plating, body height) and its footprint/drawing — on the Samtec SSW-120 product page; please upload that page/drawing.
2. **Multi-pin current derating** — we power +5 V pins 2 and 4 side by side (two in the same row) and four GND pins across both rows, so the 4.7 A single-pin figure does not apply directly; the catalog derating curve is needed. 2.5 A per 5 V contact is ~53 % of 4.7 A.
3. **Contact resistance:** Samtec specifies only a *change* (ΔLLCR 15 mΩ max after testing), not an initial value; the budget keeps a 20 mΩ placeholder (≈ 5 mΩ initial + 15 mΩ drift), with a 25 mΩ sensitivity row.
4. Body height vs the Pi header (pin length ~6 mm above the plastic): confirm full engagement; it also sets the seated gap, the M2.5 spacer length and the key-post length.

## Enclosure interactions (from the Raspberry Pi case and bumper briefs, uploaded)
- Official Pi 5 case (98.5 × 70.3 × 33 mm, approximate): HATs mount **on top of the case with standoffs and GPIO header extenders**, and cables leave through a GPIO breakout slot. The interposer's outward overhang (~14 mm beyond the Pi edge, key posts ~11 mm beyond) will not fit inside this case with the lid on; it is intended for your own enclosure or the open/lid-off case.
- Bumper (89.6 × 60.6 mm): wraps ~4.6 mm around the board edge — check it against the key posts and the overhanging board.
- PCIe FFC power pins are 500 mA each (1 A total): not an alternative path.

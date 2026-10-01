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

## Socket candidate under review — Samtec SSM-120-S-DV-K-TR (owner proposal; not yet selected)
Owner data: 40 positions, 2 rows, 2.54 mm, ~5.2 A per contact. Not yet checked (no datasheet/drawing available here):
1. **Geometry:** the SSM-xxx-S-DV family appears (from memory, unverified) to be a low-profile **surface-mount** strip, not a pass-through/stacking socket. If so it must be soldered to the interposer's *underside* pads and mate downward onto the Pi pins: then (a) the interposer needs an SMT pad pattern from Samtec's drawing instead of the current THT pattern, (b) the Pi's pins are no longer reachable from above for the Waveshare 5 V/GND leads (they would need a separate keyed outlet), and (c) the seated gap/engagement depth, hence the key-post length, change.
2. **Mechanical load:** an SMT joint is the only retention besides the M2.5 spacers; the spacers must carry the insertion/extraction force.
3. **Electrical:** 5.2 A/contact is the socket's rating; the mating Pi header pin (0.64 mm square) and the Pi's traces still limit to roughly 3 A per pin, so 2 × 5 V pins at 2.5 A each stay at ~83 % of that. The Samtec data supplied has no contact resistance; the budget keeps a 20 mΩ placeholder until it does.
4. If SMT is unsuitable, pick a through-hole 2×20 stacking/pass-through family (Samtec offers 2.54 mm 40-position receptacles in other series) — again from a datasheet that gives height, tail length, contact rating and contact resistance.
**Needed from you:** the Samtec datasheet/drawing (PDF, plus footprint/3D if available) for the exact variant.

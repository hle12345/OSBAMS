# OSBAMS Rev.2 Controller — Fabrication notes (2026-10-01)

**RC1 - REVIEW CANDIDATE - NOT FOR FABRICATION.** These are working notes for the RC1 review package, not an order specification.

## Board
- Name `OSBAMS Rev.2 Controller`, revision RC1, size 100 x 90 mm, single piece (no panelization specified yet), 4 copper layers, 1.6 mm FR-4 (TG >= 150 C suggested), outer copper 1 oz, inner copper 0.5 oz or 1 oz.
- Layer use: L1 components + signals, L2 solid GND plane, L3 routing + GND fill, L4 components/signals + GND fill. A separate **GND_HOST island** (isolated USB side) occupies x 74.5-97.5 mm, y 2.5-47.5 mm on all layers with a 3 mm gap to GND under the ISO7721.
- Finish: ENIG recommended (0.5 mm pitch LQFP-64, QFN-20). Soldermask green or black, white silkscreen. Lead-free.
- Edge: plain rectangle, no V-cut, 4 x M3 NPTH (3.2 mm) at (4,4), (96,4), (4,86), (96,86). 3 fiducials 1 mm / 2 mm mask opening.
- Design rules used (netclasses in the .kicad_pro): default track 0.2 mm / clearance 0.15 mm, POWER 0.3 mm / 0.2 mm, RAIL 0.3 mm / 0.15 mm, pack-level and Kelvin nets 0.2 mm / 0.15 mm (IPC-2221B B4 coated limit for 77 V is ~0.13 mm; the pack-level nets are not at 0.4 mm), via 0.6/0.3 mm (a few 0.5/0.3 mm vias in congested spots), copper-to-edge 0.3 mm. Measured in this layout: min track 0.20 mm, min via 0.50/0.30 mm. Check against PCBWay's current 4-layer capability before ordering.
- Controlled impedance: none required (no high-speed nets; USB 2.0 full-speed D+/D- are short, 90 ohm not controlled in RC1 - review).
- Silkscreen: connector names, pin numbers, polarity, `OSBAMS Rev.2 Controller`, `RC1 2026-10-01`, `44 V / 10 A MAX`, `NOT FOR FABRICATION` (remove at release).

## Files
Gerber/drill files in this folder are a **KiCad 10.0.6 export of a script-generated design**. They are for review and DFM discussion only. **Regenerate them from the .kicad_pcb on your own KiCad installation (and re-run ERC/DRC) before any order.** Do not fabricate from the files in this package.

## Open fabrication gates
See `PCBWAY_RELEASE_CANDIDATE_REPORT.md` (BLOCKERS BEFORE PCBWAY ORDER).

# OSBAMS Rev.2 Controller — Fabrication notes (2026-10-01)

**RC1.2 - REVIEW CANDIDATE - NOT RELEASED FOR FABRICATION.** These are working notes for the RC1 review package, not an order specification.

## Board
- Name `OSBAMS Rev.2 Controller`, revision RC1.2, size 100 x 90 mm, single piece (no panelization specified yet), 4 copper layers, 1.6 mm FR-4 (TG >= 150 C suggested), outer copper 1 oz, inner copper 0.5 oz or 1 oz.
- Layer use: L1 components + signals, L2 solid GND plane, L3 routing + GND fill, L4 components/signals + GND fill. A separate **GND_HOST island** (isolated USB side) occupies x 74.5-97.5 mm, y 2.5-47.5 mm on all layers; **every host-net copper item keeps >= 1.0 mm from every controller-net copper item on every layer** (custom DRC rule in `OSBAMS_Rev2_RC1.kicad_dru`; 3.0 mm gap in the ISO7721 area). See `ISOLATION_CHECK.txt`.
- Finish: ENIG recommended (0.5 mm pitch LQFP-64, QFN-20). Soldermask green or black, white silkscreen. Lead-free.
- Edge: plain rectangle, no V-cut, 4 x M3 NPTH (3.2 mm) at (4,4), (96,4), (4,86), (96,86). 3 fiducials 1 mm / 2 mm mask opening.
- Design rules (netclasses in the .kicad_pro + custom rules in the .kicad_dru): default track 0.2 mm / clearance 0.15 mm; POWER 0.3 mm / 0.2 mm; RAIL 0.3 mm / 0.15 mm; **pack-level and Kelvin nets 0.2 mm clearance (an intentional choice: IPC-2221B Table 6-1, 31-100 V, B4 = external conductors under permanent polymer coating/solder mask = 0.13 mm, internal B1 = 0.1 mm; 0.2 mm is 1.5x B4 — exposed pads/terminations (A6 0.6 mm) cannot be met on 0.5 mm-pitch parts, so the INA228 courtyard is exempt at 0.15 mm)**; host-to-controller 1.0 mm; via 0.6/0.3 mm (0.5/0.3 mm in a few congested spots), min track 0.20 mm, copper-to-edge 0.3 mm. **PCBWay's current 4-layer minimum track/space/drill/annular-ring capability must be confirmed in their quote/DFM tool** (this build could not reach their site); the values above are well above the usual 0.1 mm / 0.2 mm drill minimums.
- Controlled impedance: none required (no high-speed nets; USB 2.0 full-speed D+/D- are short, 90 ohm not controlled in RC1 - review).
- Silkscreen: connector names, pin numbers, polarity, `OSBAMS Rev.2 Controller`, `RC1.2 2026-10-01`, `44 V / 10 A MAX`, `NOT FOR FABRICATION` (remove at release by editing the text in KiCad before the final export).

## Files
This package contains **no Gerber or drill files**: the earlier script-generated candidate Gerbers were removed so they cannot be used by mistake. Export Gerbers/drills from the final `.kicad_pcb` in your own KiCad 10 after your local ERC/DRC (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## Open fabrication gates
See `PCBWAY_RELEASE_CANDIDATE_REPORT.md` (BLOCKERS BEFORE PCBWAY ORDER).

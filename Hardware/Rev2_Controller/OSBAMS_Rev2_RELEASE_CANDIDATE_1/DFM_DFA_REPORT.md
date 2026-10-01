# OSBAMS Rev.2 Controller — DFM / DFA report (2026-10-01)

**RC1 - REVIEW CANDIDATE - NOT FOR FABRICATION.** Automated checks are in the repository (`design/checks.py`, KiCad ERC/DRC). Human review of PCBWay's CAM feedback is still required.

## Electrical rule checks (KiCad 10.0.6)
- ERC (schematic, 11 sheets): **0 violations**.
- DRC (PCB): **3 violations, 0 unconnected pads, 0 footprint errors**. Violation types: silk_over_copper: 1, silk_overlap: 2.
- Netlist: the KiCad schematic netlist was compared with the design intent (66+ nets, every pin): see `NETLIST_CHECK.txt`.

## Polarity
| Ref | Footprint | Check | Pad 1 net | Result |
|---|---|---|---|---|
| D1 | Diode_SMD:D_SMB | cathode pad from library bar: 1 | pad1 net +12V | OK |
| D2 | Diode_SMD:D_SMA | cathode pad from library bar: 1 | pad1 net +12V | OK |
| D5 | Diode_SMD:D_SMB | cathode pad from library bar: 1 | pad1 net SHUNT_INP_RAW | OK |
| D6 | Diode_SMD:D_SMB | cathode pad from library bar: 1 | pad1 net SHUNT_INN_RAW | OK |
| D7 | Diode_SMD:D_SMB | cathode pad from library bar: 1 | pad1 net PACK_INA | OK |
| D9 | Diode_SMD:D_SMA | cathode pad from library bar: 1 | pad1 net COIL_V | OK |
| D11 | Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal | cathode pad from library bar: 1 | pad1 net ES_LED_A | OK |
| D12 | Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal | cathode pad from library bar: 1 | pad1 net FB_LED_A | OK |
| D3 | LED_SMD:LED_0805_2012Metric | cathode pad from library bar: silk C-shape convention | pad1 net GND | OK |
| D4 | LED_SMD:LED_0805_2012Metric | cathode pad from library bar: silk C-shape convention | pad1 net GND | OK |
| D10 | LED_SMD:LED_0805_2012Metric | cathode pad from library bar: silk C-shape convention | pad1 net COIL_SW | OK |

Result: **PASS**. (Rev.1's symbol-vs-footprint polarity defect is not repeated: every diode uses a KiCad symbol with K = pin 1 and a footprint with the cathode bar at pad 1.)

## Layout statistics
702 track segments, 503 vias, min track 0.20 mm, min via 0.50/0.30 mm, 102 SMD footprints, 12 through-hole footprints, 3 fiducials, 4 mounting holes, 27 test points.

## DFM items for review
- 0.5 mm pitch LQFP-64 and QFN-20: confirm PCBWay minimum solder-mask bridge and paste stencil; ENIG recommended.
- Via-in-pad is NOT used. Tracks to LQFP pads leave on the pad axis.
- THT connectors (EB21A-02-C) use a footprint drawn from the Adam Tech drawing EB21A-XX-C rev B (hole 1.30 mm, pad 2.6 mm [design choice], body 10.6 x 8.5 mm).
- Mounting holes are NPTH 3.2 mm; fiducials 1 mm / 2 mm opening at three corners.
- USB-C GCT USB4105-GF-A: confirm the shield tab/NPTH holes against the connector drawing; overhang 0.8 mm beyond the board edge is intentional.
- Isolation: GND and GND_HOST are separate copper islands. **Measured (script, KiCad zone fills): 3.0 mm between the GND and GND_HOST copper in the ISO7721 area on every layer; along the rest of the island edge only the 0.25 mm zone clearance** (functional separation, DRC-checked between nets; not a creepage design away from the isolator). No track crosses the gap except through the ISO7721. The ISO7721 D-8 package creepage/clearance rating must be confirmed against the datasheet insulation tables.
- Kelvin pair (INA_INP/INA_INN) uses a dedicated 0.25 mm / 0.4 mm class; see the layout review notes in the RC report.

## DFA items for review
- Mixed SMT + THT; THT is hand/selective-solder. 142 footprints total including features.
- Reflow/wave: one-pass reflow plus manual THT is assumed.
- Fiducials present; no components under connectors; clearance between SMT parts >= 0.35 mm courtyard margin.

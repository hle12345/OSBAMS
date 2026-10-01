# OSBAMS Rev.2 Controller — DFM / DFA report (2026-10-01)

**RC1 - REVIEW CANDIDATE - NOT FOR FABRICATION.** Automated checks are in the repository (`design/checks.py`, KiCad ERC/DRC). Human review of PCBWay's CAM feedback is still required.

## Electrical rule checks (KiCad 10.0.6)
- ERC (schematic, 11 sheets): **0 violations**.
- DRC (PCB): **12 violations, 0 unconnected pads, 0 footprint errors**. Violation types: silk_over_copper: 9, silk_overlap: 3.
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
676 track segments, 517 vias, min track 0.20 mm, min via 0.60/0.30 mm, 99 SMD footprints, 12 through-hole footprints, 3 fiducials, 4 mounting holes, 27 test points.

## DFM items for review
- 0.5 mm pitch LQFP-64 and QFN-20: confirm PCBWay minimum solder-mask bridge and paste stencil; ENIG recommended.
- Via-in-pad is NOT used. Tracks to LQFP pads leave on the pad axis.
- THT connectors (EB21A-02-C) have a **provisional footprint**: drill 1.4 mm / pad 2.6 mm / body outline are placeholders until the Adam Tech drawing is checked.
- Mounting holes are NPTH 3.2 mm; fiducials 1 mm / 2 mm opening at three corners.
- USB-C GCT USB4105-GF-A: confirm the shield tab/NPTH holes against the connector drawing; overhang 0.8 mm beyond the board edge is intentional.
- Isolation: GND and GND_HOST are separate copper islands with a 3 mm gap; no track crosses the gap except through the ISO7721 (checked by DRC clearance between nets). Pack-level nets (PACK_INA, PACK_ADC, ADC_MID, RELAY_OUT, FB_R1, FB_R2, SHUNT_*_RAW, INA_*) use a 0.4 mm clearance class.
- Kelvin pair (INA_INP/INA_INN) uses a dedicated 0.25 mm / 0.4 mm class; see the layout review notes in the RC report.

## DFA items for review
- Mixed SMT + THT; THT is hand/selective-solder. 142 footprints total including features.
- Reflow/wave: one-pass reflow plus manual THT is assumed.
- Fiducials present; no components under connectors; clearance between SMT parts >= 0.35 mm courtyard margin.

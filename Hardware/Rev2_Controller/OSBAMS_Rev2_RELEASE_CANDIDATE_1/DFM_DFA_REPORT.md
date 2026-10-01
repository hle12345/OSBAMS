# OSBAMS Rev.2 Controller — DFM / DFA report (2026-10-01)

**RC1.2 - REVIEW CANDIDATE - NOT RELEASED FOR FABRICATION.** Automated checks are in the repository (`design/checks.py`, KiCad ERC/DRC). Human review of PCBWay's CAM feedback is still required.

## Electrical rule checks (KiCad 10.0.6)
- ERC (schematic, 11 sheets): **0 violations**.
- DRC (PCB): **0 violations, 0 unconnected pads, 0 footprint errors**. Violation types: none.
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
721 track segments, 518 vias, min track 0.20 mm, min via 0.50/0.30 mm, 105 SMD footprints, 12 through-hole footprints, 3 fiducials, 4 mounting holes, 27 test points.

## DFM items for review
- 0.5 mm pitch LQFP-64 and QFN-20: confirm PCBWay minimum solder-mask bridge and paste stencil; ENIG recommended.
- Via-in-pad is NOT used. Tracks to LQFP pads leave on the pad axis.
- THT connectors (EB21A-02-C) use a footprint drawn from the Adam Tech drawing EB21A-XX-C rev B (hole 1.30 mm, pad 2.6 mm [design choice], body 10.6 x 8.5 mm).
- Mounting holes are NPTH 3.2 mm; fiducials 1 mm / 2 mm opening at three corners.
- USB-C GCT USB4105-GF-A: confirm the shield tab/NPTH holes against the connector drawing; overhang 0.8 mm beyond the board edge is intentional.
- Isolation: the whole perimeter of the GND_HOST island is the controller/host boundary. A custom DRC rule enforces >= 1.0 mm between any host-net item and any controller-net item on every layer (3.0 mm in the ISO7721 area); `ISOLATION_CHECK.txt` lists the minimum per layer with coordinates. No track, via or pad of either domain lies in the other; the ISO7721 is the only crossing. The working voltage across the barrier is at most the 44 V ceiling (functional isolation; IPC-2221B coated 0.13 mm); the ISO7721 D-8 package ratings must be confirmed against the datasheet insulation tables.
- Kelvin pair (INA_INP/INA_INN) and the other pack-level nets use the 0.2 mm clearance class (see FABRICATION_NOTES for the IPC-2221B basis); routed as a pair, with 10 Ω surge resistors R42/R43 at the connector and 10 Ω R11/R12 at the INA228.

## DFA items for review
- Mixed SMT + THT; THT is hand/selective-solder.
- Reflow/wave: one-pass reflow plus manual THT is assumed.
- Fiducials present; no components under connectors; clearance between SMT parts >= 0.35 mm courtyard margin.

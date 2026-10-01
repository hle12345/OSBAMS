# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1 (2026-10-01)

**Status: RELEASE CANDIDATE 1 — FOR REVIEW. NOT authorization to fabricate.** This report does not call the design final, production ready, hardware validated or released for fabrication; the evidence does not support those statements.

## READY FOR REVIEW
Everything below is complete and internally checked (KiCad 10.0.6 tooling in the build container, see `BUILD_ENVIRONMENT.md`):

- **Architecture** reconciled (rev D) and decisions closed: direct STM32L476RGT6, bare INA228, no 5 V rail (LMR14006Y → 3V3 → 3V3_A), TC74 on its own I²C2, isolated host path, SMD IRLML0060 relay driver with plain flyback.
- **Calculations** regenerated (`POWER_TREE_AND_CALCULATIONS.md`): ADC divider error split (divider ±0.43 % / reference), ADC protection analysis with no back-feed (powered / unpowered / reversed / transient, clamp currents, PA1 max voltage, leakage error), INA228 scaling (ADCRANGE 0, SHUNT_CAL 1250), buck design equations, relay driver, **VO610A stages recomputed from the guaranteed CTR (13 % @ 1 mA, 40 % @ 10 mA) with temperature/aging derates and 2× saturation margin — the arbitrary 20 % CTR is deleted**; ESTOP_SENSE 5.6 kΩ and RELAY_FB 3 × 4.7 kΩ both pass their own margin tests down to the supported range (RELAY_FB ≥ 24 V, supported pack range ≈ 30–44 V).
- **KiCad project** (`OSBAMS_Rev2_RC1.kicad_pro/.kicad_sch/.kicad_pcb`, 11 schematic pages, custom symbol/footprint libraries): standard KiCad 10 symbols; custom symbols only for INA228, LMR14006Y, ISO7721.
- **ERC (KiCad 10.0.6): 0 violations** (`ERC_REPORT.rpt`). A negative control (deleting a no-connect) was confirmed to make ERC fail, so the check is live.
- **Netlist check:** KiCad schematic netlist vs PCB pad nets — 0 mismatches (`NETLIST_CHECK.txt`); diode/LED polarity check — PASS (cathode pad 1 on every diode footprint verified against the footprint library geometry and the nets).
- **4-layer PCB** 100 × 90 mm: L2 solid GND, L3 signal routing + GND fill, isolated GND_HOST island (3.0 mm gap in the ISO7721 area, 0.25 mm zone clearance elsewhere), analog zone away from the buck, Kelvin pair nets, 4 × M3, 3 fiducials, connector/polarity/revision/`44 V / 10 A MAX` silkscreen, 27 test points. Autorouted with Freerouting 1.9.0 and checked with KiCad DRC.
- **DRC (KiCad 10.0.6): 3 violations, 0 unconnected pads, 0 footprint errors** — types: silk_over_copper 1, silk_overlap 2 (`DRC_REPORT.rpt`).
- **Outputs:** schematic PDF, Gerber + drill files and ZIP (named NOT_FOR_FABRICATION), BOM xlsx/csv, CPL (SMT and all parts), assembly drawing (top) and copper-layer PDFs, assembly notes, fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, evidence register (11 VERIFIED_LOCAL / 50 USER_RELAYED_MANUFACTURER / 15 UNVERIFIED), supply-chain report.
- **Remote TC74 probe PCB** (`probe/`): schematic, ERC and layout for the small pack-surface probe with the owned VJ0805Y104JXXAT at the sensor VDD.

## BLOCKERS BEFORE PCBWAY ORDER
Only items that genuinely must be resolved before ordering:

1. **Manufacturer-document verification** — 29 critical register entries are not VERIFIED_LOCAL (see `EVIDENCE_REGISTER.md`, `MANUFACTURER_DATA_RECONCILIATION.md`). Read locally from the supplied PDFs (VERIFIED_LOCAL): ISO7721, CP2102N, SRN6045TA-100M and the EB21A drawing. All other pin maps (INA228, LMR14006Y, IRLML0060, VO610A, TC74, STM32 LQFP64 pins) match the data relayed by the user but remain USER_RELAYED_MANUFACTURER until their datasheets are supplied. Still open: **IRLML0060 at a 3.3 V gate** (first-article VDS/coil-current measurement), STM32 POR/VDD max, DG57CM release time, connector footprint geometry beyond pitch/pin count, LMR14006Y SHDN threshold, INA228 differential input maximum.
1a. **LMR14006Y minimum on-time:** TON_MIN = 95 ns (relayed). 12 V passes; the 15 V corner is marginal at the highest fsw; the 24.4 V transient (64 ns) is below TON_MIN — no regulation claim there (pulse skipping expected), limited to ≈ 14–16 V steady-state input.
1b. **1.5SMBJ48A vs INA228 85 V:** clamp is 77.4 V only at 19.4 A; 100.6 V at the 8/20 µs rating point (97 A). Bounded credible transients (≤ 19.4 A) are within 85 V; fast ≥ 45 A surges are not protected. Owner sign-off (or the optional series-resistor/two-stage-clamp redesign) required — see calculations §2b.
2. **ERC/DRC and Gerber regeneration on your own KiCad 10 installation.** The ERC/DRC results above come from the build container; the Gerber/drill files in this package are exports of a script-generated design and must not be used for fabrication. Remaining DRC items (3) must be reviewed and dispositioned (see `DFM_DFA_REPORT.md`).
3. **Protection calculation sign-off:** the ADC clamp/back-feed analysis depends on UNVERIFIED diode leakage/forward-voltage and on the MCU pin structure; the 3V3_A bleeder (R4) is fitted to guard the unknown, at 1 mA permanent load.
4. **Distributor stock / lifecycle / supplier SKUs** were not checked (sites unreachable); orderable suffixes (INA228AIDGSR, LMR14006YDDCR, ISO7721DR, CP2102N-A02-GQFN20, SS14-E3/61T) must be confirmed; only 2 of ~25 VJ0805-style 100 nF are owned, and a 3rd 1.5SMBJ48A is needed.
5. **PCBWay CPL rotations** must be checked in PCBWay's CAM preview (library rotation offsets differ).
6. Relay-feedback and E-stop resistor networks are sized from user-relayed CTR data with design-margin derates (0.8 × 0.8, UNVERIFIED); confirm with the official CTR-vs-IF curve.

*First-article measurements (3V3/3V3_A ripple, coil current, release time) are bring-up items, not order blockers.*

## Package contents
`OSBAMS_Rev2_RC1.kicad_pro/.kicad_sch/.kicad_pcb` (+ sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC1_Schematic.pdf`, `OSBAMS_Rev2_RC1_Gerbers_NOT_FOR_FABRICATION.zip`, `gerber/`, `drill/`, `OSBAMS_Rev2_RC1_BOM.xlsx/.csv`, `OSBAMS_Rev2_RC1_CPL.csv`, `OSBAMS_Rev2_RC1_CPL_ALL.csv`, `OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf`, `ASSEMBLY_NOTES.md/.pdf`, `FABRICATION_NOTES.md/.pdf`, `OSBAMS_Rev2_RC1_Test_Point_Map.pdf`, `POWER_TREE_AND_CALCULATIONS.md`, `DFM_DFA_REPORT.md`, `EVIDENCE_REGISTER.md/.json`, `MANUFACTURER_DATA_RECONCILIATION.md`, `SUPPLY_CHAIN_REPORT.md`, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `probe/`.

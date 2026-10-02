# PCBWay readiness checklist — RC2 (no Gerbers yet)

Owner runs ERC/DRC and exports Gerbers/drill in KiCad 10 from the delivered projects.

- [x] 2-layer, 100 × 70 mm, 1.6 mm, 2 oz Cu in the stackup, ENIG, 4 × M3 NPTH, 3 fiducials, test points TP1–TP5
- [x] KiCad 10.0.6 ERC 0, DRC 0 (incl. schematic parity), 0 unconnected, 0 footprint errors (`reports/*_kicad10.rpt`); re-run locally
- [x] Isolation rule (≥ 8 mm PRIMARY↔ISOLATED) enforced by a custom DRC rule with a negative control (`reports/Isolation_check.txt`)
- [x] Schematic ↔ PCB net/pad check, polarity (TVS1 K→+12V_F, D1 K→PI_GND, C2/C4 + pad 1), pin-1 / connector numbering (`reports/ERC_equivalent_connectivity_report.txt`)
- [x] BOM with exact MPNs (no placeholders; DNP lines are explicit), CPL (KiCad 10 position export, Y from the bottom-left)
- [x] F1 0407008.WR, F2 0451008.MRL, U1 RSDW40F-05 from datasheets/drawings
- [ ] **Owner:** Gerber/drill export in KiCad 10, CAM preview, CPL rotation check at PCBWay (THT parts are hand/selective soldered)
- [ ] **Owner:** confirm PCBWay heavy-copper (2 oz) minimum trace/space and drill/annular limits
- [ ] **Owner:** PCBWay stock of RSDW40F-05, else **consigned**; Molex 43045 headers fit-check against the physical part (library footprints)
- [ ] **Owner:** orderable Samtec SSW-120-01 code (plating letter), Molex 43030 terminals and wire (harness, not on PCB)
- [ ] Remove `RC2 – NOT FOR FAB` silk at release
- [ ] First article: `First_article_checklist.md` (trim calibration, loaded voltage, temperatures, Pi + display)

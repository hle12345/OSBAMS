# PCBWay readiness checklist — carrier RevB (no Gerbers yet)

Owner runs ERC/DRC and exports Gerbers/drill in KiCad 10 from the delivered project.
- [x] 2-layer, 85 × 67.5 mm (with plug tab), 1.6 mm, 2 oz Cu in the stackup, ENIG, 6 NPTH (4 × M3, 2 × M2.5), 3 fiducials, test points TP1–TP5
- [x] KiCad 10.0.6 ERC 0, DRC 0 incl. schematic parity, 0 unconnected, 0 footprint errors; isolation rule + negative control; 97 pin-map / polarity checks
- [x] BOM with exact MPNs (R3 select-on-test is explicit), CPL (KiCad 10 position export, Y from the bottom-left), assembly and mechanical drawings
- [ ] **Owner:** Gerber/drill export, CAM preview, CPL rotation check (the THT parts are hand/selective soldered; J2 is soldered from the top)
- [ ] **Owner:** PCBWay 2 oz minimum trace/space and drill/annular limits; plug-tab outline (inner corners) accepted; consign RSDW40F-05 if not stocked
- [ ] **Owner:** Molex 43045 library footprints vs the physical part; SSW hole 1.0 mm / pad 1.7 mm vs Samtec's recommended hole
- [ ] Remove `RC1 - NOT FOR FAB` silk at release; first article per `First_article_checklist.md`

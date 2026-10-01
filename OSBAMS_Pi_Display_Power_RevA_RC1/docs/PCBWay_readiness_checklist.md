# PCBWay readiness checklist — RC1 (not final)

- [x] 2-layer, 100 × 70 mm, 1.6 mm, 2 oz Cu in stackup, ENIG
- [x] Gerber (RS-274X) + Excellon drill + drill map + zip
- [x] BOM XLSX with exact MPNs; CPL CSV
- [x] 4 × M3 holes, 3 fiducials, silkscreen labels, test points TP1–TP5
- [x] Electrical DRC: 0 errors (silk warnings only)
- [x] Schematic ↔ PCB connectivity cross-check PASS (custom script)
- [ ] KiCad ERC run (needs KiCad 8+; not available in build env)
- [ ] RSDW40F-05 land pattern vs Mean Well drawing
- [ ] Molex 430450200/430450400 footprints incl. pegs vs Molex drawings; mating parts verified
- [ ] Fuse (Nano2), SMB, radial cap land patterns vs datasheets
- [ ] Heavy-copper (2 oz) minimum trace/space and drill/annular limits confirmed with PCBWay
- [ ] PCBWay confirms stock of RSDW40F-05, else mark **consigned**
- [ ] THT assembly strategy (hand/selective) agreed; remove `RC1 - NOT FOR FAB` silk
- [ ] Bench: Pi-pin voltage at load, combined Pi + Waveshare current

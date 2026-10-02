# PCBWay readiness checklist — RC1.1 (not final; RC2 withheld)

- [x] 2-layer, 100 × 70 mm, 1.6 mm, 2 oz Cu in stackup, ENIG
- [x] Gerber (RS-274X) + Excellon drill + drill map + zip
- [x] BOM XLSX with exact MPNs; CPL CSV
- [x] 4 × M3 holes, 3 fiducials, silkscreen labels, test points TP1–TP5
- [x] Electrical DRC: 0 errors (silk warnings only)
- [x] Schematic ↔ PCB connectivity cross-check PASS (custom script)
- [ ] KiCad ERC run (needs KiCad 8+; not available in build env)
- [x] RSDW40F-05 land pattern implemented from Mean Well drawing (double-check mirror/rotation in KiCad)
- [x] F1 = Littelfuse 407 8 A time-lag 0407008.WR (datasheet-verified); confirm stock
- [x] Molex 43045-0200/-0400 (with pegs), Nano2 451/453, SMB, radial caps, passives now from official KiCad libraries
- [ ] Cross-check those library footprints against manufacturer PDFs; Molex mating parts verified
- [ ] 5 V voltage-drop gate closed with datasheet values (Voltage_drop_budget.md)
- [ ] Heavy-copper (2 oz) minimum trace/space and drill/annular limits confirmed with PCBWay
- [ ] PCBWay confirms stock of RSDW40F-05, else mark **consigned**
- [ ] THT assembly strategy (hand/selective) agreed; remove `RC1.1 - NOT FOR FAB` silk
- [ ] Bench: Pi-pin voltage at load, combined Pi + Waveshare current

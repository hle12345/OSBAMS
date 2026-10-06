# RevC vs RevB RC1 (layout-only size optimisation)

| Item | RevB RC1 | RevC RC1 |
|---|---|---|
| Board | 85 × 67.5 mm, 59.5 mm body + 65 × 8 mm plug tab (notched outline) | **65 × 50 mm plain rectangle** (−43 % area, −23.5 % width) |
| Schematic, netlist, parts, BOM, fuses, connectors, J2 pin map | — | **identical** (RevC changes placement and copper only) |
| RSDW40F-05 | long axis along y | long axis along x: secondary pins left (near Pi pins 2,4 / 6,9,14,20), primary pins right |
| J_IN / J_DISP | both facing the right edge | J_IN top right, facing the top edge; J_DISP bottom left, facing the left edge |
| Isolation | 10 mm rule, 13.5 mm lane (horizontal band) | 10 mm rule, 11 mm lane (vertical band) |
| Key / support posts | K1 (4,13) K2 (57.5,37) S3 S4 on the 85 mm body | K1 (61.5,21) K2 (18.5,38.3) S3 (38,36) S4 (61.5,38.5); both keys verified to land on bare Pi PCB when reversed (same check as RevB) |
| Worst-case Pi-pin voltage, 5 A + 1.0 A display | 4.962 V | 4.955 V (−7 mV: longer 5V_ISO_RAW run, wider PI_GND pour; copper squares estimated from the layout) |
| No-load maximum | 5.234 V | 5.234 V (unchanged: depends on the module, not the copper) |
| Silkscreen | front text | front: lane marker + release text; back: name / function / side labels (fewer front text, cleaner top) |
| ERC / DRC / parity / isolation / pin-map / mechanical | pass | pass (see `reports/`) |

RevB RC1 is unchanged and remains available; neither revision is a fabrication authorization.

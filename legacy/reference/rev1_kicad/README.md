# Rev.1 KiCad source — REFERENCE ONLY

Moved here on 2026-10-01. The Rev.1 80x80 mm carrier PCB is a proven-prototype reference (circuits and interfaces that worked), **not** a design to revise or manufacture. It carries a known diode-polarity defect (symbol pin 1 = anode vs footprint pad 1 = cathode on D1-D3) and no PA0/PA1/PC9 circuits.
The Rev.2 controller is a new design in `Hardware/Rev2_Controller/`.
`root_duplicate_project/` holds the second, smaller `.kicad_pro/.kicad_prl` that used to sit in the repo root.
`tools/mfg` still reads these files only for the regression tests that reproduce the Rev.1 defect.

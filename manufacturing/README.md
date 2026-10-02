# manufacturing/

**No fabrication or assembly package exists. This is intentional.**

The earlier PCBWay "candidate" package (commit `d400e2d`) was removed: it described the unrevised board, which has a critical diode-polarity defect and
a scope gap, and it was generated without KiCad. Final Gerber/BOM/CPL/PDF files may be generated **only** when every gate in
`docs/rev2/pcb/RELEASE_GATES.json` is true (blockers closed, HIGH items closed or dispositioned, ERC clean, DRC clean, BOM with manufacturer + exact MPN
for every populated part, Rev.1 physical observations recorded). `tools/mfg/build_package.py` refuses to run otherwise and
`tests/test_pcb_release_gates.py` fails if fabrication files appear while a gate is open.

See `docs/rev2/pcb/README.md`.

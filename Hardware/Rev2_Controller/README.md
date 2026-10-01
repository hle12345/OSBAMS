# OSBAMS Rev.2 Controller (new integrated design)

Status: **design phase, rev B (merged)**. No KiCad files yet; the schematic starts only after the critical datasheet inputs are verified.
- `REV2_CONTROLLER_ARCHITECTURE.md` — authoritative architecture (supersedes both earlier drafts)
- `REV2_CALCULATIONS.md` — generated: `python3 Hardware/Rev2_Controller/calc/rev2_calcs.py` (inputs: `calc/datasheet_inputs.json`)
- `REV2_PRELIM_BOM.csv`, `REV2_BLOCK_DIAGRAM.png/.svg` (`calc/make_block_diagram.py`)
- `DATASHEET_VERIFICATION.md` — what to read in which manufacturer document (currently 0 of 30 verified)
- `reference/` — the two superseded drafts, unchanged
Order: verify → schematic → ERC → review → layout → DRC → assembly review → PCBWay (gated by `docs/rev2/pcb/RELEASE_GATES.json`). Rev.1 KiCad: `legacy/reference/rev1_kicad/` (reference only).

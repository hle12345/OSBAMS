# OSBAMS Rev.2 Controller (new integrated design)

Status: **RELEASE CANDIDATE 1.2 — design package for REVIEW. NOT final, NOT released for fabrication.**
- `OSBAMS_Rev2_RELEASE_CANDIDATE_1/` — KiCad 10 project (schematic, 4-layer PCB, TC74 probe board), BOM/CPL (no Gerbers: export them from the final PCB in KiCad 10), PDFs, ERC/DRC reports, evidence register, supply-chain/DFM/assembly/fab notes, `PCBWAY_RELEASE_CANDIDATE_REPORT.md` (READY FOR REVIEW / BLOCKERS BEFORE PCBWAY ORDER).
- `REV2_CONTROLLER_ARCHITECTURE.md` — architecture (rev D, matches RC1)
- `REV2_CALCULATIONS.md` — generated: `python3 Hardware/Rev2_Controller/calc/rev2_calcs.py` (inputs: `calc/datasheet_inputs.json`, evidence states VERIFIED_LOCAL / USER_RELAYED_MANUFACTURER / UNVERIFIED)
- `REV2_BLOCK_DIAGRAM.png/.svg` (`calc/make_block_diagram.py`), `DATASHEET_VERIFICATION.md` (evidence register)
- `design/` + `build_rc1.py` + `finalize_rc1.py` — generator pipeline (single source of truth `design/rev2_design.py`); `BUILD_ENVIRONMENT.md` explains the KiCad 10 container (`tools/kc10`).
- `reference/` — superseded drafts. Rev.1 KiCad: `legacy/reference/rev1_kicad/` (reference only).
Order: RC1 review → clear every blocker in the RC1 report (manufacturer PDFs, EB21A drawing, local ERC/DRC and Gerber regeneration, stock/lifecycle) → gates in `docs/rev2/pcb/RELEASE_GATES.json` → PCBWay.

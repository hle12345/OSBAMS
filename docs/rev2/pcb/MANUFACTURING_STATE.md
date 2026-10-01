# Manufacturing state — resolved

**Current state: NO fabrication package exists.** No Gerber, drill, BOM, CPL or assembly output is in the repository.

| Source | Date | Claim | Verdict |
|---|---|---|---|
| `PCBWAY_READINESS_GAPS.md` (audit) | 2026-09-30 | No final Gerbers/BOM/CPL were generated | Correct when written |
| Candidate package `manufacturing/PCBWay_OSBAMS_Rev2_PCBA/` (script-generated, not KiCad export) | 2026-10-01 | A package exists | **Stale — removed.** It was built from the Rev.1 board, which carries the diode-polarity defect (G-01), so it would have fabricated a board that cannot work. |

Actions taken
- Whole candidate package removed (Gerbers, drill, BOM xlsx, CPL, PDFs, previews).
- Its two review documents are kept only as `REV1_BOARD_*_SNAPSHOT.md` (banner: historical).
- `RELEASE_GATES.json` holds six gates, all `false`. `python3 -m tools.mfg.build_package` refuses to run (exit non-zero, lists open gates) unless `--candidate` is passed.
- `tests/test_pcb_release_gates.py` fails if any fabrication file appears under `manufacturing/` while a gate is open.

Gates (set true only with evidence filed in this directory)
1. all BLOCKER items closed (G-01, G-02, G-05 …, see audit)
2. HIGH items closed or explicitly dispositioned
3. ERC clean (KiCad 10 run, report filed)
4. DRC clean (KiCad 10 run, report filed)
5. BOM: manufacturer + exact MPN on every populated part
6. Rev.1 physical observations recorded (bench sheet V1–V10 filed, truth inventory updated)

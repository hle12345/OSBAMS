# OSBAMS Rev.2 controller PCB — PCBWay production readiness checklist

> **SNAPSHOT — historical.** This production checklist describes the KiCad board exactly as committed in `d400e2d` (before any revision). The PCBWay package it referred to was **removed** (see `MANUFACTURING_STATE.md`); paths below that point into `manufacturing/` no longer exist. Numbers marked 'script estimate' were never KiCad DRC/ERC results. Findings R1/U1 (diode polarity) etc. remain the open work items.


Generated 2026-10-01. **Overall: NOT PRODUCTION-READY** — see the failed items and the issue list at the end.

| # | Item | Status | Evidence / note |
|---|---|---|---|
| 1 | A KiCad PCB layout exists | ✅ PASS | Hardware/Schematic/OSBAMS PCB.kicad_pcb: 20 footprints, 93 tracks, 1 GND zone, 80×80 mm outline |
| 2 | Gerbers generated | ✅ PASS | script-generated CANDIDATES (copper, mask, silk, paste, edge, drill) — **not** exported by KiCad |
| 3 | Gerbers exported by KiCad / checked by KiCad | ❌ FAIL | KiCad 10 unavailable; run tools/mfg/export_with_kicad_cli.sh |
| 4 | Layer set complete, no stray mechanical layers | ✅ PASS | 9 graphic layers + 2 drill files; nothing on mechanical/user layers |
| 5 | Board dimensions correct | ✅ PASS | 80 × 80 mm read back from the Gerbers |
| 6 | Drill files complete | ✅ PASS | 44 PTH + 5 NPTH |
| 7 | BOM file complete (all required columns filled, specific descriptions; unknown values flagged) | ✅ PASS | 14 lines, specific descriptions/packages; unknown fields marked NOT SPECIFIED rather than invented |
| 8 | All parts have a manufacturer part number | ❌ FAIL | missing MPN: C2, C3, R1, R2, J1, J2, J3, J4, J5, J6 |
| 9 | No TBD / unspecified components | ❌ FAIL | same rows; also D1/D2 manufacturer unnamed |
| 10 | CPL complete for every SMT part | ✅ PASS | SMT parts: ['D1']; rows: 1; duplicates: False; missing rotation: none |
| 11 | CPL polarity of D1 verified | ❌ FAIL | D1 polarity is an open issue (U1) |
| 12 | No missing footprints | ✅ PASS | schematic vs PCB refs/footprints: consistent |
| 13 | Schematic and PCB netlists agree | ✅ PASS | script comparison: 0 differences |
| 14 | Diode polarity consistent (schematic vs footprint) | ❌ FAIL | D1, D2, D3 mismatch — CRITICAL |
| 15 | DRC passed | ❌ FAIL | NOT RUN (script screening found no clearance < 0.2 mm, but this is not DRC) |
| 16 | ERC passed | ❌ FAIL | NOT RUN |
| 17 | Assembly drawing, schematic PDF, test-point map, assembly notes, functional test produced | ✅ PASS | script-generated; see Documentation/Assembly/Testing |
| 18 | Assembly notes complete | ✅ PASS | OSBAMS_Rev2_Assembly_Notes.pdf (polarity items marked HOLD) |
| 19 | Controller functions present on the PCB (STM32, INA228, ADC, E-stop sense, USB/Pi, 5 V) | ❌ FAIL | external modules / absent — scope gap (U2) |
| 20 | Test points present | ❌ FAIL | none on the PCB |
| 21 | Component availability confirmed | ❌ FAIL | not checked (no network) |
| 22 | Surface finish / mask colour / order options defined | ❌ FAIL | stackup copper_finish = None |

## Unresolved issues preventing production

| ID | Severity | Issue | Required action |
|---|---|---|---|
| U1 | CRITICAL | Diode polarity mismatch: D1 (TVS), D2 (flyback), D3 (reverse-polarity) | In KiCad: fix the symbol pin numbering (1 = K) or swap the footprints/nets, update the PCB from the schematic, re-run DRC/ERC, regenerate everything. Not changed here (task: do not modify the design). |
| U2 | CRITICAL (scope) | The PCB does not contain most of the requested 'controller PCB' functions | Decide: (a) order this simple carrier board as it is, or (b) complete the Rev.2 controller design (STM32/INA228 on board or full interface header, ADC divider, E-stop/feedback sensing, 12->5 V, test points) before any turnkey order. |
| U3 | HIGH | No authoritative KiCad export; DRC and ERC not run | Run tools/mfg/export_with_kicad_cli.sh on a machine with KiCad 10; fix every DRC/ERC error; replace the candidate files. |
| U4 | HIGH | BOM is incomplete | Choose and approve MPNs for the red rows of the BOM; do not let the fab pick safety/measurement parts. |
| U5 | MEDIUM | Silkscreen lacks connector names, polarity legends, revision, test points, fiducials | Add before release if desired (design change). |
| U6 | MEDIUM | Net-class track width not applied to power nets | Confirm the coil current from the relay datasheet; widen the tracks or fix the net-class patterns. |
| U7 | MEDIUM | U1 (TC74 TO-220-5) annular ring 0.087 mm; finish unspecified | Ask PCBWay DFM; enlarge pads if rejected; choose the surface finish in the order. |
| U8 | MEDIUM | Assembly mix: one SMT part, many through-hole parts | Decide: SMT-only turnkey (D1) + customer THT, or full THT turnkey. |
| U9 | LOW | Part-level questions | Confirm and record decisions. |
| U10 | LOW | Availability and obsolescence not checked; stale repo documents | Check stock at order time; archive/refresh the old spreadsheets. |

**Do not claim this board production-ready until every FAIL above is closed and the files are re-exported from KiCad.**

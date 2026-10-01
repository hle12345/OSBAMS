# PCBWay_OSBAMS_Rev2_PCBA — package index

**STATUS: NOT PRODUCTION-READY. Do not upload yet.** All fabrication files are script-generated *candidates* (KiCad 10 was unavailable). See `Documentation/OSBAMS_Rev2_PCBWAY_CHECKLIST.md`.

| Folder | Contents |
|---|---|
| `Gerber/` | copper (F/B), mask, silkscreen, paste, edge cuts + `OSBAMS_Rev2_Gerber.zip` (Gerber + drill + candidate notice) |
| `Drill/` | Excellon PTH / NPTH + drill report |
| `BOM/` | `OSBAMS_Rev2_BOM.xlsx` (BOM, External_not_assembled, Legend) |
| `PickAndPlace/` | `OSBAMS_Rev2_CPL.csv` (SMT only: D1) + all-parts reference CSV |
| `Assembly/` | `OSBAMS_Rev2_Assembly_Drawing.pdf`, `OSBAMS_Rev2_Assembly_Notes.pdf` |
| `Documentation/` | schematic PDF, PCB review, test-point map, checklist, previews, `export_with_kicad_cli.sh` |
| `Testing/` | `OSBAMS_Rev2_Functional_Test.pdf` |

Regenerate everything: `python3 -m tools.mfg.build_package` (repo root).

## What the board is
A through-hole carrier (80 × 80 mm, 2 layers): 12 V in, D3/D1/C1 protection, E-stop loop J3, MOSFET relay-coil driver Q1/D2/J2, TC74 sensor U1, headers for an external INA228 breakout (J4), NUCLEO-L476RG (J5) and UART (J6). The STM32/INA228 are modules, not on the PCB; battery fuse, XT60 power connector, disconnect, relay contacts and shunt wiring are external.

## Unresolved issues

- **U1 (CRITICAL): Diode polarity mismatch: D1 (TVS), D2 (flyback), D3 (reverse-polarity)** — In KiCad: fix the symbol pin numbering (1 = K) or swap the footprints/nets, update the PCB from the schematic, re-run DRC/ERC, regenerate everything. Not changed here (task: do not modify the design).
- **U2 (CRITICAL (scope)): The PCB does not contain most of the requested 'controller PCB' functions** — Decide: (a) order this simple carrier board as it is, or (b) complete the Rev.2 controller design (STM32/INA228 on board or full interface header, ADC divider, E-stop/feedback sensing, 12->5 V, test points) before any turnkey order.
- **U3 (HIGH): No authoritative KiCad export; DRC and ERC not run** — Run tools/mfg/export_with_kicad_cli.sh on a machine with KiCad 10; fix every DRC/ERC error; replace the candidate files.
- **U4 (HIGH): BOM is incomplete** — Choose and approve MPNs for the red rows of the BOM; do not let the fab pick safety/measurement parts.
- **U5 (MEDIUM): Silkscreen lacks connector names, polarity legends, revision, test points, fiducials** — Add before release if desired (design change).
- **U6 (MEDIUM): Net-class track width not applied to power nets** — Confirm the coil current from the relay datasheet; widen the tracks or fix the net-class patterns.
- **U7 (MEDIUM): U1 (TC74 TO-220-5) annular ring 0.087 mm; finish unspecified** — Ask PCBWay DFM; enlarge pads if rejected; choose the surface finish in the order.
- **U8 (MEDIUM): Assembly mix: one SMT part, many through-hole parts** — Decide: SMT-only turnkey (D1) + customer THT, or full THT turnkey.
- **U9 (LOW): Part-level questions** — Confirm and record decisions.
- **U10 (LOW): Availability and obsolescence not checked; stale repo documents** — Check stock at order time; archive/refresh the old spreadsheets.

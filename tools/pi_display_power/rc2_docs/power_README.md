# OSBAMS_Pi_Display_Power_RevA — {REL}

**Status: review/release candidate for the owner's local KiCad 10 ERC/DRC and Gerber export. No Gerbers are included and this is not a fabrication authorization.** Read `docs/Current_State_Summary.md` first.

PCB #2 of OSBAMS: isolated 5 V / 8 A supply for a Raspberry Pi 5 and a Waveshare 10.1" DSI display.
`120 VAC → XDR-75-12 → 12 V bus → (this board) F1 → RSDW40F-05 → F2 → isolated 5 V → J_OUT (Pi, via keyed interposer) + J_DISP (display)`.
No STM32, ADC, INA228, relay or safety logic here. `PI_GND` is **not** connected to `12V_GND` (only inside U1).

## Gates
| Gate | State |
|---|---|
| KiCad 10 ERC / DRC / parity / unconnected / footprint errors | **0 / 0 / 0 / 0** on this board and the interposer (KiCad 10.0.6, `reports/*_kicad10.rpt`). Owner re-runs locally. |
| Isolation (≥ 8 mm PRIMARY↔ISOLATED rule, negative control; single boundary in U1) | **PASS** — `reports/Isolation_check.txt`, `docs/Isolation_review.md` |
| Exact parts, no placeholder MPN in the BOM | **DONE** — `docs/Parts_and_sources.md`; owner items listed there (harness terminals, Samtec code, Waveshare data) |
| 5 V budget with the real parts | **DONE** — `docs/Power_budget_report.md` (typical 4.98 V at 5 A + 1 A; absolute worst path 4.836 V, floor 4.75 V; per-unit calibration) |
| Display feed decision | **J_DISP direct feed** — `docs/Waveshare_integration.md` |
| Interposer mechanical/keying | **PASS** (plan view + heights) — interposer `docs/Mechanical_verification.md`; physical reversed-fit test at first article |
| First article | **OPEN (by design)** — `docs/First_article_checklist.md` |
| Gerbers / CPL orientation at PCBWay | **OWNER** — export from KiCad 10 |

## Contents
| Path | What |
|---|---|
| `kicad/` | KiCad 10 project (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`), project libraries `OSBAMS_PiPwr.kicad_sym` / `OSBAMS_PiPwr.pretty`, `fp-lib-table`, `sym-lib-table`, `.kicad_dru` (isolation rule) |
| `bom/`, `cpl/` | BOM XLSX (incl. off-board harness lines), pick-and-place CSV (Y from the bottom-left) |
| `docs/` | current-state summary, parts/sources, power budget, Waveshare integration, isolation review, first-article checklist, trim calibration, assembly drawings (top/bottom), harness drawing, wiring diagram, assembly notes, PCBWay checklist, Pi configuration note |
| `reports/` | KiCad 10 ERC/DRC reports, connectivity/polarity check, isolation check |

Board: 100 × 70 mm, 2-layer, 1.6 mm, 2 oz Cu, ENIG, 4 × M3 NPTH, 3 fiducials. Y capacitor: not fitted (decision).
Regenerate: `REL=RC2 python3 tools/pi_display_power/build_k10.py <out_root>` (needs the KiCad 10 container wrapper `kc10_pi`).
Interposer: `../OSBAMS_Pi_Power_Interposer_RevA_RC2/`.

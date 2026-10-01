# OSBAMS_Pi_Display_Power_RevA — RC1

**Status: RELEASE CANDIDATE 1 — NOT FINAL, NOT AUTHORIZED FOR FABRICATION.**

PCB #2 of OSBAMS: isolated 5 V / 8 A supply for Raspberry Pi 5 + Waveshare 10.1" DSI display.
`120 VAC → XDR-75-12 → 12 V bus → (this board) → RSDW40F-05 → isolated 5 V → Pi 5 + display`.
No STM32, ADC, INA228, relay or safety logic on this board. `PI_GND` is **not** connected to `12V_GND`.

## Release gates (all must be closed before a FINAL tag)

| # | Gate | State |
|---|------|-------|
| 1 | RSDW40F-05 footprint verified against Mean Well mechanical drawing | **OPEN** — placeholder geometry (50.8×25.4 mm body, 6 pins on 5.08 mm pitch at the module ends). Mean Well site was unreachable from the build environment. |
| 2 | Molex mating parts verified (43025 housings, 43030 terminals, wire gauge) | **OPEN** — candidates only; Micro-Fit footprints have no positioning pegs yet and pin geometry is unverified |
| 3 | KiCad ERC passes | **OPEN** — `kicad-cli` 7.0.11 has no ERC. Only a custom connectivity check ran (`reports/ERC_equivalent_connectivity_report.txt`, PASS). Run real ERC in KiCad 8+. |
| 4 | KiCad DRC passes | **PARTIAL** — 0 electrical errors; only silkscreen + "library not configured" warnings (see `reports/DRC_report.rpt`). Re-run in your KiCad version after footprints are verified. |
| 5 | Isolation spacing checked | **PARTIAL** — 10 mm copper-free lane, no crossing (`docs/Isolation_review.md`); module-specific spacing not verified |
| 6 | Pi 5 voltage under load bench-verified | **OPEN** — estimate only (`docs/Isolation_review.md` §Voltage budget): margin is thin at ≥5 A |
| 7 | Waveshare + Pi combined current measured | **OPEN** |
| 8 | PCBWay sourcing of RSDW40F-05 | **OPEN** — if unavailable, mark **consigned / customer-supplied**; no substitution |

## Contents
| Path | What |
|---|---|
| `kicad/` | KiCad project, schematic, PCB (KiCad 7 format; opens in 7/8/9/10) |
| `gerbers/`, `drill/` | Gerbers (RS-274X, protel extensions), Excellon drill + map, zip |
| `bom/` | BOM XLSX (incl. mating harness parts, verification status per line) |
| `cpl/` | Pick-and-place CSV (Y measured from bottom-left, +Y up, rotation 0 = footprint as drawn) |
| `docs/` | Assembly drawing (top/bottom PDF+PNG), assembly notes, harness drawing, Pi power wiring diagram, Pi config note, isolation review, PCBWay checklist, proposals |
| `reports/` | DRC report, ERC-equivalent report, ERC status |
| `generator/` | `run_drc.py`; the full generators live in `tools/pi_display_power/` in this repo |

Board: 100 × 70 mm, 2-layer, 1.6 mm, 2 oz Cu (stackup in PCB file), ENIG, 4× M3, 3 fiducials.
Regenerate: `tools/pi_display_power/build_all.sh`.

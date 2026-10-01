# OSBAMS_Pi_Display_Power_RevA — RC1.1 (rework of RC1)

**Status: NOT FINAL, NOT AUTHORIZED FOR FABRICATION. `..._RC2` has deliberately NOT been generated** — it is gated on the items below (the Mean Well RSDW40F-05 footprint cannot be verified from the build environment, and the 5 V worst-case voltage margin is unproven).

RC1.1 changes vs RC1: (a) every footprint except U1 now comes from the official KiCad libraries (fixes a real error: Micro-Fit dual-row pin numbering runs along rows, so +5 V = outer row, GND = inner row; Nano2 fuse is ~6 mm, not 12 mm); (b) 5 V distribution re-laid and budgeted (`docs/Voltage_drop_budget.md`); (c) harness changed to 16 AWG ≤150 mm; (d) DNP trim-network pads R2/R3 added.

PCB #2 of OSBAMS: isolated 5 V / 8 A supply for Raspberry Pi 5 + Waveshare 10.1" DSI display.
`120 VAC → XDR-75-12 → 12 V bus → (this board) → RSDW40F-05 → isolated 5 V → Pi 5 + display`.
No STM32, ADC, INA228, relay or safety logic on this board. `PI_GND` is **not** connected to `12V_GND`.

## Release gates (all must be closed before RC2 / FINAL)

| # | Gate | State |
|---|------|-------|
| 1 | **5 V voltage-drop budget** ≥ 4.85 V at Pi header @ 5 A worst case, ≤ 5.25 V no-load | **CLOSED on paper** (inputs owner-cited): ±1 % RSDW, F2 7.7 mΩ, Micro-Fit 10 mΩ, Harwin M20 20 mΩ ×2/rail → untrimmed worst 4.72 V; **trim to 5.14 V (Rt = 105 kΩ)** gives 4.86 V worst, 5.19 V no-load max. Hot-fuse case 4.84 V. Needs bench confirmation. |
| 2 | RSDW40F-05 footprint | **OPEN** — body 50.8×25.4 mm, pin Ø≈1.0 mm and pinout recorded (owner-cited) but pin X/Y/drill/keepout not supplied; still placeholder. Drawing site unreachable from here. |
| 3 | Other footprints (Molex 43045-0400/-0200, Nano2 0451, SMB, radial caps, passives) | **LIBRARY-SOURCED, not manufacturer-PDF-verified** — official KiCad library, which cites the Molex/Littelfuse datasheets, incl. Micro-Fit pegs/drills. Cross-check against the Molex drawing before release. |
| 4 | Mating parts / Pi end | Molex 43025/43030 candidates; Pi end = Harwin M20 (owner-cited). **Pi-end pin map + anti-reversal keying OPEN** — an unkeyed reversed housing swaps +5 V and GND (`docs/Pi_end_connector_requirements.md`). |
| 5 | KiCad ERC passes | **OPEN** — build container only has KiCad 7.0.11 (no `sch erc`; KiCad 10 not obtainable here). Custom connectivity check passes (`reports/ERC_equivalent_connectivity_report.txt`). Run ERC in KiCad 10 locally, then regenerate. |
| 6 | KiCad DRC passes | **PARTIAL** — 0 electrical/courtyard/clearance errors; only silkscreen-overlap and "library not configured" warnings. Re-run in KiCad 10. |
| 7 | Isolation spacing checked | **PARTIAL** — 10 mm copper-free lane, no crossing; module-specific spacing not verified |
| 8 | Bench: Pi voltage under load; Waveshare + Pi current; harness temp rise | **OPEN** |
| 9 | PCBWay sourcing of RSDW40F-05 | **OPEN** — else **consigned / customer-supplied** |

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

Y capacitor: not fitted (decision: keep isolation clean unless EMC testing gives a reason).
Board: 100 × 70 mm, 2-layer, 1.6 mm, 2 oz Cu (stackup in PCB file), ENIG, 4× M3, 3 fiducials.
Regenerate: `tools/pi_display_power/build_all.sh`.

## RC2 gate
`python3 tools/pi_display_power/rc2_gate.py` lists exactly which datasheet inputs (F2 resistance, RSDW tolerance/trim/formula, RSDW drawing, Pi-end terminal, KiCad 10 ERC) are still unverified. RC2 is generated only when it reports CLEAR. R2/R3 stay DNP; **R3 (TRIM→PI_GND) is the trim-up resistor**, R2 (TRIM→+VOUT) is trim-down and likely unneeded. Candidate Rt values are in `Voltage_drop_budget.md` under an assumed topology — confirm against the Mean Well formula first.

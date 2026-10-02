# OSBAMS_Pi_Power_Carrier_RevB — {REL}

**FROZEN as the current combined Pi/display power release candidate: no schematic/PCB change unless local KiCad verification or first-article testing finds a real defect. Modeled quantities are listed in `docs/BENCH_REQUIRED.md` (not verified).** RC2 + interposer are superseded, reference-only designs (kept, not deleted).

**Status: new-revision review candidate (not a patch of RC2) for the owner's local KiCad 10 ERC/DRC and Gerber export. No Gerbers are included; not a fabrication authorization.** The previous reference design (`OSBAMS_Pi_Display_Power_RevA_RC2` + `OSBAMS_Pi_Power_Interposer_RevA_RC2`) is unchanged.

One board replaces the separate Pi/display power PCB, the Pi interposer and the Micro-Fit harness between them:
`120 VAC → XDR-75-12 → 12 V → J_IN → F1 0407008.WR → TVS1 SMBJ15A → RSDW40F-05 (isolated) → F2 0451008.MRL → 5V_PI → Pi header pins 2,4 (+5 V) / 6,9,14,20 (GND)` and `5V_PI → J_DISP → Waveshare 10.1-DSI-TOUCH-A`.
`PI_GND` is isolated from `12V_GND`; the only link is inside U1.

## Mechanical concept
85 × 67.5 mm, 2 layers, 1.6 mm, 2 oz Cu. The 85 × 59.5 mm **main body lies entirely outside the Pi 5 outline** (beside/above the Pi's header edge), carrying the module, fuses, TVS, capacitors and connectors; a **plug tab** (Pi x 0…65, y −0.5…7.5 mm, the RC2 interposer footprint) carries the Samtec SSW-120-01-L-D socket and the header-end spacer holes M1/M2. The carrier is **not above the CPU / Active Cooler**. Four M3 NPTH holes take **M3 × 20 mm enclosure standoffs**: they carry the carrier's weight (the socket carries none) and K1/K2 double as the **180° key posts** (reversed, they land on bare Pi PCB and stop the socket 2.5 mm short of the pins). `Mechanical_placement_drawing.pdf`, `reports/Mechanical_fit_check.txt`.

## Gates
| Gate | State |
|---|---|
| KiCad 10.0.6 ERC / DRC incl. schematic-parity / unconnected / footprint errors | **0 / 0 / 0 / 0** (`reports/*_kicad10.rpt`); owner re-runs locally |
| Isolation: ≥ 10 mm PRIMARY↔ISOLATED custom rule, negative control, 13.5 mm copper-free lane, no copper crossing, NPTH holes, no shield | **PASS** (`reports/Isolation_check.txt`, `docs/Isolation_report.md`) |
| Pin map: power only on Pi pins 2, 4 (+5 V) and 6, 9, 14, 20 (GND); 34 pins no-connect; polarity; module pins vs the Mean Well drawing | **PASS** — 97 checks (`reports/Connectivity_pinmap_check.txt`) |
| Mechanical fit (plan view vs Pi 5 drawing, key, heights) | **PASS on paper**; physical fit at first article (no STEP models available) |
| Voltage budget recomputed from scratch | worst case **4.962 V** at the Pi pins with 5 A + 1.0 A display (RC2: 4.829 V) — `docs/Voltage_drop_report.md` |
| Bench-required quantities (SSW contact resistance, module joint resistance, real Waveshare current, mechanical fit, reversed-fit key test, no-load maximum 5.234 V) | **BENCH_REQUIRED** — `docs/BENCH_REQUIRED.md` |
| First article | **OPEN (by design)** — `docs/First_article_checklist.md` |
| Gerbers / PCBWay CAM / CPL orientation | **OWNER** |

## Contents
`kicad/` project (`.kicad_pro/.kicad_sch/.kicad_pcb`), libraries `OSBAMS_PiPwr.kicad_sym` + `OSBAMS_PiPwr.pretty`, `fp-lib-table`, `sym-lib-table`, `.kicad_dru` (isolation rule) · `bom/` (incl. mechanical hardware and off-board harness lines) · `cpl/` · `docs/` (this README's references, assembly drawings top/bottom, mechanical placement drawing, voltage-drop report, isolation report, first-article checklist, parts and sources, changes vs RC2, trim calibration, assembly notes) · `reports/`.
Regenerate: `REL=RC1 python3 tools/pi_display_power/build_carrier_k10.py <out_root>` (needs the `kc10_pi` KiCad 10 container wrapper).

## Open items (none changes the PCB geometry unless noted)
First-article measurements (trim calibration, contact resistances, loaded voltage at the Pi pins and J_DISP, temperatures, Pi + display, throttling, isolation resistance, reversed-fit test); Waveshare maximum current (unpublished); 43030-0038 current rating with 18 AWG; SSW hole 1.0 mm / pad 1.7 mm vs Samtec's recommended hole; Molex 43045 library footprints vs the Molex drawing; manufacturer data that was relayed by the owner (Waveshare, Samtec, SMBJ15A row) is marked user-relayed.

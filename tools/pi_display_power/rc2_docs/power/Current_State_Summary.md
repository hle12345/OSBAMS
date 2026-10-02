# Pi / display power — current state (RC2)

Branch `claude/affectionate-fermi-qkgfwz`. This supersedes the RC1 / RC1.1 README gate table and older notes (`Voltage_drop_budget.md` is now a detail file; scenarios are in `Power_budget_report.md`). The controller PCB and its firmware are not touched.

## Architecture (unchanged)
120 VAC → Mean Well XDR-75-12 → 12 V bus → **this board** (F1 0407008.WR, TVS1, RSDW40F-05 isolated 12 V → 5 V / 8 A, F2 0451008.MRL) → isolated 5 V → **J_OUT → keyed interposer → Pi 5** and **J_DISP → Waveshare 10.1" DSI display**. `PI_GND` is isolated from `12V_GND`; the only link is inside U1 (1.6 kVDC).

## Changes since RC1.1
1. **Display feed `J_DISP` added** (Molex 430450200): the interposer covers the Pi header, so the display cannot be wired to Pi pins; the display current stays out of the harness/interposer/socket (`Waveshare_integration.md`).
2. **KiCad 10 clean:** both projects regenerated with KiCad 10.0.6 (official KiCad 10 library footprints, project libraries `OSBAMS_PiPwr`, schematic↔PCB parity, board-only footprints marked): ERC 0, DRC 0, 0 unconnected, 0 footprint errors on both.
3. Isolation rule (≥ 8 mm PRIMARY↔ISOLATED) enforced by a custom DRC rule with a negative control.
4. R2 (trim-down) has no part; R3 is a select-on-test trim-up resistor (kit 61.9k / 71.5k / 84.5k); no placeholder MPN in the BOM.
5. Power-budget report with element drops and scenarios (Pi only / Pi + display), including the setpoint window.
6. **Harness gauge corrected to 18 AWG** (Molex ATS-638280200: 43030-0038 is the 18 AWG terminal; no 16 AWG 43030 exists); budget, BOM, harness drawing and docs updated.
7. Tooling: `tools/pi_display_power/build_k10.py` (+ `kc10_pi`, `k10_*.py`, `kcompat.py`, `sexp.py`) rebuilds everything in the KiCad 10 container; no Gerbers are generated.

## Verified (from manufacturer documents in the project)
RSDW40F-05 pin drawing, trim formula, accuracy/line/load/temperature terms, ON/OFF, protections, isolation data; F1 and F2 (datasheets); Samtec SSW dimensions (catalog F-226); Raspberry Pi 5 mechanical drawing and HAT+ geometry (key/stack checks).
Also verified by checks: netlist = PCB pads, polarity, pin map (+5 V on Pi pins 2, 4; GND on 6, 9, 14, 20; 34 no-connects), isolation lane, hole/shield paths, ERC/DRC/parity.

## Provisional (documented, not independently verified)
Molex 43045 ratings (8.5 A, ≤ 10 mΩ per contact, owner-cited) and footprints (KiCad library); manufacturer data **relayed by the owner, not read locally**: Waveshare 10.1-DSI-TOUCH-A (4.75–5.30 V, 0.8 A typical, maximum unpublished), Samtec SSW-120-01-L-D, Littelfuse SMBJ15A row; 43030 24–20 / 30–26 AWG table rows; passive/LED/capacitor MPNs (no datasheets); interposer copper (2 mΩ/rail estimate); display current scenario 1.0 A.

## Requires bench validation (first article — `First_article_checklist.md`)
Per-unit trim calibration on the assembled system; **measured** socket and Micro-Fit contact resistances (budget uses 20 mΩ per socket contact as an acceptance limit); loaded voltage at the Pi pins (1/3/5 A, Pi + display); temperature of connectors/fuses/module/harness; ripple/transients; throttling/under-voltage; reversed-fit test of the key; isolation resistance; Pi + display simultaneous operation.

## Budget headline (`Power_budget_report.md`)
With the **18 AWG harness** (43030-0038): calibrated unit, 5 A Pi + 1 A display: typical ≈ **4.973 V** at the Pi pins; every resistance at its maximum with F2 hot and +15 °C: **4.829 V** — misses the preferred 4.85 V target by **21 mV** (16 AWG would have been 4.836 V, −14 mV), clears the **4.75 V design floor by 79 mV**. No-load worst case 5.234 V (< 5.25 V; display range 4.75–5.30 V also met: 5.01 V lowest, 5.234 V highest). The worst-path setpoint window is closed (−5 mV); the typical window is ≈ 96 mV wide: calibration per assembled system and loaded-voltage measurement are mandatory first-article acceptance steps.

## What blocks RC2
Nothing that changes the PCB or the interposer geometry. **Closed in this update:** Waveshare power data (4.75–5.30 V, 0.8 A typ; max unpublished), Molex harness (18 AWG + 43030-0038; **16 AWG was not valid**), Samtec MPN (SSW-120-01-L-D), SMBJ15A row. Remaining: owner's local KiCad 10 ERC/DRC + Gerber export, first-article measurements, 43030-0038 current rating with 18 AWG (temperature check), Waveshare maximum current (measure).

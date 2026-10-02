# Findings from the uploaded datasheets

Sources read in this session: Mean Well **RSDW40/RDDW40 spec (2022-05-24)** and Harwin **M20-1160042** datasheet (TraceParts export, 2025-11-18). Not supplied: Harwin M20-1070500 housing, the Harwin M20 series spec (the 20 mΩ figure), Littelfuse 0451005/0451008, Molex 43045.

## RSDW40F-05 — now verified
- **Drawing** (p.5, Bottom View, tol ±0.35 mm, pin Ø1±0.1 mm, height 10.5 mm): pins 4/5/6 are 2.54 mm from one end at 2.54 / 12.7 / 22.86 mm across the 25.4 mm width; pins 1/2/3 are 2.54 mm from the other end at 5.08 / 10.16 / 20.32 mm across (45.72 mm between rows). Implemented in `build_pcb.py` (mirrored for the PCB top view; 1.3 mm drill, 2.4 mm pad). **The pin pattern differs from the RC1.1 placeholder**; the layout was redone around it (module long axis along X, pins 1–3 at the primary end). This mirroring/rotation is the one step to double-check in KiCad against the drawing before release.
- **Trim formula** (p.4) matches what was used; the datasheet's own 5.5 V example (5.476 kΩ) is reproduced by the script. Trim-up resistor TRIM→−Vout (board pad **R3**); R2 (TRIM→+Vout) is trim-down.
- **Remote ON/OFF:** open circuit = ON, <1.2 V to −Vin = OFF. Pin 3 left open is correct.
- **Output tolerance is more than ±1 %:** accuracy ±1 % (at 24 V in, rated load, 25 °C) **plus** line ±0.2 %, load ±0.5 %, and 0.05 %/°C temperature coefficient (0–55 °C). See `Voltage_drop_budget.md`.
- **Ripple** 100 mVp-p (20 MHz, with 0.1 µF + 47 µF) — C4 680 µF + C5 10 µF + C6 100 nF on the output cover this; verify on the bench. Max capacitive load 20,000 µF (fine). No minimum load. UVLO 8 V, surge 50 V/100 ms. Efficiency 89 % typ, full-load input current 1.9 A at 24 V (≈ 3.8–4 A at 12 V). EN55032 Class A with no external parts.

## F1 and F2 — Littelfuse datasheets (uploaded)
- **Correction confirmed:** the 451/453 Nano2 family is **very fast-acting** (453 is only the silver-cap variant), so `0453008.MRL` is the wrong characteristic for Mean Well's "8 A delay time" recommendation and has been **removed**.
- **F1 = Littelfuse 407 series, `0407008.WR`** (1206 time-lag, 8 A; part-number system 0407 · 008. · W (3000 pcs) · R (reel)). Datasheet values: max voltage **24 V**, interrupting rating **60 A @ 24 VDC**, nominal resistance **9 mΩ** (0.097 V drop at 8 A → 12.1 mΩ hot), melting I²t **24.12 A²s**, 0.8 W at rated current, opening 100 % ≥ 4 h, 200 % 1–120 s, 300 % 0.1–3 s, 800 % 2–50 ms; run continuously ≤ 80 % of rating (6.4 A) plus temperature re-rating; mount with marking up. Land pattern: pads 1.0 × 1.8 mm, 1.5 mm gap, 3.5 mm span (implemented). At 3.9 A full-load input it dissipates ~0.19 W.
- **F2 = `0451008.MRL`** (very fast-acting, correct for the 5 V output): 8 A, 125 V, **7.7 mΩ** cold, I²t 20.23 A²s, pads 1.96 × 3.15 mm with 6.86 mm span — matches the library footprint, so F2's land pattern is now datasheet-verified.
- The bus is 12 V (≤ 14.4 V), well inside F1's 24 V rating; the SMBJ15A clamps ~24 V only during a surge.

## Raspberry Pi HAT+ specification (uploaded)
Power HAT+ boards must supply ≥ 3 A at **5.1 V** and "strongly" should supply 5 A at 5.1 V (supports a setpoint slightly above 5.0 V); the 5 V rail may be on while 3.3 V is off (STANDBY) — GPIO 5 V feeding is the intended path. Mechanical: 65 × 56.5 mm outline, mounting holes 3.5 mm from the edges on a 58 × 49 mm pattern, the 40-pin header centred between the end holes **on the hole-row axis** (so the header axis is 3.5 mm from the Pi edge); at least one hole aligned; use a stacking header + spacers; ≥ 15 mm (16 ideal) board-to-board over an Active Cooler; do not foul the PoE header or the camera/display/PCIe flex connectors.

## Harwin M20-1160042 contact (verified from the file)
Female crimp contact, selective gold + tin, brass, 22–30 AWG, mates 0.64 mm square pin (matches the Pi header), −40…+105 °C, **3 A rating listed as "signal"**. The file contains **no contact-resistance figure**; the 20 mΩ max remains owner-cited from the M20 series spec. The housing M20-1070500 datasheet was not supplied, so its position count/layout and polarisation are still unconfirmed.

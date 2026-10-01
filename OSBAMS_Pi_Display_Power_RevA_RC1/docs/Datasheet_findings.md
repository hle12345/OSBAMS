# Findings from the uploaded datasheets

Sources read in this session: Mean Well **RSDW40/RDDW40 spec (2022-05-24)** and Harwin **M20-1160042** datasheet (TraceParts export, 2025-11-18). Not supplied: Harwin M20-1070500 housing, the Harwin M20 series spec (the 20 mΩ figure), Littelfuse 0451005/0451008, Molex 43045.

## RSDW40F-05 — now verified
- **Drawing** (p.5, Bottom View, tol ±0.35 mm, pin Ø1±0.1 mm, height 10.5 mm): pins 4/5/6 are 2.54 mm from one end at 2.54 / 12.7 / 22.86 mm across the 25.4 mm width; pins 1/2/3 are 2.54 mm from the other end at 5.08 / 10.16 / 20.32 mm across (45.72 mm between rows). Implemented in `build_pcb.py` (mirrored for the PCB top view; 1.3 mm drill, 2.4 mm pad). **The pin pattern differs from the RC1.1 placeholder**; the layout was redone around it (module long axis along X, pins 1–3 at the primary end). This mirroring/rotation is the one step to double-check in KiCad against the drawing before release.
- **Trim formula** (p.4) matches what was used; the datasheet's own 5.5 V example (5.476 kΩ) is reproduced by the script. Trim-up resistor TRIM→−Vout (board pad **R3**); R2 (TRIM→+Vout) is trim-down.
- **Remote ON/OFF:** open circuit = ON, <1.2 V to −Vin = OFF. Pin 3 left open is correct.
- **Output tolerance is more than ±1 %:** accuracy ±1 % (at 24 V in, rated load, 25 °C) **plus** line ±0.2 %, load ±0.5 %, and 0.05 %/°C temperature coefficient (0–55 °C). See `Voltage_drop_budget.md`.
- **Ripple** 100 mVp-p (20 MHz, with 0.1 µF + 47 µF) — C4 680 µF + C5 10 µF + C6 100 nF on the output cover this; verify on the bench. Max capacitive load 20,000 µF (fine). No minimum load. UVLO 8 V, surge 50 V/100 ms. Efficiency 89 % typ, full-load input current 1.9 A at 24 V (≈ 3.8–4 A at 12 V). EN55032 Class A with no external parts.

## F1 — decision taken: time-delay 8 A
Mean Well's input protection note: *"Fuse recommended. 24Vin models: 8 A delay time type."* F1 is the locked **0451005 (5 A, fast-acting)**. At the 5 A design load the input current is only ≈2.5–3 A, but at the module's full 8 A load it is ≈4 A, i.e. ~80 % of a 5 A fast-acting fuse (fuse makers usually recommend ≤75 %), and a fast-acting fuse is more exposed to start-up/inrush than the recommended delay type. **Decision (owner): follow Mean Well — F1 becomes an 8 A time-delay Nano2.** Candidate `0453008.MRL` (Littelfuse Nano2 453 time-lag family, same footprint as the 451). The exact MPN, DC cold resistance, DC voltage rating, interrupt rating and I²t are **not verified** (datasheet unreachable) — please upload the datasheet to close it. Heating/drop estimate in `Voltage_drop_budget.md`.

## Harwin M20-1160042 contact (verified from the file)
Female crimp contact, selective gold + tin, brass, 22–30 AWG, mates 0.64 mm square pin (matches the Pi header), −40…+105 °C, **3 A rating listed as "signal"**. The file contains **no contact-resistance figure**; the 20 mΩ max remains owner-cited from the M20 series spec. The housing M20-1070500 datasheet was not supplied, so its position count/layout and polarisation are still unconfirmed.

# BENCH_REQUIRED — quantities that are modeled or estimated, not verified (carrier RevB RC1)

The design is frozen. Nothing below is claimed as verified until a first article measures it (`First_article_checklist.md`). Budget numbers (`Voltage_drop_report.md`) stay as modeled: path resistance 28.5 mΩ worst case; 5 A Pi + 1 A display typical 5.056 V, modeled worst case 4.962 V (+112 mV vs 4.85 V, +212 mV vs the 4.75 V floor); no-load maximum 5.234 V.

| # | Quantity | Modeled / assumed | Status | Measured by |
|---|---|---|---|---|
| 1 | SSW-120-01-L-D socket contact resistance (per contact, incl. the Pi header pin interface) | 20 mΩ max (conservative; Samtec publishes no initial value for this code); 12 mΩ typ | **BENCH_REQUIRED** — measure the actual voltage drop across the socket at high load | A6, B1 |
| 2 | Module (U1) solder-joint / PTH-barrel resistance, pins 4 and 5 | 0.5 mΩ each (estimate) | **BENCH_REQUIRED** | B1 (module pin → TP3) |
| 3 | Pi-side header pin + solder joint resistance | 1 mΩ/contact (estimate) | **BENCH_REQUIRED** | B1, D2 |
| 4 | Real Waveshare 10.1-DSI-TOUCH-A current | 0.8 A typical (manufacturer); maximum **unpublished**; 1.0 A is a design scenario, **not** a manufacturer maximum | **BENCH_REQUIRED** | B6, D5 |
| 5 | Mechanical Pi / Active Cooler / USB-Ethernet (5.8 mm) / small connector (0.2 mm) / DSI ribbon / enclosure fit | paper plan-view analysis only; no STEP models | **BENCH_REQUIRED** — physical fit test | D1 |
| 6 | Reversed-fit key-post test (K1/K2, M3 × 20 mm, Pi standoffs 7.4 mm) | +2.5 mm margin on paper | **BENCH_REQUIRED** — attempt a reversed fit on a spare Pi board, power off | D1 |
| 7 | No-load maximum | 5.234 V (16 mV below the 5.25 V ceiling) | **BENCH_REQUIRED** — measure cold and warm after trim | C4 |
| 8 | Temperatures (SSW pins, J_DISP, F1, F2, U1, TVS1) | < 0.4 W per element; module ~3.5 W | **BENCH_REQUIRED** | B2, D4, D5 |
| 9 | 43030-0038 current rating with 18 AWG; Molex 43045 footprint vs the physical part; SSW hole 1.0 mm vs Samtec's recommended hole | not in the supplied documents | **BENCH_REQUIRED** (fit / temperature check) | A5b, B2 |
| 10 | Isolation resistance 12V_GND ↔ PI_GND | module spec 1000 MΩ @ 500 VDC | **BENCH_REQUIRED** (≥ 100 MΩ) | A5 |

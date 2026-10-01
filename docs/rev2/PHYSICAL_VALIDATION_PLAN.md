# Rev.2 physical validation plan

The ordered, step-by-step list is **`BENCH_CHECKLIST.md`** (generated from
`desktop/equipment/validation.py`; track results with `ValidationLog`).
Remote-control verification is tracked in **`6060B_COMMAND_EVIDENCE.md`**.

| Instrument | Role in validation |
|---|---|
| EDU36311A | low-energy commissioning source (never pretends to be a 42 V battery) |
| EDU34450A | reference DMM — every OSBAMS/6060B number is compared with it |
| EDUX1052G | transient / shutdown observation (contactor, E-stop, current steps) |
| Analog Discovery 2 | low-voltage digital/protocol debugging (I2C, UART) |
| 6060B | the actual battery load, **manual** until a GPIB path is confirmed and commands are VERIFIED |
| handheld DMM | polarity, continuity, rails |

Phases: A records → B low-energy commissioning → C 6060B without a battery →
D supervised battery tests → E remote control (blocked). Every step is
**NOT_RUN**; nothing is claimed BENCH_TESTED or HARDWARE_VALIDATED.

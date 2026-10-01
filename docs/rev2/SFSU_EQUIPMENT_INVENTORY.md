# SFSU equipment inventory (Rev.2)

Source of truth in code: `desktop/equipment/inventory.py`. Asset IDs and
calibration status are **UNKNOWN until read off the instruments**.

| Instrument | Role | Envelope | Never |
|---|---|---|---|
| Agilent/Keysight 6060B | PRIMARY electronic load | 3–60 V, 60 A, 300 W; CC/CV/CR; GPIB; transient | exceed V ≤ 60, I ≤ 60, V·I ≤ 300 W; assume 60 A at all voltages |
| Keysight EDU34450A | Primary independent reference DMM | V, I, R, continuity, temperature | — |
| Keysight EDU36311A | Low-energy commissioning source | CH1 0–6 V/5 A; CH2, CH3 0–30 V/1 A; series operation per manufacturer docs | pose as a 42 V high-current battery |
| Keysight EDUX1052G | Oscilloscope: contactor/E-stop/sag/protocol timing | — | probe arbitrary high-energy nodes because the input rating allows it |
| Keysight EDU33212A | Waveform generator: sensor/ADC/fault injection | — | be a battery power source |
| Analog Discovery 2 | UART/SPI/I²C/PWM/low-voltage analog, BMS comms research | — | be a high-energy measurement instrument |
| Handheld multimeter | Continuity, polarity, rails, wiring checks | — | replace the bench DMM as quantitative reference |

Batteries on hand: Ninebot NEB1002-H (36 V, 5.2 Ah, 187 Wh), Shenzhen Elite
HY-RDF-S1004UM-MH1 (37 V, 12.8 Ah, 473.6 Wh), Ninebot NEE1006-M (36 V, 15.3 Ah, 551 Wh).

Out of scope for Rev.2 (`OUT_OF_SCOPE_FOR_REV2`): packs above 60 V, EV
modules/packs, regenerative cyclers and their drivers, "90 A" testing, and the
removed Rev.1 USB load (archived in `legacy/rev1/`).

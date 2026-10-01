# RC1.3 protection calculations (INA228 differential clamp + connector-entry ESD stage)

Status of inputs: **verified** = INA228 limits, 1.5SMBJ48A, ERJP08 (uploaded datasheets). 1.5SMBJ12CA is now **verified** from the same Bourns 1.5SMBJ datasheet (VRWM 12 V, VBR 13.3-14.7 V, IR 1 uA, VC 19.9 V @ 75.4 A, 25.9 V @ 377 A). Only the D20 capacitance remains ASSUMED (not in the datasheet). The connector-entry diodes D15-D19 are the verified 1.5SMBJ48A; the other connector-entry rows below are sensitivity cases only. Architecture: connector -> fast ESD diode -> pulse-rated series resistor (R41/R42/R43) -> surge TVS (1.5SMBJ48A) -> filter (R11/R12/R13 + C26/C28) -> INA228.

ESD target: IEC 61000-4-2 +-8 kV contact / +-15 kV air - a **design / first-article target, not a certification claim**. Generator model: 330 ohm / 150 pF discharge, source current Vg/330 into the clamp network (8 kV: 24 A; 15 kV: 45 A). DC-level clamp analysis only: the first-nanosecond L di/dt spike is not resolvable by a datasheet model (needs TLP / gun test).

## 1. ESD on the VBUS lead (J6.1): R41 = 47 ohm, then D7 1.5SMBJ48A, then R13 10 ohm to the INA228 VBUS pin

| connector-entry device | event | connector node V | ESD diode A | series R A | V across series R | peak P in R (W) | R pulse energy (uJ) | D5/D7 clamp V | margin to 85 V | VBUS-pin V (pin 5 mA bound) |
|---|---|---|---|---|---|---|---|---|---|---|
| none (RC1.2: series R first) | 8 kV contact | 1066 | 0.0 | 21.01 | 988 V | 20754 | 521.4 | 77.9 | +7.1 | <= 77.9 (pin current = (V_D - pin clamp)/10 ohm) |
| none (RC1.2: series R first) | 15 kV air | 1943 | 0.0 | 39.57 | 1860 V | 73579 | 1848.7 | 83.4 | +1.6 | <= 83.4 (pin current = (V_D - pin clamp)/10 ohm) |
| none (RC1.2: series R first) | 15 kV air, +60 K | 1946 | 0.0 | 39.56 | 1859 V | 73544 | 1847.8 | 87.0 | -2.0 | <= 87.0 (pin current = (V_D - pin clamp)/10 ohm) |
| SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve) | 8 kV contact | 205 | 20.6 | 3.05 | 143 V | 436 | 11.0 | 61.8 | +23.2 | <= 61.8 (pin current = (V_D - pin clamp)/10 ohm) |
| SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve) | 15 kV air | 334 | 38.7 | 5.73 | 269 V | 1544 | 38.8 | 64.4 | +20.6 | <= 64.4 (pin current = (V_D - pin clamp)/10 ohm) |
| SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve) | 15 kV air, +60 K | 337 | 38.7 | 5.73 | 269 V | 1543 | 38.8 | 67.9 | +17.1 | <= 67.9 (pin current = (V_D - pin clamp)/10 ohm) |
| SMBJ48A-class, Rdyn 2.4 ohm | 8 kV contact | 114 | 22.8 | 1.14 | 54 V | 61 | 1.5 | 60.0 | +25.0 | <= 60.0 (pin current = (V_D - pin clamp)/10 ohm) |
| SMBJ48A-class, Rdyn 2.4 ohm | 15 kV air | 162 | 42.8 | 2.14 | 101 V | 216 | 5.4 | 60.9 | +24.1 | <= 60.9 (pin current = (V_D - pin clamp)/10 ohm) |
| SMBJ48A-class, Rdyn 2.4 ohm | 15 kV air, +60 K | 165 | 42.8 | 2.14 | 101 V | 216 | 5.4 | 64.5 | +20.5 | <= 64.5 (pin current = (V_D - pin clamp)/10 ohm) |
| **1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built** | 8 kV contact | 81 | 23.5 | 0.47 | 22 V | 10 | 0.3 | 59.3 | +25.7 | <= 59.3 (pin current = (V_D - pin clamp)/10 ohm) |
| **1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built** | 15 kV air | 101 | 44.3 | 0.88 | 41 V | 36 | 0.9 | 59.7 | +25.3 | <= 59.7 (pin current = (V_D - pin clamp)/10 ohm) |
| **1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built** | 15 kV air, +60 K | 104 | 44.3 | 0.88 | 41 V | 36 | 0.9 | 63.3 | +21.7 | <= 63.3 (pin current = (V_D - pin clamp)/10 ohm) |
| hypothetical low-Rdyn 0.3 ohm | 8 kV contact | 66 | 23.9 | 0.15 | 7 V | 1 | 0.0 | 59.0 | +26.0 | <= 59.0 (pin current = (V_D - pin clamp)/10 ohm) |
| hypothetical low-Rdyn 0.3 ohm | 15 kV air | 72 | 45.0 | 0.28 | 13 V | 4 | 0.1 | 59.2 | +25.8 | <= 59.2 (pin current = (V_D - pin clamp)/10 ohm) |
| hypothetical low-Rdyn 0.3 ohm | 15 kV air, +60 K | 76 | 44.9 | 0.28 | 13 V | 4 | 0.1 | 62.7 | +22.3 | <= 62.7 (pin current = (V_D - pin clamp)/10 ohm) |

## 1. ESD on the Kelvin line (J5.1 / J5.2): R42, R43 = 10 ohm, then D5/D6 1.5SMBJ48A, then R11/R12 10 ohm to the pin

| connector-entry device | event | connector node V | ESD diode A | series R A | V across series R | peak P in R (W) | R pulse energy (uJ) | D5/D7 clamp V | margin to 85 V | VBUS-pin V (pin 5 mA bound) |
|---|---|---|---|---|---|---|---|---|---|---|
| none (RC1.2: series R first) | 8 kV contact | 312 | 0.0 | 23.30 | 233 V | 5428 | 136.4 | 78.6 | +6.4 | <= 78.6 (pin current = (V_D - pin clamp)/10 ohm) |
| none (RC1.2: series R first) | 15 kV air | 523 | 0.0 | 43.87 | 439 V | 19244 | 483.5 | 84.7 | +0.3 | <= 84.7 (pin current = (V_D - pin clamp)/10 ohm) |
| none (RC1.2: series R first) | 15 kV air, +60 K | 527 | 0.0 | 43.86 | 439 V | 19235 | 483.3 | 88.2 | -3.2 | <= 88.2 (pin current = (V_D - pin clamp)/10 ohm) |
| SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve) | 8 kV contact | 161 | 14.4 | 9.34 | 93 V | 873 | 21.9 | 67.8 | +17.2 | <= 67.8 (pin current = (V_D - pin clamp)/10 ohm) |
| SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve) | 15 kV air | 251 | 27.1 | 17.58 | 176 V | 3089 | 77.6 | 75.7 | +9.3 | <= 75.7 (pin current = (V_D - pin clamp)/10 ohm) |
| SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve) | 15 kV air, +60 K | 255 | 27.1 | 17.57 | 176 V | 3088 | 77.6 | 79.2 | +5.8 | <= 79.2 (pin current = (V_D - pin clamp)/10 ohm) |
| SMBJ48A-class, Rdyn 2.4 ohm | 8 kV contact | 106 | 19.6 | 4.30 | 43 V | 185 | 4.6 | 63.0 | +22.0 | <= 63.0 (pin current = (V_D - pin clamp)/10 ohm) |
| SMBJ48A-class, Rdyn 2.4 ohm | 15 kV air | 148 | 36.9 | 8.09 | 81 V | 654 | 16.4 | 66.6 | +18.4 | <= 66.6 (pin current = (V_D - pin clamp)/10 ohm) |
| SMBJ48A-class, Rdyn 2.4 ohm | 15 kV air, +60 K | 151 | 36.9 | 8.09 | 81 V | 654 | 16.4 | 70.1 | +14.9 | <= 70.1 (pin current = (V_D - pin clamp)/10 ohm) |
| **1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built** | 8 kV contact | 80 | 22.1 | 1.92 | 19 V | 37 | 0.9 | 60.7 | +24.3 | <= 60.7 (pin current = (V_D - pin clamp)/10 ohm) |
| **1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built** | 15 kV air | 98 | 41.6 | 3.60 | 36 V | 130 | 3.3 | 62.3 | +22.7 | <= 62.3 (pin current = (V_D - pin clamp)/10 ohm) |
| **1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built** | 15 kV air, +60 K | 102 | 41.5 | 3.60 | 36 V | 130 | 3.3 | 65.9 | +19.1 | <= 65.9 (pin current = (V_D - pin clamp)/10 ohm) |
| hypothetical low-Rdyn 0.3 ohm | 8 kV contact | 66 | 23.4 | 0.64 | 6 V | 4 | 0.1 | 59.5 | +25.5 | <= 59.5 (pin current = (V_D - pin clamp)/10 ohm) |
| hypothetical low-Rdyn 0.3 ohm | 15 kV air | 72 | 44.0 | 1.21 | 12 V | 15 | 0.4 | 60.0 | +25.0 | <= 60.0 (pin current = (V_D - pin clamp)/10 ohm) |
| hypothetical low-Rdyn 0.3 ohm | 15 kV air, +60 K | 76 | 44.0 | 1.21 | 12 V | 15 | 0.4 | 63.6 | +21.4 | <= 63.6 (pin current = (V_D - pin clamp)/10 ohm) |

Reading the table: without a connector-entry device (RC1.2) the series resistor carries almost the whole gun current (21-44 A) and drops 0.2-1.9 kV across a 1206 anti-surge part whose datasheet gives only 125 V limiting-element voltage / 500 V overload voltage and **no pulse curve**, and the RC1.2 pin clamp reached 83-87 V (15 kV air: 85 V limit exceeded at +60 K): the RC1.2 ESD behaviour of R41/R42/R43 and the INA228 VBUS/CM margin was undemonstrated. With a connector-entry 1.5SMBJ48A (as built, Rdyn ~0.95 ohm) the connector node is held at ~80-104 V, the series resistor sees 19-41 V (Kelvin 10 ohm) / 22-41 V (VBUS 47 ohm) instead of 0.2-1.9 kV, the resistor pulse energy drops from 136-2440 uJ to 0.3-3.3 uJ, and the surge clamp D5/D7 stays near 60-66 V (margin >= 19 V to 85 V). The result depends strongly on the entry device's dynamic resistance: a 200 W SOD-123FL 48 V part (~7 ohm) would leave 93-269 V across the resistor and 76-79 V at the Kelvin pin (margin 6-9 V), which is why the SMF48A candidate used in the first RC1.3 draft was replaced. No purpose-built >= 48 V ESD diode with a verified Rdyn <= 1 ohm was identified in the supplied files. DC-level clamp analysis only; the first-nanosecond spike and the ERJP08 pulse survival remain first-article test items.

## 2. INA228 IN+/IN- differential stress with D20 (1.5SMBJ12CA, verified Bourns data) across SHUNT_INP_RAW / SHUNT_INN_RAW

D20 sits on the connector side of R11/R12 so the INA228 pins only ever see the clamp level minus the pin-current drop (<= 5 mA x 10 ohm = 50 mV).

| one-sided event on IN+ | IN+_RAW before D20 (D5 clamp, V) | IN- condition | I through D20 (A) | differential at pins (V) | limit | margin |
|---|---|---|---|---|---|---|
| ESD 8 kV contact | 77.9 | IN- lead connected, pack at 44 V | 1.0 | 14.8 | 40 | +25.2 |
| ESD 8 kV contact | 77.9 | IN- lead connected, pack at 0 V | 3.1 | 14.9 | 40 | +25.1 |
| ESD 8 kV contact | 77.9 | IN- lead open (floating) | ~0.01-0.05 (node charge) | 14.7 | 40 | +25.3 |
| ESD 15 kV air | 83.4 | IN- lead connected, pack at 44 V | 1.2 | 14.8 | 40 | +25.2 |
| ESD 15 kV air | 83.4 | IN- lead connected, pack at 0 V | 3.4 | 14.9 | 40 | +25.1 |
| ESD 15 kV air | 83.4 | IN- lead open (floating) | ~0.01-0.05 (node charge) | 14.7 | 40 | +25.3 |
| hot-plug / interruption (D5 at 20 A) | 77.6 | IN- lead connected, pack at 44 V | 0.9 | 14.8 | 40 | +25.2 |
| hot-plug / interruption (D5 at 20 A) | 77.6 | IN- lead connected, pack at 0 V | 3.1 | 14.9 | 40 | +25.1 |
| hot-plug / interruption (D5 at 20 A) | 77.6 | IN- lead open (floating) | ~0.01-0.05 (node charge) | 14.7 | 40 | +25.3 |
| hot-plug node (RLC model, 59.5 V) | 59.5 | IN- lead connected, pack at 44 V | 0.0 | 14.7 | 40 | +25.3 |
| hot-plug node (RLC model, 59.5 V) | 59.5 | IN- lead connected, pack at 0 V | 2.2 | 14.9 | 40 | +25.1 |
| hot-plug node (RLC model, 59.5 V) | 59.5 | IN- lead open (floating) | ~0.01-0.05 (node charge) | 14.7 | 40 | +25.3 |

Without D20 (RC1.2) the same one-sided events put 77.9 / 83.4 V (IN- near 0 V or open) or 33.9 / 39.4 V (IN- at 44 V) across the 40 V differential limit: the open-lead and 0 V cases exceeded the absolute maximum by 38-43 V. With D20 the differential is held to ~15-17 V (hot: +6 % of VBR at +60 K = ~+1 V) in every case, leaving > 22 V margin. Common-mode level (pin to GND) is unchanged: 53-84 V, within 85 V - that margin is unchanged from the audit and still depends on the 1.5SMBJ48A + R-chain for the first-nanosecond spike.

## 3. Normal-operation error, leakage, capacitance, recovery (0-50 mV differential, common mode up to 44 V)

| item | assumption | result |
|---|---|---|
| D20 leakage current: flat worst-case bound: IR 1 uA (datasheet, at VRWM 12 V) applied at all voltages | I = 1e+03 nA | differential error = I x (R42+R43) = 20 uV = 400 ppm of 50 mV (offset-like: removed by the zero-current offset trim) |
| D20 leakage current: ohmic scaling 1 uA/12 V x 0.05 V (leakage at 50 mV differential, 25 C) | I = 4.17 nA | differential error = I x (R42+R43) = 0.0833 uV = 2 ppm of 50 mV (offset-like: removed by the zero-current offset trim) |
| D20 leakage current: ohmic scaling x 10 for +85 C | I = 41.7 nA | differential error = I x (R42+R43) = 0.833 uV = 17 ppm of 50 mV (offset-like: removed by the zero-current offset trim) |
| D20 leakage at a CM of 44 V | the clamp is differential: both terminals at the same potential -> no voltage across it | 0 (no common-mode leakage) |
| D20 capacitance (ASSUMED 2 nF, 0 V bias; falls with bias) | in parallel with C26 100 nF | differential filter tau 4.00 -> 4.08 us (+2 %), fc 39.8 -> 39.0 kHz |
| D20 recovery after a clamp event | clamp not conducting below VBR (14.7 V); recovery = filter settling | to 0.01 % of 50 mV: 9.2 tau = 38 us (INA228 conversion time >= 50 us; discard the first conversion after an event) |
| connector-entry diodes D15/D16 on the Kelvin lines (1.5SMBJ48A, leakage <= 1 uA at VRWM 48 V / 25 C per the supplied datasheet, CM up to 44 V) | they sit BEFORE R42/R43, so their leakage flows through the cable / shunt Kelvin lead (assume <= 1 ohm), not through the 10 ohm resistors | mismatch error <= 1 uA x 1 ohm = 1 uV = 20 ppm of 50 mV; with the 1.5SMBJ48A footprint (also <= 1 uA) the same bound |
| D5/D6 (existing) leakage x R42/R43 | <= 1 uA x 10 ohm | 10 uV line-to-line mismatch worst case (0.02 % of 50 mV) - unchanged from RC1.2 and now measurable by the zero-current offset test |
| D17/D19 (PACK_INA_CON, RELAY_OUT) leakage | before R41 / R26 and fed by the stiff pack node | no divider/gain effect; VBUS gain error stays 57 ohm / ZVBUS = 0.005-0.007 % |
| D18 (PACK_ADC) leakage | diode before the 150 kohm divider R17+R18; source = pack lead resistance (<= 1 ohm) | <= 1 uV; no effect on the 16:1 ADC divider ratio |
| connector-entry diode capacitance (1.5SMBJ48A: datasheet value not extracted; assume <= 500 pF) | on 10 ohm / 47 ohm series: corner >> 10 MHz | no effect on the 40 kHz differential filter (10 ohm x 500 pF = 5 ns); slightly slows the fast hot-plug edge (damping, beneficial) |

## 4. ERJP08 (Panasonic) - unchanged status

Candidate Panasonic ERJ-P08F47R0V / F10R0V: 0.66 W @ 70 C, limiting-element voltage 125 V, overload voltage 500 V, no pulse-energy / pulse-limiting curve in the supplied datasheet. **No verified pulse-energy limit is claimed.** With the connector-entry stage the series resistor sees (V_node - V_D) instead of the full generator: the table above gives the new stress; whether it survives is a first-article (pulse-test) item.


# Pack-sense protection audit (independent recomputation)

INA228 limits (TI datasheet, verified): VBUS and IN+/IN- common-mode -0.3..85 V; differential (IN+ - IN-) +-40 V; input current into any pin 5 mA; HBM +-2 kV; ZVBUS 0.8-1.2 Mohm; IB 0.1 nA typ / 2.5 nA max; RDIFF 92 kohm.

## 1. Credible events (as defined in the brief)

| Event | model | node clamp V (1.5SMBJ48A) | margin to 85 V | node V (1.5SMBJ45A) | margin |
|---|---|---|---|---|---|
| interrupt 18.5 A (firmware trip bound), Rs=0 | I_TVS = 18.5 A | 76.5 | +8.5 | 70.9 | +14.1 |
| interrupt 20 A | I_TVS = 20.0 A | 77.6 | +7.4 | 72.2 | +12.8 |
| ESD 8 kV contact (IEC 61000-4-2), 330 ohm gun + 47 ohm upstream | I_TVS = 21 A (48A) / 21 A (45A) | 77.9 | +7.1 | 72.8 | +12.2 |
| ESD 15 kV air (IEC 61000-4-2), 330 ohm gun + 47 ohm upstream | I_TVS = 40 A (48A) / 40 A (45A) | 83.4 | +1.6 | 77.7 | +7.3 |
| ESD 15 kV air, +60 K hot (VBR tempco) | 40 A / 40 A | 87.0 | -2.0 | 81.0 | +4.0 |

ESD note: these are *DC-level clamp* values. The first-nanosecond spike (L di/dt of the TVS leads and the trace to the INA pin: 5 nH x 30 A / 1 ns = 150 V) is NOT in the clamp curve and cannot be resolved by a datasheet model; only a TLP/IEC-gun test at the connector can demonstrate the INA228 pin stays below 85 V. The 47 ohm upstream resistor barely helps against ESD (330 ohm gun impedance dominates).

## 2. Hot-plug onto a live 44 V pack - VBUS path: 47 ohm upstream, 10 ohm to the pin, 100 nF at VBUS

| L (uH) | C_tvs (nF) | TVS node peak V | INA pin peak V | TVS peak A | energy in upstream R (uJ) | margin to 85 V (node) |
|---|---|---|---|---|---|---|
| 0.5 | 0.3 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 0.5 | 1 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 0.5 | 3 | 44.0 | 44.0 | 0.00 | 83 | +41.0 |
| 2 | 0.3 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 2 | 1 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 2 | 3 | 44.0 | 44.0 | 0.00 | 83 | +41.0 |
| 5 | 0.3 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 5 | 1 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 5 | 3 | 44.0 | 44.0 | 0.00 | 83 | +41.0 |
| 10 | 0.3 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 10 | 1 | 44.0 | 44.0 | 0.00 | 80 | +41.0 |
| 10 | 3 | 44.0 | 44.0 | 0.00 | 83 | +41.0 |

Worst R41 combination: node 44.0 V (limit 85 V).

## 2. Hot-plug onto a live 44 V pack - Kelvin path: 10 ohm upstream, 10 ohm to the pin, ~1 nF pin/filter capacitance (no 100 nF)

| L (uH) | C_tvs (nF) | TVS node peak V | INA pin peak V | TVS peak A | energy in upstream R (uJ) | margin to 85 V (node) |
|---|---|---|---|---|---|---|
| 0.5 | 0.3 | 55.3 | 54.3 | 0.00 | 1 | +29.7 |
| 0.5 | 1 | 55.3 | 54.6 | 0.00 | 2 | +29.7 |
| 0.5 | 3 | 51.6 | 51.4 | 0.00 | 4 | +33.4 |
| 2 | 0.3 | 59.2 | 59.1 | 0.32 | 1 | +25.8 |
| 2 | 1 | 59.3 | 59.2 | 0.44 | 1 | +25.7 |
| 2 | 3 | 59.4 | 59.2 | 0.49 | 3 | +25.6 |
| 5 | 0.3 | 59.2 | 59.2 | 0.35 | 1 | +25.8 |
| 5 | 1 | 59.3 | 59.3 | 0.45 | 1 | +25.7 |
| 5 | 3 | 59.5 | 59.4 | 0.59 | 3 | +25.5 |
| 10 | 0.3 | 59.2 | 59.2 | 0.30 | 0 | +25.8 |
| 10 | 1 | 59.3 | 59.2 | 0.39 | 1 | +25.7 |
| 10 | 3 | 59.4 | 59.4 | 0.53 | 2 | +25.6 |

Worst R42/R43 combination: node 59.5 V (limit 85 V).

## 3. INA228 IN+/IN- differential stress (limit +-40 V)

One-sided transient: IN+ driven to the clamp level while IN- is at the pack voltage (both leads connected) or near 0 V (IN- lead not yet connected / broken, so IN- is held only by the 92 kohm differential impedance).

| clamp level on IN+ | IN- at 44 V | IN- at ~0 V |
|---|---|---|
| interrupt 18.5 A bound (76.5 V) | +32.5 V (OK) | +76.5 V (EXCEEDS) |
| ESD 8 kV contact (~77.9 V) | +33.9 V (OK) | +77.9 V (EXCEEDS) |
| ESD 15 kV air (~83.4 V) | +39.4 V (OK) | +83.4 V (EXCEEDS) |
| hot-plug worst (model) | +15.5 V (OK) | +59.5 V (EXCEEDS) |

Both leads connected and live: a one-sided event stays under 40 V with 1-6 V margin at the ESD levels. If an IN- lead is open or connects later, a one-sided transient exceeds the +-40 V absolute maximum for as long as the 92 kohm / pin-capacitance time constant holds IN- down. A symmetric (common-mode) transient does not stress the differential limit. -> add a differential clamp across IN+/IN- on the INA side of R11/R12 (see recommendations).

## 4. Leakage and gain errors (steady state)

| item | value |
|---|---|
| VBUS gain error from 57 ohm in series with ZVBUS 0.8-1.2 Mohm | 0.0047 - 0.0071 % (fixed ratio; calibration against the reference meter removes it, its Z spread 0.0024 % does not) |
| TVS leakage (1 uA max at VRWM, 25 C) x 47 ohm on PACK_INA | 47 uV (1.1 ppm of 44 V) |
| TVS leakage (1 uA max) x (10+10 ohm) on each Kelvin line | 20 uV worst-case line-to-line mismatch = 8 mA shunt-current equivalent (shunt 50 mV/20 A = 2.5 mohm), 0.04 % of 20 A |
| INA228 bias current (2.5 nA max) x 20 ohm | 50 nV (negligible) |

Leakage rises with temperature and with proximity to VRWM; the Bourns file gives only 1 uA max at VRWM/25 C (no temperature curve), so the real figure is a first-article measurement (INA228 shunt reading at 0 A, cold and warm).

## 5. Panasonic ERJP08 (1206) - from the uploaded datasheet (28-Mar-26)

0.66 W @ 70 C, limiting element voltage 125 V, max overload voltage 500 V, TCR +-200 ppm/K for R>=10 ohm (R<10: -100..+600), AEC-Q200. 47 ohm: RCWV = min(sqrt(0.66 x 47), 125) = 5.6 V; 10 ohm: 2.6 V. Overload test = 2.5 x RCWV for 5 s (about 4.1 W / 20 J into 47 ohm). Orderable pattern ERJP08 F 47R0 V = 1 % (F, four-digit code), embossed 4 mm carrier, 5000 pcs; ERJP08F10R0V is at the lower limit of the +-1 % range (10 ohm to 1 Mohm). **The datasheet contains no pulse-energy / pulse-limiting curve** (only the ESD test: 3 kV / 150 pF, 0.68 mJ, resistance change plotted), so the resistor pulse rating stays OPEN even though the credible pulses are only 0.3-0.4 mJ (hot-plug/interruption) - request the Panasonic pulse-limiting-voltage / surge curve or test the part.


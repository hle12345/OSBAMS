# OSBAMS Rev.2 controller — calculations (design phase, merged)

All results are generated. ⚠[unverified] marks a datasheet-dependent input that is still a placeholder. **Nothing in this file is frozen until its inputs are verified** (§8).

## 1. Independent ADC channel  PACK_ADC → 75 k → 75 k → ADC_TAP → 10 k → GND ; 1 k series ; 100 nF at the pin

| Vpack | ADC_TAP (3.3 V full scale) |
|---|---|
| 30 V | 1.875 V |
| 36 V | 2.250 V |
| 42 V | 2.625 V |
| 44 V | 2.750 V |
| 48 V | 3.000 V |
| 77.4 V | 4.838 V |

Ratio 16:1 · LSB(12 bit, 3.3 V) = 0.806 mV → 12.9 mV per LSB at the pack · full scale 52.8 V.
Divider current at 44 V 275 µA, 12.1 mW total, each 75 kΩ sees 20.6 V and 5.7 mW (0805 thin film: fine). Source impedance (tap ∥ 1 k series) ≈ 10.38 kΩ, τ with 100 nF ≈ 1.04 ms.

**Error budget — three separate groups (do not mix them):**

| Group | Item | Worst case |
|---|---|---|
| A. Divider (resistors only) | 0.1 % tolerance, all three resistors | ±0.19 % |
| A. Divider | tempco 25 ppm/K, 40 K excursion | ±0.20 % |
| A. Divider | clamp leakage (placeholder ⚠[unverified]) | ±0.04 % |
| **A. subtotal (divider)** | | **±0.43 %** |
| B. ADC | TUE 4.0 LSB 12-bit ⚠[unverified] | ±0.10 % |
| C. Reference | VDDA = 3.3 V ± 2 % (assumption, uncorrected) | ±2.00 % |
| C. Reference | after VREFINT correction ⚠[unverified] | ±0.30 % |

Total worst case uncorrected ±2.53 % (≈ ±1.11 V at 44 V); with VREFINT correction ±0.83 % (≈ ±0.36 V). RSS corrected ±0.42 %.
**Only ±0.43 % of the uncorrected figure comes from the divider; the rest is the 3V3 reference, which the firmware removes by measuring VREFINT.** Adequate for a plausibility cross-check against the INA228 (firmware agreement window 1.5 V); not metrology.

### 1.1 PACK+ present, controller unpowered (back-feed analysis)

Decision: **no upper clamp to 3V3 on PA1.** Protection is 1 kΩ series + a clamp **to GND only** (negative excursions) — so the external circuit offers no path into the 3V3 rail. Whether the pin's own structure has a diode to VDD/VDDA is a datasheet item (`stm32_pa1_io_type`, unverified). If it does, the divider (≤ 0.29 mA) could lift the rail; the guard is a bleeder across 3V3A:

| Bleeder | max rail rise = I·R | vs POR min |
|---|---|---|
| none | up to the diode-clamped node voltage (≈ 2.75 V) → **can reach POR** ⚠ | 1.6 V ⚠[unverified] |
| 6.8 kΩ (0.49 mA from 3V3) | 1.97 V | 1.6 V |
| 3.3 kΩ (1.00 mA from 3V3) | 0.95 V | 1.6 V |
| 2.2 kΩ (1.50 mA from 3V3) | 0.64 V | 1.6 V |

Back-feed current ≤ 0.29 mA at 44 V. Baseline: bleeder footprint (3.3 kΩ) **DNP**; fit it if the datasheet shows an upper protection diode on PA1. Overvoltage: 1.5SMBJ48A clamp 77.4 V → tap 4.84 V (needs the pin tolerance from the datasheet); reverse pack −44 V → GND clamp holds the pin ≥ −0.3 V with ≤ 0.3 mA.

## 2. INA228 + Bourns RSA-20-50 (2.5 mΩ, 20 A / 50 mV)  — equations ⚠[unverified]

| I | Vshunt | P shunt |
|---|---|---|
| 1 A | 2.50 mV | 0.003 W |
| 7.14 A | 17.85 mV | 0.127 W |
| 10 A | 25.00 mV | 0.250 W |
| 15 A | 37.50 mV | 0.562 W |
| 18.5 A | 46.25 mV | 0.856 W |
| 20 A | 50.00 mV | 1.000 W |

ADCRANGE=0 (±163.84 mV, 312.5 nV/LSB → 125 µA/LSB native) is kept: ADCRANGE=1 (±40.96 mV) saturates at 16.38 A and would hide the 18.5 A firmware trip (46.25 mV).
- IMAX 20 A: CURRENT_LSB = 38.147 µA, **SHUNT_CAL = 1250** (limit 32767)  ← chosen (20 A shunt scale)
- IMAX 30 A: CURRENT_LSB = 57.220 µA, **SHUNT_CAL = 1875** (limit 32767)  (old firmware app_config.h scale — to be changed)
- Offset 1.0 µV ⚠[unverified] → 0.40 mA = 0.0040 % of 10 A.
- 2 × 10 Ω + 100 nF differential: fc = 80 kHz; bias 2.0 nA ⚠[unverified] × 10 Ω = 20 nV.
- TVS 1.5SMBJ48A Vc ≈ 77.4 V ⚠[unverified] vs abs max 85.0 V ⚠[unverified] → margin 7.6 V (thin; verify the clamp at the real surge current).
- Sense wiring: IN+ = relay load side (RELAY_OUT), IN− = shunt load-side Kelvin; **VBUS from PACK_INA (upstream of K1)** so open-circuit voltage is read with the relay open; separate PACK_ADC lead for the independent channel; only GND_SENSE bonds logic ground to the pack.

## 3. Relay driver (Durakool DG57CM-5021-76-1012-R) — coil data ⚠[unverified]

| Coil V | I | P |
|---|---|---|
| 10.5 V | 117 mA | 1.23 W |
| 11.55 V | 128 mA | 1.48 W |
| 12.0 V | 133 mA | 1.60 W |
| 13.8 V | 153 mA | 2.12 W |
| 15.0 V | 167 mA | 2.50 W |

XDR-75-12 is adjustable (to ~15 V): **set and verify 12.0 V** (2.5 W in the coil at 15 V).
**MOSFET acceptance criteria (replaces the IRLZ44N by decision):** SMD, VDSS ≥ 60 V, RDS(on) *specified* at VGS = 2.5 V **and** 3.3 V, VGS(th) max ≤ 2.0 V, ID ≥ 1 A, gate charge small enough for a 3.3 V GPIO via 220 Ω. With the coil at 0.17 A, RDS(on) ≤ 0.3 Ω keeps VDS ≤ 50 mV and P ≤ 9 mW. Gate network: 220 Ω in series, 10 kΩ pull-down → relay OFF when the MCU is in reset/unpowered/Hi-Z (gate leakage × 10 kΩ ≪ VGS(th)). Candidate part: **not selected** (chosen part: VDSS, RDS(on) specified at VGS=2.5 V and 3.3 V, VGS(th) max, ID, Ciss, SOA, footprint).
- Flyback energy ½LI² = 1.78 mJ (L 0.2 H ⚠[unverified]); diode-only decay τ = L/R = 2.2 ms; with diode + 27 V TVS in series the current decays 3.2× faster (clamp ≈ 40 V + Vf vs MOSFET VDSS ≥ 60 V). **Baseline: plain diode; a series link/TVS footprint is provided (DNP). Do not commit to 27 V until the relay release-time data and MOSFET VDSS are verified.**

## 4. VO610A-1 stages — design-to-guaranteed method (NOT frozen)

The datasheet guarantees CTR_min only at one LED current; the stage must still saturate at the real IF after temperature and aging. Method:

1. CTR_eff = CTR_min(IF curve) × temp derate × aging derate  →  0.20 × 0.75 × 0.80 = **0.120** (all three ⚠[unverified], placeholders; the 40 % @ 10 mA bin figure is 0.40 ⚠[unverified]).
2. Required: IF · CTR_eff ≥ 2 × I_pullup_needed  (2× margin), I_pullup_needed = (3.3 − VCEsat)/Rpu.
3. Evaluate over the whole supply range; reject any network that does not meet step 2 at the minimum voltage.

**RELAY_FB, Chat draft 4×3.6 k + 22 k** — R_LED 14.4 kΩ, pull-up 22 kΩ (needs 0.132 mA)

| V | IF | IC available (CTR_eff) | margin | R dissipation |
|---|---|---|---|---|
| 24 V | 1.58 mA | 0.190 mA | ×1.4 | 36 mW |
| 28 V | 1.86 mA | 0.223 mA | ×1.7 | 50 mW |
| 30 V | 2.00 mA | 0.240 mA | ×1.8 | 58 mW |
| 36 V | 2.42 mA | 0.290 mA | ×2.2 | 84 mW |
| 44 V | 2.97 mA | 0.357 mA | ×2.7 | 127 mW |
| 77.4 V | 5.29 mA | 0.635 mA | ×4.8 | 403 mW |

Minimum voltage for 2× margin: **32.8 V** (required ≤ 28 V → FAIL (placeholder CTR)).

**RELAY_FB, Code draft 2×6.8 k + 33 k** — R_LED 13.6 kΩ, pull-up 33 kΩ (needs 0.088 mA)

| V | IF | IC available (CTR_eff) | margin | R dissipation |
|---|---|---|---|---|
| 24 V | 1.68 mA | 0.201 mA | ×2.3 | 38 mW |
| 28 V | 1.97 mA | 0.236 mA | ×2.7 | 53 mW |
| 30 V | 2.12 mA | 0.254 mA | ×2.9 | 61 mW |
| 36 V | 2.56 mA | 0.307 mA | ×3.5 | 89 mW |
| 44 V | 3.15 mA | 0.378 mA | ×4.3 | 135 mW |
| 77.4 V | 5.60 mA | 0.672 mA | ×7.7 | 427 mW |

Minimum voltage for 2× margin: **21.1 V** (required ≤ 28 V → PASS).

**ESTOP_SENSE, Chat draft 5.6 k + 22 k** — R_LED 5.6 kΩ, pull-up 22 kΩ (needs 0.132 mA)

| V | IF | IC available (CTR_eff) | margin | R dissipation |
|---|---|---|---|---|
| 10.5 V | 1.66 mA | 0.199 mA | ×1.5 | 15 mW |
| 11.55 V | 1.85 mA | 0.222 mA | ×1.7 | 19 mW |
| 12 V | 1.93 mA | 0.231 mA | ×1.8 | 21 mW |
| 15 V | 2.46 mA | 0.296 mA | ×2.2 | 34 mW |

Minimum voltage for 2× margin: **13.5 V** (required ≤ 10.5 V → FAIL (placeholder CTR)).

**ESTOP_SENSE, Code draft 5.1 k + 33 k** — R_LED 5.1 kΩ, pull-up 33 kΩ (needs 0.088 mA)

| V | IF | IC available (CTR_eff) | margin | R dissipation |
|---|---|---|---|---|
| 10.5 V | 1.82 mA | 0.219 mA | ×2.5 | 17 mW |
| 11.55 V | 2.03 mA | 0.244 mA | ×2.8 | 21 mW |
| 12 V | 2.12 mA | 0.254 mA | ×2.9 | 23 mW |
| 15 V | 2.71 mA | 0.325 mA | ×3.7 | 37 mW |

Minimum voltage for 2× margin: **8.7 V** (required ≤ 10.5 V → PASS).

Both drafts' networks are *candidate sizing only*: they pass or fail purely on placeholder derates. **Frozen resistor values come from the official VO610A-1 datasheet CTR-vs-IF data**; no assumed 20 % CTR may remain in the frozen schematic.
Single-fault and surge notes: two or more series resistors on the LED so one short cannot overdrive it; 1N4148 antiparallel across the LED limits reverse voltage (LED VR max 6.0 V ⚠[unverified]); at the 77.4 V TVS clamp IF ≈ 5.3 mA and each of four 3.6 k resistors dissipates 101 mW (0805 = 125 mW — marginal, check pulse rating).

## 5. ARM_SENSE divider (status only)  COIL_V → 270 k → ARM_DIV → 100 k → GND ; 1 k ; 100 nF

| COIL_V | ARM_DIV |
|---|---|
| 0 V | 0.00 V |
| 10.5 V | 2.84 V |
| 11.55 V | 3.12 V |
| 12 V | 3.24 V |
| 13.8 V | 3.73 V |
| 15 V | 4.05 V |

VIH = 2.31 V ⚠[unverified] → thresholds satisfied from 10.5 V up (2.84 V); at 15 V the node is 4.05 V. **No clamp to 3V3** (same back-feed argument as §1.1): protection is 1 kΩ + 100 nF and **PC10 must be a 5 V-tolerant pin** (`stm32_pa1_io_type`, unverified); if it is not, the ratio changes to ≤ 0.22 so that 15 V stays ≤ 3.3 V. HIGH = ARM closed with E-stop closed; E-stop tripped → COIL_V = 0 → ARM unknown. Sensing only, no authority.

## 6. I²C buses (rise time tr = 0.8473·R·C; standard-mode limit 1000 ns)

| Bus | Rpu | Cb | tr | note |
|---|---|---|---|---|
| I2C1 INA228 (board only) | 4.7 k | 50 pF | 199 ns | 400 kHz budget tr ≤ 300 ns → use 2.2 kΩ if Cb > 50 pF |
| I2C2 TC74, 1 m cable | 4.7 k | 155 pF | 617 ns | ≈ 30 pF board + 100 pF cable + TC74/ESD |
| I2C2 TC74, 1.5 m | 4.7 k | 215 pF | 856 ns | go/no-go limit |
| I2C2 TC74, 2 m | 2.2 k | 285 pF | 531 ns | 2.2 kΩ option |
| I2C2 TC74, 3 m | 2.2 k | 400 pF | 746 ns | beyond limit |

TC74 stays on its own I²C2 (PB10/PB11) at ≤ 100 kHz; INA228 on I²C1 (PB8/PB9). Limit: ≤ 1.5 m of shielded twisted pair; beyond that or if V1 fails, stop and propose another interface (DS18B20/NTC are contingency only, not in the baseline schematic).

## 7. Power tree (wide-input buck directly to 3.3 V; **no 5 V rail**)

XDR-75-12 (set to 12.0 V) → J1 → F1 1 A fast → reverse-protection Schottky → SMBJ15A → +12V. +12V feeds (a) the coil chain E-stop → ARM → coil → Q1, (b) the buck → 3V3 → ferrite → 3V3A.

| 3V3 load | mA (typical, ⚠ datasheet values not verified) |
|---|---|
| STM32L476 @ 80 MHz + peripherals | 20.0 |
| INA228 | 1.0 |
| pull-ups/sense/ISO7721 MCU side | 11.0 |
| TC74 probe | 0.5 |
| 2 status LEDs | 6.0 |
| **total** | **38.5 (design for 150 mA)** |

Buck at 150 mA, η 0.85: input 49 mA, loss 87 mW

Buck at 150 mA, η 0.80: input 52 mA, loss 124 mW

12 V rail: coil 133 mA + buck ≈ 45 mA + sense 4 mA ≈ 182 mA of a 6.24 A supply; F1 1 A. Series Schottky drop ≈ 0.4 V → coil at ≈ 11.6 V.
Surge margin: SMBJ15A clamp 24.4 V ⚠[unverified] vs buck VIN abs max (**datasheet: LMR14006 family 40 V class vs TPS54202 28 V class — unverified**). Wide-input margin is the reason for preferring the 40 V part. Buck output → LC → 3V3; 3V3A = ferrite + 1 µF + 100 nF (VDDA, INA228); ripple at bring-up, not by calculation.

## 8. Schematic-freeze status

**BLOCKED — 30 of 30 datasheet inputs unverified.**

Unverified inputs (see `DATASHEET_VERIFICATION.md` for what to read and where it is used):

`vo610a_ctr_min_10mA`, `vo610a_ctr_min_IF_curve`, `vo610a_ctr_temp_derate`, `vo610a_ctr_aging_derate`, `vo610a_vf_at_IF`, `vo610a_vcesat`, `vo610a_led_vr_max`, `stm32_vih_frac`, `stm32_vil_frac`, `stm32_pa1_io_type`, `stm32_vrefint_tol`, `stm32_adc_tue_lsb`, `stm32_por_min`, `ina228_vos_max`, `ina228_abs_max_in`, `ina228_shunt_cal_eq`, `ina228_lsb`, `ina228_bias_current`, `ina228_pinout_vssop10`, `tvs_smbj15a_vc`, `tvs_1p5smbj48a_vc`, `relay_coil_ohm`, `relay_coil_L`, `mosfet_candidate`, `buck_candidate`, `isolator_iso7721`, `cp2102n_package`, `rsa_20_50`, `connectors`, `led_resistors_misc`

*Generated by `calc/rev2_calcs.py` from `calc/datasheet_inputs.json`; re-run after changing either.*

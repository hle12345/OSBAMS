# OSBAMS Rev.2 controller — calculations (design phase)

All numbers below are produced by `Hardware/Rev2_Controller/calc/rev2_calcs.py` (re-run it after changing any value). Items marked **[ASSUMED]** are not from a datasheet read in
this environment and must be confirmed at schematic review. Conclusions are written under each block.

## ADC divider  PACK+ -> 75k -> 75k -> ADC_TAP -> 10k -> GND ; 1k series ; 100 nF at ADC pin
```
Vpack  30.0 V -> ADC_TAP  1.875 V   (VDDA 3.3 V)
  Vpack  36.0 V -> ADC_TAP  2.250 V   (VDDA 3.3 V)
  Vpack  42.0 V -> ADC_TAP  2.625 V   (VDDA 3.3 V)
  Vpack  44.0 V -> ADC_TAP  2.750 V   (VDDA 3.3 V)
  Vpack  48.0 V -> ADC_TAP  3.000 V   (VDDA 3.3 V)
  Vpack  77.4 V -> ADC_TAP  4.838 V   (VDDA 3.3 V)
  Vpack  85.0 V -> ADC_TAP  5.312 V   (VDDA 3.3 V)
  ratio 16.0:1 ; LSB(12 bit, 3.3 V)=0.806 mV -> 12.9 mV per LSB at the pack
  divider current at 44 V: 275 uA ; power 12.1 mW ; each 75k sees 22 V, 6.5 mW
  source impedance seen by ADC (tap || series): 10375 ohm ; RC = 1.04 ms ; fc = 153 Hz
  settling to 1/2 LSB (ln 8192 = 9.0 tau): 9.3 ms  (sample period 500 ms)
  resistor ratio error: tolerance <= +/-0.20 % worst case ; TCR 25 ppm/C over +/-40 C delta (tracking) <= 0.20 %
  at 30 V: worst-case error 2.55 % = +/-0.77 V ; RSS 2.03 % = +/-0.61 V   (firmware agreement window 1.5 V)
  at 42 V: worst-case error 2.55 % = +/-1.07 V ; RSS 2.03 % = +/-0.85 V   (firmware agreement window 1.5 V)
  at 44 V: worst-case error 2.55 % = +/-1.12 V ; RSS 2.03 % = +/-0.89 V   (firmware agreement window 1.5 V)
  with VREFINT correction (vref_err -> 0.3 %): worst case 0.85 % = +/-0.37 V at 44 V
  clamp: BAT54S at ADC pin (to 3V3 / GND). Overvoltage 77.4 V (TVS clamp) -> tap 4.84 V -> clamp current 119 uA (<< 1 mA); reversed pack: GND-side clamp limits pin to -0.3 V, current 300 uA at 48 V
```
**Result:** 44 V → 2.750 V (limit 3.3 V). 12.9 mV/LSB at the pack. Worst-case error ±2.55 % (±1.12 V at 44 V) if VDDA is the reference; ±0.85 % (±0.37 V) with VREFINT correction. The firmware agreement window (1.5 V) is met in both cases, with 1.3× margin uncorrected. 77 V TVS transient → 4.84 V at the tap → BAT54S clamp passes ~0.12 mA through the 1 k series resistor, so the pin stays within 3.3 V + diode drop. Each 75 k resistor sees ≤ 22 V (0805 thin film is rated far above).

## INA228 + Bourns RSA-20-50 (2.5 mOhm, 20 A / 50 mV)
```
I  1.00 A -> Vshunt   2.50 mV ; shunt power  0.003 W
  I  7.14 A -> Vshunt  17.85 mV ; shunt power  0.127 W
  I 10.00 A -> Vshunt  25.00 mV ; shunt power  0.250 W
  I 15.00 A -> Vshunt  37.50 mV ; shunt power  0.562 W
  I 18.50 A -> Vshunt  46.25 mV ; shunt power  0.856 W
  I 20.00 A -> Vshunt  50.00 mV ; shunt power  1.000 W
  ADCRANGE=0 (+/-163.84 mV, 312.5 nV/LSB): full scale 65.5 A ; LSB 125 uA ; ADCRANGE=1 (+/-40.96 mV, 78.125 nV/LSB): full scale 16.38 A ; LSB 31.2 uA
  -> 18.5 A firmware trip needs 46.3 mV: ADCRANGE=1 would saturate at 16.4 A. Keep ADCRANGE=0 (current firmware).
  IMAX 30.0 A: CURRENT_LSB  57.2 uA ; SHUNT_CAL  1875.0 (limit 32767)
  IMAX 20.0 A: CURRENT_LSB  38.1 uA ; SHUNT_CAL  1250.0 (limit 32767)
  Kelvin input filter: 2 x 10 ohm + 100 nF differential -> fc = 80 kHz ; error from ~2 nA bias into 10 ohm = 20 nV (= 0.01 mA)
  INA228 offset (assumed +/-1 uV max, ADCRANGE=0) -> 0.40 mA ; at 10 A that is 0.0040 %
  VBUS/IN pins abs max 85 V ; 1.5SMBJ48A Vc ~77.4 V at 19.4 A [ASSUMED from datasheet table] -> margin 7.6 V
```
**Result:** ADCRANGE 0 is required: it covers the 18.5 A firmware trip (46.3 mV); ADCRANGE 1 saturates at 16.4 A. Use IMAX = 20 A (SHUNT_CAL 1250, 38 µA/LSB). Resolution and offset are far finer than the shunt tolerance, so system accuracy is set by calibration against the EDU34450A.

## Relay driver: Durakool DG57CM-5021-76-1012-R, 12 V coil
```
coil @ 10.5 V:   117 mA, 1.23 W
  coil @ 12.0 V:   133 mA, 1.60 W
  coil @ 13.8 V:   153 mA, 2.12 W
  coil @ 15.0 V:   167 mA, 2.50 W
  NOTE: XDR-75-12 output is adjustable 12-15 V: 15 V gives 2.5 W in a 12 V coil -> set to 12.0 V (open question)
  gate: GPIO peak 15.0 mA ; static gate voltage 3.23 V ; static GPIO load 0.32 mA ; tau (Ciss 1.7 nF [ASSUMED]) 0.37 us
  Q1 off with floating GPIO: leakage 100 nA x 10 kohm = 1.0 mV (Vth min 1 V)
  Q1 dissipation: Rds(on) <= 0.1 ohm [ASSUMED @3.3 V] x (0.133 A)^2 = 1.8 mW
  flyback: clamp 12.9 V << Vds 55 V ; energy (L ~0.2 H [ASSUMED]) 1.8 mJ
  fast-release option: add 27 V TVS in series with the diode -> clamp 40 V (<55 V), release ~3.3x faster
  12 V rail loading at 12 V: coil 0.133 A + 2 sense LEDs/opto 0.004 A + buck input (see power tree)
```
**Result:** 133 mA at 12 V; the gate network is safe for a 3.3 V GPIO (15 mA peak, 3.23 V static) and Q1 is OFF with a floating GPIO (1 mV vs 1 V threshold). At 15 V the coil dissipates 2.5 W, which is why the XDR output must be set to 12.0 V. Diode-only flyback clamps at ~12.9 V; a series 27 V TVS clamps at ~40 V (< 55 V Vds) and releases ~3.3× faster.

## VO610A-1 stages (CTR_min 40 % at 10 mA; assume 20 % at 1-2 mA [ASSUMED])
```
RELAY_FB  (4 x 3.6k series): R_led 14.4k, pull-up 22k, collector current needed 0.13 mA
      11.0 V -> IF  0.68 mA, Ic available  0.14 mA, margin x 1.0, R dissipation   6.7 mW
      15.0 V -> IF  0.96 mA, Ic available  0.19 mA, margin x 1.5, R dissipation  13.2 mW
      20.0 V -> IF  1.31 mA, Ic available  0.26 mA, margin x 2.0, R dissipation  24.5 mW
      30.0 V -> IF  2.00 mA, Ic available  0.40 mA, margin x 3.0, R dissipation  57.6 mW
      36.0 V -> IF  2.42 mA, Ic available  0.48 mA, margin x 3.7, R dissipation  84.1 mW
      42.0 V -> IF  2.83 mA, Ic available  0.57 mA, margin x 4.3, R dissipation 115.6 mW
      44.0 V -> IF  2.97 mA, Ic available  0.59 mA, margin x 4.5, R dissipation 127.2 mW
      77.4 V -> IF  5.29 mA, Ic available  1.06 mA, margin x 8.0, R dissipation 403.2 mW
     guaranteed ON (margin >= 1 at CTR 20 %): pack >= 10.7 V ; relay open (0 V) -> LED dark -> PC9 HIGH
     per-resistor voltage at 44 V: 11.0 V, 32 mW each (0805: 150 V, 0.125 W) ; transient 77.4 V: 5.3 mA, 101 mW each
     reverse pack (-44 V): LED reverse voltage clamped by 1N4148 to ~0.7 V (VO610A LED VR max 6 V)
  ESTOP_SENSE (1 x 5.6k): R_led 5.6k, pull-up 22k, collector current needed 0.13 mA
      10.5 V -> IF  1.66 mA, Ic available  0.33 mA, margin x 2.5, R dissipation  15.4 mW
      12.0 V -> IF  1.93 mA, Ic available  0.39 mA, margin x 2.9, R dissipation  20.8 mW
      13.8 V -> IF  2.25 mA, Ic available  0.45 mA, margin x 3.4, R dissipation  28.4 mW
      15.0 V -> IF  2.46 mA, Ic available  0.49 mA, margin x 3.7, R dissipation  34.0 mW
     E-stop open/broken wire: no LED current -> collector off -> PA0 pulled HIGH = tripped (fail-safe, matches firmware)
     input filter 10 nF: RC = 0.22 ms
```
**Result:** RELAY_FB: 4 × 3.6 k (14.4 k) with a 22 k pull-up is guaranteed ON (margin ≥ 1 at an assumed 20 % CTR) above 10.7 V, 3× margin at the 30 V minimum pack; resistor dissipation at 44 V is 32 mW each, 101 mW each at the 77 V transient (0805 = 125 mW). ESTOP_SENSE: 5.6 k with a 22 k pull-up has ≥ 2.5× margin across 10.5–15 V; open loop → LED dark → PA0 high (tripped), the firmware polarity. ARM divider 270 k/100 k gives 2.84 V at 10.5 V (> VIH 2.31 V) and is clamped above 12 V.

## ARM_SENSE divider  COIL_V -> 270k -> ARM_DIV -> 100k -> GND ; 1k series ; 100 nF ; BAT54S
```
COIL_V   0.0 V -> ARM_DIV  0.00 V
  COIL_V  10.5 V -> ARM_DIV  2.84 V
  COIL_V  12.0 V -> ARM_DIV  3.24 V
  COIL_V  13.8 V -> ARM_DIV  3.73 V
  COIL_V  15.0 V -> ARM_DIV  4.05 V
  VIH(0.7 VDD)=2.31 V, VIL(0.3 VDD)=0.99 V [ASSUMED]; 10.5 V -> 2.84 V OK ; 15 V -> 4.05 V clamped by BAT54S ; divider impedance 73 k, RC 7.3 ms
```
## I2C bus (100 kHz): rise time = 0.8473 * Rpu * Cb ; limit 1000 ns
```
Rpu 4.7k Cb 100 pF -> tr   398 ns ; Isink 0.70 mA
  Rpu 4.7k Cb 200 pF -> tr   796 ns ; Isink 0.70 mA
  Rpu 4.7k Cb 300 pF -> tr  1195 ns ; Isink 0.70 mA
  Rpu 4.7k Cb 400 pF -> tr  1593 ns ; Isink 0.70 mA
  Rpu 2.2k Cb 100 pF -> tr   186 ns ; Isink 1.50 mA
  Rpu 2.2k Cb 200 pF -> tr   373 ns ; Isink 1.50 mA
  Rpu 2.2k Cb 300 pF -> tr   559 ns ; Isink 1.50 mA
  Rpu 2.2k Cb 400 pF -> tr   746 ns ; Isink 1.50 mA
  budget: board ~30 pF + INA228 ~10 pF + MCU ~10 pF + probe cable 1 m twisted pair ~100 pF + TC74 ~5 pF => ~155 pF -> 4.7k OK; >2 m -> use 2.2k or differential I2C
```
**Result:** with a 1 m probe cable (≈ 155 pF total) 4.7 k gives 0.55–0.8 µs rise, inside the 1 µs standard-mode limit. Above ≈ 250 pF use 2.2 k; beyond ~2 m use a different remote-sensing interface.

## Power tree: XDR-75-12 (12 V) -> fuse -> Schottky -> TVS -> {coil path, 5 V buck -> 3V3 LDO}
```
3V3 loads: STM32L476 @80 MHz + peripherals 20.0 mA, INA228 1.0 mA, I2C pull-ups + sense + LEDs 8.0 mA, ISO7721 (MCU side) 3.0 mA, TC74 probe 0.5 mA, status LEDs 6.0 mA -> 38.5 mA typical, design for 150 mA
  LDO 5V->3V3 (AP2112K-3.3, 600 mA): dissipation at 150 mA = 0.26 W ; at 60 mA 0.07 W
  buck 12->5 V (TPS54202) load 160 mA @ eff 0.85: input 78 mA, loss 141 mW
  buck 12->5 V (TPS54202) load 160 mA @ eff 0.80: input 83 mA, loss 200 mW
  12 V rail total: coil 133 mA + buck 83 mA + sense 4 mA = 220 mA (XDR-75-12: 6.24 A) -> fuse 1 A fast (>=2x)
  series Schottky drop ~0.45 V at 220 mA -> rail 11.55 V (relay pull-in needs <= ~9.6 V)  P_diode 99 mW
  TPS54202 5 V feedback: Vref 0.596 V [ASSUMED]; Rb 10k, Rt 73.2k -> Vout 4.959 V
  inductor: dI = 0.35*Imax(2 A)*... ripple 0.7 A at 500 kHz -> L >= 8.3 uH -> 10 uH ; peak current 0.51 A (Isat >= 2.5 A for margin)
  5 V output ripple with 2 x 22 uF (derated 50 % -> 22 uF): 8.0 mV
  VDDA: ferrite (600 ohm @100 MHz class) + 1 uF + 100 nF from 3V3 ; 3V3 ripple from the buck rejected by LDO PSRR [ASSUMED 40 dB at 500 kHz]
```
**Result:** typical 12 V draw 0.22 A against a 6.24 A supply; 1 A fuse. LDO 0.26 W worst case. Rail after the Schottky ≈ 11.55 V (relay needs ≈ 9.6 V to pull in). The 5 V rail is internal only.

## TVS / protection
```
SMBJ15A: VRWM 15 V, Vc 24.4 V @ Ipp (datasheet table) [ASSUMED]; XDR output up to 15 V -> leakage at VRWM ok; buck Vin max 28 V > 24.4 V OK
  1.5SMBJ48A: VRWM 48 V > 44 V ceiling ; Vc ~77.4 V < INA228 85 V
```
**Result:** SMBJ15A clamp (≈ 24 V) is below the buck input limit (28 V); the 1.5SMBJ48A clamp (≈ 77 V) is below the INA228 85 V limit and above the 44 V ceiling with standoff 48 V.

## Assumptions to verify at schematic review
1. Relay coil resistance ~90 Ω / 133 mA (listing) — measure and read the Newark 10190042 datasheet for the exact suffix (V6).
2. VO610A-1 CTR at 1–2 mA (20 % assumed; datasheet guarantees 40 % at 10 mA); LED Vf 1.2 V.
3. Q1 RDS(on) at VGS = 3.3 V, Ciss 1.7 nF.
4. TPS54202 Vref 0.596 V, switching frequency, Isat of L1; AP2112K dropout/accuracy; LDO PSRR.
5. SMBJ15A and 1.5SMBJ48A clamping voltages; INA228 absolute-maximum pin ratings (85 V) and input bias current.
6. STM32 ADC: sampling time/source impedance, VIH/VIL thresholds, VDDA tolerance; CP2102N VDD regulator output; ISO7721 supply ranges.
7. 3V3 rail accuracy (2 % assumed) — removable by VREFINT correction.

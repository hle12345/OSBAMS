# Datasheet verification worklist (Rev.2 controller)

Generated from `calc/datasheet_inputs.json`. **This sandbox cannot reach any manufacturer site** (st.com, ti.com, vishay.com … return HTTP 403 from the egress policy; distributor and datasheet-mirror sites are likewise unreachable), so no value below is verified and no citation can honestly be written. Values you relayed from the manufacturer documents are recorded in the “Reported” column but stay unverified until the PDF itself is read. To close an item: upload the manufacturer PDF (or its relevant pages), the value is read, `verified` is set to true with `doc` = document number + table/figure/page, and the calculations are re-run.

The schematic is not created until the **critical** items are verified (`tests/test_pcb_release_gates.py` enforces: no `.kicad_sch` in `Hardware/Rev2_Controller/` while any `critical` input is unverified).

| # | Input | Critical | Part | What to read | Reported by you (unverified) | Verified | Document / location |
|---|---|---|---|---|---|---|---|
| 1 | `vo610a_ctr_min_10mA` | **yes** | VO610A-1 | CTR min at IF=10 mA, VCE=5 V, 25 C (guaranteed table) | — | no | — |
| 2 | `vo610a_ctr_min_IF_curve` | **yes** | VO610A-1 | guaranteed/typical CTR vs IF curve at the actual IF (1-3 mA), min-line, or a guaranteed spec at low IF | datasheet link supplied (Vishay doc 81775); values not relayed (user) | no | — |
| 3 | `vo610a_ctr_temp_derate` | **yes** | VO610A-1 | CTR vs temperature over the enclosure range (-10..+60 C assumed) | — | no | — |
| 4 | `vo610a_ctr_aging_derate` | **yes** | VO610A-1 | CTR degradation allowance over life at the chosen IF (Vishay application note / datasheet) | — | no | — |
| 5 | `vo610a_vf_at_IF` | **yes** | VO610A-1 | LED VF max at the actual IF | — | no | — |
| 6 | `vo610a_vcesat` | **yes** | VO610A-1 | VCE(sat) max at the actual IC/IF | — | no | — |
| 7 | `vo610a_led_vr_max` | no | VO610A-1 | LED reverse voltage absolute max | — | no | — |
| 8 | `stm32_vih_frac` | **yes** | STM32L476RG | VIH min (FT/FTf pin) as fraction of VDD | — | no | — |
| 9 | `stm32_vil_frac` | no | STM32L476RG | VIL max as fraction of VDD | — | no | — |
| 10 | `stm32_pa1_io_type` | **yes** | STM32L476RG | I/O structure of PA1 and PC10 (5 V tolerance, presence of a diode to VDD/VDDA, behaviour in analog mode, abs-max with VDD=0) | datasheet link supplied (270-page Rev. 11); values not relayed (user) | no | — |
| 11 | `stm32_vrefint_tol` | **yes** | STM32L476RG | VREFINT factory-calibrated accuracy (VREFINT_CAL at 3.0 V, temperature coefficient, 'VDDA correction' formula) | — | no | — |
| 12 | `stm32_adc_tue_lsb` | no | STM32L476RG | ADC total unadjusted error / offset+gain after calibration, 12-bit, source impedance limit for SMPR=92.5 | — | no | — |
| 13 | `stm32_por_min` | **yes** | STM32L476RG | power-on-reset / brown-out release threshold (min) | — | no | — |
| 14 | `ina228_vos_max` | no | INA228 | shunt input offset max (ADCRANGE=0) | — | no | — |
| 15 | `ina228_abs_max_in` | **yes** | INA228 | IN+/IN-/VBUS absolute maximum | -0.3 to +85 V common-mode range; +/-163.84 / +/-40.96 mV ranges (user, from TI page) | no | — |
| 16 | `ina228_shunt_cal_eq` | **yes** | INA228 | equation and register limits (SHUNT_CAL max 32767) | — | no | — |
| 17 | `ina228_lsb` | no | INA228 | LSB sizes | — | no | — |
| 18 | `ina228_bias_current` | no | INA228 | input bias current (IN+/IN-) | — | no | — |
| 19 | `ina228_pinout_vssop10` | **yes** | INA228 | VSSOP-10 pin table (not in the KiCad 7 library: custom symbol needed) | — | no | — |
| 20 | `tvs_smbj15a_vc` | no | SMBJ15A | VRWM, VBR, VC at IPP, leakage at VRWM | Littelfuse SMBJ series; SMBJ15A clamp 24.4 V in the series table (user) | no | — |
| 21 | `tvs_1p5smbj48a_vc` | **yes** | 1.5SMBJ48A | VRWM, VBR, VC at IPP, leakage at VRWM, IPP | manufacturer is Bourns (not Littelfuse); VRWM 48 V, max clamp 77.4 V at the specified 10/1000 us pulse current (user) | no | — |
| 22 | `relay_coil_ohm` | **yes** | DG57CM-5021-76-1012-R | coil resistance, rated coil voltage/current, pick-up/drop-out voltage, operate/release time, coil inductance, DC make/break rating at 44 V/10 A and 15 A fault | Durakool DG57CM datasheet lists DC1 loads 80 A @12 V, 60 A @36 V, 50 A @48 V; DG57CM-5021-76-1012 appears as an ordering example (user). Coil resistance/current, pick-up/drop-out, release time, inductance NOT provided | no | — |
| 23 | `relay_coil_L` | no | DG57CM-5021-76-1012-R | coil inductance (or release time with diode / diode+TVS) | — | no | — |
| 24 | `mosfet_candidate` | **yes** | SMD logic-level N-FET, >=60 V | AO3400A: VGS(th) min/max, RDS(on) at 2.5 V and 3.3-4.5 V (48 mOhm @2.5 V reported), ID, Ciss/Qg, SOA, SOT-23 pinout, and VDSS 30 V vs +12V transient (SMBJ15A 24.4 V clamp) | 30 V, SOT-23, RDS(on) max 48 mOhm at VGS=2.5 V (user); VGS(th) max, ID, Ciss, pinout, SOA NOT provided | no | — |
| 25 | `buck_candidate` | **yes** | LMR14006 family or TPS54202 | LMR14006Y: fsw (Y suffix), VREF, FB equation/resistors for 3.3 V, inductor and Isat recommendation, min on-time at 12->3.3 V, EN thresholds, abs-max VIN | 4-40 V input, 600 mA output (user); switching frequency/VREF/FB equation/Isat NOT provided | no | — |
| 26 | `isolator_iso7721` | **yes** | ISO7721 | supply range both sides, default output state, pinout, creepage | 1 forward + 1 reverse channel; NO integrated isolated power: both supplies must be provided and verified (user) | no | — |
| 27 | `cp2102n_package` | **yes** | CP2102N | choose package (KiCad 7 library holds QFN20 only; BOM candidate was QFN24), reference schematic, VREGIN/VDD behaviour, regulator output current | CP2102N datasheet link supplied; package choice not stated (user) | no | — |
| 28 | `rsa_20_50` | no | Bourns RSA-20-50 | confirm tolerance/TCR/2-3 derating and Kelvin terminal geometry from the Bourns RSA datasheet | RSA-20 = 20 A, 2.5 mOhm at 50 mV; tolerance +/-0.25 % standard; element TCR +/-15 ppm/C; continuous operation recommended <= 2/3 rated current = 13.3 A (user) | no | — |
| 29 | `connectors` | **yes** | Adam Tech EB21A-02-C, Molex 22-27-2031/2041, JST B4B-PH-K-S, GCT USB4105-GF-A, Samtec FTSH-105-01-L-DV-K | mechanical drawings (drill, pitch, keep-out), current/voltage ratings | EB21A-02-C = 5.00 mm pitch right-angle (Adam Tech 2025 catalog, via user); Mouser lists 8 A / 300 V; NO standalone mechanical drawing found: footprint must NOT be frozen from the catalog alone (user) | no | — |
| 30 | `led_resistors_misc` | no | Wurth 150080GS75000/AS75000 | VF/IF for the status LEDs | — | no | — |

## Checked from the installed KiCad 7 libraries (not datasheets)

- STM32L476RGTx: symbol + `LQFP-64_10x10mm_P0.5mm` footprint present; LQFP-64 pin numbers for every signal in the pin table read from the library (PA0=14, PA1=15, PA2=16, PA3=17, PA5=21, PA6=22, PA9=42, PA10=43, PA13=46, PA14=49, PB0=26, PB3=55, PB8=61, PB9=62, PB10=29, PB11=30, PC8=39, PC9=40, PC10=51, NRST=7, VBAT=1, VDDA=13, VSSA=12, VDDUSB=48).
- **Missing symbols (must be drawn from datasheet pin tables): INA228, ISO7721, VO610A, LMR14006, TC74.** Present: TPS54202DDC, BAT54S, D_TVS, USBLC6-2*, AP2112K (not used).
- CP2102N: the library symbol is QFN20 only; the BOM candidate is QFN24 → package decision needed.
- Footprints present: LQFP-64, VSSOP-10, SOIC-8, DIP-4_W7.62, QFN-24/QFN-20 variants, KK-254, JST PH, USB4105. **EB21A-02-C has no library footprint** (draw from the Adam Tech drawing).

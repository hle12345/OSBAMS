# Evidence register (Rev.2 RC1)

Generated from `calc/datasheet_inputs.json`. States: **VERIFIED_LOCAL** (read by the build), **USER_RELAYED_MANUFACTURER** (manufacturer data supplied by the user; PDF not opened by the build), **UNVERIFIED** (assumption/proposal). Manufacturer sites are unreachable from the build environment (HTTP 403 policy denial), so nothing has been read from a manufacturer PDF by the build. Every `critical` entry must become VERIFIED_LOCAL (by you on your machine, or by a re-run that has the PDFs) before ordering.

| # | Item | Part | Parameter | Value | Evidence | Critical | Doc/location |
|---|---|---|---|---|---|---|---|
| 1 | `vo610a_ctr_min_1mA` | VO610A-1 | CTR min at IF=1 mA, VCE=5 V | 0.13 | USER_RELAYED_MANUFACTURER | **yes** | — |
| 2 | `vo610a_ctr_typ_1mA` | VO610A-1 | CTR typ at IF=1 mA, VCE=5 V | 0.3 | USER_RELAYED_MANUFACTURER | no | — |
| 3 | `vo610a_ctr_min_10mA` | VO610A-1 | CTR min at IF=10 mA, VCE=5 V | 0.4 | USER_RELAYED_MANUFACTURER | **yes** | — |
| 4 | `vo610a_ctr_max_10mA` | VO610A-1 | CTR max at IF=10 mA, VCE=5 V | 0.8 | USER_RELAYED_MANUFACTURER | no | — |
| 5 | `vo610a_ctr_monotonic` | VO610A-1 | CTR(IF) >= CTR(1 mA) for 1 mA <= IF <= 10 mA (curve is monotonic in this range) | assumed | UNVERIFIED | **yes** | — |
| 6 | `vo610a_temp_derate` | VO610A-1 | CTR derate over temperature (design margin, not a datasheet value) | 0.8 | UNVERIFIED | no | — |
| 7 | `vo610a_aging_derate` | VO610A-1 | CTR derate for aging (design margin, not a datasheet value) | 0.8 | UNVERIFIED | no | — |
| 8 | `vo610a_vf_max` | VO610A-1 | LED forward voltage max: 1.6 V at IF = 50 mA (used as a conservative bound at the low IF of this design; VF at 1-3 mA is lower) | 1.6 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 9 | `vo610a_vcesat` | VO610A-1 | VCE(sat) max at IC ~0.1 mA | 0.4 V | UNVERIFIED | no | — |
| 10 | `vo610a_vcesat_rel` | VO610A-1 | VCE(sat) max 0.3 V at IF = 10 mA, IC = 1 mA (design uses 0.4 V at IC ~ 0.07 mA as the conservative figure) | 0.3 V | USER_RELAYED_MANUFACTURER | no | — |
| 11 | `vo610a_ratings` | VO610A-1 | VCEO 70 V, IC max 50 mA, IF max 60 mA, operating -55..+110 C | — | USER_RELAYED_MANUFACTURER | no | — |
| 12 | `vo610a_led_vr` | VO610A-1 | LED reverse voltage absolute max | 6.0 V | USER_RELAYED_MANUFACTURER | no | — |
| 13 | `vo610a_pinout` | VO610A-1 | DIP-4 pinout: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector | 1 A, 2 K, 3 E, 4 C | USER_RELAYED_MANUFACTURER | **yes** | — |
| 14 | `ina228_status` | INA228 | lifecycle / package | ACTIVE, VSSOP-10 | USER_RELAYED_MANUFACTURER | no | — |
| 15 | `ina228_supply` | INA228 | supply range | 2.7-5.5 V | USER_RELAYED_MANUFACTURER | no | — |
| 16 | `ina228_cm` | INA228 | common-mode / VBUS range | -0.3 to +85 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 17 | `ina228_ranges` | INA228 | shunt full-scale ranges | +/-163.84 mV, +/-40.96 mV | USER_RELAYED_MANUFACTURER | no | — |
| 18 | `ina228_vos` | INA228 | shunt input offset max | 1e-06 V | USER_RELAYED_MANUFACTURER | no | — |
| 19 | `ina228_pinmap` | INA228 | DGS VSSOP-10 pin map (TI table; symbol compared pin-for-pin: PASS) | 1 A1, 2 A0, 3 ALERT, 4 SDA, 5 SCL, 6 VS, 7 GND, 8 VBUS, 9 IN-, 10 IN+ | USER_RELAYED_MANUFACTURER | **yes** | — |
| 20 | `ina228_shunt_cal` | INA228 | SHUNT_CAL = 13107.2e6 x CURRENT_LSB x RSHUNT (ADCRANGE 0); RSA-20-50, IMAX 20 A -> 1250 | 13107.2e6 x CURRENT_LSB x RSHUNT (x4 for ADCRANGE=1); max 32767 | USER_RELAYED_MANUFACTURER | **yes** | — |
| 21 | `ina228_bias` | INA228 | input bias current | 2.5e-09 A | USER_RELAYED_MANUFACTURER | no | — |
| 22 | `ina228_diff_max` | INA228 | IN+ to IN- differential absolute maximum | unknown | UNVERIFIED | no | — |
| 23 | `lmr_status` | LMR14006Y | lifecycle / input / current | ACTIVE, 4-40 V, 0.6 A | USER_RELAYED_MANUFACTURER | no | — |
| 24 | `lmr_fsw` | LMR14006Y | switching frequency (Y suffix) | 2100000.0 Hz | USER_RELAYED_MANUFACTURER | no | — |
| 25 | `lmr_fsw_range` | LMR14006Y | switching frequency Y version: min 1.785 / typ 2.100 / max 2.415 MHz | — | USER_RELAYED_MANUFACTURER | no | — |
| 26 | `lmr_vref` | LMR14006Y | feedback reference | 0.765 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 27 | `lmr_vfb_range` | LMR14006Y | FB reference: min 0.747 / typ 0.765 / max 0.782 V | — | USER_RELAYED_MANUFACTURER | **yes** | — |
| 28 | `lmr_pkg` | LMR14006Y | package DDC (TSOT-6); KiCad SOT-23-6 (0.95 mm pitch) used - TI land pattern not compared | SOT-23-6 (DDC) | USER_RELAYED_MANUFACTURER | no | — |
| 29 | `lmr_pinmap` | LMR14006Y | DDC TSOT-6 pin map: 1 CB, 2 GND, 3 FB, 4 /SHDN, 5 VIN, 6 SW (symbol compared: PASS) | 1 CB, 2 GND, 3 FB, 4 /SHDN, 5 VIN, 6 SW | USER_RELAYED_MANUFACTURER | **yes** | — |
| 30 | `lmr_ton_min` | LMR14006Y | minimum turn-on time | 9.5e-08 s | USER_RELAYED_MANUFACTURER | **yes** | — |
| 31 | `lmr_limits` | LMR14006Y | VIN recommended 4-40 V, absolute max 45 V; IOUT 600 mA; current limit ~1.2 A typ; max duty (Y) ~97 % | — | USER_RELAYED_MANUFACTURER | no | — |
| 32 | `lmr_en` | LMR14006Y | EN threshold / abs max / pull-up method | — | UNVERIFIED | **yes** | — |
| 33 | `lmr_l_c` | LMR14006Y | Bourns SRN6045TA-100M: 10 uH +/-20 %, DCR 52 mohm, Irms 3.20 A, Isat 4.60 A (LMR14006Y current limit ~1.2 A typ is a separate [UR] entry) | Isat 4.6 A | VERIFIED_LOCAL | no | docs/rev2/pcb/evidence/SRN6045TA_datasheet.pdf |
| 34 | `dg57_basic` | DG57CM-5021-76-1012-R | SPST-NO, 12 V coil, ~1.6 W | as stated | USER_RELAYED_MANUFACTURER | no | — |
| 35 | `dg57_dc1` | DG57CM-5021-76-1012-R | DC1 rated load | 80 A @12 VDC, 60 A @36 VDC, 50 A @48 VDC | USER_RELAYED_MANUFACTURER | **yes** | — |
| 36 | `dg57_vmax` | DG57CM-5021-76-1012-R | maximum switching voltage | 145.0 VDC | USER_RELAYED_MANUFACTURER | no | — |
| 37 | `dg57_operate` | DG57CM-5021-76-1012-R | typical operate time | 0.007 s | USER_RELAYED_MANUFACTURER | no | — |
| 38 | `dg57_coil_ohm` | DG57CM-5021-76-1012-R | coil resistance 90 ohm +/-10 % at 23 C (code 1012) | 90.0 ohm | USER_RELAYED_MANUFACTURER | **yes** | — |
| 39 | `dg57_coil_l` | DG57CM-5021-76-1012-R | coil inductance / release time with diode | 0.2 H | UNVERIFIED | no | — |
| 40 | `dg57_pickup` | DG57CM-5021-76-1012-R | must-operate 7.2 V max @23 C; must-release 1.2 V min @23 C; max allowable coil 17.4 V @23 C / 12.5 V @85 C | 7.2 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 41 | `rsa_tol` | RSA-20-50 | tolerance | 0.0025 ratio | USER_RELAYED_MANUFACTURER | no | — |
| 42 | `rsa_tcr` | RSA-20-50 | element TCR | 1.5e-05 1/K | USER_RELAYED_MANUFACTURER | no | — |
| 43 | `rsa_derate` | RSA-20-50 | recommended continuous current <= 2/3 rated (13.3 A) | 13.3 A | USER_RELAYED_MANUFACTURER | no | — |
| 44 | `tvs48` | 1.5SMBJ48A | 1.5SMBJ48A: VRWM 48 V, VBR 53.3-58.9 V; VC max 77.4 V @ IPP 19.4 A (10/1000 us) | 77.4 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 45 | `tvs48_820` | 1.5SMBJ48A | VC max 100.6 V @ IPP 97.0 A (8/20 us) - EXCEEDS the INA228 85 V absolute maximum; see the protection analysis | 100.6 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 46 | `tvs48_ipp` | 1.5SMBJ48A | IPP 19.4 A (10/1000 us), 97.0 A (8/20 us) | 19.4 A | USER_RELAYED_MANUFACTURER | no | — |
| 47 | `rs_pulse_rating` | Panasonic ERJ-P08F47R0V / ERJ-P08F10R0V | anti-surge 1206 pulse withstand (energy for 8/20 us) - selection criterion >= 50 mJ credible-set margin; datasheet not read; failure mode is fail-safe (open) | — | UNVERIFIED | no | — |
| 48 | `tvs_leakage` | 1.5SMBJ48A | reverse leakage at 44 V (assumed <= 1 uA max, ~0.1 uA typ) - enters the Kelvin-line offset budget (first-article: 0 A shunt voltage cold/warm) | 1e-06 A | UNVERIFIED | no | — |
| 49 | `tvs15` | SMBJ15A | clamp 24.4 V in series table | 24.4 V | USER_RELAYED_MANUFACTURER | no | — |
| 50 | `iso_basic` | ISO7721 | 1 fwd + 1 rev channel, no integrated isolated power | as stated | USER_RELAYED_MANUFACTURER | no | — |
| 51 | `iso_pinmap` | ISO7721 | SOIC-8 (D) pin map, Table 5-1 / Fig. 5-4; symbol corrected in RC1.1 (earlier symbol followed the ISO7720 table) | 1 VCC1, 2 OUTA, 3 INB, 4 GND1, 5 GND2, 6 OUTB, 7 INA, 8 VCC2 | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/ISO7721_datasheet_SLLSEP3G.pdf |
| 52 | `iso_supply` | ISO7721 | supply 2.25-5.5 V each side; default output HIGH (no suffix); ISO7721DR orderable, SOIC-D 8 | 2.25-5.5 V | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/ISO7721_datasheet_SLLSEP3G.pdf |
| 53 | `cp_package` | CP2102N | package/symbol (KiCad 10 library: QFN20 symbol + SiliconLabs QFN-20 3x3 footprint) | CP2102N-A02-GQFN20 | VERIFIED_LOCAL | **yes** | — |
| 54 | `cp_pinmap` | CP2102N | QFN20 pin map: 1 GPIO.1/RS485, 2 GPIO.0/CLK, 3 GND, 4 D+, 5 D-, 6 VDD, 7 VREGIN, 8 VBUS, 9 RSTb, 10 NC, 11 SUSPENDb, 12 GND, 13 WAKEUP, 14 SUSPEND, 15 CTS, 16 RTS, 17 RXD, 18 TXD, 19 GPIO.3, 20 GPIO.2, EP GND (compared with the library symbol: PASS) | — | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/CP2102N_datasheet_rev1.5.pdf |
| 55 | `cp_vbus_div` | CP2102N | VBUS divider 22.1 k / 47.5 k (R38/R39); VBUS VIH = VIO - 0.6 V, abs max VIO + 2.5 V | 22.1 k / 47.5 k | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/CP2102N_datasheet_rev1.5.pdf |
| 56 | `cp_vdd` | CP2102N | regulator output current 100 mA total (device 9.5-13.7 mA + USB pull-up 0.23 mA + ISO7721 VCC2 ~3 mA) | 0.1 A | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/CP2102N_datasheet_rev1.5.pdf |
| 57 | `cp_rstb` | CP2102N | RSTb: 1 k pull-up to VDD recommended in all cases (added in RC1.1 as R40); 4.7 uF + 0.1 uF bypass per power pin (C22 raised from 1 uF to 4.7 uF) | 1 k / 4.7 uF | VERIFIED_LOCAL | no | docs/rev2/pcb/evidence/CP2102N_datasheet_rev1.5.pdf |
| 58 | `stm32_pins` | STM32L476RGT6 | LQFP-64 (standard, not SMPS) pin numbers for every signal: compared with the relayed list: PASS | from KiCad 10 symbol | VERIFIED_LOCAL | no | — |
| 59 | `stm32_io` | STM32L476RGT6 | PA1 (pin 15) FT_la, ADC12_IN6 - NOT 5 V tolerant while the analog switch is connected (diode to VDDA/VREF+); PC10 (pin 51) FT_l | PA1 FT_la, PC10 FT_l | USER_RELAYED_MANUFACTURER | **yes** | — |
| 60 | `stm32_vih` | STM32L476RGT6 | VIH min as fraction of VDD | 0.7 | UNVERIFIED | **yes** | — |
| 61 | `stm32_vih_ttl` | STM32L476RGT6 | TTL input levels: VIH min 2.0 V, VIL max 0.8 V; CMOS VIL max 0.3 VDD (CMOS VIH min not relayed) | 2.0 V | USER_RELAYED_MANUFACTURER | no | — |
| 62 | `stm32_vrefint` | STM32L476RGT6 | VREFINT calibration accuracy | 0.003 | UNVERIFIED | **yes** | — |
| 63 | `stm32_vrefint_range` | STM32L476RGT6 | VREFINT typ 1.212 V, 1.182-1.232 V over temperature; per-device factory calibration constant in system memory | — | USER_RELAYED_MANUFACTURER | **yes** | — |
| 64 | `stm32_por` | STM32L476RGT6 | power-on reset release threshold (min) | 1.6 V | UNVERIFIED | **yes** | — |
| 65 | `stm32_tue` | STM32L476RGT6 | ADC total unadjusted error (LSB) | 4.0 | UNVERIFIED | no | — |
| 66 | `q_vdss` | IRLML0060TRPBF | VDSS | 60.0 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 67 | `q_vth` | IRLML0060TRPBF | VGS(th) 1.0-2.5 V (max used) | 2.5 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 68 | `q_rds` | IRLML0060TRPBF | RDS(on) at VGS = 3.3 V (not specified: conservative placeholder) | 0.5 ohm | UNVERIFIED | **yes** | — |
| 69 | `q_rds_4v5` | IRLML0060TRPBF | RDS(on) max 116 mohm @ VGS 4.5 V, 92 mohm @ 10 V; ID 2.7 A @10 V; VGS +/-16 V; RthJA ~100 C/W (NOT guaranteed at 3.3 V) | 0.116 ohm | USER_RELAYED_MANUFACTURER | no | — |
| 70 | `q_curves` | IRLML0060TRPBF | Infineon typical output curves at VGS 3.0 and 3.3 V make the ~0.17 A coil load plausible; RDS(on) is NOT guaranteed at 3.3 V -> first-article VDS / coil-current measurement is the validation item | — | USER_RELAYED_MANUFACTURER | no | — |
| 71 | `q_pinout` | IRLML0060TRPBF | SOT-23 (Micro3) pinout 1 G, 2 S, 3 D (netlist compared: PASS) | 1 G, 2 S, 3 D | USER_RELAYED_MANUFACTURER | **yes** | — |
| 72 | `bat54s_ir` | BAT54S | reverse leakage at ~3 V | 1e-07 A | UNVERIFIED | no | — |
| 73 | `bat54s_vf` | BAT54S | forward voltage at 0.1 mA | 0.25 V | UNVERIFIED | no | — |
| 74 | `eb21a_catalog` | EB21A-02-C | 5.00 mm pitch, right-angle, 8 A / 300 V | 5.00 mm pitch, 8 A, 300 V (drawing spec block) | VERIFIED_LOCAL | no | docs/rev2/pcb/evidence/EB21A-XX-C_drawing_revB.pdf |
| 75 | `eb21a_drawing` | EB21A-02-C | PCB hole, pin, body and pin-offset dimensions (footprint EB21A-02-C) | hole 1.30 mm; pins 0.90x0.60, tail 4.00; body 10.60 W x 8.50 D x 10.20 H; pin1 2.50 / pin2 3.10 from body ends; pins 4.00 from back, 4.50 from wire-entry face | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/EB21A-XX-C_drawing_revB.pdf |
| 76 | `conn_pitch` | Molex 22-27-2031/2041, JST B4B-PH-K-S, Samtec FTSH-105-01-L-DV-K, GCT USB4105-GF-A | pitch/pin count vs KiCad stock footprints: KK 2.54 mm x3/x4, PH 2.00 mm x4 (A = 6.0 mm), FTSH 1.27 mm 2x5, USB4105 16P horizontal: PASS (pitch and pin count only) | — | USER_RELAYED_MANUFACTURER | no | — |
| 77 | `conn_footprints` | Molex KK/JST PH/GCT USB4105/Samtec FTSH | connector footprints are KiCad stock; pad/drill/shield/CC/pin-1/tail geometry NOT compared with the manufacturer drawings (only pitch and pin count) | KiCad 10 library | UNVERIFIED | **yes** | — |
| 78 | `tc74_pinmap` | TC74A5-3.3VAT | TO-220-5 pin map: 1 NC, 2 SDA, 3 GND, 4 SCLK, 5 VDD; tab = pin 3 (GND); supply 2.7-5.5 V; +/-2 C (25-85 C); symbol compared: PASS | — | USER_RELAYED_MANUFACTURER | **yes** | — |

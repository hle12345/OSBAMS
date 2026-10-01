# Evidence register (Rev.2 RC1)

Generated from `calc/datasheet_inputs.json`. States: **VERIFIED_LOCAL** (read by the build), **USER_RELAYED_MANUFACTURER** (manufacturer data supplied by the user; PDF not opened by the build), **UNVERIFIED** (assumption/proposal). Manufacturer sites are unreachable from the build environment (HTTP 403 policy denial), so nothing has been read from a manufacturer PDF by the build. Every `critical` entry must become VERIFIED_LOCAL (by you on your machine, or by a re-run that has the PDFs) before ordering.

| # | Item | Part | Parameter | Value | Evidence | Critical | Doc/location |
|---|---|---|---|---|---|---|---|
| 1 | `vo610a_ctr_min_1mA` | VO610A-1 | CTR min at IF=1 mA, VCE=5 V | 0.13 | USER_RELAYED_MANUFACTURER | **yes** | — |
| 2 | `vo610a_ctr_typ_1mA` | VO610A-1 | CTR typ at IF=1 mA, VCE=5 V | 0.3 | USER_RELAYED_MANUFACTURER | no | — |
| 3 | `vo610a_ctr_min_10mA` | VO610A-1 | CTR min at IF=10 mA, VCE=5 V | 0.4 | USER_RELAYED_MANUFACTURER | **yes** | — |
| 4 | `vo610a_ctr_max_10mA` | VO610A-1 | CTR max at IF=10 mA, VCE=5 V | 0.8 | USER_RELAYED_MANUFACTURER | no | — |
| 5 | `vo610a_ctr_monotonic` | VO610A-1 | CTR(IF) >= CTR(1 mA) for 1 mA <= IF <= 10 mA (curve is monotonic in this range) | assumed | UNVERIFIED | **yes** | — |
| 6 | `vo610a_temp_derate` | VO610A-1 | CTR derate over temperature (design margin, not a datasheet value) | 0.8 | UNVERIFIED | **yes** | — |
| 7 | `vo610a_aging_derate` | VO610A-1 | CTR derate for aging (design margin, not a datasheet value) | 0.8 | UNVERIFIED | **yes** | — |
| 8 | `vo610a_vf_max` | VO610A-1 | LED forward voltage max at IF ~1.5-3 mA | 1.6 V | UNVERIFIED | **yes** | — |
| 9 | `vo610a_vcesat` | VO610A-1 | VCE(sat) max at IC ~0.1 mA | 0.4 V | UNVERIFIED | no | — |
| 10 | `vo610a_led_vr` | VO610A-1 | LED reverse voltage absolute max | 6.0 V | UNVERIFIED | no | — |
| 11 | `vo610a_pinout` | VO610A-1 | DIP-4 pinout 1 anode, 2 cathode, 3 emitter, 4 collector | standard 4-pin opto | UNVERIFIED | **yes** | — |
| 12 | `ina228_status` | INA228 | lifecycle / package | ACTIVE, VSSOP-10 | USER_RELAYED_MANUFACTURER | no | — |
| 13 | `ina228_supply` | INA228 | supply range | 2.7-5.5 V | USER_RELAYED_MANUFACTURER | no | — |
| 14 | `ina228_cm` | INA228 | common-mode / VBUS range | -0.3 to +85 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 15 | `ina228_ranges` | INA228 | shunt full-scale ranges | +/-163.84 mV, +/-40.96 mV | USER_RELAYED_MANUFACTURER | no | — |
| 16 | `ina228_vos` | INA228 | shunt input offset max | 1e-06 V | USER_RELAYED_MANUFACTURER | no | — |
| 17 | `ina228_pinmap` | INA228 | VSSOP-10 pin map (INA226-family analogy used in the symbol) | 1 A1, 2 A0, 3 ALERT, 4 SDA, 5 SCL, 6 VS, 7 GND, 8 VBUS, 9 IN-, 10 IN+ | UNVERIFIED | **yes** | — |
| 18 | `ina228_shunt_cal` | INA228 | SHUNT_CAL equation and limits | 13107.2e6 x CURRENT_LSB x RSHUNT (x4 for ADCRANGE=1); max 32767 | UNVERIFIED | **yes** | — |
| 19 | `ina228_bias` | INA228 | input bias current | 2e-09 A | UNVERIFIED | no | — |
| 20 | `ina228_diff_max` | INA228 | IN+ to IN- differential absolute maximum | unknown | UNVERIFIED | no | — |
| 21 | `lmr_status` | LMR14006Y | lifecycle / input / current | ACTIVE, 4-40 V, 0.6 A | USER_RELAYED_MANUFACTURER | no | — |
| 22 | `lmr_fsw` | LMR14006Y | switching frequency (Y suffix) | 2100000.0 Hz | USER_RELAYED_MANUFACTURER | no | — |
| 23 | `lmr_vref` | LMR14006Y | feedback reference | 0.765 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 24 | `lmr_pkg` | LMR14006Y | package | SOT-23-6 (DDC) | USER_RELAYED_MANUFACTURER | no | — |
| 25 | `lmr_pinmap` | LMR14006Y | pin map (LMR16006YQ library analogy) | 1 CB, 2 GND, 3 FB, 4 EN, 5 VIN, 6 SW | UNVERIFIED | **yes** | — |
| 26 | `lmr_ton_min` | LMR14006Y | minimum controllable on-time | — | UNVERIFIED | **yes** | — |
| 27 | `lmr_en` | LMR14006Y | EN threshold / abs max / pull-up method | — | UNVERIFIED | **yes** | — |
| 28 | `lmr_l_c` | LMR14006Y | recommended inductor and Cin/Cout, current limit | — | UNVERIFIED | **yes** | — |
| 29 | `dg57_basic` | DG57CM-5021-76-1012-R | SPST-NO, 12 V coil, ~1.6 W | as stated | USER_RELAYED_MANUFACTURER | no | — |
| 30 | `dg57_dc1` | DG57CM-5021-76-1012-R | DC1 rated load | 80 A @12 VDC, 60 A @36 VDC, 50 A @48 VDC | USER_RELAYED_MANUFACTURER | **yes** | — |
| 31 | `dg57_vmax` | DG57CM-5021-76-1012-R | maximum switching voltage | 145.0 VDC | USER_RELAYED_MANUFACTURER | no | — |
| 32 | `dg57_operate` | DG57CM-5021-76-1012-R | typical operate time | 0.007 s | USER_RELAYED_MANUFACTURER | no | — |
| 33 | `dg57_coil_ohm` | DG57CM-5021-76-1012-R | coil resistance (1.6 W at 12 V implies 90 ohm) | 90.0 ohm | UNVERIFIED | **yes** | — |
| 34 | `dg57_coil_l` | DG57CM-5021-76-1012-R | coil inductance / release time with diode | 0.2 H | UNVERIFIED | no | — |
| 35 | `dg57_pickup` | DG57CM-5021-76-1012-R | pick-up / drop-out voltage | — | UNVERIFIED | **yes** | — |
| 36 | `rsa_tol` | RSA-20-50 | tolerance | 0.0025 ratio | USER_RELAYED_MANUFACTURER | no | — |
| 37 | `rsa_tcr` | RSA-20-50 | element TCR | 1.5e-05 1/K | USER_RELAYED_MANUFACTURER | no | — |
| 38 | `rsa_derate` | RSA-20-50 | recommended continuous current <= 2/3 rated (13.3 A) | 13.3 A | USER_RELAYED_MANUFACTURER | no | — |
| 39 | `tvs48` | 1.5SMBJ48A | standoff 48 V, max clamp 77.4 V | 77.4 V | USER_RELAYED_MANUFACTURER | **yes** | — |
| 40 | `tvs15` | SMBJ15A | clamp 24.4 V in series table | 24.4 V | USER_RELAYED_MANUFACTURER | no | — |
| 41 | `iso_basic` | ISO7721 | 1 fwd + 1 rev channel, no integrated isolated power | as stated | USER_RELAYED_MANUFACTURER | no | — |
| 42 | `iso_pinmap` | ISO7721 | SOIC-8 pin map | 1 VCC1, 2 INA, 3 OUTB, 4 GND1, 5 GND2, 6 INB, 7 OUTA, 8 VCC2 | UNVERIFIED | **yes** | — |
| 43 | `iso_supply` | ISO7721 | supply range both sides, ICC, default output state | — | UNVERIFIED | **yes** | — |
| 44 | `cp_package` | CP2102N | package/symbol (KiCad 10 library: QFN20 symbol + SiliconLabs QFN-20 3x3 footprint) | CP2102N-A02-GQFN20 | VERIFIED_LOCAL | **yes** | — |
| 45 | `cp_vdd` | CP2102N | VDD regulator output current capability, VBUS pin connection method, reference design | — | UNVERIFIED | **yes** | — |
| 46 | `stm32_pins` | STM32L476RGT6 | LQFP-64 pin numbers for every signal | from KiCad 10 symbol | VERIFIED_LOCAL | no | — |
| 47 | `stm32_io` | STM32L476RGT6 | I/O structure of PA1 / PC10 (5 V tolerance, diode to VDD, behaviour with VDD=0) | — | UNVERIFIED | **yes** | — |
| 48 | `stm32_vih` | STM32L476RGT6 | VIH min as fraction of VDD | 0.7 | UNVERIFIED | **yes** | — |
| 49 | `stm32_vrefint` | STM32L476RGT6 | VREFINT calibration accuracy | 0.003 | UNVERIFIED | **yes** | — |
| 50 | `stm32_por` | STM32L476RGT6 | power-on reset release threshold (min) | 1.6 V | UNVERIFIED | **yes** | — |
| 51 | `stm32_tue` | STM32L476RGT6 | ADC total unadjusted error (LSB) | 4.0 | UNVERIFIED | no | — |
| 52 | `q_vdss` | IRLML0060TRPBF | VDSS | 60.0 V | UNVERIFIED | **yes** | — |
| 53 | `q_vth` | IRLML0060TRPBF | VGS(th) max | 2.5 V | UNVERIFIED | **yes** | — |
| 54 | `q_rds` | IRLML0060TRPBF | RDS(on) at VGS = 3.3 V (not specified: conservative placeholder) | 0.5 ohm | UNVERIFIED | **yes** | — |
| 55 | `q_pinout` | IRLML0060TRPBF | SOT-23 pinout 1 G, 2 S, 3 D | as KiCad Transistor_FET:IRLML0030 symbol | UNVERIFIED | **yes** | — |
| 56 | `bat54s_ir` | BAT54S | reverse leakage at ~3 V | 1e-07 A | UNVERIFIED | no | — |
| 57 | `bat54s_vf` | BAT54S | forward voltage at 0.1 mA | 0.25 V | UNVERIFIED | no | — |
| 58 | `eb21a_catalog` | EB21A-02-C | 5.00 mm pitch, right-angle, 8 A / 300 V | 5.00 mm pitch, 8 A, 300 V (drawing spec block) | VERIFIED_LOCAL | no | docs/rev2/pcb/evidence/EB21A-XX-C_drawing_revB.pdf |
| 59 | `eb21a_drawing` | EB21A-02-C | PCB hole, pin, body and pin-offset dimensions (footprint EB21A-02-C) | hole 1.30 mm; pins 0.90x0.60, tail 4.00; body 10.60 W x 8.50 D x 10.20 H; pin1 2.50 / pin2 3.10 from body ends; pins 4.00 from back, 4.50 from wire-entry face | VERIFIED_LOCAL | **yes** | docs/rev2/pcb/evidence/EB21A-XX-C_drawing_revB.pdf |
| 60 | `conn_footprints` | Molex KK/JST PH/GCT USB4105/Samtec FTSH | footprint = KiCad stock; MPN-to-footprint match not checked against drawings | KiCad 10 library | UNVERIFIED | **yes** | — |

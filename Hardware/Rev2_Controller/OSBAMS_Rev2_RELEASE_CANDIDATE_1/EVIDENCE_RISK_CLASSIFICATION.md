# Evidence risk classification — RC1.2e (2026-10-01)

Every register entry that is **not VERIFIED_LOCAL** is classified by what a wrong value could actually cause. `USER_RELAYED_MANUFACTURER` values are used as authoritative for electrical checks; the PDFs have not been read by the build. Entries read locally (ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing, KiCad library facts) are not listed.

59 entries are not VERIFIED_LOCAL: WRONG_PINOUT: 4, EXCEEDED_ABS_MAX: 12, WRONG_FOOTPRINT: 5, UNSAFE_PROTECTION: 4, FIRST_ARTICLE / INFORMATIONAL: 34.


## Could cause a WRONG PINOUT (supply the datasheet to move these to VERIFIED_LOCAL — highest priority)

| id | part | parameter | evidence | note |
|---|---|---|---|---|
| `vo610a_pinout` | VO610A-1 | DIP-4 pinout: 1 LED anode, 2 LED cathode, 3 emitter, 4 collector | USER_RELAYED_MANUFACTURER | DIP-4 opto: wrong pin order would make both status inputs dead; relayed pinout matches the netlist. |
| `lmr_pinmap` | LMR14006Y | DDC TSOT-6 pin map: 1 CB, 2 GND, 3 FB, 4 /SHDN, 5 VIN, 6 SW (symbol compared: PASS) | USER_RELAYED_MANUFACTURER | relayed table matches; a mismatch would stop the 3.3 V rail. |
| `q_pinout` | IRLML0060TRPBF | SOT-23 (Micro3) pinout 1 G, 2 S, 3 D (netlist compared: PASS) | USER_RELAYED_MANUFACTURER | relayed 1 G / 2 S / 3 D matches; a mismatch would leave the relay always off/on. |
| `tc74_pinmap` | TC74A5-3.3VAT | TO-220-5 pin map: 1 NC, 2 SDA, 3 GND, 4 SCLK, 5 VDD; tab = pin 3 (GND); supply 2.7-5.5 V; +/-2 C (25-85 C); sy | USER_RELAYED_MANUFACTURER | relayed table matches (probe board). |

## Could cause an EXCEEDED ABSOLUTE MAXIMUM

| id | part | parameter | evidence | note |
|---|---|---|---|---|
| `vo610a_ratings` | VO610A-1 | VCEO 70 V, IC max 50 mA, IF max 60 mA, operating -55..+110 C | USER_RELAYED_MANUFACTURER | VCEO 70 V vs the 3.3 V pull-up: large margin. |
| `vo610a_led_vr` | VO610A-1 | LED reverse voltage absolute max | USER_RELAYED_MANUFACTURER | 1N4148 limits the LED reverse voltage to ~0.7 V. |
| `lmr_limits` | LMR14006Y | VIN recommended 4-40 V, absolute max 45 V; IOUT 600 mA; current limit ~1.2 A typ; max duty (Y) ~97 % | USER_RELAYED_MANUFACTURER | VIN abs max 45 V vs SMBJ15A clamp 24.4 V (relayed). |
| `lmr_en` | LMR14006Y | EN threshold / abs max / pull-up method | UNVERIFIED | SHDN threshold/abs max not relayed; SHDN is pulled to +12V through 100 k (limits current); confirm the pin allows +12 V through 100 k. |
| `dg57_vmax` | DG57CM-5021-76-1012-R | maximum switching voltage | USER_RELAYED_MANUFACTURER | 145 VDC switching vs 44 V ceiling. |
| `dg57_pickup` | DG57CM-5021-76-1012-R | must-operate 7.2 V max @23 C; must-release 1.2 V min @23 C; max allowable coil 17.4 V @23 C / 12.5 V @85 C | USER_RELAYED_MANUFACTURER | coil max allowable 12.5 V at 85 C vs the XDR set to 12.0 V: needs the XDR set/verified at 12.0 V (first article). |
| `tvs15` | SMBJ15A | clamp 24.4 V in series table | USER_RELAYED_MANUFACTURER | SMBJ15A clamp vs LMR14006 VIN abs max 45 V (relayed). |
| `stm32_io` | STM32L476RGT6 | PA1 (pin 15) FT_la, ADC12_IN6 - NOT 5 V tolerant while the analog switch is connected (diode to VDDA/VREF+); P | USER_RELAYED_MANUFACTURER | PA1 not 5 V tolerant while the ADC switch is connected: the clamp network protects it (relayed structure). |
| `stm32_vrefint_range` | STM32L476RGT6 | VREFINT typ 1.212 V, 1.182-1.232 V over temperature; per-device factory calibration constant in system memory | USER_RELAYED_MANUFACTURER | firmware must use the factory calibration constant. |
| `q_vdss` | IRLML0060TRPBF | VDSS | USER_RELAYED_MANUFACTURER | 60 V vs 12 V coil + flyback: large margin. |
| `bat54s_ir` | BAT54S | reverse leakage at ~3 V | UNVERIFIED | diode leakage/forward voltage enter the PA1 back-feed analysis; the R4 bleeder guards the unknown. |
| `bat54s_vf` | BAT54S | forward voltage at 0.1 mA | UNVERIFIED | same. |

## Could cause a WRONG FOOTPRINT

| id | part | parameter | evidence | note |
|---|---|---|---|---|
| `lmr_pkg` | LMR14006Y | package DDC (TSOT-6); KiCad SOT-23-6 (0.95 mm pitch) used - TI land pattern not compared | USER_RELAYED_MANUFACTURER | KiCad SOT-23-6 vs the TI DDC land pattern (pitch/pin numbering match; land pattern not compared). |
| `conn_pitch` | Molex 22-27-2031/2041, JST B4B-PH-K-S, Samtec FTSH-105-01-L-DV-K, GCT USB4105-GF-A | pitch/pin count vs KiCad stock footprints: KK 2.54 mm x3/x4, PH 2.00 mm x4 (A = 6.0 mm), FTSH 1.27 mm 2x5, USB | USER_RELAYED_MANUFACTURER | pitch and pin count match. |
| `conn_samtec_key` | Samtec FTSH-105-01-L-DV-K (J9) | Samtec -K keying: which long side of the shroud carries the key slot (pin-1 row side vs pin-2 row side) is not | UNVERIFIED | J9 land pattern is verified; which shroud side carries the -K key slot is not resolved by the drawings -> check on the part (F6). |
| `conn_molex` | Molex 22-27-2031 / 22-27-2041 (J5, J6) | Molex pad/drill/outline/pin-1 geometry for 22-27-2031 (J5) and 22-27-2041 (J6): the 022272041 drawing supplied | UNVERIFIED | 022272041 drawing is a 3D isometric without dimensions, 022272031 not supplied -> J5/J6 pad/drill/outline/ramp side OPEN. |
| `conn_footprints` | Molex KK/JST PH/GCT USB4105/Samtec FTSH | connector footprints: J7 (JST) and J8 (GCT) VERIFIED against the drawings; J9 (Samtec) part number/pitch/tail  | UNVERIFIED | J7, J8 and J9 verified against manufacturer drawings; J5/J6 (Molex) still OPEN. |

## Protection-related (analysis closed in `REV2_CALCULATIONS.md` using the relayed numbers)

| id | part | parameter | evidence | note |
|---|---|---|---|---|
| `ina228_status` | INA228 | lifecycle / package | USER_RELAYED_MANUFACTURER | informational. |
| `dg57_dc1` | DG57CM-5021-76-1012-R | DC1 rated load | USER_RELAYED_MANUFACTURER | relay DC rating >> the 10 A / 44 V ceiling. |
| `rs_pulse_rating` | Panasonic ERJ-P08F47R0V / ERJ-P08F10R0V | ERJP08 single-pulse / repetitive-pulse capability: NOT PUBLISHED. AOA0000C331 (read) gives ratings (0.66 W, 50 | UNVERIFIED | Not published: AOA0000C331 and the catalog (both read) give DC ratings and the +/-3 kV 150 pF ESD test only. ERJP08 catalog row (read locally): 500 V limiting / 1000 V overload (a relayed 125/500 V does not match; 125 is the terminal temperature in C); modeled 8 kV ESD = about 1.3 kV across R41, above the 1000 V overload rating -> ESD_PROTECTION_OPEN. |
| `esd_connector` | J5/J6 connectors | ESD_FIRST_ARTICLE_CONDITIONAL (RC-A = YES confirmed: J5/J6 internal, permanently mated; reopen and require the | UNVERIFIED | ESD at J5/J6 cannot be shown by simulation; R41-R43 sit upstream of the TVS -> first-article test F1, connector-level TVS = RC1.3 fallback. |

## First-article measurements / design margins / informational (cannot cause a wrong pinout, absolute-maximum violation, wrong footprint or unsafe protection)

| id | part | parameter | evidence | note |
|---|---|---|---|---|
| `vo610a_ctr_min_1mA` | VO610A-1 | CTR min at IF=1 mA, VCE=5 V | USER_RELAYED_MANUFACTURER |  |
| `vo610a_ctr_typ_1mA` | VO610A-1 | CTR typ at IF=1 mA, VCE=5 V | USER_RELAYED_MANUFACTURER |  |
| `vo610a_ctr_min_10mA` | VO610A-1 | CTR min at IF=10 mA, VCE=5 V | USER_RELAYED_MANUFACTURER |  |
| `vo610a_ctr_max_10mA` | VO610A-1 | CTR max at IF=10 mA, VCE=5 V | USER_RELAYED_MANUFACTURER |  |
| `vo610a_ctr_monotonic` | VO610A-1 | CTR(IF) >= CTR(1 mA) for 1 mA <= IF <= 10 mA (curve is monotonic in this range) | UNVERIFIED |  |
| `vo610a_temp_derate` | VO610A-1 | CTR derate over temperature (design margin, not a datasheet value) | UNVERIFIED |  |
| `vo610a_aging_derate` | VO610A-1 | CTR derate for aging (design margin, not a datasheet value) | UNVERIFIED |  |
| `vo610a_vf_max` | VO610A-1 | LED forward voltage max: 1.6 V at IF = 50 mA (used as a conservative bound at the low IF of this design; VF at | USER_RELAYED_MANUFACTURER |  |
| `vo610a_vcesat` | VO610A-1 | VCE(sat) max at IC ~0.1 mA | UNVERIFIED |  |
| `vo610a_vcesat_rel` | VO610A-1 | VCE(sat) max 0.3 V at IF = 10 mA, IC = 1 mA (design uses 0.4 V at IC ~ 0.07 mA as the conservative figure) | USER_RELAYED_MANUFACTURER |  |
| `lmr_status` | LMR14006Y | lifecycle / input / current | USER_RELAYED_MANUFACTURER |  |
| `lmr_fsw` | LMR14006Y | switching frequency (Y suffix) | USER_RELAYED_MANUFACTURER |  |
| `lmr_fsw_range` | LMR14006Y | switching frequency Y version: min 1.785 / typ 2.100 / max 2.415 MHz | USER_RELAYED_MANUFACTURER |  |
| `lmr_vref` | LMR14006Y | feedback reference | USER_RELAYED_MANUFACTURER |  |
| `lmr_vfb_range` | LMR14006Y | FB reference: min 0.747 / typ 0.765 / max 0.782 V | USER_RELAYED_MANUFACTURER |  |
| `lmr_ton_min` | LMR14006Y | minimum turn-on time | USER_RELAYED_MANUFACTURER |  |
| `dg57_basic` | DG57CM-5021-76-1012-R | SPST-NO, 12 V coil, ~1.6 W | USER_RELAYED_MANUFACTURER |  |
| `dg57_operate` | DG57CM-5021-76-1012-R | typical operate time | USER_RELAYED_MANUFACTURER |  |
| `dg57_coil_ohm` | DG57CM-5021-76-1012-R | coil resistance 90 ohm +/-10 % at 23 C (code 1012) | USER_RELAYED_MANUFACTURER |  |
| `dg57_coil_l` | DG57CM-5021-76-1012-R | coil inductance / release time with diode | UNVERIFIED |  |
| `rsa_tol` | RSA-20-50 | tolerance | USER_RELAYED_MANUFACTURER |  |
| `rsa_tcr` | RSA-20-50 | element TCR | USER_RELAYED_MANUFACTURER |  |
| `rsa_derate` | RSA-20-50 | recommended continuous current <= 2/3 rated (13.3 A) | USER_RELAYED_MANUFACTURER |  |
| `tvs_leakage_temp` | 1.5SMBJ48A | reverse leakage vs temperature and vs voltage below VRWM: NOT specified in the datasheet (only the 25 C maximu | UNVERIFIED | Bourns gives IR <= 1.0 uA at 48 V/25 C only; leakage vs temperature/voltage is unspecified: sets the hot Kelvin-line offset (4 mA per uA) and the PACK_INA error (47 uV per uA) -> first-article measurement. |
| `iso_basic` | ISO7721 | 1 fwd + 1 rev channel, no integrated isolated power | USER_RELAYED_MANUFACTURER |  |
| `stm32_vih` | STM32L476RGT6 | VIH min as fraction of VDD | UNVERIFIED |  |
| `stm32_vih_ttl` | STM32L476RGT6 | TTL input levels: VIH min 2.0 V, VIL max 0.8 V; CMOS VIL max 0.3 VDD (CMOS VIH min not relayed) | USER_RELAYED_MANUFACTURER |  |
| `stm32_vrefint` | STM32L476RGT6 | VREFINT calibration accuracy | UNVERIFIED |  |
| `stm32_por` | STM32L476RGT6 | power-on reset release threshold (min) | UNVERIFIED |  |
| `stm32_tue` | STM32L476RGT6 | ADC total unadjusted error (LSB) | UNVERIFIED |  |
| `q_vth` | IRLML0060TRPBF | VGS(th) 1.0-2.5 V (max used) | USER_RELAYED_MANUFACTURER |  |
| `q_rds` | IRLML0060TRPBF | RDS(on) at VGS = 3.3 V (not specified: conservative placeholder) | UNVERIFIED |  |
| `q_rds_4v5` | IRLML0060TRPBF | RDS(on) max 116 mohm @ VGS 4.5 V, 92 mohm @ 10 V; ID 2.7 A @10 V; VGS +/-16 V; RthJA ~100 C/W (NOT guaranteed  | USER_RELAYED_MANUFACTURER |  |
| `q_curves` | IRLML0060TRPBF | Infineon typical output curves at VGS 3.0 and 3.3 V make the ~0.17 A coil load plausible; RDS(on) is NOT guara | USER_RELAYED_MANUFACTURER |  |

## Mandatory first-article measurements (not PCBWay blockers)
1. **Relay driver (IRLML0060, K1 coil):** VGS at the gate, VDS while energized, coil current (expect ≈ 121–148 mA at 12.0 V), MOSFET case temperature; XDR output set and verified at 12.0 V (coil limit 12.5 V at 85 °C).
2. **3V3 / 3V3_A:** ripple and level with the real load, and during an input step to 12.5 V; confirm no pulse-skipping instability at 12.0 V.
3. **INA228 chain:** shunt voltage at 0 A (leakage of the TVS diodes through R42/R43, cold and warm), VBUS vs the EDU34450A, scope on IN+/IN− during sense-harness hot-plug.
4. **PA1 ADC protection:** pack powered / controller unpowered, reversed pack, injection test; read VREFINT calibration.
5. **Status networks:** ESTOP_SENSE and RELAY_FB thresholds at 10.5–15 V and 24–44 V; ARM_SENSE.
6. **CP2102N / ISO7721:** USB enumeration, VBUS detect (reference divider: threshold 3.96 V typical, 4.40 V worst case), UART echo through the isolator, 3V3_HOST rail current.


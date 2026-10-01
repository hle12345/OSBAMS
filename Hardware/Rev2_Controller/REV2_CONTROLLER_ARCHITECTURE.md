# OSBAMS Rev.2 Controller — architecture (rev D, matches RELEASE CANDIDATE 1)

**Status: RC1 is a complete design package for REVIEW. It is NOT authorization to fabricate.** The schematic, PCB layout and outputs live in `OSBAMS_Rev2_RELEASE_CANDIDATE_1/`; fabrication remains gated by manufacturer-document verification (`DATASHEET_VERIFICATION.md`). Rev.1 is reference only (`legacy/reference/rev1_kicad/`).

Evidence states used everywhere: **VERIFIED_LOCAL** (read by the build) · **USER_RELAYED_MANUFACTURER** (manufacturer data supplied by the user; PDF not opened by the build; tag [UR]) · **UNVERIFIED** (assumption/proposal; tag [UV]).

Envelope: Li-ion scooter packs ~30–42 V, 44 V ceiling, ≤ 10 A operating ceiling, 15 A external fuse, Bourns RSA-20-50 shunt, XT60 external, Agilent 6060B external load, 300 W ceiling. **Main battery discharge current never flows through this PCB.**

```
Battery → XT60 → 15 A fuse → manual disconnect → Durakool K1 main contacts → RSA-20-50 → 6060B → Battery−     (external)
12 V → F1 → D2 → +12V → E-stop NC (J2) → ARM (J3) → K1 coil (J4) → Q1 → GND                                (this PCB, ≈ 0.13 A)
Pi requests actions; STM32 authorizes; E-stop and ARM physically override both.
```

## 1. Decisions (closed)
| Topic | Decision |
|---|---|
| MCU | STM32L476RGT6 directly on the board; HSI16 → PLL 80 MHz (no crystal, no LSE, no native USB); NUCLEO-L476RG kept intact as ST-LINK/fallback |
| Measurement | bare INA228AIDGSR (VSSOP-10/MSOP footprint), ADCRANGE 0, IMAX 20 A → SHUNT_CAL 1250; spare Adafruit INA228 modules = reference only |
| ADC cross-check | 75k+75k / 10k → PA1, 0.1 %/25 ppm thin film, VREFINT correction, **no-back-feed clamp (VCLAMP)** |
| Power | LMR14006Y wide-input buck straight to 3.3 V, 3V3_A via ferrite; **no 5 V rail**; Pi/display on an external 5 V supply |
| Relay driver | IRLML0060TRPBF (60 V SOT-23) + 220 Ω + 10 kΩ pull-down, plain S1M flyback; no fast-release TVS |
| E-stop / ARM | Eaton M22-PV-K02 and C&K T102SHZQE are series elements in the 12 V coil path; ESTOP_SENSE opto (PA0, LOW = healthy), ARM_SENSE divider (PC10, HIGH = armed, status only) |
| Relay feedback | K1 load-side voltage → 3 × 4.7 kΩ → VO610A-1 → PC9 (active low), sized from the user-relayed CTR guarantee |
| Temperature | TC74A5-3.3VAT on a separate remote probe PCB, own I²C2 (PB10/PB11) ≤ 100 kHz, cable ≤ 1.5 m |
| Host | USART2 → ISO7721 → CP2102N-A02-GQFN20 → USB-C → Pi 5; GND and GND_HOST never joined |

## 2. Pin assignment (LQFP-64 pin numbers read from the KiCad 10 symbol — VERIFIED_LOCAL for the library, not the ST datasheet)
| Signal | Pin | Notes |
|---|---|---|
| ESTOP_SENSE | PA0 (14) | LOW = healthy, HIGH = tripped/broken; external pull-up 47 k |
| ADC_SENSE | PA1 (15) | 16:1, ADC1_IN6 |
| UART_TX / UART_RX | PA2 (16) / PA3 (17) | USART2 → ISO7721 |
| LED heartbeat | PA5 (21) | |
| INA_ALERT | PB0 (26) | 10 k pull-up |
| I2C2 SCL/SDA | PB10 (29) / PB11 (30) | TC74 only |
| LOAD_EN | PC8 (39) | default low, gate pull-down |
| RELAY_FB | PC9 (40) | active low |
| ARM_SENSE | PC10 (51) | status only |
| SWDIO / SWCLK / SWO | PA13 (46) / PA14 (49) / PB3 (55) | J9 |
| I2C1 SCL/SDA | PB8 (61) / PB9 (62) | INA228 only |
| NRST (7), BOOT0 (60) | | reset button + TP; BOOT0 10 k pull-down + JP1 |

Every unused MCU pin has a no-connect flag and is configured analog/pulled low in firmware.

## 3. Schematic (11 pages, hierarchical, global labels)
01 Power input · 02 Buck/3V3 · 03 MCU · 04 Host (isolated) · 05 INA228/shunt · 06 ADC/pack-sense · 07 Coil driver · 08 Status sensing · 09 Temp probe interface · 10 Test points/mechanical. KiCad ERC (10.0.6): see `OSBAMS_Rev2_RELEASE_CANDIDATE_1/ERC_REPORT.rpt`. A netlist comparison between the KiCad netlist and the design source is in `NETLIST_CHECK.txt`.

## 4. Calculations (generated: `REV2_CALCULATIONS.md`)
- ADC: 44 V → 2.750 V; error budget separated into divider ±0.43 %, ADC ±0.1 %, reference ±2 % uncorrected / ±0.3 % corrected; protection analysis for powered, unpowered, reversed and transient cases with clamp currents and the PA1 maximum voltage.
- INA228: 25 mV at 10 A, 46.25 mV at the 18.5 A trip; range 0 required; SHUNT_CAL 1250.
- Buck: Vout = 0.765 × (1 + 33.2 k/10 k) = 3.305 V; ΔIL 114 mA (12 V, 10 µH, 2.1 MHz); min on-time check flagged.
- Relay: coil 128–167 mA; MOSFET drop/power with a pessimistic RDS(on) placeholder; VDSS margin 35.6 V over the TVS clamp.
- VO610A: CTR_eff = 13 % × 0.8 × 0.8 = 8.3 %; ESTOP_SENSE 5.6 kΩ passes 2× margin down to 10.0 V (supply min 10.5 V); RELAY_FB 3 × 4.7 kΩ passes down to 22.7 V (supported range starts ≈ 30 V; design floor 24 V).

## 5. Connectors
| Ref | Function | Part | Footprint status |
|---|---|---|---|
| J1 | 12 V in (1 +12 V, 2 GND) | Adam Tech EB21A-02-C | footprint from the Adam Tech drawing (VERIFIED_LOCAL; hole 1.30 mm, body 10.6×8.5 mm, wire entry toward −x) |
| J2 | E-stop loop | EB21A-02-C | verified (drawing) |
| J3 | ARM switch | EB21A-02-C | verified (drawing) |
| J4 | K1 coil | EB21A-02-C | verified (drawing) |
| J5 | Shunt Kelvin (IN+, IN−, shield) | Molex 22-27-2031, mate 22-01-3037 + 08-50-0114 | KiCad stock |
| J6 | Pack sense (PACK_INA, PACK_ADC, RELAY_OUT, GND_SENSE) | Molex 22-27-2041, mate 22-01-3047 | KiCad stock |
| J7 | Temp probe (3V3, SDA2, SCL2, GND) | JST B4B-PH-K-S, mate PHR-4 | KiCad stock |
| J8 | Host USB-C | GCT USB4105-GF-A | KiCad stock |
| J9 | SWD | Samtec FTSH-105-01-L-DV-K | KiCad stock (generic 2×5 1.27 mm SMD) |

Test points (27 pads, silk-labelled): +12V, 3V3, 3V3_A, GND ×2, SDA1, SCL1, SDA2, SCL2, INA_IN+, INA_IN−, VBUS, ADC_SENSE, GATE, COIL_SW, COIL_V, ESTOP_SENSE, ARM_SENSE, RELAY_FB, UART_TX, UART_RX, NRST, SWDIO, SWCLK, LOAD_EN, GND_HOST, 3V3_HOST.

## 6. PCB
100 × 90 mm, 4 layers (L1 comp/signal, **L2 solid GND**, L3 +3V3 island + routing + GND fill, L4 comp/signal + GND fill), separate GND_HOST island with 3 mm gap, analog (INA228/ADC/pack-sense) bottom-left away from the buck (top-left), 4 × M3 NPTH, 3 fiducials, silkscreen labels/polarity/revision/`44 V / 10 A MAX`. Routed with Freerouting and verified by KiCad DRC; results and remaining items are in `DFM_DFA_REPORT.md` and `DRC_REPORT.rpt`.

## 7. What is not done (fabrication gates)
See `OSBAMS_Rev2_RELEASE_CANDIDATE_1/PCBWAY_RELEASE_CANDIDATE_REPORT.md`: manufacturer-PDF verification of the critical items (INA228/LMR14006Y/ISO7721/TC74/IRLML0060 pin maps, CP2102N reference design, STM32 I/O types, relay coil data), EB21A-02-C drawing, local ERC/DRC and Gerber regeneration, distributor stock/lifecycle/SKU, PCBWay CPL rotations.

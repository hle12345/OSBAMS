# OSBAMS Rev.2 Controller PCB — architecture (design phase, DRAFT for approval)

**Status:** design phase only. No schematic, no layout, no manufacturing files. The old 80 × 80 mm carrier PCB is **reference only**
(`legacy/reference/rev1_carrier_kicad/`); the earlier PCBWay "candidate" package and the carrier-revision plan in `docs/rev2/pcb/` are **obsolete**.
Companion files: `REV2_BLOCK_DIAGRAM.svg/.png`, `REV2_CALCULATIONS.md` (numbers come from `calc/rev2_calcs.py`), `REV2_PRELIM_BOM.csv`.
Marking: **[V]** = taken from a purchase record or from firmware in this repo · **[A]** = assumed / from memory or a distributor listing, must be confirmed
against the manufacturer datasheet at schematic review · **[D]** = design decision made here, needs your approval.

## 1. What Rev.2 is

One purpose-built controller board that replaces Rev.1's carrier + Nucleo + INA228 breakout + off-board wiring. It does sensing, control and status
monitoring only. **The battery discharge current never enters the board.**

```
Battery -> XT60 -> 15 A fuse -> disconnect -> relay contacts (DG57CM) -> RSA-20-50 shunt -> Agilent 6060B -> battery return     (all external)
```
Envelope: ~30–42 V Li-ion scooter packs, 44 V ceiling, ≤ 10 A operating ceiling (300 W / V at the 6060B: 7.14 A at 42 V), 15 A fuse, 20 A shunt.
Ownership: **Pi requests, STM32 authorizes; hardware E-stop and ARM interrupt the relay coil independent of any firmware.**

### Rev.1 lessons carried over (reference only; Rev.1 is not claimed hardware-validated)
| Rev.1 fact | Rev.2 use |
|---|---|
| STM32L476 firmware architecture worked, register-level, HSI16→PLL 80 MHz [V] | keep the same silicon, pins and clock scheme |
| INA228 telemetry and UART telemetry were online [V, operator/report] | INA228 on board, same I²C address 0x40 and USART2 |
| Low-side MOSFET relay drive (Q1 IRLZ44N, 220 Ω, 10 k pull-down, flyback) [V] | kept, production-cleaned |
| Relay = Durakool DG57CM-5021-76-1012-R (Newark 10190042) [V] | kept; no SW60 |
| TC74 offline; root cause unproven (SCL timing, 250 ms first conversion, lost init status) | firmware fixes + redesigned probe interface; viability decided by bench V1 |
| ADC divider never built [V] | new circuit (section 8) |
| Rev.1 KiCad had **diode symbol/footprint polarity mismatch** (symbol pin 1 = anode, footprint pad 1 = cathode) | Rev.2 uses only standard KiCad symbols (K = pin 1) and a scripted polarity check on every netlist |

## 2. MCU decision (item 3)

**Recommendation [D]: A — STM32L476RGT6 directly on the board.** Needs your approval (Q1).

| Criterion | A. direct STM32L476RGT6 (LQFP-64) | B. NUCLEO-L476RG as a removable module |
|---|---|---|
| Product fit | one board, no loose modules, no J5-style 14-way interface | module on headers; large footprint; 14+ wires/pins to get PA0/PA1/PC9/PC10 out |
| Firmware change | none for pins/clock (same silicon; HSI16, no crystal) — pins PA0, PA1, PA2, PA3, PA5, PB8, PB9, PC8, PC9 unchanged [V] | none |
| New hardware risk | power/decoupling/reset/boot/SWD must be right first time; **mitigation:** standard ST reference practice, SWD header, probing TPs, Nucleo's ST-LINK can program it | none, but Nucleo ST-LINK ties host ground and PA2/PA3 are shared with the ST-LINK VCP (solder bridges SB13/SB14) |
| Safety | LOAD_EN pull-down on the board (guaranteed); no module reset/ST-LINK states in the safety path | pull-down on the carrier, but the module's startup states are outside our design |
| Assembly (PCBWay) | LQFP-64 is routine for PCBWay | PCBWay cannot place the module; hand-fit |
| Cost | one MCU (~$) + passives | Nucleo (owned) but extra headers and wiring |
| Debug | 2×5 1.27 mm Cortex SWD header, reset, BOOT0, TPs | ST-LINK on the module |
| Verdict | **chosen** — the risk is mitigated by SWD access and identical silicon | fallback if bring-up of A fails (Appendix A gives the verified Nucleo pin mapping) |

Direct-implementation checklist (all in the schematic): all VDD pins 100 nF + 4.7 µF bulk; VDDA/VREF+ via ferrite + 1 µF + 100 nF from 3V3A; VBAT to VDD;
NRST 100 nF + button + SWD + TP; BOOT0 10 k pull-down + 2-pin jumper (DFU/UART bootloader); **no crystal** (HSI16 → PLL, as firmware); no LSE; SWD (PA13/PA14, SWO PB3 on the header);
host link UART via isolator + USB bridge (no native USB, so no 48 MHz clock requirement). Pin numbers are taken from the KiCad symbol/DS10198 at schematic capture — the table in section 5 is by **port name**.

## 3. Block diagram (item 2)
See `REV2_BLOCK_DIAGRAM.svg` (and `.png`). Summary of domains: **12 V control** (input → fuse → Schottky → TVS → rail), **5 V/3V3** (buck + LDO + filtered 3V3A),
**MCU**, **measurement** (INA228, ADC divider), **coil safety chain** (E-stop → ARM → coil → Q1), **status sensing** (E-stop, ARM, relay feedback), **temperature probe**, **host** (isolated UART + USB-C).

## 4. Schematic section list (item 4) — one sheet each, flat hierarchy
| Sheet | Contents |
|---|---|
| S1 12 V input & protection | J1, F1 1 A, D2 SB560 (series, reverse polarity), D1 SMBJ15A TVS, C1 bulk; nets `+12V_F`, `+12V` |
| S2 Rails | TPS54202 5 V buck (L1, FB divider 73.2 k/10 k), AP2112K-3.3 LDO, `3V3`, `3V3A` (ferrite), power LED, TPs |
| S3 MCU | STM32L476RGT6, decoupling, reset, BOOT0, SWD J9, heartbeat LED, test points |
| S4 Host interface | J8 USB-C, USBLC6-2 ESD, CP2102N bridge, ISO7721 isolator, UART to PA2/PA3 |
| S5 INA228 | U4, Kelvin connector J5 (IN+, IN−, shield), 2×10 Ω + 100 nF filter, TVS on IN+, pack-sense connector J6 → VBUS, I²C pull-ups, ALERT |
| S6 ADC cross-check | J6 PACK_ADC → 75 k + 75 k + 10 k, 1 k, 100 nF, BAT54S → PA1 |
| S7 Coil safety chain & driver | J2 E-stop, J3 ARM, J4 coil, Q1, R 220, R 10 k, D8 flyback (+ link for fast-release), coil LED |
| S8 Status sensing | E-stop opto (PA0), relay-feedback opto (PC9), ARM divider (PC10) |
| S9 Temperature probe interface | J7 (JST PH 4-pin), 100 Ω series, ESD, 100 nF, pull-ups, SDA/SCL TPs |
| S10 Mechanical / production | 4 × M3, 3 fiducials, test-point list, silkscreen text, revision marking |

Design rules for the KiCad project: standard KiCad library symbols only (no custom diode symbols); every symbol carries Manufacturer + MPN + footprint;
project-local `sym-lib-table`/`fp-lib-table` so the project is self-contained; scripted checks (diode polarity, connector pin-1, net names) run alongside ERC;
ERC clean or every warning dispositioned in writing before layout.

## 5. MCU pin assignment (item 5) — by port name (all current-firmware pins preserved)
| Signal | Port | Dir / mode | Net | Behaviour | Firmware today |
|---|---|---|---|---|---|
| LOAD_EN | PC8 | out, push-pull, default low | `GATE` via 220 Ω; 10 k pull-down | high = request relay on (cannot override E-stop/ARM) | `load_driver.c` ✓ |
| RELAY_FB | PC9 | in, **no internal pull** | opto collector, 22 k pull-up to 3V3 | **low = relay closed / pack voltage present downstream** | `load_driver.c` active-low ✓ |
| ESTOP_SENSE | PA0 | in, no internal pull | opto collector, 22 k pull-up | **low = healthy (loop closed), high = tripped or wire broken** | `estop.c` ✓ |
| ADC_SENSE | PA1 | analog, ADC1_IN6 | divider tap after 1 k | 16:1; pack mV = ADC mV × 16 | `adc_safety.c` ✓ |
| ARM_SENSE | PC10 | in, no internal pull | divider after ARM, 1 k, 100 nF, clamp | **high = ARM closed (with E-stop closed)** | new (status only) |
| INA228_ALERT | PB0 | in, EXTI-capable, 10 k pull-up | `INA_ALERT` | optional, not used by firmware yet | new |
| I2C1_SCL / SDA | PB8 / PB9 | AF4 open-drain | `SCL`/`SDA`, 4.7 k pull-ups | ≤ 100 kHz for TC74 | `i2c_bus.c` (timing fix needed) |
| USART2_TX / RX | PA2 / PA3 | AF7 | to ISO7721 MCU side | 115200 8N1 | `uart.c` ✓ |
| LED_HB | PA5 | out | green LED + 1 k | heartbeat | `main.c` ✓ |
| SWDIO / SWCLK / SWO | PA13 / PA14 / PB3 | debug | J9 | | — |
| NRST, BOOT0 (PH3) | pins | | reset button + TP, BOOT0 jumper | | — |
| unassigned | rest | analog / pulled low in firmware | — | | — |

Firmware to-do list (not done here): I²C timing for ≤ 100 kHz (e.g. PRESC 7, SCLL 27, SCLH 22 ≈ 98 kHz at 40 MHz); TC74 init window ≥ 300 ms and keep the raw status;
ARM state read-only (`ARMED / DISARMED / UNKNOWN`, never a permission); VREFINT correction of the ADC reference; INA228 `IMAX` review (20 A shunt).

## 6. Power tree (item 6) — numbers in `REV2_CALCULATIONS.md`
```
XDR-75-12 (12 V, set to 12.0 V) -> J1 -> F1 1 A -> D2 Schottky -> D1 TVS -> +12V rail
   +12V -> E-stop -> ARM -> relay coil -> Q1 (low-side)                       ~133 mA
   +12V -> TPS54202 -> 5 V (internal only) -> AP2112K-3.3 -> 3V3 (digital) -> FB1 + caps -> 3V3A (VDDA, INA228, probe)
```
Typical 12 V draw ≈ 0.22 A (coil 0.133 + buck 0.083 + sense 0.004); fuse 1 A. 3V3 ≈ 40 mA typical, designed for 150 mA; LDO dissipation 0.26 W at 150 mA.
5 V exists only as the buck output feeding the LDO (no 5 V connector). **No Pi/display converter is on this board**; the Pi 5 + touchscreen use a separate external 5 V supply.
Risk: the XDR-75-12 output is adjustable 12–15 V; at 15 V the coil dissipates ≈ 2.5 W and the TVS margin shrinks → set and verify 12.0 V (Q3).

## 7. INA228 / shunt (item 7)
RSA-20-50 = 2.5 mΩ, 20 A/50 mV, external, Kelvin leads on keyed J5 (IN+, IN−, shield). 10 A → 25 mV (0.25 W); 15 A fuse fault → 37.5 mV; 18.5 A firmware trip → 46.3 mV.
**ADCRANGE = 0** (±163.84 mV, 125 µA/LSB) is retained: ADCRANGE = 1 (±40.96 mV) would saturate at 16.4 A and hide the 18.5 A trip. SHUNT_CAL = 1250 with `IMAX` = 20 A.
Kelvin input filter 2 × 10 Ω + 100 nF (fc 80 kHz); IN+ clamped by a 1.5SMBJ48A (Vc ≈ 77 V < 85 V abs max [A]); `VBUS` from its own lead on J6 (PACK_INA, **upstream of the relay**, so OCV is measurable before the relay closes).
Layout: IN+/IN− routed as a tight differential pair on one layer over solid GND, away from the buck, relay driver and USB; TPs on the connector side of the filter.

## 8. ADC divider (item 8)
PACK_ADC → 75 k → 75 k → ADC_TAP → 10 k → GND; 1 k + 100 nF + BAT54S at PA1. 44 V → 2.750 V; 12.9 mV/LSB at the pack; τ ≈ 1 ms. Worst-case error ±2.55 % (±1.1 V at 44 V) with VDDA as reference, ±0.85 % with VREFINT correction; the firmware 1.5 V agreement window is satisfied either way.
It uses a **separate lead (PACK_ADC)** from the INA228 VBUS lead, both upstream of the relay, so a broken sense wire produces a disagreement fault rather than two identical zeros.

## 9. Relay driver and coil chain (items 9, 10)
```
+12V -> J2 E-STOP (NC loop) -> ESTOP_OUT -> J3 ARM switch -> COIL_V -> J4 relay coil -> COIL_SW -> Q1 drain, source GND
 D8 flyback across the coil (cathode COIL_V) ; R 220 gate series ; R 10 k gate pull-down ; amber LED + 2.2 k from COIL_V to COIL_SW
```
133 mA @ 12 V [A: coil ~90 Ω from the listing; measure in V6]. Gate 3.23 V static, 15 mA peak; Q1 loss ≈ 2 mW; flyback clamp ≈ 12.9 V; Q1 default OFF through the 10 k pull-down.
**Firmware cannot energize the coil without both J2 and J3 closed.** Recommended [D]: wire **both** NC contacts of the E-stop block in series through J2 (dual-channel opening).
Open: diode-only flyback slows contact release ~3×; a 27 V TVS in series (footprint provided via link R12) gives ~3.3× faster release — Q5.

## 10. E-stop / ARM / relay-feedback architecture (item 10)
Sensing never gates anything; it informs the UI, log and diagnostics. All three read the **actual circuit nodes**, not a separate contact, so a broken wire shows as a fault.
| Signal | Taps | Circuit | Result |
|---|---|---|---|
| ESTOP_SENSE (PA0) | `ESTOP_OUT` | 5.6 k → VO610A LED (+1N4148 antiparallel) ; collector 22 k pull-up to 3V3 ; 10 nF | **low = loop closed**; open / broken wire → high (fail-safe), matches the firmware |
| ARM_SENSE (PC10) | `COIL_V` | 270 k / 100 k divider, 1 k, 100 nF, BAT54S | high = E-stop **and** ARM closed. ARM-only state: `ESTOP healthy & ARM_SENSE low` = DISARMED; E-stop tripped → ARM UNKNOWN |
| RELAY_FB (PC9) | `RELAY_OUT` (pack side, **downstream** of the relay contacts, J6 pin 3) | 4 × 3.6 k → VO610A LED (+1N4148) ; 22 k pull-up ; 10 nF | **low = pack voltage present after the relay** (guaranteed on at ≥ 10.7 V; relay open → 0 V → high). Also detects a welded relay by comparing with PACK_ADC |
Because the Durakool has no auxiliary contact, relay feedback is **voltage-based**, as in Rev.1. 44 V sits only across resistors/LED; the 1N4148 limits reverse LED voltage if the pack is wired backwards.
The two VO610A-1 you hold are exactly enough (buy spares).

## 11. Ground and isolation strategy
One solid GND plane. The only intended bond between the controller GND and the pack negative is the **GND_SENSE lead (J6 pin 4)**, landing at the pack-negative / load-return terminal; the XDR output (isolated) returns through J1.
The Pi's ground never touches the board: the host UART passes through the **ISO7721 isolator** (USB host side powered from VBUS). SWD probe ground is connected only during debug. Cable shields terminate at one end only.

## 12. Temperature interface (item 4 of your list)
Keep **TC74A5-3.3VAT** (0x4D) on a separate probe board: TO-220-5 on the pack surface, **VJ0805Y104JXXAT 100 nF at VDD**, keyed 4-wire JST PH cable (3V3, SDA, SCL, GND), ≤ 1 m shielded twisted pair.
On the controller: 100 Ω series on SDA/SCL, ESD array, 100 nF, 4.7 k pull-ups (2.2 k option), SDA/SCL TPs, firmware ≤ 100 kHz. Bus budget ≈ 155 pF → 4.7 k gives ~0.55 µs rise.
**If V1 shows TC74 is not viable, or the cable must exceed ~2 m:** stop and use one of these instead (not forced): (a) **DS18B20** (1-Wire, ±0.5 °C, long cable, waterproof probes, one GPIO), (b) **10 k NTC** + ADC input with a divider at the probe, (c) differential I²C extender (PCA9615) at both ends. Recommendation: (a).

## 13. Connector / interface table (item 11) and test points
Distinct families on purpose so a mis-plug cannot reach the pack-sense or I²C pins.
| Ref | Function | Pins / nets | Part (MPN) | Mating | Rating | Keyed |
|---|---|---|---|---|---|---|
| J1 | 12 V control in | 1 +12V, 2 GND | Adam Tech EB21A-02-C **[V]** | bare wire | 8 A / 300 V | no (silk + reverse protection) |
| J2 | E-stop loop | 1 +12V, 2 ESTOP_OUT | EB21A-02-C | bare wire | 8 A | no |
| J3 | ARM switch | 1 ESTOP_OUT, 2 COIL_V | EB21A-02-C | bare wire | 8 A | no |
| J4 | Relay coil | 1 COIL_V, 2 COIL_SW | EB21A-02-C | bare wire | 8 A | no |
| J5 | Shunt Kelvin | 1 IN+, 2 IN−, 3 SHIELD | Molex 22-27-2031 | 22-01-3037 + 08-50-0114 | 250 V / 4 A | yes (polarized, 3-pin) |
| J6 | Pack sense | 1 PACK_INA, 2 PACK_ADC, 3 RELAY_OUT, 4 GND_SENSE | Molex 22-27-2041 | 22-01-3047 | 250 V / 4 A | yes (4-pin KK) |
| J7 | Temp probe | 1 3V3, 2 SDA, 3 SCL, 4 GND | JST B4B-PH-K-S | PHR-4 | 100 V / 2 A | yes (different family from J6) |
| J8 | Host | USB-C 2.0 | GCT USB4105-GF-A | USB-C cable | 5 V | yes |
| J9 | SWD | Cortex 2×5 1.27 mm | Samtec FTSH-105-01-L-DV-K | ribbon | 3.3 V | yes (shrouded) |
The EB21A-02-C footprint (5.00 mm pitch, drill, keep-out) is drawn **from the Adam Tech drawing**, not copied from the Rev.1 MaiXu footprint. Rev.1's 2×4 header "keyed" claim is retired.
Test points (labelled, 1.5 mm): +12V, 5V, 3V3, 3V3A, GND ×2, SDA, SCL, INA_IN+, INA_IN−, VBUS_SENSE, ADC_SENSE, GATE, COIL_SW, ESTOP_SENSE, ARM_SENSE, RELAY_FB, UART_TX, UART_RX, NRST, SWDIO, SWCLK, TC74_VDD = 24.

## 14. PCB intent (for the later layout phase; nothing routed)
4 layers, ~100 × 90 mm, 1.6 mm: L1 components/signals, **L2 solid GND**, L3 power (+3V3, +12V, +5V islands), L4 signals/components. ENIG finish. Analog zone (INA228, ADC divider, J5/J6) separated from the buck, relay driver and USB zone.
Spacing: pack-side nets (≤ 44 V, 77 V transients) ≥ 1.0 mm from logic (IPC-2221 external 0.6 mm for 31–100 V); coil/12 V path ≥ 0.5 mm wide; 3 fiducials, 4 × M3, silkscreen: "OSBAMS Rev.2 Controller", revision/date, connector names, pin-1, polarity, "44 V / 10 A max" legend.

## 15. Open questions (item 13)
| # | Question | My default |
|---|---|---|
| Q1 | Approve direct STM32 (A)? | A |
| Q2 | Host link: USB-C + bridge + **isolator** (default) vs non-isolated | isolated |
| Q3 | Will you set and lock the XDR-75-12 to **12.0 V**? (adjustable to 15 V) | yes |
| Q4 | Newark 10190042 datasheet for the exact suffix: coil resistance/current, DC make/break at 44 V/10 A (RELAY_VERIFICATION V6) | needed before layout |
| Q5 | Relay release: diode only, or diode + 27 V TVS (faster)? | diode + link, decide after Q4 |
| Q6 | E-stop block contacts: confirm 2 NC; wire both in series through J2? | yes |
| Q7 | Where does the shunt/PACK+ sense land (lead lengths, terminals)? Separate PACK_INA and PACK_ADC wires OK? | yes |
| Q8 | Probe cable length / environment; run V1 before freezing the TC74 | ≤ 1 m; fall back to DS18B20 |
| Q9 | Enclosure mounting: standoffs vs DIN adapter; board outline limit | 100 × 90 mm, 4 × M3 |
| Q10 | Consigned vs PCBWay-sourced parts (you own 2 × 100 nF, 2 VO610A, 2 1N4148, 2 TVS each, 5 EB21A, 2 IRLZ44N, 2 1N5408G, 2 SB560) | PCBWay sources the rest |
| Q11 | Accept THT assembly (Q1, D2, D8, VO610A, EB21A, J5–J7, C1) or swap to SMT equivalents | accept THT |
| Q12 | Datasheet checks pending **[A]** items (listed in `REV2_CALCULATIONS.md`) | at schematic review |
| Q13 | Availability/pricing at PCBWay/LCSC was **not** checked (no access from here) | check at BOM review |

## Appendix A — Nucleo pin mapping (only if option B is ever chosen; from ST UM1724 tables found online, to be re-verified on the board)
PA0 CN8-1 (A0) · PA1 CN8-2 (A1) · PC10 CN7-1 · PC9 CN10-1 · PC8 CN10-2 · PB9 CN5-9 / CN10-5 · PB8 CN5-10 / CN10-3 · PA2 CN9-2 · PA3 CN9-1 (USART2, shared with ST-LINK VCP via SB13/SB14) · 3V3 CN6-4 · GND CN6-6/7.

## Next step
On your approval of Q1–Q3 (and answers to Q4/Q6 if available): create the new KiCad project in `Hardware/Rev2_Controller/kicad/`, sheets S1–S10 above, run ERC, review, **then** layout/DRC/assembly review. No Gerbers until every gate in `docs/rev2/pcb/RELEASE_GATES.json` is evidenced.

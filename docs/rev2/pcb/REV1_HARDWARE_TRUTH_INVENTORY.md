# OSBAMS Rev.1 Hardware Truth Inventory

**Purpose:** reconcile what Rev.1 actually is (KiCad + Mouser invoices + firmware) before any Rev.2 manufacturing files are made.
**Date:** 2026-09-30 · **Scope:** inventory only. No redesign, no Gerbers/BOM/CPL.
**Rule applied:** KiCad + invoices + firmware are evidence. Old planning documents lose any conflict.

## 0. Method, evidence keys, vocabulary

**Evidence keys**

| Key | Source |
|---|---|
| SCH / PCB | `OSBAMS_PCB.kicad_sch` / `.kicad_pcb` (byte-identical to `Hardware/Schematic/OSBAMS PCB.*` in the repo) |
| INV-A | Mouser 91393224, 2026-07-14 |
| INV-B | Mouser 91665418, 2026-07-29 |
| INV-C | Mouser 91854909, 2026-08-07 |
| INV-D | Mouser 91939009, 2026-08-13 |
| FW | `Firmware/` (version string `0.9.0-dev3`) |
| CT / HD / VR | `CONNECTION_TABLE.md` / `Documentation/HARDWARE_DESIGN.md` / `Documentation/VALIDATION_REPORT.md` |
| BOMX / PL | `Hardware/OSBAMS_BOM.xlsx` / `Hardware/OSBAMS_Final_Design_Purchase_List.xlsx` |
| FUND / RPT | Rev.2 funding request (2026-09-24) / ENGR696 report |

**Status:** CONFIRMED = at least two independent sources agree and none conflicts · ASSUMED = one source only, or inferred · MISSING = required/used but absent from KiCad and/or evidence · CONFLICT = sources disagree.
**Rev.2 recommendation:** KEEP · FIX · REPLACE · REMOVE · VERIFY_PHYSICALLY.

**Validation vocabulary.** The repo's own terms are PASS / PARTIAL / NOT RUN (VR §3) and "Host-tested" (VR §2, citing `MODULE_STATUS.md`, which is **not in the repo**). `HARDWARE_VALIDATED` is not defined anywhere in the repo, and nothing here is assigned it. Claims that Rev.1 "worked" come from FUND/RPT (operator-reported); **no recorded bench data exists in the repo**. VR is dated 2026-07-22, predates the build, and lists every hardware ACC row NOT RUN. It is stale, not contradicted.

**"Installed?"** column: Mouser invoices prove purchase, not installation. "Unknown" means nothing in the repo records what was soldered or wired.

## 1. Headline finding: what the KiCad project actually is

The KiCad project is **not** the whole Rev.1 system. It is an 80 × 80 mm, 2-layer carrier with **16 schematic symbols** (plus 4 board-only M3 holes):

- 12 V control input with reverse-polarity diode and TVS (J1, D3, D1, C1)
- E-stop loop terminals (J3) and contactor-coil MOSFET driver (J2, Q1, R1, R2, D2)
- I²C sensor bus: INA228 module header (J4), TC74 (U1), bypass caps (C2, C3)
- Nucleo interface header (J5) and UART header (J6)

**Not in KiCad at all:** STM32 (it is a plug-in Nucleo-L476RG via J5), INA228 silicon (Adafruit module via J4), relay/contactor, shunt, fuses, E-stop switch, ARM switch, VO610A feedback optocoupler, ADC divider, 1N4148, pack-side TVS, XT60, any 5 V rail, test points. Several of these are in firmware and on invoices. The Rev.1 power stage, feedback and ADC circuits were **hand-wired off-board and are undocumented in KiCad.**

J5 carries only: 3V3, GND, SDA(PB9), SCL(PB8), GPIO_GATE(PC8), UART TX/RX(PA2/PA3), SPARE. **PA0 (E-stop sense), PC9 (K1 feedback) and PA1 (ADC divider) are not on J5.**

## 2. Critical conflicts found (details in the tables)

1. **Diode polarity: symbol vs footprint (D1, D2, D3).** Custom symbols `OSBAMS:D_H` and `OSBAMS:D_TVS` have **pin 1 = anode**. KiCad's `D_DO-201AD` and `D_SMB` footprints have **pad 1 = cathode** (PCB shows `K` text and the silkscreen band at pad 1). The PCB nets are therefore reversed relative to schematic intent:
   - D3 (series reverse-protect): cathode on `12V_IN`, anode on `+12V`. Blocks normal polarity.
   - D2 (coil flyback): cathode on `COIL_SW` (drain), anode on `COIL_V` (+12 V). Conducts when Q1 turns on, which would short +12 V through the diode to Q1.
   - D1 (SMBJ15A): cathode on GND, anode on `+12V`. Forward-biased clamp across the 12 V rail.
   A PCBA built from these files would be dead or damaged. Since Rev.1 reportedly worked, the diodes were **probably soldered against the footprint marking**. That must be confirmed on the physical board.
2. **Temperature subsystem**: root cause not determinable from the repo (§5). Variant/address/voltage are consistent for TC74A5-3.3VAT; several other defects exist.
3. **Relay identity**: firmware says Durakool `DG57CM-5021-76-1012-R`; BOMX says Albright SW60; FUND says Durakool "80A" in Rev.1 and SW60 planned for Rev.2. No invoice exists for either.
4. **Netclass not applied**: the project defines `Powerpath(12V/coil)` = 1.2 mm and `3V3` = 0.5 mm, but patterns `+12V, COIL_SW, COIL_V` do not match the actual net names (`/+12V`, `/COIL_SW`, …). Every routed track is **0.3 mm**, including the coil/12 V path.
5. **Purchased vs footprint**: C2/C3 (0805 purchased, 5 mm disc footprint); terminal blocks (Adam Tech EB21A-02-C pluggable purchased, MaiXu MX126 fixed footprint); headers (Samtec 2×2 RA and GCT 14-pos purchased, 1×4 and 2×4 footprints).
6. **Firmware current limits exceed hardware**: `OSBAMS_DEFAULT_MAX_CURRENT_MA = 18500` vs 15 A fuse, 20 A shunt and the 10 A Rev.2 ceiling.
7. **BOMX is stale throughout**: designators collide with the schematic (R1/R2 = I²C pull-ups in BOMX but gate/pull-down in SCH; D1 flyback vs TVS; U1 Nucleo vs TC74); TC74 listed as `A0-5.0VAT`; flyback 1N4007 vs 1N5408; E-stop Schneider vs Eaton.

## 3. Component and circuit inventory

Columns: Ref · Function · Mfr / exact MPN · SCH value · PCB footprint · Purchase evidence · Firmware dependency · Installed? · Status · Rev.2.

### 3.1 On the KiCad board

| Ref | Function | Mfr / MPN | SCH value | PCB footprint | Purchase evidence | Firmware dep. | Installed? | Status | Rev.2 |
|---|---|---|---|---|---|---|---|---|---|
| U1 | Pack temperature sensor, I²C | Microchip **TC74A5-3.3VAT** | `TC74A5-3.3VAT` | `TO-220-5_Vertical` | INV-C L1, qty 2, $1.82 | `TC74_I2C_ADDR = 0x4D<<1`; mandatory channel `SENSOR_CH_TEMP_PACK`; `TC74_Init` | **Unknown** (variant physically fitted not recorded) | **CONFLICT** (SCH, FW, INV-C, RPT agree on A5-3.3V; BOMX says `TC74A0-5.0VAT`; a different part, TC74A1-5.0VCTTR, was also bought) | **FIX** + VERIFY_PHYSICALLY (§5) |
| C2 | TC74 bypass | Vishay **VJ0805Y104JXXAT** (0.1 µF 25 V 0805) if purchased part used | `0.1uF (TC74 bypass)` | `C_Disc_D5.0mm_W2.5mm_P5.00mm` (THT) | INV-D L2, qty 2 (0805 SMD) | none | Unknown | **CONFLICT** (SMD bought, THT footprint). C2 sits ~16.7 mm from U1 VDD | **FIX** (footprint ↔ part; place at VDD pin) |
| C3 | Logic 3V3 bypass | as C2 | `0.1uF (logic bypass)` | same THT disc | as C2 | none | Unknown | **CONFLICT** | **FIX** |
| J4 | INA228 module header (3V3, GND, SCL, SDA) | Adafruit **5832** INA228 module | `INA228_MODULE` | `PinHeader_1x04_P2.54mm` | INV-B L6, $14.95 | `ina228.c` addr `0x40`; `SHUNT=2500 µΩ`, `IMAX=30000 mA`; mandatory V/I/P channels | FUND: module "soldered directly to the Rev.1 board" (operator-reported) | **CONFIRMED** (module identity, bus wiring, FW comms operator-reported). Module IN+/IN−/VBUS wiring and onboard-shunt handling are **not in KiCad** | **KEEP**; VERIFY_PHYSICALLY pin order, ALERT/A0/A1 straps, onboard shunt state |
| U1/J5 | Nucleo interface (3V3, GND, SDA, SCL, GPIO_GATE, TX, RX, SPARE) | n/a | `NUCLEO_INTERFACE` | `PinHeader_2x04_P2.54mm` | none that matches (see §3.2) | PB8/PB9, PC8, PA2/PA3 | Unknown | **ASSUMED** (SCH note: "keyed connector"; footprint is a plain unkeyed header; which Nucleo pins J5 reaches is undocumented) | **VERIFY_PHYSICALLY**; add keying |
| J6 | UART header (3V3, GND, TX, RX) for host | n/a | `UART_HDR` | `FanPinHeader_1x04_P2.54mm` | none | USART2 115200 (`system_clock.h`) | Unknown | **ASSUMED**. Net names are Nucleo-side (TX = Nucleo TX); pin 1 exposes 3V3, a contention risk if tied to a Pi 3V3 pin; PA2/PA3 are also on the ST-LINK VCP | **FIX** labels, drop 3V3 pin |
| Q1 | Contactor-coil low-side driver | Infineon **IRLZ44NPBF** | `IRLZ44NPBF` | `TO-220-3_Vertical` (G-D-S) | INV-B L8, qty 2, $1.80 | PC8 `LOAD_ENABLE`, active-high, default low (`load_driver.c`) | Unknown, probably yes | **CONFIRMED** (SCH + INV + FW + footprint pin map) | **KEEP** |
| R1 | Gate resistor | Not purchased from Mouser (no resistor on any invoice) | `220 (gate)` | `R_Axial_DIN0207…P10.16mm` | none | none | Unknown | **CONFLICT** (BOMX/PL say 100 Ω) | VERIFY_PHYSICALLY; KEEP |
| R2 | Gate pull-down | not on invoices | `10k (gate pulldown)` | same | none | FW header relies on a pull-down so reset ⇒ load OFF | Unknown | **ASSUMED** | VERIFY_PHYSICALLY; KEEP |
| D2 | Coil flyback | onsemi **1N5408G** | `1N5408 (flyback)` | `D_DO-201AD_P15.24mm` | INV-B L9, qty 2 | none (safety-relevant) | Unknown | **CONFLICT**: polarity (§2.1); BOMX says 1N4007 | **FIX**; VERIFY_PHYSICALLY band orientation |
| D3 | Reverse-polarity, series on 12 V | Vishay **SB560-E3/73** | `SB560-E3/73 (rev-polarity, Schottky)` | `D_DO-201AD_P15.24mm` | INV-C L2, qty 2 | none | Unknown | **CONFLICT**: polarity (§2.1) | **FIX** |
| D1 | 12 V rail TVS | Littelfuse **SMBJ15A** | `SMBJ15A (confirmed, DO-214AA/SMB)` | `D_SMB` | INV-C L7, qty 2 | none | Unknown | **CONFLICT**: polarity (§2.1) | **FIX** |
| C1 | 12 V bulk | Panasonic **ECA-1EM100I** (10 µF 25 V) | `ECA-1EM100I: 10uF 25V` | `CP_Radial_D5.0mm_P2.00mm` | INV-B L10, qty 5 | none | Unknown | **CONFIRMED** | **KEEP** |
| J1 | 12 V input (+12V_IN, GND) | See §3.2 terminal blocks | `PWR_IN_12V` | MaiXu `MX126-5.0-02P` | none matches | none | Unknown | **CONFLICT** | **VERIFY_PHYSICALLY** |
| J2 | Contactor coil (COIL_V, COIL_SW) | as J1 | `CONTACTOR_COIL` | MX126 | as J1 | PC8 via Q1 | Unknown | **CONFLICT** | VERIFY_PHYSICALLY |
| J3 | E-stop loop (+12V → COIL_V) | as J1 | `ESTOP_LOOP` | MX126 | as J1 | none (sense is separate, §3.3) | Unknown | **CONFLICT** | VERIFY_PHYSICALLY |
| MH1–4 | M3 mounting | DFRobot FIT0066 (nylon M3×10, hardware) | PCB-only | `MountingHole_3.2mm_M3` | INV-C L3 | none | Unknown | **ASSUMED** | KEEP; match enclosure |

SCH `U1` TC74 row above uses the schematic's U1 designator. BOMX uses U1 for the Nucleo and U3 for the TC74: another designator collision.

### 3.2 Purchased, but no matching KiCad part

| Item | Mfr / MPN | Invoice | What the repo says | Status |
|---|---|---|---|---|
| Terminal blocks | Adam Tech **EB21A-02-C**, 2P pluggable, ×5 | INV-C L6 | KiCad uses fixed MaiXu MX126-5.0 footprint; pitch of EB21A must be checked against 5.00 mm | **CONFLICT** → VERIFY_PHYSICALLY |
| Header | Samtec **TSW-102-08-H-D-RA** (2×2 right-angle) ×1 | INV-C L5 | matches no KiCad footprint (J4 is 1×4, J5 is 2×4) | **MISSING** link |
| Header/socket | GCT **BG040-14-A-0450-0300-N-G** (14-pos 2.54 mm) ×2 | INV-C L4 | matches no KiCad footprint | **MISSING** link |
| INA260 module | Adafruit **4226** | INV-A L3 | superseded: INA260 36 V limit (CT) | **REMOVE** from Rev.2 scope |
| Fuses 5 A / 10 A | Littelfuse **0997005.WXN**, **0997010.WXN**, ×5 each | INV-A L1–2 | not the selected fuse (15 A); a 10 A fuse nuisance-trips at the 10 A ceiling | **REMOVE** from Rev.2 BOM |

### 3.3 Circuits and parts that exist only off-board, or only in firmware/purchase records

| Item | Function | Mfr / MPN | SCH value | Footprint | Purchase evidence | Firmware dep. | Installed? | Status | Rev.2 |
|---|---|---|---|---|---|---|---|---|---|
| STM32L476RG controller | Safety authority, acquisition | ST **NUCLEO-L476RG** (module, not on PCB) | via J5 | n/a | BOMX "Owned"; FUND spare Nucleo (not Mouser) | whole firmware; register-level, PCLK1 40 MHz | Yes (FW builds/flashes; INA228 comms and UART telemetry operator-reported, RPT/FUND) | **CONFIRMED** (as module) | **KEEP** module (PCBWay cannot place a Nucleo) |
| INA228 (voltage/current) | Primary metrology | TI INA228 on Adafruit 5832 | see J4 | | INV-B L6 | addr `0x40`, `ADCRANGE=0`, `SHUNT_CAL` fixed (header comments) | per FUND "working" | **CONFIRMED** (module) | **KEEP** |
| Independent ADC voltage | Redundant V cross-check | Resistors: **no MPN anywhere** | none | none | none; PL says `ADC-R` "DO NOT ORDER YET" | `adc_safety.c`: PA1/ADC1_IN6, ratio 16:1 (150 kΩ/10 kΩ, comment says "confirmed"), 1.5 V agreement window; missing ADC ⇒ SENSOR_DISAGREE fault | Unknown | **CONFLICT** (FW "confirmed physical divider" vs PL "unfinished" vs not in KiCad). No clamp or RC filter is documented | **VERIFY_PHYSICALLY**, then **FIX** (add to PCB with protection) |
| Shunt | Current sense | Bourns **RSA-20-50** (20 A / 50 mV = 2.5 mΩ) | none | chassis mount | INV-B L1, $39.46 | `OSBAMS_SHUNT_MICRO_OHM = 2500` | RPT: shunt wiring in place (unspecific) | **CONFIRMED** (purchase = FW value). Module/shunt Kelvin wiring is undocumented | **KEEP**; fix FW range config |
| Main fuse | Pack-path protection | Littelfuse **0997015.WXN** (58 V, 15 A) | none | inline | INV-B L4, qty 2 | none | Unknown | **CONFIRMED** purchased | **KEEP** |
| Fuse holder | | Littelfuse **0FHM0001ZXJ-RED** (MINI inline) | none | inline | INV-B L3, qty 1 | none | Unknown | **ASSUMED** (holder DC voltage/current rating not in repo; must cover 42 V / 15 A) | **VERIFY_PHYSICALLY**, datasheet check |
| Relay/contactor K1 | Pack disconnect | Rev.1: Durakool **DG57CM-5021-76-1012-R** (string only in `load_driver.c`), 12 V coil, "80 A" (FUND, RPT); no aux contact (FW comment) | none | off-board; coil via J2 | **None** (not on any Mouser invoice; RPT lists $18) | PC8 command; K1 state read via PC9 | Unknown, "automotive relay substituted" (FUND) | **ASSUMED** (exact variant from a code comment only). BOMX/PL say Albright **SW60** (never bought) | **REPLACE** (SW60 + aux per FUND, not yet quoted); VERIFY_PHYSICALLY label of installed relay |
| Relay MOSFET driver | see Q1/R1/R2/D2 | | | | | | | CONFIRMED part, polarity CONFLICT | KEEP/FIX |
| Feedback optocoupler | K1 closed ⇒ HV present ⇒ PC9 LOW | Vishay **VO610A-1** | none | none | INV-D L1, qty 2 | `load_driver.c`: PC9 active-low, pull-up "external", `LOAD_CLOSE_TIMEOUT_MS=250`, `Load_Disable` returns LOAD_STUCK if still "closed" | Unknown (FW states it is wired) | **MISSING** from KiCad: resistor chain values, pull-up, 1N4148 role, pack-side wiring all undocumented | **VERIFY_PHYSICALLY**, then **FIX** (draw it); REPLACE logic if SW60 aux is used |
| 1N4148 | Not referenced anywhere | onsemi **1N4148** ×2 | none | none | INV-D L3 | none | Unknown | **MISSING** (purpose undocumented; do not assume) | VERIFY_PHYSICALLY |
| Pack-side TVS | HV bus transient clamp | Bourns **1.5SMBJ48A** ×2 | none (SCH note: "belongs on HV battery bus ONLY") | none | INV-B L2 | none | Unknown | **ASSUMED** purchased for the pack bus; not on the PCB; PL says `TVS1` "DO NOT ORDER YET" (stale) | VERIFY_PHYSICALLY; define location |
| E-stop | Hardware coil interrupt | Eaton **M22-PV-K02** | `ESTOP_LOOP` (J3 only) | panel | INV-B L11, $58.61 | PA0 `ESTOP_SENSE`: LOW healthy, HIGH tripped, **no internal pull**, external pull-up assumed (`estop.c`) | FUND: E-stop is in the enclosure | **CONFIRMED** (switch, loop); **MISSING** sense/pull-up circuit; BOMX "Schneider XB4BS8445" stale | **KEEP** loop; **FIX** add sense circuit; VERIFY_PHYSICALLY contact block (NC count/rating) |
| ARM toggle | Control enable | C&K **T102SHZQE** (SPDT, invoice text "Off-None-On") | none | panel | INV-B L12 | **no firmware reference** | Unknown | **MISSING** from KiCad; where it sits in the circuit is not recorded | VERIFY_PHYSICALLY; add to schematic |
| 12 V supply | Control power | Mean Well **XDR-75-12** (74.88 W, 6.24 A) | none | DIN | INV-B L5, $36.50 | none | Unknown, referenced as installed in FUND | **CONFIRMED** purchased | **KEEP** |
| 5 V rail (Nucleo / Pi) | | RPT: "Pololu 5 V" (no MPN), FUND: 12→5 V converter for Pi 5 + touchscreen + STM32 | none; **no 5 V net on the PCB** | none | none on Mouser | none | Unknown | **MISSING** (no MPN, no capacity; no listed part is sized for Pi 5 + 10.1" display + STM32) | **FIX**; BLOCKER |
| Raspberry Pi interface | UI host | Pi 5 + 10.1" display | none | none | none | protocol over USART2 (ST-LINK VCP via USB per CT; J6 is an unlabelled alternative) | n/a | **ASSUMED**; no Rev.1 hardware defines the Pi link | FIX / decide |
| UART/USB | Host link | Nucleo ST-LINK VCP, USB micro (CT) | J5/J6 | | n/a | 115200 | Yes (telemetry operator-reported) | **CONFIRMED** (CT + FW + RPT) | KEEP |
| Programming/debug | | Nucleo on-board ST-LINK | none | none | n/a | | Yes | **CONFIRMED** (as module). No SWD header on PCB | **KEEP**; add header only if MCU moves on-board |
| Battery connector | Pack interface | Amass **XT60** (BOMX planned) | none | none | **none** | none | Unknown | **MISSING** purchase evidence | **KEEP** XT60 only (no XT90) |
| Test points | | | none | none | none | | n/a | **MISSING** (none exist) | add (§ Change Request) |

## 4. Power architecture review (Rev.2 target: 30–42 V packs, XT60, Agilent 6060B, 300 W, 10 A)

| Topic | Finding | Status |
|---|---|---|
| Voltage margin | INA228 VBUS ≤ 85 V; fuse 58 VDC; SB560 60 V; IRLZ44N 55 V (12 V domain only); 1.5SMBJ48A V<sub>RWM</sub> 48 V: all clear 42 V. SMBJ15A V<sub>RWM</sub> 15 V on a 12 V rail | CONFIRMED by part rating (datasheets not in repo; ratings quoted from invoice descriptions) |
| Power vs current ceiling | 300 W load ceiling means the usable current is P/V: **10 A at 30 V, ≈7.1 A at 42 V**. The 10 A ceiling is therefore binding only at the low end of the pack range. Firmware has **no power limit** (`DEFAULT_MAX_CURRENT_MA` 18.5 A; grep finds no 300 W limit) | CONFLICT (FW vs product spec) |
| Current chain | Fuse 15 A < shunt 20 A; firmware default 18.5 A > fuse; `INA228_IMAX_MA=30000` > shunt rating (affects only LSB size). INA228 `ADCRANGE=0` (±163.84 mV): 10 A = 25 mV on 2.5 mΩ, usable; ADCRANGE=1 would give 4× finer resolution if desired | CONFLICT (FW) |
| Contactor DC rating | No contactor datasheet in the repo. DC breaking rating at 42 V / 10 A inductive is **unverified for both** the Rev.1 relay and the planned SW60 | MISSING; BLOCKER |
| Coil supply path | Coil is fed through D3 (≈0.4–0.6 V Schottky drop) and the E-stop contacts. Coil current is **unknown** (no datasheet). Tracks are 0.3 mm | MISSING |
| Logic power | PCB takes 3V3 *from* the Nucleo (SCH note). Nothing on the PCB powers the Nucleo. FUND says Nucleo + Pi + display run from XDR-75-12 through a converter that is not specified | MISSING; BLOCKER |
| XDR-75-12 headroom | 74.88 W total; coil + Pi 5 (up to 5 V / 5 A class) + touchscreen + STM32 is plausible but unsized | ASSUMED |
| Grounding | CT says the pack's energy "never reaches the logic rails", yet the INA228 sense lines and the ADC divider (150 kΩ to pack +, 10 kΩ to GND) tie pack and logic references together. The bond point and where the divider's low side returns are undocumented | MISSING |
| Interfaces | One external load only (Agilent 6060B); desktop `electronic_load.py` has `Agilent6060BLoad` as an unimplemented stub, and an `OwonLoad` class still ships. Rev.2 hardware needs no load interface, but firmware/desktop still carry an OWON driver (out of PCB scope, flagged) | FLAG |
| Scope hygiene | No XT90 or MV/HV hardware in KiCad or firmware. `chemistry_profiles.py` still mentions NiMH (desktop, out of PCB scope) | FLAG |

## 5. Temperature subsystem: why was it offline?

**Symptom evidence.** FUND (2026-09-24): "TC74 temperature sensor is currently non-functional (offline fault)". RPT: "TC74 bring-up" still open. Firmware: `SENSOR_HEALTH_OFFLINE` on TC74 blocks `RunSelfChecks` (main.c), so the unit cannot reach IDLE. **The repo contains no bus scan, no status code, no scope capture and no photo.** `SensorManager_Init` collapses the TC74 init result to a boolean, so the failure cause (NACK vs TIMEOUT vs NOT_READY) was **not recorded**.

**Is variant/address/voltage/interface mismatch the cause?**

| Check | Result |
|---|---|
| Schematic part | TC74A5-3.3VAT, TO-220-5 |
| Firmware address | 0x4D. Matches the TC74A5 default (`1001 101b`, from Microchip DS21462 via search excerpts) |
| Purchased 3.3 V part | TC74A5-3.3VAT ×2, INV-C (2026-08-07). Consistent with SCH/FW |
| Purchased 5.0 V part | TC74A1-5.0VCTTR ×2, INV-B (2026-07-29): **A1 ⇒ address 0x49, SOT-23-5 SMD**. It cannot be dropped onto the TO-220-5 footprint |
| Rail | 3V3 from Nucleo. The datasheet states all variants operate 2.7–5.5 V; accuracy is only specified at nominal V<sub>DD</sub>. FW comment "5.0 V part would be a rail mismatch" is overstated |
| Pin map | SCH/PCB: 1 NC, 2 SDA, 3 GND, 4 SCLK, 5 VDD. Search excerpts for the TO-220 pin table were garbled; **verify against DS21462 in hand** |
| Shared bus | INA228 (0x40) reportedly works on the same SDA/SCL. So bus wiring, Nucleo pin map, pull-ups and the I²C driver are demonstrated for INA228; the fault is **TC74-specific** |
| Pull-ups | None on the PCB (R1/R2 were repurposed as gate parts; BOMX pull-ups never drawn). Pull-ups presumably come from the Adafruit module (unverified). INA228 working makes absence unlikely to be the cause |

**Therefore:** a variant mismatch can explain the failure **only if the wrong physical part (A1/5.0 V, or a different address variant) was fitted**; nothing in the repo shows which part is on the board. If TC74A5-3.3VAT is on the board correctly, address, voltage and interface all match.

**Defects found that could cause or contribute (ranked by what the evidence supports):**

1. **SCL timing outside TC74 spec.** `I2C1_TIMINGR` (PRESC=7, SCLL=19, SCLH=15 at PCLK1 = 40 MHz) gives t<sub>LOW</sub> ≈ 4.0 µs, t<sub>HIGH</sub> ≈ 3.2 µs, ≈ 125–139 kHz. The TC74 is specified 10–100 kHz with t<sub>LOW</sub> ≥ 4.7 µs and t<sub>HIGH</sub> ≥ 4.0 µs. INA228 tolerates this; the TC74 is out of spec. The header comment "~96 kHz" does not match the arithmetic. (Datasheet figures from search excerpts; verify.)
2. **Init window shorter than worst-case first conversion.** `TC74_Init` polls DATA_RDY 500× back-to-back (~0.27 ms each ≈ 135 ms) while the datasheet allows up to **250 ms** after power-on. Init at boot can return NOT_READY. Later retries (`SensorManager_AttemptRecovery`) should recover, so this alone would not give a permanent offline state.
3. **Wrong or misplaced physical part** (see above): unknown.
4. **Assembly/pin-to-pad issues**: 1.7 mm lead pitch, 0.425 mm pad gap (bridge risk when hand-soldered), lead-form vs footprint unverified; bypass cap C2 is ~17 mm from VDD.
5. **Diagnostics lost** (process gap, not a cause).

**Conclusion: the root cause is NOT established from the repository.** Four bench measurements discriminate (30 min):
1. Read the package marking on installed U1 (A-code and V-code).
2. Measure VDD at pin 5 and idle SDA/SCL levels with U1 powered.
3. Run `I2C1_Scan` and log the raw status from `TC74_Init` (NACK ⇒ address/part/solder; TIMEOUT/BUS_ERROR ⇒ bus; NOT_READY ⇒ timing).
4. Scope SCL during a TC74 transaction; compare t<sub>LOW</sub>/t<sub>HIGH</sub> with 4.7/4.0 µs.

## 6. Verification limits of this inventory

- No `kicad-cli` was available: ERC/DRC were **not run**. Connectivity was re-derived by parsing the S-expression files (schematic nets from wires/labels; PCB track connectivity per net).
- No datasheets are in the repo; ratings are from invoice descriptions, firmware comments or search excerpts and are marked for verification.
- No photos or build records exist; "Installed?" is therefore Unknown for almost everything.

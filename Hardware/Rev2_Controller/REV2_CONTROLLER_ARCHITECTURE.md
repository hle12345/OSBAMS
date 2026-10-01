# OSBAMS Rev.2 Controller — Architecture (design phase, rev A)

**Status: DESIGN PHASE. No schematic, no layout, no manufacturing files exist for Rev.2 yet.** This document is the review package that must be approved before the KiCad schematic is created. Nothing here is bench-validated. The Rev.1 carrier PCB (`legacy/reference/rev1_kicad/`) is reference material only; the old PCBWay candidate package is obsolete and was deleted (`docs/rev2/pcb/MANUFACTURING_STATE.md`).

Evidence tags used below: **[P]** purchased/confirmed by the user (Mouser invoice 62257BB, 2026-08-13, and the purchase list); **[R1]** worked in Rev.1 / firmware contract in this repo; **[C]** candidate chosen here — datasheet, pinout, footprint and orderability **must be verified before the schematic is frozen** (this session had no datasheet access; every [C] MPN is a proposal, not a verified part); **[N]** new Rev.2 circuit, no Rev.1 evidence.

Envelope (unchanged): Li-ion 30–42 V packs, 44 V absolute project ceiling, ≤ 10 A operating ceiling, 15 A fuse (fault only), RSA-20-50 shunt (2.5 mΩ, 20 A/50 mV), XT60 externally, Agilent 6060B external load, 300 W ceiling. The battery discharge current **never enters this PCB**:

`Battery → XT60 → 15 A fuse → disconnect → [E-stop/ARM/relay K1 contacts] → RSA-20-50 shunt → 6060B → battery return`

---

## 1. Rev.1 lessons carried forward

| Rev.1 fact | Rev.2 consequence |
|---|---|
| Nucleo/STM32 firmware, UART telemetry, INA228 telemetry worked [R1] | Keep register-level firmware; keep PA0/PA1/PA2/PA3/PB8/PB9/PC8/PC9 assignments (§5) so the port is minimal |
| TC74 offline, cause unproven (Inventory §5) | Separate I²C bus for the probe (§5, §10 TC74), keep TC74A5-3.3VAT, no sensor change until V1 data exists |
| Redundant ADC divider never built | New circuit [N], §8 |
| J5 carried no PA0/PA1/PC9, diode symbol/footprint polarity bug | New symbols and footprints built together; a netlist polarity check is part of the schematic review gate |
| Durakool DG57CM-5021-76-1012-R confirmed relay, 12 V coil, ≈ 90 Ω (listing, unverified) | Keep; datasheet DC rating to be recorded (`docs/rev2/pcb/RELAY_VERIFICATION.md`) |
| Rev.1 is not hardware validated | Rev.2 claim stays as `config.REV2_CLAIM`; no BENCH_TESTED / HARDWARE_VALIDATED |

The Rev.1 V1–V10 bench sheet (`docs/rev2/pcb/BENCH_V1_V10_ONE_PAGE.pdf`) stays useful, but its role changes: it records *reference-circuit facts* to import (V2 feedback stage values, V4 divider, V6 E-stop contact count and relay marking, V1 TC74 discriminators). V7 (Rev.1 diode orientation) no longer blocks anything. Items marked "needed" in §13 are the only ones that can still change the Rev.2 schematic.

---

## 2. Block diagram

```
                    EXTERNAL (high-current, NOT on this PCB)
 Pack+ ──XT60──15A fuse──disconnect──[K1 contacts DG57CM]──┬─RSA-20-50 (2.5 mΩ)──6060B── Pack−
                                                           │      │ Kelvin IN+/IN−
                                       RELAY_LOAD_SIDE ────┘      │
 ══════════════════════════════════════════════════════════════ J_SHUNT ═══ J_FB ═══ J_PACKV ══ (sense-level, ≤ 44 V)
                         OSBAMS Rev.2 CONTROLLER PCB                │          │         │
  ┌──────────────────────────────────────────────────────────────────┼──────────┼─────────┼───────────┐
  │  PACK-SIDE (sense only)                                          │          │         │           │
  │   INA228 (U2) ◄─ IN+/IN−/VBUS filters+TVS ◄──────────────────────┘          │         │           │
  │       │ I²C1 400 kHz  ALERT                          Opto U4 (VO610A-1) ◄────┘         │           │
  │       │                                              LED side (pack)                    │           │
  │       │                                         ─ ─ ─ ISOLATION BARRIER (≥ 2 mm) ─ ─ ─ │ ─ ─ ─ ─  │
  │   ADC divider 75k+75k / 10k ◄───────────────────────────────────────────────────────────┘           │
  │       │ ADC_SENSE → RC → clamp                                                                       │
  │       ▼                                                                                              │
  │   ┌─────────────────────────┐  USART2 (PA2/PA3)  ┌────────┐  ┌──────────────┐  USB-C  ┌───────────┐│
  │   │ STM32L476RGT6  (U1)     │◄──────────────────►│ ISO7721│◄►│ CP2102N      │◄───────►│ Pi 5 host ││
  │   │ safety authority        │                    │ (U7)   │  │ USB-UART (U8)│  (VBUS  │ (ext. 5 V ││
  │   │ HSI16/PLL 80 MHz        │  I²C2 ≤100 kHz     └────────┘  └──────────────┘  isolated supply)   ││
  │   │ SWD, NRST, BOOT0        │◄──────────► J_TEMP ──► remote TC74A5-3.3VAT probe (pack surface)    ││
  │   └──▲──▲──▲────────┬───────┘                                                                      │
  │ PA0 │  │PC9│PC10    │PC8 LOAD_EN                                                                   │
  │  ESTOP_SENSE  RELAY_FB  ARM_SENSE   │                                                              │
  │   (opto U3)  (opto U4)  (opto U5)   ▼                                                              │
  │       ▲          ▲        ▲      R 220 Ω ─ Q1 IRLZ44N ─ COIL_SW ── J_COIL− ──► K1 coil (12 V, ≈ 90 Ω)│
  │       │          │        │       10 kΩ pull-down      D2 flyback                                  │
  │  12V_IN ► D3 ► +12V ─► J_ESTOP ─ESTOP_OUT─► J_ARM ─COIL_V─► J_COIL+                                │
  │   (J_12V)  TVS    │      (Eaton NC, series)    (C&K, series)                                       │
  │                   └─► buck 12→3V3 (U6) ─► 3V3 (digital) ─ferrite→ 3V3_A (INA228, VDDA)             │
  └──────────────────────────────────────────────────────────────────────────────────────────────────┘
  Hard-wired safety chain: +12V → E-stop NC → ARM → relay coil → Q1 (the only thing the MCU controls).
  E-stop and ARM physically open the coil supply; the MCU only observes them.
```

Authority: **Pi requests, STM32 authorises.** The Pi has no hardware path to Q1. E-stop and ARM are series elements in the coil supply; no firmware path can bypass them (sensing inputs are read-only and cannot drive anything).

---

## 3. MCU decision: A (direct STM32L476RG) vs B (removable Nucleo)

| Criterion | A. STM32L476RGT6 on the board | B. NUCLEO-L476RG module |
|---|---|---|
| One-board product, wiring errors | Single assembly, no inter-board header (Rev.1's J5 omission class of bug disappears) | Needs a keyed 2-row interface to a module whose pinout we do not control; Rev.1's J5 shows the failure mode |
| Production / PCBWay turnkey | LQFP-64 is routine for turnkey assembly | Module is not assembled by the fab; hand-plugged, hand-wired |
| Safety authority | Fixed, known hardware; no ST-LINK/USB back-power paths | ST-LINK, solder bridges, E5V/VIN/USB power selection and a 3V3 LDO that can back-power — extra undocumented states around the safety MCU |
| Supply / noise | Board's own rail, filtered 3V3_A for ADC/INA228 | Nucleo 3V3 from LDO fed from USB, shared noise, separate ground wire |
| Debug / programming | SWD header; the owned Nucleo's ST-LINK is reused as an external probe (remove CN2 jumpers) | Built in |
| Firmware port effort | Low: HSI16/PLL (no crystal in firmware), same pins, USART2 → isolator/bridge instead of ST-LINK VCP; new I²C2 instance for the probe | None |
| Bring-up risk | **Real:** new hardware, first-article risk (clock, reset, BOOT0, decoupling, SWD). Mitigated by tiny, conventional MCU circuit and keeping the Rev.1 Nucleo stack as the working fallback until the Rev.2 board is bring-up-validated | Lowest |
| Cost/BOM | +MCU, passives, SWD; − Nucleo | Nucleo already owned |

**Decision proposed: A — STM32L476RGT6 directly on the board**, with these conditions: (1) build 2–3 first-article boards; (2) the Rev.1 stack stays available as fallback and as the firmware reference until first-article bring-up passes; (3) bring-up checklist written before layout (power rails, reset, SWD attach, HSI/PLL 80 MHz, GPIO, I²C scan, UART echo); (4) firmware change list in §14 reviewed first. B is the fallback only if the user rejects first-article risk; then the schematic needs a *keyed* module interface carrying PA0/PA1/PA2/PA3/PB8–PB11/PC7–PC10 plus GND/3V3 and the V9 findings.

MCU circuit contents (A): VDD×(per-pin 100 nF **VJ0805Y104JXXAT [P]**) + 4.7 µF bulk, VDDA via ferrite + 1 µF + 100 nF (VREF+ tied to VDDA; VREFBUF unused), NRST with 100 nF to GND and reset test point/pad (no pull-up needed; internal), BOOT0 (PH3) with 10 kΩ pull-down and a 2-pin jumper to 3V3 for the ROM bootloader, SWD header (§11), HSI16 clock (matching the firmware), **DNP footprint** for an 8 MHz HSE crystal with load caps (not used by the proven firmware; reserved), no LSE (RTC not used), USB OTG pins PA11/PA12 left unconnected/reserved (no native USB — see §10 host).

---

## 4. Schematic section list (hierarchical sheets)

1. **Power input and protection** — J_12V, reverse-blocking Schottky D3, TVS D1, bulk, +12V rail, test points.
2. **Rails** — 12 V→3.3 V buck, LC/ferrite filters, 3V3 / 3V3_A, power-good/LED.
3. **MCU core** — STM32L476RGT6, decoupling, reset, BOOT0, SWD, DNP HSE, status LEDs.
4. **INA228 + shunt interface** — J_SHUNT Kelvin connector, input filter/TVS, INA228, straps, ALERT.
5. **Independent ADC voltage channel** — J_PACKV, divider, RC, clamp, TP.
6. **Relay driver** — LOAD_EN → R → Q1, pull-down, flyback, J_COIL, test points.
7. **Safety chain and sensing** — J_ESTOP, J_ARM, ESTOP_SENSE (U3), ARM_SENSE (U5), RELAY_FB (U4, J_FB).
8. **Temperature interface** — J_TEMP, I²C2 pull-ups (DNP), ESD, series damping, decoupling.
9. **Host interface** — USB-C, CP2102N, ISO7721, ESD, host-side supply.
10. **Test points and mechanical** — TP list, mounting, fiducials, markings.

Hierarchical design rule: every net crossing the isolation barrier appears only in sections 7 and 9.

---

## 5. Pin assignment (STM32L476RGT6, LQFP-64; physical pin numbers are filled from the datasheet when the symbol is built — not asserted here)

| Signal | MCU pin | Function / AF | Direction | Source of assignment |
|---|---|---|---|---|
| ESTOP_SENSE | PA0 | GPIO in, no internal pull. **LOW = healthy**, HIGH = tripped/broken | in | [R1] firmware contract |
| ADC_SENSE | PA1 | ADC1_IN6, 92.5-cycle sampling, 16:1 scale | analog in | [R1] firmware (circuit [N]) |
| UART_TX / UART_RX | PA2 / PA3 | USART2 AF7 (→ ISO7721) | out / in | [R1] |
| LED_STATUS | PA5 | GPIO out (Nucleo LD2 equivalent) | out | [R1] |
| LED_FAULT | PA6 | GPIO out | out | [N] |
| I²C1 SCL / SDA | PB8 / PB9 | I2C1 AF4 → INA228 only, 400 kHz | od | [R1] |
| I²C2 SCL / SDA | PB10 / PB11 | I2C2 AF4 → remote TC74 only, ≤ 100 kHz | od | [N] (firmware: TC74 moves to I2C2) |
| INA_ALERT | PC7 | EXTI7, open-drain from INA228 | in | [N] |
| LOAD_EN | PC8 | GPIO out, default low, resets Hi-Z → pulled low | out | [R1] |
| RELAY_FB | PC9 | GPIO in, **active-low** via VO610A, external pull-up | in | [R1] |
| ARM_SENSE | PC10 | GPIO in, **LOW = armed**, sense only | in | approved decision 2 |
| SWDIO / SWCLK / SWO | PA13 / PA14 / PB3 | debug | io | standard |
| NRST, BOOT0 | NRST, PH3 | — | — | standard |
| USART1 pads (opt.) | PA9 / PA10 | ROM-bootloader access, test pads only | io | [C] |
| USB OTG FS | PA11 / PA12 | **unused / reserved** | — | decision §10 |
| Spare | PB0, PB1, PB2, PA4, PA7, PB12–PB15, PC0–PC6, PC11–PC13 | 1×6 AUX header carries PB0, PB1, PB2, PA4 (+3V3, GND); rest unconnected, configured analog | — | [N] |

Polarity conventions are chosen so the existing firmware (PA0 LOW=healthy, PC9 active-low) works unchanged. ARM_SENSE follows the same style (LOW = armed/enabled path present).

---

## 6. Power tree

Inputs: 12 V control supply (Mean Well XDR-75-12 **[P]**, 6.24 A/74.88 W — vastly oversized; adjustable, assumed set to 12.0 V). Pi/display 5 V is external and never touches this PCB.

```
J_12V ─ D3 (series Schottky, ≈0.4 V @ 0.15 A) ─┬─ +12V ─► J_ESTOP→J_ARM→COIL_V→J_COIL+ (coil 128–167 mA)
 TVS D1 (SMBJ15A) across +12V after D3 ─────────┤
 bulk C (35 V rated, ≥ 22 µF) ──────────────────┴─► buck U6 → 3V3 ─► MCU, ISO7721 (controller side), TC74 probe, pull-ups, LEDs
                                                              └► ferrite+C → 3V3_A → INA228, MCU VDDA
```

| Load (3V3) | Typical mA | Basis |
|---|---|---|
| STM32L476 @ 80 MHz | 15 | ~100–150 µA/MHz run mode, peripherals on; **[C] verify datasheet** |
| INA228 | 1.0 | datasheet class value, verify |
| TC74 (probe) | 0.3 | active, verify |
| ISO7721 (controller side) | 3 | verify at 3.3 V |
| 2 status LEDs | 4 | 2 mA each |
| pull-ups / misc | 1.5 | |
| **Total** | **≈ 25 mA (≈ 82 mW); design for 100 mA** | |

12 V rail: coil 128.9 mA @ 11.6 V (typ.) up to 166.7 mA @ 15 V; two sense LEDs ≈ 2.1 mA each; buck input ≈ 8 mA at 25 mA load (85 % eff.) → **≈ 0.15 A typical, ≈ 0.2 A worst**; D3 ≥ 1 A, external control fuse F2 = 1 A.

**Regulator choice (open for review).** A linear 12 → 3.3 V at 25–50 mA dissipates 0.22–0.44 W (0.59 W at 15 V) — thermally awkward next to the analog section; a small buck dissipates ≈ 15 mW. Proposed: **wide-input buck [C] (TI LMR14006 family: 4.2–40 V, 0.6 A, SOT-23-6; confirm which suffix/frequency)** — wide input chosen because the 12 V TVS clamps near 24 V, above a 17 V-class buck's rating — followed by an LC filter and a ferrite-isolated 3V3_A. Rail ripple on 3V3_A is measured at bring-up; the INA228's delta-sigma filtering rejects MHz switching noise, but this is **not measured, only expected**. Alternative if bring-up shows noise: pre-regulate with the buck to 4.5 V and use a low-noise LDO to 3V3_A. No 5 V rail is needed (the USB-UART bridge's side is supplied from the host's USB VBUS, isolated).

TVS D1: SMBJ15A across +12V (standoff 15 V; clamp ≈ 24.4 V peak). Capacitor ratings ≥ 35 V so the clamp does not exceed them (Rev.1's 25 V bulk cap was marginal).

---

## 7. INA228 / shunt calculation

Shunt RSA-20-50 [P]: 2.5 mΩ, 20 A / 50 mV, external; the INA228 [C: INA228AIDGSR, VSSOP-10] sits on the PCB. The shunt is in the **positive** lead (after K1), so IN± common-mode ≈ pack voltage (≤ 44 V) — within the INA228's rated range (up to 85 V abs.; verify datasheet).

| Quantity | Value |
|---|---|
| Shunt voltage @ 10 A / 18.5 A (firmware trip) / 20 A | 25.0 mV / 46.25 mV / 50 mV |
| Shunt dissipation @ 10 A / 18.5 A / 20 A | 0.25 W / 0.86 W / 1.0 W |
| ADCRANGE | **0 (±163.84 mV)** — range 1 (±40.96 mV = ±16.4 A) would clip at the 18.5 A trip, so it is rejected |
| ADC LSB (range 0) | 312.5 nV → 125 µA native current resolution |
| Firmware scale (`app_config.h`) | `OSBAMS_INA228_IMAX_MA` = 30 000 mA → CURRENT_LSB = 30/2¹⁹ = 57.22 µA |
| SHUNT_CAL (range 0) | 13107.2×10⁶ × 57.22×10⁻⁶ × 2.5×10⁻³ = **1875** |
| Input offset contribution | 1 µV ⇒ 0.4 mA ⇒ 0.004 % of 10 A (3.5 µV worst ⇒ 0.014 %) — **datasheet offset must be verified** |
| VBUS | 195.3125 µV/LSB, 44 V = code ≈ 225 280 |

Dominant error is the shunt itself (tolerance and tempco of the RSA-20-50 — **not in the repo, must be read from its datasheet/calibrated**), not the INA228. Calibration against the EDU34450A at the pack's operating points is already the project's rule.

Interface (J_SHUNT, keyed 4-pin, shielded twisted cable, sense level only):

| Pin | Net | Connects at the shunt |
|---|---|---|
| 1 | SHUNT_IN+ | Kelvin sense terminal, K1/source side |
| 2 | SHUNT_IN− | Kelvin sense terminal, load (6060B) side |
| 3 | VBUS_SENSE | bus tap at the load-side power terminal |
| 4 | PACK_NEG_SENSE | pack-negative sense return — this wire is the **only** place logic GND is bonded to the pack (single bond point, V10) |

Front end: 10 Ω ±1 % in each of IN+/IN− with 10 nF X7R across the inputs (fc ≈ 800 kHz) placed at the INA228 pins; **VBUS has its own wire and its own filter and is not tied after the IN− resistor** (the VBUS input current through a series resistor would otherwise appear as a shunt error); 100 nF at VS (0805 **[P]**); TVS on the connector side sized below the INA228's 85 V rating: **SMBJ45A [C]** (standoff 45 V ≥ 44 V; clamp ≈ 73 V < 85 V, **verify datasheet clamp curve**). A (A0/A1) address straps default to 0x40 (the address Rev.1 firmware uses); ALERT → PC7 with 10 kΩ pull-up. Kelvin routing: IN+/IN− are a matched, tightly coupled pair on one layer, guarded by ground, no vias in the pair, away from the buck and the coil.

---

## 8. Independent ADC voltage channel (new circuit)

`PACK+ ─ 75 kΩ ─ 75 kΩ ─ ADC_SENSE ─ 10 kΩ ─ GND`, then `ADC_SENSE ─ 100 nF ─ GND` at the node, `─ 1 kΩ ─ PA1`, clamp BAT54S [C: Nexperia BAT54S,215] to 3V3/GND at the pin.

| Quantity | Value |
|---|---|
| Ratio | 160 kΩ / 10 kΩ = **16:1** |
| Node voltage @ 44 V / 42 V / 30 V | **2.750 V** / 2.625 V / 1.875 V |
| ADC full-scale equivalent (3.3 V) | 52.8 V (headroom 20 % above the ceiling) |
| LSB (12-bit, 3.3 V) | 0.806 mV at the pin = 12.9 mV at the pack |
| Divider current / dissipation @ 44 V | 0.275 mA / 12.1 mW total; 5.7 mW per 75 kΩ — 0805 is fine |
| Source impedance | 75k+75k ∥ 10k = 9.375 kΩ (+1 kΩ series) — 100 nF at the node is the sampling reservoir; fc ≈ 170 Hz, settling τ ≈ 0.94 ms |
| Parts | thin-film 0.1 %, 25 ppm/K, 0805, 75 kΩ ×2 and 10 kΩ — **[C] Vishay TNPW0805-series (verify suffix: 0.1 %/25 ppm)** |
| Overvoltage on the pack input | 100 V at the connector ⇒ 0.64 mA into the clamp; the pin never exceeds ≈ 3.6 V |

Error budget (ratio only, worst case): 0.1 % resistors ⇒ **±0.19 %** ratio error; tempco 25 ppm/K each (50 ppm/K differential worst) over 40 K ⇒ ±0.20 %; clamp leakage (< 1 mV) ⇒ ±0.04 %; 12-bit ADC (total unadjusted error of a few LSB, [C] verify) ⇒ ±0.1 %; reference: VDDA 3.3 V ± buck tolerance — corrected in firmware by measuring VREFINT (factory-calibrated) ⇒ ±0.5 % [C verify]. Root-sum / worst-case total ≈ **±0.6 % typical, ±1 % worst** (≈ ±0.4 V at 42 V). That is adequate for its job (plausibility cross-check against INA228, 1.5 V agreement window in the firmware), **not** for metrology; the INA228 + EDU34450A remain the measurement truth.

Known issue to review: the upper clamp diode to 3V3 can back-feed the 3V3 rail if the pack is connected while the board is unpowered (≈ 0.27 mA through the divider). The 10 kΩ gate pull-down keeps the relay off in all cases and the MCU's reset keeps the pin Hi-Z, but the partially-powered state is undesirable. Options: (a) accept, documented; (b) clamp to GND only with a low-leakage zener (costs ≈ 0.3 % of leakage error); (c) add a series switch/diode at the J_PACKV input. Proposed: (a) pending the rail-state analysis at schematic review.

Independence: J_PACKV is a separate connector/wire pair from J_SHUNT, tapped at the pack/fuse side, so a broken or mis-wired INA228 sense lead is distinguishable from a real voltage change.

---

## 9. Relay driver calculation

Relay K1 = Durakool DG57CM-5021-76-1012-R [P], 12 V coil ≈ 90 Ω (listing data; **measure and record: V6**).

| Case | Coil current | Coil power |
|---|---|---|
| 11.4 V (after D3 drop, supply sag) | 127 mA | 1.44 W |
| 12.0 V | 133 mA | 1.60 W |
| 15.0 V (supply at top of adjust range, worst) | 167 mA | 2.5 W |

- **Q1 = IRLZ44NPBF [P] (TO-220-3, retained)** — owned, proven in Rev.1, logic-level; the drive is 3.3 V and the coil current is only ≈ 0.13–0.17 A, so the MOSFET dissipation is negligible (Vds drop ≈ I·Rds ≈ 0.17 × ≲ 0.1 Ω ≪ 20 mV even at a pessimistic Rds at 3.3 V). The IRLZ44N's datasheet gives Rds(on) at 4 V and above, not at 3.3 V — the margin comes from the tiny current, not from a rating at 3.3 V. A justified SMD replacement (60 V logic-level SOT-23/SOT-223) is possible but is a *change from a proven part* with no benefit except assembly cost; **kept as an open question**.
- **R_gate = 220 Ω** (Rev.1 proven): τ with Ciss ≈ 1.7 nF ≈ 0.4 µs; MCU pin current ≤ 15 mA at 3.3 V.
- **R_pulldown = 10 kΩ** gate → GND ⇒ **default state is relay OFF** whenever the MCU is in reset, unpowered, or Hi-Z. Gate leakage ≪ 1 µA, so the gate sits at ≈ 0 V.
- **Flyback D2 = 1N5408 [P]** across the coil, cathode on COIL_V (+12 V side), anode on COIL_SW (Q1 drain). Coil energy ≈ ½·L·I² ≈ 2–3 mJ (L assumed 0.2–0.4 H; coil inductance not in the repo) — trivial for a 3 A diode. A bare diode lengthens the contact release time (τ ≈ L/R ≈ 2–4 ms); acceptable here, and a series Zener can be added later if the relay datasheet's release time matters.
- **Test points:** TP_GATE (Q1 gate), TP_COILSW (drain), TP_COILV.
- **Connector J_COIL**: Molex Micro-Fit 3.0 2-pos (5 A/pin) — current margin 30×.

The coil supply is switched **low-side by Q1 and high-side interrupted by E-stop and ARM**: opening any one of the three de-energises K1.

---

## 10. E-stop / ARM / relay-feedback architecture

### Series chain (hardware, independent of the MCU)
`+12V → J_ESTOP (Eaton M22-PV-K02 NC, series) → ESTOP_OUT → J_ARM (C&K T102SHZQE, series) → COIL_V → K1 coil → Q1`
Both switch connectors carry ≈ 0.15 A at 12 V (switch ratings ≥ 24 VDC/2 A per the purchase list). Wire break, E-stop press or ARM off ⇒ coil de-energised, no MCU involvement.

### Sensing (read-only; none of these signals can drive anything)
Each stage is an opto-isolated, active-low status with an external pull-up, using **Vishay VO610A-1 [P]** (CTR bin 40–80 % at 10 mA — datasheet class value, **verify**; package: confirm from the invoice whether the purchased part is the 4-pin DIP — the design assumes through-hole DIP-4).

| Signal | LED fed from | Output | Logic | Firmware meaning |
|---|---|---|---|---|
| ESTOP_SENSE (U3) → PA0 | ESTOP_OUT (12 V present only if E-stop released and wiring intact) | pull-up to 3V3 | LOW = 12 V present = **healthy**; HIGH = tripped or broken wire | same contract as Rev.1 (PA0 LOW=healthy) |
| ARM_SENSE (U5) → PC10 | COIL_V (after ARM) | pull-up to 3V3 | LOW = armed path closed | valid only while ESTOP_SENSE is healthy (E-stop opens both nodes) |
| RELAY_FB (U4) → PC9 | K1 **load-side** terminal vs pack negative (J_FB) | pull-up to 3V3 | LOW = pack voltage present on the load side = contacts closed | same contract as Rev.1 (PC9 active-low) |

E-stop sense topology (decision 4) is open only in its *contact* sense: this opto stage works with a single NC block (E-stop must interrupt the coil loop itself and a second contact is not needed). If V6 shows two NC contacts, a second option — a dry NC to GND on J_ESTOP pins 3/4 with an on-board pull-up — is kept as **DNP footprints** only; the baseline needs no second contact.

Calculations (LED forward ≈ 1.2 V at 2 mA — datasheet class value, verify):

- **ESTOP/ARM LED resistor 5.1 kΩ:** I_F = 1.92 mA @ 11.0 V, 2.04 mA @ 11.6 V, 2.12 mA @ 12 V, 2.71 mA @ 15 V; R dissipation ≤ 37 mW @ 15 V.
- **RELAY_FB LED chain 2 × 6.8 kΩ (13.6 kΩ) + 1N4148 [P] antiparallel across the LED** (reverse protection: LED reverse rating ≈ 6 V): I_F = 1.68 mA @ 24 V, **1.97 mA @ 28 V, 2.12 mA @ 30 V**, 3.0 mA @ 42 V, 3.15 mA @ 44 V; total 138 mW @ 44 V, 67 mW per resistor — use 1206 0.25 W or 0805 ≥ 0.25 W-class resistors; two resistors in series so a single shorted resistor does not overdrive the LED. Minimum pack voltage for reliable feedback ≈ 24 V (I_F ≥ 1.7 mA) — below the 30 V supported minimum.
- **Output stage:** to guarantee saturation with the worst-case CTR (assume 10 % at I_F = 2 mA, end-of-life, hot ⇒ I_C available ≈ 0.2 mA), the pull-up must demand ≤ half of it: **R_pullup = 33 kΩ** ⇒ I_C needed = (3.3 − 0.4)/33 k = 0.088 mA (margin 2.3×). (A 10 kΩ pull-up would need 0.29 mA and could fail to saturate at low I_F — the Rev.1 value, if it was 10 kΩ, would need re-checking; V2.) 10 nF at the MCU pin + firmware debounce; rise time ≈ 33 k × 10 nF ≈ 0.33 ms.
- **Isolation/creepage:** the relay-feedback LED side is "pack level" (≤ 44 V DC): keep ≥ 2 mm creepage/clearance across the barrier and a PCB slot; the DIP-4 pin rows are 7.62 mm apart, which gives the barrier for free. Pack-side net names carry the `PK_` prefix so layout rules and DRC custom rules can target them.

### Fault philosophy
The MCU opens Q1 on any fault; E-stop/ARM/relay-feedback disagreement is a diagnostic/logging event, never a permission. Firmware may *refuse to start* if ESTOP is not healthy; it may never close K1 on the strength of ARM_SENSE or RELAY_FB. Mismatches (LOAD_EN high while RELAY_FB high for > debounce ⇒ welded/stuck/failed contacts) force fault state and report.

### Temperature probe (decision 3, conditional on V1)
J_TEMP: keyed 4-pin (3V3, GND, SDA2, SCL2), I²C2 only (kept off the INA228 bus so cable faults cannot take down measurement), ≤ 100 kHz, 4.7 kΩ pull-ups to 3V3 with DNP footprints, 100 Ω series damping in SDA/SCL, ESD diode array at the connector, test points TP_SDA2/TP_SCL2. At the probe end: TC74A5-3.3VAT (TO-220-5, address 0x4D) with **one Vishay VJ0805Y104JXXAT 100 nF [P] at the sensor's VDD pin ≤ 3 mm** and a keyed connector — a tiny probe PCB (a separate small design, same release gates). Cable-length check: with 4.7 kΩ and the 1 µs I²C standard-mode rise-time limit, bus capacitance may be ≤ ≈ 235 pF ⇒ ≈ 2 m of 80 pF/m shielded twisted pair after TC74 and connector capacitance (~20 pF). **Go/no-go limit proposed: ≤ 1.5 m; beyond that, or if V1 shows the TC74 cannot work, stop** — fallback architectures to document and propose: 10 kΩ NTC probe into a spare ADC pin (PA4), or a 1-Wire sensor. TC74 interface firmware: ≤ 100 kHz, init wait ≥ 300 ms (Inventory §5).

### Host interface
The Pi never touches safety hardware; the link is **USART2 (PA2/PA3) — ISO7721 digital isolator — CP2102N USB-UART — USB-C — Pi 5**, because (1) the existing UART protocol and firmware are proven, (2) no native-USB stack (PLL48 from HSI16 is not accurate enough for USB; it would need the HSE crystal, a new USB firmware stack and a new failure surface), (3) isolation prevents the Pi's earthed power/touchscreen cabling from forming a second ground path to the pack-bonded logic ground. The isolated side is powered from the host's USB VBUS via the CP2102N regulator — no isolated DC/DC. USB shield: 1 MΩ ∥ 4.7 nF to the host-side ground. ESD: USBLC6-2SC6 [C]. If you prefer to skip isolation, replace U7 with 0 Ω links (documented option, not baseline).

### Ground bonding
One bond point: pack-negative ↔ logic GND via J_SHUNT pin 4 only. Mounting holes isolated (plastic standoffs, NPTH); chassis earth never connected on this PCB. 12 V control supply return = logic GND (SELV, floating supply).

---

## 11. Connector / interface table

| Ref | Function | Pins | Candidate (all [C], verify) | Notes |
|---|---|---|---|---|
| J_12V | 12 V control input | 2 | Molex Micro-Fit 3.0 vertical header 43650-0200 ↔ housing 43645-0200 | 5 A/pin, keyed, latching; silk +/− |
| J_COIL | K1 coil | 2 | same family | |
| J_ESTOP | E-stop loop (+2 spare sense) | 4 | 43650-0400 ↔ 43645-0400 | pins 1–2 loop, 3–4 DNP option |
| J_ARM | ARM switch | 2 | 43650-0200 | |
| J_FB | relay load-side vs pack negative | 2 | 43650-0200 | pack-level, barrier side |
| J_SHUNT | IN+, IN−, VBUS, PACK_NEG | 4 | JST B4B-XH-A ↔ XHP-4 | shielded twisted pair, keyed |
| J_PACKV | independent divider input | 2 | JST B2B-XH-A ↔ XHP-2 | PACK+ (fused side), PACK−/GND |
| J_TEMP | remote TC74 probe | 4 | JST B4B-XH-A ↔ XHP-4 | 3V3, GND, SDA2, SCL2 |
| J_HOST | Pi 5 USB | USB-C receptacle | GCT USB4105-GF-A | UFP only, CC 5.1 kΩ ×2 |
| J_SWD | programming/debug | 1×6, 2.54 mm | standard header | pinout matched to the Nucleo's ST-LINK CN4 (VDD, SWCLK, GND, SWDIO, NRST, SWO — **verify against UM1724**) so the owned ST-LINK is the probe |
| J_AUX | spare GPIO | 1×6 | standard header | 3V3, GND, PB0, PB1, PB2, PA4 |
| — | Pi/display 5 V | not on this PCB | | external supply, spec in `docs/rev2/pcb/PI_POWER_ARCHITECTURE.md` |

No connector on this PCB carries battery discharge current.

Test points (labelled 1.5 mm pads, Keystone-class or plain SMD pad): **12V, 3V3, 3V3_A, GND (×2), SDA, SCL (INA228 bus), SDA2, SCL2, IN+, IN−, VBUS_SENSE, ADC_SENSE, GATE (relay-gate output), COIL_SW, COIL_V, ESTOP_SENSE, ARM_SENSE, RELAY_FB, UART_TX, UART_RX, NRST, SWDIO, SWCLK**; 5 V is absent by design (so no 5 V test point).

---

## 12. Preliminary BOM (manufacturer / MPN / footprint; status per §legend)

All counts are for one board; BOM freeze only after datasheets are checked. **No "fully specified" claim is made for [C] lines.** Capacitor quantity purchased (VJ0805Y104JXXAT), VO610A-1 quantity and package, and 1N4148 package (assumed DO-35 THT) need to be read from the invoice.

| Ref | Qty | Part | Manufacturer | MPN | Footprint | Tag |
|---|---|---|---|---|---|---|
| U1 | 1 | STM32L476RG MCU | STMicroelectronics | STM32L476RGT6 | LQFP-64 10×10 mm 0.5 mm | C |
| U2 | 1 | Current/power monitor | Texas Instruments | INA228AIDGSR | VSSOP-10 | C |
| U3, U4, U5 | 3 | Optocoupler | Vishay | VO610A-1 | DIP-4, 7.62 mm (confirm vs invoice) | P |
| U6 | 1 | 12→3.3 V buck | Texas Instruments | LMR14006 family, suffix TBD | SOT-23-6 | C |
| U7 | 1 | Digital isolator, 1 fwd/1 rev | Texas Instruments | ISO7721DR | SOIC-8 | C |
| U8 | 1 | USB-UART bridge | Silicon Labs | CP2102N-A02-GQFN24R | QFN-24 4×4 | C |
| U9 | 1 | USB ESD | STMicroelectronics | USBLC6-2SC6 | SOT-23-6 | C |
| Q1 | 1 | N-FET logic-level 55 V | Infineon | IRLZ44NPBF | TO-220-3 vertical | P |
| D1 | 1 | TVS 15 V (12 V rail) | Littelfuse | SMBJ15A | SMB | C |
| D_PK | 1 | TVS 45 V (shunt/VBUS side) | Littelfuse | SMBJ45A | SMB | C |
| D2 | 1 | Coil flyback | Vishay / onsemi | 1N5408G (as purchased) | DO-201AD | P |
| D3 | 1 | Series Schottky (reverse protection) | Vishay | SS14-class, TBD | SMA | C |
| D4–D6 | 3 | 1N4148 (FB LED reverse protection ×1; spare) | onsemi | 1N4148 | DO-35 THT (confirm) | P |
| D7 | 1 | Dual Schottky clamp | Nexperia | BAT54S,215 | SOT-23 | C |
| D8 | 1 | I²C ESD array | TBD (2-ch, ≤ 5 V, low C) | TBD | SOT-23/SOT-143 | open |
| C* | ≈ 25 | 100 nF 25 V X7R ±5 % | Vishay | VJ0805Y104JXXAT | 0805 | P |
| C_bulk | 2 | ≥ 22 µF, ≥ 35 V | TBD | TBD | | open |
| R_div | 3 | 75 kΩ, 75 kΩ, 10 kΩ 0.1 %/25 ppm | Vishay | TNPW0805 series, suffix TBD | 0805 | C |
| R_*, other | — | gate 220 Ω, pull-down 10 kΩ, FB 2×6.8 kΩ, 5.1 kΩ ×2, 33 kΩ ×3, 1 kΩ, 10 Ω ×2, pull-ups 4.7 kΩ DNP | TBD (e.g. Yageo/Vishay thick film 1 %) | TBD | 0805 (FB: 1206) | open |
| FB1 | 1 | Ferrite bead | TBD | TBD | 0603/0805 | open |
| J_* | see §11 | connectors | Molex / JST / GCT | per §11 | per datasheet | C |
| MH | 4 | M3 mounting (NPTH) | — | — | — | — |
| FID | 3 | fiducials | — | — | — | — |

External (not on this PCB): Eaton M22-PV-K02 E-stop, C&K T102SHZQE ARM, Durakool K1, RSA-20-50, fuse + holder, XT60, XDR-75-12, 6060B, Pi 5 + display + 5 V supply, probe PCB.

---

## 13. Open questions

1. **MCU:** approve A (direct STM32) with the first-article conditions in §3? (decision needed)
2. Host isolation: baseline isolated USB-UART (ISO7721 + CP2102N). Accept, or drop isolation?
3. Rail: buck-based 3V3 baseline vs LDO; accept the stated noise risk until measured.
4. ADC clamp back-feed (§8): option a/b/c.
5. Q1: keep IRLZ44NPBF (TO-220, THT) or switch to an SMD logic-level FET (justify with a datasheet at 3.3 V gate).
6. V6 (needed): Eaton block NC count and the **installed** relay marking; relay datasheet DC make/break at ≤ 44 V/10 A and the 15 A fault window.
7. V1 (needed): TC74 discriminators before the probe is frozen; accepted probe cable length ≤ 1.5 m?
8. Invoice facts (needed): VO610A-1 quantity/package, VJ0805Y104JXXAT quantity, 1N4148 package, other lines.
9. RSA-20-50: tolerance, tempco, Kelvin terminal geometry (datasheet); where the 6060B interface sits (still unidentified, GPIB path unconfirmed — no impact on this board).
10. XDR-75-12 adjusted output setting (affects TVS/buck margin).
11. Every [C] MPN/footprint/pin function verified against datasheets before schematic freeze (the schematic review gate).
12. Enclosure/mounting size: 4-layer, target ≈ 100 × 80 mm — to be fixed at placement.

---

## 14. Firmware impact (for review before the schematic freezes)

1. TC74 driver moves to **I2C2** (PB10/PB11) at ≤ 100 kHz; INA228 stays on I2C1 at 400 kHz (the Rev.1 TIMINGR gives ≈ 125–139 kHz — out of TC74 spec; Inventory §5).
2. USART2 stays on PA2/PA3 (no VCP any more; same baud).
3. New GPIO inputs: ARM_SENSE (PC10), INA_ALERT (PC7, optional), LED_FAULT (PA6). No input can set LOAD_EN.
4. VREFINT-corrected ADC scaling for the 16:1 channel.
5. Unit tests for "sensing can never enable the relay" (firmware tests in `Firmware/Tests`).
No firmware has been changed yet.

---

## 15. PCB productization plan (for the layout phase, after schematic approval)

- **4 layers justified:** L1 components/signals, L2 unbroken GND plane, L3 power (+12V, 3V3) and slow signals, L4 components/signals + GND pour. Reason: Kelvin pair and ADC reference need an uninterrupted ground plane; the buck's current loop must be small; creepage slots and a second routing layer for the isolator/USB.
- Zones: pack-side (J_SHUNT, J_PACKV, J_FB, TVS) at one edge; analog (INA228, divider, 3V3_A) next to it; digital in the middle; host side (isolator, USB) at the opposite edge; the barrier slot between pack-level LED sides and the logic side.
- Kelvin pair guarded by GND, no vias; ADC divider tap routed over solid GND and away from the buck inductor.
- 12 V coil path ≥ 0.5 mm; power ≥ 1.0 mm; creepage ≥ 2 mm for pack-level nets (PK_ netclass).
- Mechanical: 4 × M3 isolated holes, 3 fiducials, silk: `OSBAMS Rev.2 Controller`, revision/date, connector names, pin-1 and polarity marks, "≤ 44 V / ≤ 10 A (provisional)" legend, test-point labels.
- DFM/DFA for PCBWay: single-sided SMT where possible, THT limited to Q1, D2, optos, connectors, header; fiducials; paste-mask and drill checks; polarity marks for every diode/electrolytic; DRC custom rules for creepage.

---

## 16. Sequence and gates

1. **You review this document** and answer §13 (items 1–5 decide the schematic).
2. I create the Rev.2 KiCad **schematic** in `Hardware/Rev2_Controller/` (new project; Rev.1 files stay in `legacy/reference/`), plus a netlist-level polarity/rail-integrity check (the Rev.1 diode bug class), then stop for schematic review. **No routing before schematic approval.**
3. After approval: ERC, PCB layout, DRC, assembly review.
4. Only then a PCBWay package. `docs/rev2/pcb/RELEASE_GATES.json` stays all-false until each gate has evidence; **no final Gerbers/BOM/CPL** before that; the obsolete candidate package must not be used.

Documents in `docs/rev2/pcb/` that referred to revising the Rev.1 board (`REV2_SCHEMATIC_PCB_PLAN.md`) are superseded by this document where they conflict; the relay, Pi-power and approved-decision documents remain valid.

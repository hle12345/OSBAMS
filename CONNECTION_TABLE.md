# OSBAMS Hardware — Connection Table

**Doc OSBAMS-HW-001 Rev A · companion to `OSBAMS_schematic.svg`**

**DRAFT — not yet built or bench-verified.** Pin assignments match the
firmware source; component values are starting points to be finalised during
hardware design.

---

## ⚠ Part change from the current codebase

| | Current firmware | This schematic |
|---|---|---|
| Current/voltage sensor | **INA260** | **INA228 + external shunt RS1** |
| Bus voltage limit | 36 V (integrated shunt) | 85 V (shunt-less) |
| 42 V charged pack | **exceeds limit — cannot measure** | within limit |
| Driver | `ina260.c` (written) | INA228 driver **not yet written** — different I²C register map |

The INA260's 36 V bus limit is the single hazard documented throughout the
project (`LIMITATIONS.md` §10, `SYSTEM_SPECIFICATION.md` RSK-03). The INA228 is
the intended fix: it measures bus voltage up to 85 V and uses an external shunt
you size for the current and power you expect. Moving to it requires a new
firmware driver because the register maps differ.

---

## STM32L476RG GPIO assignments

These match the firmware exactly.

| Pin | Net | Function | Direction | Connects to | Source file |
|---|---|---|---|---|---|
| PB8 | I2C1_SCL | I²C clock | bidir | INA228, TC74 | `i2c_bus.c` |
| PB9 | I2C1_SDA | I²C data | bidir | INA228, TC74 | `i2c_bus.c` |
| PC8 | LOAD_EN | Load / contactor enable | output | Q1 gate | `load_driver.c` |
| PC9 | K1_AUX | Contactor feedback | input | K1 aux contact | `load_driver.c` |
| PA0 | ESTOP_SENSE | E-stop status | input | SW1 aux | (to be added) |
| PA2 | USART2_TX | Serial to host | output | ST-LINK VCP | `uart.c` |
| PA3 | USART2_RX | Serial from host | input | ST-LINK VCP | `uart.c` |
| PA5 | LED (LD2) | Status heartbeat | output | on-board LED | `main.c` |

`LOAD_EN` is active-high and defaults low. The pin is driven low **before**
being configured as an output, and has an internal pull-down, so a reset,
brown-out, or unprogrammed MCU leaves the load OFF (`load_driver.c`,
`Load_Init`).

---

## Power path (high-energy domain)

| Ref | Component | Notes |
|---|---|---|
| BT1 | Second-life pack | 10S NMC, 36 V nom, 42 V max, up to ~10 A |
| F1 | DC fuse, fast-blow | rating &gt; max discharge current, &lt; wiring limit |
| SW1 | Emergency disconnect | manual, latching, breaks the + rail; aux contact → PA0 |
| K1 | Contactor or SSR | main switching element, normally open; coil driven by Q1 |
| RS1 | Sense shunt | external, sized for max current and power dissipation |
| LOAD1 | DC electronic load | manual (v1) or remote; its internal cutoff is a firmware layer |

## Sensing

| Ref | Component | Interface | Address | Notes |
|---|---|---|---|---|
| U2 | INA228 | I²C | 0x40 | V/I/P/charge; IN+/IN− across RS1; VBUS from pack + |
| U3 | TC74 | I²C | 0x48–0x4D | pack surface temperature, 1 °C resolution |
| R1,R2 | I²C pull-ups | — | — | 4.7 kΩ to 3V3 (usually on the breakout boards) |

## Control

| Ref | Component | Notes |
|---|---|---|
| U1 | STM32L476RG Nucleo-64 | HSI16 → PLL, 80 MHz |
| Q1 | Logic-level N-MOSFET | low-side driver for K1 coil; gate from PC8 |
| D1 | Flyback diode | across K1 coil (inductive load) |

## Power / USB

| Rail | Source | Feeds |
|---|---|---|
| 5 V VIN | USB micro (ST-LINK) | on-board LDO |
| 3V3 | on-board LDO | STM32, INA228, TC74, pull-ups |
| Serial | USART2 over ST-LINK VCP | host PC |

**The pack's energy never reaches the logic rails.** The MCU and sensors are
powered entirely from USB 5 V / 3V3. The only coupling to the high-energy side
is the shunt sense lines (into the INA228), the contactor aux contact (into
PC9), and the E-stop aux (into PA0) — all low-current signals.

---

## Protection hierarchy (most independent first)

1. **F1 fuse** — passive, truly independent
2. **SW1 emergency disconnect** — manual, truly independent
3. **STM32-local cutoff** — independent of the PC, firmware
4. **Electronic-load internal cutoff** — independent of PC and STM32, but firmware
5. **PC supervision** — least independent

Layers 1–2 carry the safety argument. Layer 4 is an additional layer, not a
substitute for the fuse and disconnect.

---

## Still to be specified during hardware design

Fuse rating and interrupt capacity · shunt resistance, tolerance, and power
rating · contactor coil voltage and MOSFET gate-drive details · gate pull-down
and flyback diode values · connector types and wire gauge for the power path ·
star-ground layout · whether the electronic-load cutoff is firmware or a real
comparator · INA228 shunt calibration.

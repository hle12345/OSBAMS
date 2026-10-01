# OSBAMS Hardware Design

> **Naming:** Rev.2 calls the sides "A. battery / discharge power path" and "B. low-voltage control / instrumentation path" (see `docs/rev2/HARDWARE_FREEZE_CANDIDATE.md`).
>
> **Rev.2 note:** the Rev.1 design below is retained for history. Rev.2 power-path limits and the redesign needed to use more of the 6060B envelope are in `docs/rev2/LV_POWER_PATH_CAPABILITY.md`; targets above 60 V are out of scope.


**Build:** 0.9.0-dev1 — Engineering Prototype
**Status:** The architecture is defined and captured in a block schematic. The
design is **not frozen**: the contactor, E-stop, sensor front end, and power
supply are still being selected, and no board has been built or bench-verified.
This document describes the intended design and marks what remains open.

Supporting files:
- `hardware/schematic/OSBAMS_schematic.svg` / `.png` — block schematic
- `hardware/bom/OSBAMS_BOM.csv` — bill of materials (27 line items)
- `hardware/wiring/CONNECTION_TABLE.md` — pin/net connection table
- `hardware/Calculations/` — fuse, shunt, divider, thermal calculations (pending)

---

## 1. Design intent

OSBAMS is a bench fixture for discharging and measuring second-life 10S NMC
packs (36 V nominal, 42 V maximum, up to ~10 A). It is an engineering
instrument, not an EV drivetrain, so switching and protection are sized to the
actual energy of the pack under test — not to hundreds of amps.

Two guiding principles:

1. **Physical safety does not depend on firmware.** An E-stop must remove
   contactor-coil power by hardware, even if the firmware hangs, USB is removed,
   or the desktop freezes.
2. **The controller survives a pack disconnect.** Control power is separate from
   the pack, so the STM32 can save state, log the fault, and send the last
   telemetry when the pack is removed.

---

## 2. High-energy power path

```
Battery +  →  keyed connector (J1)  →  58 V DC fuse (F1)
           →  Blue Sea manual disconnect (SW1)
           →  DC contactor (K1)
           →  precision shunt (RS1) / INA228
           →  electronic load
           →  Battery −  (single-point star ground)
```

Notes and open items:
- **Connector (J1):** keyed/polarised (XT60 or Anderson) so the pack cannot be
  connected backwards casually.
- **Fuse (F1):** DC-rated with a **documented DC interrupt rating** at this
  voltage — not a generic automotive fuse. Value from `hardware/Calculations/`
  (pending).
- **Manual disconnect (SW1):** Blue Sea 6006, a physical service disconnect that
  breaks the pack rail.
- **Contactor (K1):** a **DC-rated** contactor with a published DC breaking
  rating for 42–60 V under load. The specific part is **not yet frozen** — this
  is the single most important remaining hardware selection, and it must not be
  a generic relay whose datasheet lacks a DC interrupt rating.
- **Shunt (RS1):** external shunt sized so full-scale current stays within the
  INA228's ±163.84 mV shunt range. Kelvin connection. Value pending calibration.

---

## 3. Control path (separate 12 V)

```
120 VAC  →  12 V supply (PS1)
         ├─────────────────────────────┐
         │                             │
  contactor-coil branch          5 V branch
   F2 control fuse                12→5 V converter
   ARM switch (SW2)               →  STM32
   E-stop NC (ES1)
   MOSFET low-side driver (Q1)  →  contactor coil (K1)
```

The E-stop is wired in series with the contactor coil supply as a
**normally-closed** contact, so opening it de-energises the coil directly,
independent of the STM32. The MOSFET (Q1) is only the low-side switch the STM32
uses to command the coil **within** that safety chain — it cannot override an
open E-stop. A flyback/suppression diode across the coil is required (see BOM).

Open items: the E-stop part, the 12 V supply, and the MOSFET are selected in the
BOM as starting points but not frozen.

---

## 4. Measurement and sensing

| Quantity | Device | Notes |
|---|---|---|
| Bus voltage, current, power, energy, charge | INA228 (U2) | primary metrology; 85 V bus covers 42 V pack; external shunt |
| Redundant voltage | STM32 ADC via protected divider | diverse cross-check, gross-error only, **not** certified-independent |
| Pack temperature | TC74 (U3) | I²C, 1 °C resolution |

The INA228 and TC74 share the I²C bus (PB8/PB9) with pull-ups. The ADC divider
scales the 42 V pack into the 3.3 V ADC range; its exact ratio, resistor
tolerances and voltage ratings, RC filter, input protection, and ADC sample time
are part of the analog design still to be finalised in `hardware/Calculations/`.

---

## 5. STM32 connections

| Signal | Pin | Direction | To |
|---|---|---|---|
| I²C SCL / SDA | PB8 / PB9 | bidir | INA228, TC74 |
| Load enable | PC8 | out | Q1 gate (contactor coil driver) |
| Contactor aux feedback | PC9 | in | K1 auxiliary contact |
| E-stop sense | PA0 | in | E-stop / disconnect status |
| UART TX / RX | PA2 / PA3 | bidir | USB virtual COM (host) |
| Heartbeat LED | PA5 | out | status LED |
| Redundant voltage | ADC channel | in | protected divider |

Full net-by-net detail is in `hardware/wiring/CONNECTION_TABLE.md`.

---

## 6. Protection (engineering review pending)

The following must be reviewed and specified before the design is frozen. They
are listed here so the gap is explicit, per the design review:

- DC fuse interrupt rating at the working voltage
- TVS / transient suppression on the pack input
- Reverse-polarity handling (keyed connector in V1; firmware polarity check)
- Contactor-coil flyback / bidirectional suppression
- Shunt Kelvin connections
- USB ESD protection
- Grounding and ground-loop control (single-point star)
- Connector touch safety, covered terminals, cable strain relief
- Enclosure with separation of high-energy wiring from logic

---

## 7. Bill of materials

See `hardware/bom/OSBAMS_BOM.csv`. Each line item carries manufacturer, part
number, rating, quantity, supplier, and Installed/Verified status. The
biggest-ticket item is the contactor. Every "Verified" field is currently No,
because nothing has been built. Before the design is frozen, the BOM must have a
DC-rated contactor and fuse with documented interrupt ratings, a finalised shunt
value, and an approved substitute for each critical part.

---

## 8. What "frozen" will require

The hardware moves from Engineering Prototype to a frozen revision only when:

- the schematic is complete (not a block diagram) and reviewed,
- the BOM has exact, in-stock parts with documented DC ratings,
- the protection review in §6 is closed,
- the board (PCB or well-organised perfboard) is built and matches the schematic,
- and the acceptance tests in `VALIDATION_REPORT.md` that touch hardware pass
  with recorded data.

Until then this remains a documented design, not verified hardware.

# Rev.2 hardware — freeze candidate

Status: **candidate, not frozen.** Exact installed part numbers are still to be read off the
hardware (§6; record them in `HARDWARE_ACCEPTANCE_RECORD.md`). Nothing here is bench-validated.

Naming: the two sides are **A. Battery / discharge power path** and
**B. Low-voltage control / instrumentation path** — not "HV/LV". The battery
side is only ~30–44 V for the packs on hand.

## 1. Envelope (layered; three different things)
| Layer | Value | Notes |
|---|---|---|
| 6060B instrument rating | 3–60 V, 60 A, 300 W | `I_max = min(60 A, 300 W / V)`; not an OSBAMS claim |
| **OSBAMS system ceiling (provisional)** | **44 V**, **10 A** | `config.OSBAMS_VALIDATED_MAX_VOLTAGE_V`, `SAFETY_MAX_CURRENT_A`; the finished system is **not** a "60 V system" |
| Firmware hard trip | 18.5 A, 60 °C | protection boundary, not an operating limit |
| Pack at 42 / 36 / 30 V (6060B) | 7.14 / 8.33 / 10 A | power-limited first |

## 2. A. Battery / discharge power path
```
USED Li-ion PACK (10S-class, ~30-42 V) → XT60 connector (adapter only if needed)
  → FUSE (15 A target) → BLUE SEA 6006 manual disconnect
  → DURAKOOL DG57CM relay (SPST-NO, 12 V coil; firmware records DG57CM-5021-76-1012-R)
  → CURRENT SHUNT (existing 20 A class, Kelvin sense, IN SERIES with the current)
  → AGILENT 6060B (3-60 V / 60 A / 300 W) → battery −
```
| Part | Rating used | Verification level |
|---|---|---|
| Blue Sea 6006 | 48 V DC max, 300 A continuous, **25 A switching** | manufacturer-spec values as shown in distributor listings; not read from a Blue Sea datasheet here |
| Durakool DG57CM | DC switching ~80 A@12 V, 60 A@36 V, 50 A@48 V, 145 V DC max, 6–50 V coils — **depends on the exact variant** | from the Durakool product listing; exact suffix of the physical relay NOT yet read |
| Fuse | 15 A target | part/holder not confirmed; needs a DC voltage rating ≥ 44 V (≥ 48 V preferred) |
| Shunt | 20 A class (RSA-20-50, 2.5 mΩ per repo) | exact installed part not yet confirmed |
| INA228 | bus 85 V | covers 44 V with wide margin |
| XT60 (Amass) | ~500 V DC; 60 A on 8 AWG, lower on thinner wire (spec-sheet summaries) | XT60 = supported. **Connector type does not determine test capability — the validated power path does.** |

Current-sensing redesign stays deferred (`CURRENT_SENSING_REDESIGN.md`).
Not to be bought/added: EV200, precharge, SB120, 90 A wiring — none increases what a 300 W load can test on these packs. **Relay note:** the BOM/purchase spreadsheets still list an Albright SW60; the firmware (`load_driver.c`) records the Durakool DG57CM-5021-76-1012-R as K1. The spreadsheets are stale — confirm the physical relay and update them.

## 3. B. Measurement, temperature, safety, power, UI
- **Measurement:** INA228 (primary V/I/P) and an independent ADC divider cross-check feed the STM32L476RG. Calibrate both against the EDU34450A.
- **Temperature:** TC74 (I²C, 1 °C) on the pack surface for the first build. **Thermal protection is not validated** until the TC74 works and is attached at a sensible location; later add shunt / relay / connector sensors.
- **Safety path (independent of the Pi):** 12 V → E-stop (NC) in series with ARM → relay-coil permission → DG57CM coil. In parallel, E-stop status, ARM status, relay command (MOSFET driver) and relay feedback go to the STM32. The Pi must never be the last thing between a fault and the relay opening.
- **Auxiliary power:** 120 VAC → Mean Well XDR-75-12 (12 V / 6.3 A, adjustable 12–15 V) → relay coil, controls, and 5 V rails. Pi 5 is specified for 5 V / 5 A and the Waveshare 10.1" panel ~5 V / 0.8 A, so size the converter **≥ 7 A** regulated, or better two rails: 5 V / 5 A for the Pi and 5 V / 1–2 A for display/control, keeping Pi transients off the measurement rail.
- **UI path:** STM32 → USB/UART → Raspberry Pi 5 (SQLite, OSBAMS application) → HDMI/USB touch → 10.1" screen. STM32 owns deterministic safety; Pi owns application/storage/UI. (The current software is the PySide6 desktop app; the Pi 5 deployment has not been tested.)
- **External instruments (outside the enclosure):** 6060B (the only one in the normal test power path); EDU34450A (reference measurement); EDUX1052G (validation-only observation).

## 4. Enforced in software now
44 V system ceiling and 10 A ceiling in `equipment/capability.py` (packs above 44 V are refused even though the 6060B accepts 60 V); the 15 A fuse, 20 A shunt and 48 V disconnect rating are in `REV2_POWER_PATH`; firmware `OSBAMS_DEFAULT_MAX_VOLTAGE_MV` (44000) is checked equal to the config ceiling by `tests/test_protocol.py`. Simulator scenarios are all 36–44 V lithium-ion.

## 5. Layered current limits (documented, not a defect)
| Layer | Value | Purpose |
|---|---|---|
| Battery profile | e.g. 1–7 A | per-pack test current |
| 6060B at the pack voltage | 300 W / V (7.14 A at 42 V) | instrument power limit |
| **OSBAMS operating limit** | **10 A** | normal operating/test boundary, enforced in software |
| **Fuse** | **15 A** | protects wiring/hardware against **abnormal fault current**, not normal regulation |
| Firmware hard trip | 18.5 A | absolute electronic protection boundary |
| Shunt rating | 20 A | measurement range |

A 15 A fuse with a 10 A software limit is a reasonable arrangement: the software controls
normal operation and the fuse is the passive last resort. Between 15 A and 18.5 A the fuse, not the
firmware, is what acts; that is accepted and documented rather than forced to match.

## 5b. Other items to keep in view
1. **Shunt placement** must be in series with the load current; high-side vs low-side must follow the existing INA228 PCB and grounding (not yet checked against the KiCad files).
2. **Blue Sea 6006 switching rating (25 A)** is fine at ≤ 10 A, but the relay does the switching; do not open the disconnect under load as routine.
3. **Relay ratings are variant-specific**; the relay current rating stays "unspecified" in the capability model until the datasheet for the installed part is read.
4. **Independent ADC divider and TVS are unfinished** (purchase list: "DO NOT ORDER YET"). Bench step C2 needs the divider built.
5. **12→5 V sizing**: the purchase list specifies ≥ 2 A for the DC/DC converter; a Pi 5 needs a much larger 5 V budget (see §3).

## 6. Needed before freezing (read off the installed hardware)
1. Relay part number (firmware: DG57CM-5021-76-1012-R) and its datasheet rating. 2. Shunt part number/spec (firmware: RSA-20-50). 3. The exact 12→5 V DC/DC converter(s) and the Pi 5 5 V supply. 4. Exact fuse and fuse-holder part numbers (DC rating). 5. XT60 supplier (genuine Amass). 6. The 6060B interface method. All go in `HARDWARE_ACCEPTANCE_RECORD.md`.

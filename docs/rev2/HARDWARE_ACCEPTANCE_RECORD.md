# Hardware acceptance record — OSBAMS Rev.2 power path and controls

Complete before the first battery connection (`FIRST_BATTERY_TEST_PROCEDURE.md` §1). Read every part number **off the
installed part**; the "expected" column is what the repository says, not proof. Anything not read stays UNKNOWN.
This record does not make the hardware BENCH_TESTED or HARDWARE_VALIDATED; it records what is installed.

## 1. Identification
| Field | Value |
|---|---|
| Unit / enclosure | |
| Date / operator | |
| Software commit / firmware version | |
| Photos stored at | |

## 2. Power path — as installed
| Ref | Part | Expected (source) | **As-installed part number** | Rating read from datasheet | Datasheet ≥ requirement? | Verified (Y/N) |
|---|---|---|---|---|---|---|
| J1 | Battery connector | Amass XT60 (BOM, purchase list: genuine XT60; datasheet figures: ~500 V DC, 60 A on 8 AWG, lower on thinner wire) | | | needs ≥ 10 A at the 12 AWG wire in use | |
| F1 | Main DC fuse | **15 A**, ≥ 58 V DC, Littelfuse/Eaton DC fuse (purchase list: "HOLD - verify part") | | | DC interrupt rating documented? | |
| FH1 | Fuse holder | Littelfuse 0FHM0001ZXJ-RED holder (per purchase record; verify DC V/A rating — V5) with fuse Littelfuse 0997015.WXN 15 A / 58 V | | | accepts the chosen fuse style? | |
| SW1 | Manual disconnect | Blue Sea 6006 (48 V DC max, 300 A continuous, 25 A switching — distributor listings) | | | ≥ 44 V system ceiling | |
| K1 | Relay / contactor | firmware records **Durakool DG57CM-5021-76-1012-R** (no aux contact). BOM/purchase spreadsheets still say Albright SW60 — stale | | | DC rating at ≥ 44 V / 10 A from the datasheet for THIS suffix; coil voltage 12 V? | |
| RS1 | Current shunt | firmware: **RSA-20-50** (2.5 mΩ, 20 A / 50 mV); purchase list: "15 A or 20 A / 50 mV candidate" | | | rating, tolerance, power | |
| W1 | Power wiring | 12 AWG, ≥ 60 V insulation | | | ampacity for the cable actually fitted | |
| — | Ring terminals / lugs | matched to studs | | | | |

Layered limits to confirm against the above: battery profile · 6060B 300 W/V · **OSBAMS operating limit 10 A** ·
**fuse 15 A (abnormal fault current only)** · firmware trip 18.5 A · shunt 20 A. Enter any rating that is *below* 10 A here: ____

## 3. Control and measurement hardware — as installed
| Ref | Part | Expected | As-installed | Notes |
|---|---|---|---|---|
| U1 | STM32L476RG Nucleo-64 | NUCLEO-L476RG | | |
| U2 | INA228 | Adafruit 5832 breakout | | shunt cal matches RS1? |
| U3 | TC74 | TC74A0-5.0VAT (address 0x48) | | **thermal protection unvalidated until working**; attachment point on the pack: |
| Q1 / D1 | coil driver / flyback | IRLZ44NPBF / 1N5408G (per purchase record; confirm installed — V8) | | |
| ES1 | E-stop (NC) | Eaton M22-PV-K02 (per purchase record; verify NC contact count — V6) | | wired in series with the coil supply |
| SW2 | ARM switch | C&K T102SHZQE SPDT (per purchase record; verify — V6) | | |
| PS1 | 12 V supply | Mean Well XDR-75-12 (12 V / 6.24 A / 74.88 W) | | purchase list only says "≥ 2 A, TBD" |
| DCDC1 | 12→5 V | undefined — decision pending, see `pcb/PI_POWER_ARCHITECTURE.md` (external 5 V recommended) | | **a Pi 5 needs a much larger 5 V budget — specify before powering the Pi from it** |
| VO610A feedback | K1 voltage feedback on PC9 | firmware: PC9 = VO610A, active low | | confirm wiring matches |
| ADC divider | independent voltage channel | **unfinished** (purchase list: "DO NOT ORDER YET") | | needed for bench step C2 |
| TVS | pack-input protection | **unfinished** (purchase list: hold) | | |

## 4. Visual and wiring checks (power off, pack not connected)
- [ ] Matches `HARDWARE_FREEZE_CANDIDATE.md` power path; shunt in series; sense leads on the Kelvin terminals
- [ ] High-energy wiring separated from logic; studs covered; strain relief; labels (polarity, fuse rating)
- [ ] Enclosure grounding present

## 5. Continuity / polarity (EDU34450A, power off)
| Check | Reading | OK? |
|---|---|---|
| + to − (must be open) | | |
| Relay contacts, coil de-energised (must be open) | | |
| Fuse continuity | | |
| Shunt resistance | ____ mΩ (expect ≈ 2.5 mΩ if RSA-20-50) | |
| Polarity marks match meter test of the connector | | |

## 6. Safety-function checks (no battery) — bench steps B2, B3
| Function | Expected | Result | Evidence file |
|---|---|---|---|
| Relay default state | open after reset/brown-out/unprogrammed MCU | | |
| E-stop de-energises the coil with the firmware dead (MCU held in reset) | coil off | | |
| ARM off → no relay command | | | |
| Sensor unplugged → FAULT, load-enable OFF | | | |
| Host disconnect → FAULT/safe state | | | |
| Relay close / open times (EDUX1052G, ≥ 10 repetitions) | recorded | | |

## 7. 6060B interface (remote control stays blocked until confirmed)
| Question | Answer |
|---|---|
| Rear-panel interface present (GPIB connector, any other)? | |
| GPIB address setting | |
| USB↔GPIB adapter / LAN↔GPIB gateway / GPIB-equipped PC available at SFSU? | |
| Result | `6060B_REMOTE_CONTROL = BLOCKED_BY_INTERFACE_CONFIRMATION` until a concrete interface is identified **and** commands are VERIFIED (`6060B_DRIVER_EVIDENCE.md`). The first battery test uses the manual front panel. |

## 8. Decision
☐ **ACCEPTED for the first relay-open / low-current test** — all rows in §2 and §3 for the power path and E-stop read and recorded, no rating below 10 A, §6 checks pass.
☐ **NOT ACCEPTED** — reasons: ____

Operator / date: ____________   Reviewer / date: ____________

Statuses BENCH_TESTED and HARDWARE_VALIDATED are not set here. They may be claimed only for what the executed
bench steps (`BENCH_CHECKLIST.md`) actually measured, with data stored.

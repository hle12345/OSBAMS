# OSBAMS Rev.2: PCBWay Readiness Gaps

**Verdict: NOT READY to send to PCBWay.** Every item below must be closed, or explicitly accepted by the owner with a recorded reason. No arbitrary parts have been chosen to hide a gap.
**Evidence base:** `REV1_HARDWARE_TRUTH_INVENTORY.md`. **Plan:** `PCBWAY_REV2_CHANGE_REQUEST.md`.
**Severity:** BLOCKER = unsafe or non-functional if shipped · HIGH = likely re-spin · MEDIUM = quality/cost.

## A. Gap register

| ID | Sev. | Gap | Evidence | To close |
|---|---|---|---|---|
| G-01 | BLOCKER | **Diode polarity conflict** (D1, D2, D3): symbol pin 1 = anode vs footprint pad 1 = cathode; PCB nets reversed vs schematic intent. PCBA would be dead or damaged | SCH `D_H`/`D_TVS` pins; PCB footprint `K` text, silkscreen band at pad 1; pad nets | Fix symbol/footprint, re-annotate, produce a net-vs-polarity check table; confirm Rev.1 as-built orientation (V7) |
| G-02 | BLOCKER | **Relay/contactor unknown and unrated.** Installed Rev.1 relay is only a firmware comment (Durakool `DG57CM-5021-76-1012-R`); SW60 never purchased or quoted; no datasheet in repo; DC breaking rating at 42 V / 10 A inductive unverified for both | `load_driver.c`; FUND; BOMX; no invoice | Read the installed label (V6); obtain SW60 variant, coil voltage/current, DC breaking rating, aux contact type from Curtis Instruments |
| G-03 | BLOCKER | **Power rails unresolved.** No 5 V rail on the PCB; Nucleo supply path, Pi 5 + 10.1" display supply, and the 12→5 V converter MPN/capacity are undefined | SCH (no 5 V net); FUND; RPT "Pololu 5 V" no MPN | Choose and size the converter; define Nucleo feed (E5V/VIN/USB); add the rail to schematic with fuse/PG |
| G-04 | BLOCKER | **Temperature subsystem unresolved.** Root cause not established; no recorded failure signature | FUND "offline fault"; no logs; Inventory §5 | Complete V1 bench discriminators; decide fix; amend F2 |
| G-05 | BLOCKER | **Safety-critical circuits not in KiCad**: E-stop sense (PA0), K1 feedback VO610A stage (PC9), ADC divider (PA1) | `estop.c`, `load_driver.c`, `adc_safety.c` vs SCH | Document as-built (V2, V4), draw, review, add protection |
| G-06 | BLOCKER | **ERC and DRC have not been run**; no saved reports; sandbox had no `kicad-cli` | project has no ERC/DRC exclusions or reports | Run `kicad-cli sch erc` and `kicad-cli pcb drc` on the Rev.2 revision, zero errors, warnings dispositioned |
| G-07 | HIGH | **BOM MPNs incomplete.** Symbols have no MPN/Manufacturer fields; values contain notes; BOMX designators collide with the schematic; PL lists "TBD" items | SCH properties; BOMX; PL | One BOM generated from KiCad fields; every line has Mfr + MPN + footprint; stale rows removed |
| G-08 | HIGH | **Purchased part ≠ footprint** for passives and connectors (C2/C3 0805 vs 5 mm disc; EB21A-02-C pluggable vs MX126 fixed; TSW-102-08-H-D-RA and BG040-14… match nothing) | INV-C/D vs PCB footprints | Choose parts by function, then footprint, then purchase; confirm pitch on datasheet |
| G-09 | HIGH | **Coil current unknown**; coil/12 V tracks are 0.3 mm and the project netclass (1.2 mm) is not applied | PCB tracks; `.kicad_pro` netclass patterns | Get coil data (G-02); re-route; check Q1, D2, D3, J2, E-stop contact ratings |
| G-10 | HIGH | **Current ceiling inconsistent** across FW (18.5 A), fuse (15 A), shunt (20 A), product (10 A), plus no 300 W limit in firmware | `app_config.h`; invoices; spec | Reset limits and add a power cap; recheck INA228 range/IMAX |
| G-11 | HIGH | **Pull-up/ownership of I²C pull-ups** undefined (none on PCB; presumed on Adafruit module) | SCH; CT "usually on breakout boards" | Verify module pull-ups; add on-board pull-ups with DNP option |
| G-12 | HIGH | **INA228/shunt interface unverified**: module IN+/IN−/VBUS wiring, onboard shunt state, pin order vs J4 not in KiCad | SCH J4 only 4 pins | V3; draw Kelvin connector; document |
| G-13 | HIGH | **Ground reference/bond undefined**; ADC divider and INA228 tie pack and logic references together | CT vs FW | Define bond point; document in schematic |
| G-14 | HIGH | **ARM switch not in KiCad or firmware**; position in circuit unknown | INV-B L12; no FW ref | V6; add to schematic; decide whether firmware sees it |
| G-15 | MEDIUM | **Fuse holder DC rating unknown** (0FHM0001ZXJ-RED) vs 42 V / 15 A | INV-B L3; no datasheet | Datasheet check (V5) |
| G-16 | MEDIUM | **Pack-side TVS (1.5SMBJ48A) not placed** anywhere; PL says "DO NOT ORDER YET" | INV-B L2; SCH text | Decide location; check clamp vs INA228 85 V |
| G-17 | MEDIUM | **1N4148 purpose undocumented** | INV-D L3 | V2 |
| G-18 | MEDIUM | **Raspberry Pi link undefined** in hardware (USB over ST-LINK vs J6 UART); J6 exposes 3V3 | CT; SCH J6 | Choose one link; relabel header |
| G-19 | MEDIUM | **Connector keying/orientation not enforced**; J5 note says "keyed", footprint is plain | SCH note; PCB | Polarised connectors |
| G-20 | MEDIUM | **No test points, fiducials, board ID silkscreen, or debug header** | PCB | Change Request I1, I3, I4, I8 |
| G-21 | MEDIUM | **Controller is a plug-in Nucleo module**; PCBWay cannot place it and must not be asked to. PCBA vs hand-assembly split undefined | SCH J5 | Define PCBA scope (SMD + selected THT) vs hand-fit parts |
| G-22 | MEDIUM | **Duplicate/stale project files** (root `OSBAMS PCB.kicad_pro` differs from `Hardware/Schematic/`) and missing `MODULE_STATUS.md` | repo | Consolidate |
| G-23 | MEDIUM | **No bench evidence recorded.** Every "working" claim is operator-reported; VR (2026-07-22) lists all hardware ACC rows NOT RUN | VR | Record bench results for the items being KEPT, using PASS/PARTIAL/NOT RUN |
| G-24 | MEDIUM | **XT60 battery interface** has no purchase record and is not on the PCB | BOMX | Confirm part; keep off-board |

## B. Manufacturing-readiness assessment (the ten questions)

| # | Question | Answer |
|---|---|---|
| 1 | Is the schematic complete? | **No.** It is internally consistent for what it contains (16 symbols; nets re-derived and every pin is on a net or an NC flag), but it models only the 12 V coil driver, I²C sensor header, TC74 and headers. It omits the feedback optocoupler, ADC divider, E-stop sense, ARM switch, fuses, 5 V rail, pack-side TVS, test points and MPN data. |
| 2 | Is the PCB layout complete? | **Complete for the Rev.1 netlist, not for Rev.2.** All 13 signal/power nets are routed (93 tracks, no vias, GND via B.Cu pour). Missing: the omitted circuits, test points, fiducials, silkscreen, correct power-track widths. Connectivity was checked by parsing the file, not by DRC. |
| 3 | Does ERC pass? | **Unknown. Not run.** No `kicad-cli` in the sandbox and no saved report. Static checks found no duplicate references and no dangling nets other than a single-pin `SPARE_GPIO` label. |
| 4 | Does DRC pass? | **Unknown. Not run.** Proxies: all tracks 0.3 mm (min rule 0.2 mm); TC74 pad gap 0.425 mm; outline closed 80 × 80 mm; no saved DRC exclusions; a ~0.8 mm dangling track stub on `SPARE_GPIO` at J5.8 (expect a `track_dangling` warning). The polarity conflict is **not** a DRC error (it is a symbol/footprint semantic error DRC cannot see). |
| 5 | Are all footprints assigned? | **Yes, all 16 schematic symbols have footprints** (stock KiCad libraries). But several do not match purchased parts (G-08) and three diode footprints conflict with symbol polarity (G-01). |
| 6 | Are all active Rev.2 components represented? | **No.** Missing: VO610A stage, ADC divider, E-stop sense, ARM, control fuse, 5 V converter, relay-aux input, probe connector, pull-ups, test points. The INA228 is represented as a module header only. |
| 7 | Are BOM MPNs complete? | **No.** Schematic has no MPN fields; only 6 of 16 values contain a recognisable part number; BOMX is stale and inconsistent with the schematic. |
| 8 | Is the temperature problem understood? | **No (partially).** Address, voltage and interface are mutually consistent for TC74A5-3.3VAT, so a variant mismatch explains it only if the wrong part was physically fitted. Firmware defects (SCL timing out of TC74 spec, short init window, lost status) are identified. Root cause needs the V1 bench steps. |
| 9 | What must change before PCBWay? | Close G-01 to G-06 (blockers) and G-07 to G-14 (high), then regenerate the BOM and run ERC/DRC. In short: fix diode polarity; draw the missing safety circuits; settle relay and 5 V rail; resolve TC74; real MPNs and footprints; DRC clean. |
| 10 | Revise the existing PCB or new layout? | **Revise.** The Rev.1 netlist (coil driver, I²C, 12 V input) is the proven part and is small and cleanly routed. Keep outline, mounting scheme and block placement. Expect to re-route the power tracks, add the missing circuits (likely fits in 80 × 80 mm but not verified), re-pitch connectors, and re-run the diode symbols. A from-scratch layout is not justified by the evidence. |

## C. Not done (by instruction or limit)

- No Gerbers, BOM, CPL or PCBWay order files were generated.
- No schematic/PCB files were modified.
- ERC/DRC not executed (tool unavailable).
- No Rev.1 hardware was inspected; all "Installed?" fields are from records only.

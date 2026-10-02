# Exact parts and source documents (RC2)

Status key: **verified** = value read from the manufacturer document that was supplied to the project; **owner-cited** = given by the project owner with a source, not independently re-read; **library** = footprint from the official KiCad 10 library (which cites the manufacturer drawing), not compared with the manufacturer PDF; **not verified** = no manufacturer document in the project. No MPN below is a placeholder; open items are called out.

| Ref | Function | Exact MPN | Source document | Status / what is still open |
|---|---|---|---|---|
| U1 | isolated 12 V -> 5 V / 8 A / 40 W converter | Mean Well **RSDW40F-05** | RSDW40/RDDW40 spec (2022-05-24, uploaded): pin drawing p.5, trim formula p.4, accuracy +-1 %, line 0.2 %, load 0.5 %, 0.05 %/C, 1.6 kVDC isolation, 1500 pF, ON/OFF open = on, input fuse 8 A delay type | **verified** (footprint implemented from the drawing; mirror/rotation to be eyeballed once in KiCad). Stock at PCBWay unknown -> **consign**, do not substitute |
| F1 | input fuse | Littelfuse **0407008.WR** (407 series, 1206, 8 A time-lag, 24 V, 60 A @ 24 VDC, 9 mOhm, I2t 24.12) | Littelfuse 407 datasheet rev 09/14/20 (uploaded) | **verified** incl. land pattern (1.0 x 1.8 mm pads, 3.5 mm span). Matches Mean Well's "8 A delay type" input-fuse recommendation |
| F2 | 5 V output fuse | Littelfuse **0451008.MRL** (Nano2 451, 8 A very fast-acting, 125 V, 7.7 mOhm cold, I2t 20.23) | Littelfuse 451/453 datasheet (uploaded) | **verified** incl. footprint. Protects the harness (16 AWG, 8.5 A Micro-Fit contacts). Output protection otherwise = the module's continuous short-circuit protection and its diode-clamp OVP (spec); no separate output TVS |
| TVS1 | 12 V bus surge clamp | Littelfuse **SMBJ15A** (DO-214AA, 15 V standoff, ~24 V clamp) | none for this MPN (the Bourns 1.5SMBJ datasheet in `docs/rev2/pcb/evidence/` covers the 1.5SMBJ series, not SMBJ) | **not verified** (standard JEDEC SMB footprint, library). Function is not critical: bus <= 14.4 V, module input rated 36 V (50 V / 100 ms surge). Owner may swap to the verified Bourns 1.5SMBJ15A (same SMB footprint) |
| J_IN, J_DISP | 12 V in; 5 V display feed | Molex **43045-0200** (shown as 430450200), Micro-Fit 3.0, right-angle, 2 circuits | owner-cited (8.5 A per contact, <= 10 mOhm); no Molex drawing in the project | footprint = KiCad library (pegs + drills). **Library, not PDF-verified**: fit-check with the physical part before volume order |
| J_OUT | 5 V to the interposer | Molex **43045-0400** (430450400), right-angle, 4 circuits (2 x 2) | as above | as above. Numbering runs along the rows: pins 1,2 = +5 V (outer row), 3,4 = GND (inner row) |
| (mates) | harness housings | Molex **43025-0200** (x2: J_IN, J_DISP), **43025-0400** (x2: J_OUT, interposer J1) | family naming | housing part numbers are the standard mates of the 43045 headers; **crimp terminals (43030 family) and wire are NOT selected** - need the Molex terminal sales drawing (16 AWG for the Pi branch). Open harness item; not on the PCB |
| J1 (interposer) | harness side of the interposer | Molex **43045-0400** | as J_OUT | as J_OUT |
| J2 (interposer) | Pi header socket | Samtec **SSW-120-01-S-D** (owner selection) | Samtec catalog page F-226 (uploaded, `ssw_th`): 40 positions, body 8.51 mm, lead style -01 tail 2.64 mm, 4.7 A per pin with 2 pins powered, 465 VAC / 655 VDC | **dimensions verified; plating letter open**: the catalog lists plating -F/-L/-G/-T and -S/-D as row options, so "-S" in the plating position is not a code I can match (it may be a distributor legacy code). Geometry is identical for every plating option; the owner confirms the orderable code at purchase (catalog-valid: SSW-120-01-L-D 10 uin Au, SSW-120-01-G-D 20 uin Au). Hole 1.0 mm / pad 1.7 mm carried over - check against Samtec's recommended hole at first fit |
| C1, C6 | 100 nF 50 V X7R 0603 | Murata GRM188R71H104KA93D | none | not verified (standard part) |
| C2 | input bulk 100 uF 50 V | Panasonic EEU-FM1H101 (8 x 11.5 mm radial) | none | not verified; library footprint D8 / 3.5 mm pitch |
| C4 | output bulk 680 uF 16 V | Panasonic EEU-FR1C681 (D10, 5.0 mm pitch) | none | not verified; library footprint D10 / 5.0 mm |
| C5 | 10 uF 25 V X5R 0805 | Murata GRM21BR61E106KA73L | none | not verified |
| R1, D1 | power-good LED, 1.5 k, green 0603 | Yageo RC0603FR-071K5L; Wurth 150060GS75000 | none | not verified |
| R2 | trim-DOWN pad | none - DNP, footprint only | Mean Well trim formula p.4 | **not used**: the calibrated setpoint is always above nominal; no part is purchased |
| R3 | trim-UP resistor TRIM -> -Vout | select-on-test, 0603 1 %: Yageo RC0603FR-0771K5L (nominal 71.5 k), -0761K9L (61.9 k), -0784K5L (84.5 k) | Mean Well trim formula (verified): Rt = a*R2/(R2-a) - R3, a = Vref*R1/(Vo'-Vref), Vref 1.24 V, R1 15.47 k, R2 5.1 k, R3 33 k, range +-10 % | **formula verified**; not fitted at assembly; value chosen per unit (`Trim_calibration_procedure.md`). Calibration kit values are E96 for the calculated 5.165-5.205 V setpoints |
| TP1-TP5 | test points | Keystone 5015 | none | not verified (SMT pad) |

## Pi-end and display connections
| Item | Selection | Status |
|---|---|---|
| Pi power connection | keyed interposer (2 x 20 SSW socket, key standoffs M2.5 x 20 mm, spacers M2.5 x 11 mm) | geometry verified against Pi 5 drawing RP-008347 and HAT+ spec RP-008281 (`Mechanical_verification.md`) |
| Display power | `J_DISP` direct feed (`Waveshare_integration.md`) | design decision; Waveshare data open |
| Pi pins | +5 V on Pi pins 2, 4; GND on 6, 9, 14, 20; all other 34 pins unconnected | verified by the netlist check |

## Items that need an owner document (none is a PCB footprint)
1. Molex 43030 crimp terminal sales drawing -> harness terminals / wire gauge.
2. Waveshare 10.1" DSI display datasheet (supply, current, power connector) -> display lead and J_DISP current confirmation.
3. Orderable Samtec code (plating letter) at purchase.
4. Optional: Littelfuse SMBJ15A datasheet (or accept Bourns 1.5SMBJ15A).

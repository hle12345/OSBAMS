# Exact parts and source documents (RC2)

Status key: **verified** = value read from the manufacturer document that was supplied to the project; **owner-cited** = given by the project owner with a source, not independently re-read; **library** = footprint from the official KiCad 10 library (which cites the manufacturer drawing), not compared with the manufacturer PDF; **not verified** = no manufacturer document in the project. **user-relayed** = manufacturer data relayed by the owner from the manufacturer page (not read locally from the source document). No MPN below is a placeholder; open items are called out.

| Ref | Function | Exact MPN | Source document | Status / what is still open |
|---|---|---|---|---|
| U1 | isolated 12 V -> 5 V / 8 A / 40 W converter | Mean Well **RSDW40F-05** | RSDW40/RDDW40 spec (2022-05-24, uploaded): pin drawing p.5, trim formula p.4, accuracy +-1 %, line 0.2 %, load 0.5 %, 0.05 %/C, 1.6 kVDC isolation, 1500 pF, ON/OFF open = on, input fuse 8 A delay type | **verified** (footprint implemented from the drawing; mirror/rotation to be eyeballed once in KiCad). Stock at PCBWay unknown -> **consign**, do not substitute |
| F1 | input fuse | Littelfuse **0407008.WR** (407 series, 1206, 8 A time-lag, 24 V, 60 A @ 24 VDC, 9 mOhm, I2t 24.12) | Littelfuse 407 datasheet rev 09/14/20 (uploaded) | **verified** incl. land pattern (1.0 x 1.8 mm pads, 3.5 mm span). Matches Mean Well's "8 A delay type" input-fuse recommendation |
| F2 | 5 V output fuse | Littelfuse **0451008.MRL** (Nano2 451, 8 A very fast-acting, 125 V, 7.7 mOhm cold, I2t 20.23) | Littelfuse 451/453 datasheet (uploaded) | **verified** incl. footprint. Protects the harness (18 AWG, 8.5 A Micro-Fit contacts). Output protection otherwise = the module's continuous short-circuit protection and its diode-clamp OVP (spec); no separate output TVS |
| TVS1 | 12 V bus surge clamp | Littelfuse **SMBJ15A** (unidirectional, DO-214AA / SMB) | Littelfuse SMBJ series datasheet, SMBJ15A row (**user-relayed**): VRWM 15.0 V, VBR 16.7-18.5 V @ 1 mA, VC max 24.4 V @ IPP 24.6 A (10/1000 us), 600 W, IR 1 uA @ VRWM, Tj -65..+150 C | **user-relayed manufacturer data**. Consistent with the 12 V bus (<= 14.4 V < VRWM, leakage <= 1 uA) and the module input (36 V; 50 V / 100 ms surge): VC 24.4 V < 36 V. Standard SMB land pattern (KiCad `D_SMB`), cathode = pad 1: matches. Not read locally |
| J_IN, J_DISP | 12 V in; 5 V display feed | Molex **43045-0200** (shown as 430450200), Micro-Fit 3.0, right-angle, 2 circuits | owner-cited (8.5 A per contact, <= 10 mOhm); no Molex drawing in the project | footprint = KiCad library (pegs + drills). **Library, not PDF-verified**: fit-check with the physical part before volume order |
| J_OUT | 5 V to the interposer | Molex **43045-0400** (430450400), right-angle, 4 circuits (2 x 2) | as above | as above. Numbering runs along the rows: pins 1,2 = +5 V (outer row), 3,4 = GND (inner row) |
| (mates) | harness housings | Molex **43025-0200** (x2: J_IN, J_DISP), **43025-0400** (x2: J_OUT, interposer J1) | family naming | standard mates of the 43045 headers (mating drawings not in the project) |
| (terminals) | harness crimp terminals | Molex **43030-0038** (18 AWG / 0.75 mm2, tin; -0039 / -0040 are the selective-gold variants) x 12 (J_IN 2, J_OUT 4, J_DISP 2, interposer J1 4) | **Molex ATS-638280200** (hand-crimp tool 63828-0200 application spec, uploaded): 43030-0038/-0039/-0040 = 18 AWG / 0.75 mm2, insulation OD 1.60-1.85 mm, strip 2.54-2.92 mm, conductor crimp height 1.00-1.10 mm (18 AWG), pull force >= 89 N, locator 63828-0275. The 24-20 AWG (-0001/-0007) and 30-26 AWG rows are **user-relayed** | **verified for 18 AWG**. **There is no 16 AWG 43030 terminal**: the RC2 harness is 18 AWG UL1061-type (insulation OD <= 1.85 mm), not 16 AWG. 18 AWG current rating of the terminal: not in the uploaded file (first-article temperature check) |
| J1 (interposer) | harness side of the interposer | Molex **43045-0400** | as J_OUT | as J_OUT |
| J2 (interposer) | Pi header socket | Samtec **SSW-120-01-L-D** | Samtec product page SSW-120-01-L-D (**user-relayed**): 40 pos, 2 rows, 2.54 mm, vertical THT, 10 uin Au mating, tin post, post 2.64 mm, insulation 8.51 mm, 4.7 A per contact, -55..+125 C; dimensions also **verified** from catalog F-226 (uploaded) | **closed**: exact orderable code (the earlier `-S-D` is replaced). Geometry unchanged (8.51 mm body, 2.64 mm tail). 4.7 A is Samtec's rating with two pins powered: 2.5 A on each of the two +5 V pins is 53 %. Hole 1.0 mm / pad 1.7 mm carried over - check against Samtec's recommended hole at first fit |
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

## Items that remain open (none changes the PCB)
1. Molex 43030-0038 terminal current rating with 18 AWG wire (not in the uploaded tooling spec): first-article temperature rise (B2).
2. Waveshare maximum input current is **not published** (0.8 A typical); first article measures it (D5).
3. Manufacturer pages for Waveshare, Samtec and Littelfuse SMBJ15A were relayed by the owner, not read locally: re-check against the PDFs if they are supplied.
4. Molex 43045/43025 drawings (library footprints, owner-cited ratings).

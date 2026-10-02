# Exact parts and source documents — carrier RevB

Status: **verified** = read from a manufacturer document supplied to the project; **user-relayed** = manufacturer data relayed by the owner, not read locally; **owner-cited** = given by the owner; **library** = KiCad 10 library footprint. No placeholder MPN.

| Ref | Function | Exact MPN | Source | Status |
|---|---|---|---|---|
| U1 | isolated 12 V → 5 V / 8 A | Mean Well **RSDW40F-05** | RSDW40/RDDW40 spec (2022-05-24): pin drawing, trim formula, ±1 % accuracy, line 0.2 %, load 0.5 %, 0.05 %/°C, 1.6 kVDC, ON/OFF open = on, 8 A delay input fuse | **verified**; consign unless PCBWay stocks it |
| F1 | input fuse | Littelfuse **0407008.WR** (8 A time-lag, 24 V) | Littelfuse 407 datasheet rev 09/14/20 | **verified** |
| F2 | 5 V fuse (Pi and display branches) | Littelfuse **0451008.MRL** (8 A, 125 V, 7.7 mΩ) | Littelfuse 451/453 datasheet | **verified** |
| TVS1 | 12 V surge clamp | Littelfuse **SMBJ15A** (DO-214AA) | Littelfuse SMBJ series datasheet, SMBJ15A row: VRWM 15.0 V, VBR 16.7–18.5 V @ 1 mA, VC 24.4 V @ 24.6 A, 600 W, IR 1 µA | **user-relayed** |
| J2 | Pi header socket | Samtec **SSW-120-01-L-D** | Samtec product page (40 pos, 2 rows, 2.54 mm, vertical THT, 10 µin Au, tin post 2.64 mm, insulation 8.51 mm, 4.7 A/contact); dimensions also in catalog F-226 | MPN **user-relayed**; dimensions **verified**; mounted from the underside |
| J_IN, J_DISP | 12 V in; display feed | Molex **430450200** (43045-0200) | owner-cited (8.5 A/contact, ≤ 10 mΩ); KiCad library footprint | library, not PDF-verified |
| (mates) | housings | Molex **43025-0200** ×2 | family naming | standard mate |
| (terminals) | crimp terminals | Molex **43030-0038** ×4 (18 AWG, tin) | Molex ATS-638280200 (uploaded) | **verified** for 18 AWG; no 16 AWG 43030 exists |
| C1, C6 | 100 nF 50 V | Murata GRM188R71H104KA93D | — | not verified |
| C2 | 100 µF 50 V | Panasonic EEU-FM1H101 | — | not verified |
| C4 | 680 µF 16 V | Panasonic EEU-FR1C681 | — | not verified |
| C5 | 10 µF 25 V | Murata GRM21BR61E106KA73L | — | not verified |
| R1, D1 | 1.5 k; green LED | Yageo RC0603FR-071K5L; Wurth 150060GS75000 | — | not verified |
| R3 | trim-UP, select-on-test, not fitted at assembly | Yageo RC0603FR-0771K5L (nominal) / -0761K9L / -0784K5L | Mean Well trim formula (verified) | formula verified |
| TP1–TP5 | test points | Keystone 5015 | — | not verified |
| hardware | enclosure standoffs / spacers | M3 × 20 mm F-F (×4), M2.5 × 11 mm F-F (×2), Pi standoffs M2.5 × 7.4 mm (×4) | computed (`Mechanical_fit_check.txt`) | computed |

Waveshare 10.1-DSI-TOUCH-A (SKU 30052): input 4.75 / 5.00 / 5.30 V, 0.8 A typical, maximum not published, 0–60 °C (**user-relayed**); package cables MX1.25 2PIN→2.54 3PIN and MX1.25 2PIN→MX1.25 4PIN.
Removed vs RC2: see `Changes_vs_RC2.md`.

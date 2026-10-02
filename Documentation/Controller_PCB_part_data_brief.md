# Controller PCB (OSBAMS Rev.2) — manufacturer data brief (extracted from uploaded sources)

Scope note: these parts belong to the **STM32 controller PCB #1**, not the Pi/Display power branch. That board's Rev.2 KiCad project is **not in this repository** (only the old Rev.1 `Hardware/Schematic/OSBAMS PCB.*` with generic CONN symbols is), so **no footprint comparison or protection-network closure was done**. This brief records what the uploaded documents actually say, and what is missing.

| # | Item | Received? | Usable for |
|---|---|---|---|
| 1 | Molex 22-27-2031 / 22-27-2041 | **No** (neither page uploaded; molex.com blocked here) | — |
| 2 | JST B4B-PH-K-S | Yes (`074fc31e-ePH.pdf`, PH series catalog) | footprint + ratings |
| 3 | GCT USB4105-GF-A | Yes (`f06fcb94-usb4105.pdf`, drawing) | ratings + drawing (footprint values need a controlled extraction) |
| 4 | Samtec FTSH-105-01-L-DV-K | Partly (`65e22790-clp-ftsh.pdf` = CLP/FTSH/FTS/FW **family spec only**) | ratings; **no series print / footprint** |
| 5 | Panasonic ERJP08 47 Ω / 10 Ω | **Wrong series** (`a16b00c0-RDO0000C337.pdf` = **ERJP6W, 0805**, "not recommended for new design") | — |
| 6 | Bourns 1.5SMBJ | Yes (`a8ad3c6e-1-5smbj.pdf`) | electrical + curves |

## JST B4B-PH-K-S (verified from the PH catalog)
Top-entry through-hole header, 4 circuits, 2.0 mm pitch. `B 4 B - PH - K - S` = top entry (B), 4 circuits, clinched/kinked (K), natural-white housing (S). PCB layout (viewed from the mounting surface): pitch **2.0 ±0.05 mm**, tolerance non-accumulating; holes **Ø0.7 +0.1/0 mm** (JST notes larger holes for fibreglass boards; "contact JST"); connector outline width **4.5 mm**, mounted height **8 mm**; reference offsets 1.95 mm and 1.7 mm from the outline to the pin row/edge; No. 1 circuit marked on the housing. Table: for 4 circuits **A = 6.0 mm** (3 pitches), **B = 9.9 mm** (A + 3.9; overall length). Ratings: **2 A AC/DC (AWG 24), 100 V**, −40…+105 °C, contact resistance **10 mΩ max initial / 20 mΩ after test**, wire AWG 32–24, insulation Ø0.5–1.5 mm, PCB thickness 0.8–1.6 mm, tin-plated posts.
Mating: PHR-4 housing with SPH-002T-P0.5(S/L) contacts (AWG 30–24 for -002T). Mating direction: from above (top entry).

## GCT USB4105-GF-A (from the drawing, rev B4, 2019/2023)
USB Type-C receptacle for USB 2.0, SMT, PCB top mount; ordering `USB4105-[GF|15|30]-A`: GF = gold flash (the "-GF-A" = gold flash, tape & reel; 800 pcs/reel). Current: **5.00 A collectively on VBUS pins, 6.25 A collectively on GND, 1.25 A on A5/B5 (CC), 0.25 A per other pin**; 48 V DC; contact resistance **40 mΩ max initial / 50 mΩ after test**; −40…+85 °C; mating force 5–20 N; 20 000 cycles; LCP insulator, stainless shell (shell tied to GND). Pins: A1/B12/A12/B1 GND, A4/B9/A9/B4 VBUS, A5 CC1/B5 CC2, A6 D+, A7 D−, A8 SBU1, B8 SBU2, B7 D−, B6 D+ (USB 2.0 only: both D± rows). The recommended PCB layout (shell/positioning-hole/solder-area dimensions; overall width 8.94, 8.64/8.34 body figures, Ø0.65 positioning holes, Ø0.50 holes, 2.56 ±0.04, tolerance ±0.05) is a dimensioned drawing and must be compared pad-by-pad against your footprint rather than read from text; I did not transcribe pad coordinates.

## Samtec FTSH-105-01-L-DV-K — only the family spec was supplied
`65e22790-clp-ftsh.pdf` is the CLP/FTSH/FTS/FW product specification (rev B, 2022): **4.2 A with one pin powered per row, 280 VAC**, gold −55…+125 °C, 500 cycles, normal force ≥ 30 g, LLCR change ≤ 15 mΩ after tests, reflow 260 °C, 3 passes max. It says prints/footprints are on samtec.com/products/ftsh. **No pad pattern, shroud/key, pin-1, or height data** are in the file — the series print and the vertical SMT footprint for the exact ordering code are still needed.

## Panasonic — wrong document
The file is **ERJP6W (0805)**: 0.5 W @ 70 °C, limiting element voltage 150 V, max overload 200 V, 10 Ω–1 MΩ ±1 % (E24/E96), 1 Ω–1 MΩ ±5 %, TCR ±200 ppm/K (R < 10 Ω: −100…+600), ESD 3 kV/150 pF, L 2.00 × W 1.25 × T 0.65, and it is marked **"Not recommended for new design"**. It is **not** the 1206 ERJP08 (0.66 W, 125 V, 500 V overload per your description). Do not use it for the 47 Ω / 10 Ω pulse calculation; please supply the actual ERJP08 datasheet (incl. pulse-limiting curves and the orderable codes for 47 Ω and 10 Ω ±1 %).

## Bourns 1.5SMBJ (verified)
DO-214AA (SMB), 1500 W (10/1000 µs), IFSM 100 A (8.3 ms, unidirectional), −55…+150 °C, ΔV_BR ≈ 0.1 % × V_BR per °C. Reverse leakage **I_R max 1 µA at V_RWM (25 °C)**; no leakage-versus-temperature curve in the file.
| Part | V_RWM | V_BR min–max @1 mA | V_C @ I_PP (10/1000) | V_C @ I_PP (8/20) |
|---|---|---|---|---|
| 1.5SMBJ12A | 12.0 V | 13.3–14.7 V | 19.9 V @ 75.4 A | 25.9 V @ 377 A |
| 1.5SMBJ13A | 13.0 V | 14.4–15.9 V | 21.5 V @ 69.8 A | 28.0 V @ 349 A |
| 1.5SMBJ15A | 15.0 V | 16.7–18.5 V | 24.4 V @ 61.5 A | 31.7 V @ 307.5 A |
Suffix A = 5 % unidirectional, CA = 5 % bidirectional; reel: blank = 13 in, -H = 7 in. Copper pad 5 × 5 mm assumed for the power curves.
Leakage error on a node = I_R × R_source: 1 µA × 47 Ω = 47 µV; × 10 kΩ = 10 mV; × 100 kΩ = 0.1 V (at 25 °C and V_RWM; rises with temperature — not given). Clamp error: V_C at the real surge current, not the I_PP rating — needs the circuit's surge level and series resistance.

## Needed to finish the controller-board verification
1. The **Rev.2 controller KiCad project** (schematic + footprints/PCB) so the five connector footprints (and which nets carry the 47 Ω / 10 Ω resistors and the TVS) can be compared.
2. Molex **22-27-2031 and 22-27-2041** product pages/drawings (3- and 4-position KK 2.54 mm headers).
3. Samtec **FTSH-105-01-L-DV-K series print + SMT footprint**.
4. Panasonic **ERJP08** (1206) datasheet with pulse curves and orderable codes.
5. The protection-network definition: which signals, surge/ESD level and source impedance, TVS location, ADC full-scale.

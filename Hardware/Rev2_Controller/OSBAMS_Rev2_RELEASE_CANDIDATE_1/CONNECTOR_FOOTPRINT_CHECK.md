# Connector footprint check — RC1.2 (2026-10-01)

**Status: PARTLY CLOSED.** J7 (JST) and J8 (GCT USB-C) are verified against the manufacturer drawings supplied (committed in `docs/rev2/pcb/evidence/`). **J5/J6 (Molex 22-27-2031/-2041) and J9 (Samtec FTSH-105-01-L-DV-K) remain OPEN:** the Molex files supplied are the product-detail web pages (they confirm circuits, 2.54 mm pitch, 3.56 mm tail, 1.60 mm PCB, partially shrouded/polarized to the mating part — all consistent with the footprints — but contain no dimensioned drawing; the sales drawings `022272031_sd.pdf` / `022272041_sd.pdf` they list are still needed), and the Samtec document supplied (CLP/FTSH/FTS/FW product specification) contains no print or footprint — it refers to samtec.com for them. The EB21A footprint is verified separately.

## Results
| Part | Footprint | Source | Result |
|---|---|---|---|
| JST B4B-PH-K-S (J7) | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | JST PH catalog ePH (p.1 through-hole layout, p.3 header table) | **PASS** — pitch 2.0 ±0.05 (pads at 0/2/4/6), recommended hole φ0.7 +0.1/0 (footprint drill 0.75 is inside that range; JST notes larger holes may be needed for hard PCB material), A = 6.0, B = 9.9 (outline x −1.95…7.95), body depth 4.5 with the pin row 1.7 mm from one edge (outline y −1.7…2.8), No. 1 circuit at the left viewed from the mounting surface (pin 1 at left, as placed), top-entry mating (cable/mating part comes from +Z; keep ≥ 8 mm above the board). Pad size 1.2 × 1.75 is a design choice (not on the drawing). |
| GCT USB4105-GF-A (J8) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | GCT drawing rev B | **PASS (footprint) + placement corrected.** Pad x positions ±0.25/0.75/1.25/1.75 (0.30 wide) and ±2.40/±3.20 (0.60 wide), pad length 1.15, A1…A12/B1…B12 order with A1 at the left viewed from the component side, shell slots 1.0 × 2.1 (hole 0.6 × 1.7) and 1.0 × 1.8 (hole 0.6 × 1.4) at ±4.32 (spacing 4.18), two NPTH φ0.65 at ±2.89 (5.78 apart), rear slot centre 2.60 from the PCB edge — all identical in the KiCad footprint. **Mismatch found and fixed:** the connector sat 0.275 mm too close to the board edge (the footprint's PCB-edge reference line was 0.275 mm outside the real edge); J8 moved from x = 96.600 to 96.325 mm so the shell slots are 2.60 mm from the edge and the front overhang is 0.6 mm as drawn. Signals: CC1/CC2 on A5/B5 with 5.1 kΩ, D± tied A6/B6 and A7/B7, SBU unused, all VBUS/GND pads and the four shell slots connected. |
| Samtec FTSH-105-01-L-DV-K (J9) | `PinHeader_2x05_P1.27mm_Vertical_SMD` | Samtec FTSH catalog page F-226 + CLP/FTSH specification (no print) | **OPEN (partly consistent)** — part number decodes as FTSH-1 / 05 pins per row (10 pins) / -01 (3.05 mm post) / -L gold / -DV double vertical / -K keying shroud; pitch 1.27, 0.40 mm square post, tail-to-tail width 5.84 mm (fits inside the footprint's 6.30 mm pad span: pads 0.74 × 2.40 at ±1.95). Land pattern and the key-slot position relative to pin 1 are not on these pages; the generic KiCad footprint is not keyed. |
| Molex 22-27-2031 (J5), 22-27-2041 (J6) | `Molex_KK-254_AE-6410-03A/04A_1x0N_P2.54mm_Vertical` | Molex product pages, supplied twice (no drawing) | **OPEN (partly consistent)** — circuits 3/4, vertical, through-hole, pitch 2.54, tail 3.56, PCB 1.60, partially shrouded, polarized to the mating part match; pad 1.74 × 2.19 / drill 1.19 / outline / pin-1 side need the sales drawing. |

## Extracted geometry of the footprints as placed
```
== J5 Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical rot 0.0 layer F.Cu
  pad   1 roundrect size 1.74x2.19 drill 1.19x1.19 rel (0.00,0.00) THT
  pad   2 oval      size 1.74x2.19 drill 1.19x1.19 rel (2.54,0.00) THT
  pad   3 oval      size 1.74x2.19 drill 1.19x1.19 rel (5.08,0.00) THT
  bbox 8.67 x 6.85 mm
  courtyard 8.71 x 6.89 mm
== J6 Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical rot 0.0 layer F.Cu
  pad   1 roundrect size 1.74x2.19 drill 1.19x1.19 rel (0.00,0.00) THT
  pad   2 oval      size 1.74x2.19 drill 1.19x1.19 rel (2.54,0.00) THT
  pad   3 oval      size 1.74x2.19 drill 1.19x1.19 rel (5.08,0.00) THT
  pad   4 oval      size 1.74x2.19 drill 1.19x1.19 rel (7.62,0.00) THT
  bbox 11.21 x 6.85 mm
  courtyard 11.25 x 6.89 mm
== J7 Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical rot 0.0 layer F.Cu
  pad   1 roundrect size 1.20x1.75 drill 0.75x0.75 rel (0.00,0.00) THT
  pad   2 oval      size 1.20x1.75 drill 0.75x0.75 rel (2.00,0.00) THT
  pad   3 oval      size 1.20x1.75 drill 0.75x0.75 rel (4.00,0.00) THT
  pad   4 oval      size 1.20x1.75 drill 0.75x0.75 rel (6.00,0.00) THT
  bbox 10.95 x 5.55 mm
  courtyard 10.99 x 5.59 mm
== J8 Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal rot 90.0 layer F.Cu
  pad     circle    size 0.65x0.65 drill 0.65x0.65 rel (-2.60,2.89) THT
  pad     circle    size 0.65x0.65 drill 0.65x0.65 rel (-2.60,-2.89) THT
  pad  A1 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,3.20) SMD
  pad  A4 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,2.40) SMD
  pad  A5 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,1.25) SMD
  pad  A6 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,0.25) SMD
  pad  A7 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,-0.25) SMD
  pad  A8 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,-1.25) SMD
  pad  A9 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,-2.40) SMD
  pad A12 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,-3.20) SMD
  pad  B1 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,-3.20) SMD
  pad  B4 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,-2.40) SMD
  pad  B5 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,-1.75) SMD
  pad  B6 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,-0.75) SMD
  pad  B7 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,0.75) SMD
  pad  B8 roundrect size 0.30x1.15 drill 0.00x0.00 rel (-3.68,1.75) SMD
  pad  B9 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,2.40) SMD
  pad B12 roundrect size 0.60x1.15 drill 0.00x0.00 rel (-3.68,3.20) SMD
  pad  SH oval      size 1.00x2.10 drill 0.60x1.70 rel (-3.10,4.32) THT
  pad  SH oval      size 1.00x1.80 drill 0.60x1.40 rel (1.07,4.32) THT
  pad  SH oval      size 1.00x2.10 drill 0.60x1.70 rel (-3.10,-4.32) THT
  pad  SH oval      size 1.00x1.80 drill 0.60x1.40 rel (1.07,-4.32) THT
  bbox 8.99 x 10.69 mm
  courtyard 9.03 x 10.73 mm
== J9 Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD rot 0.0 layer F.Cu
  pad   1 rect      size 2.40x0.74 drill 0.00x0.00 rel (-1.95,-2.54) SMD
  pad   2 rect      size 2.40x0.74 drill 0.00x0.00 rel (1.95,-2.54) SMD
  pad   3 rect      size 2.40x0.74 drill 0.00x0.00 rel (-1.95,-1.27) SMD
  pad   4 rect      size 2.40x0.74 drill 0.00x0.00 rel (1.95,-1.27) SMD
  pad   5 rect      size 2.40x0.74 drill 0.00x0.00 rel (-1.95,0.00) SMD
  pad   6 rect      size 2.40x0.74 drill 0.00x0.00 rel (1.95,0.00) SMD
  pad   7 rect      size 2.40x0.74 drill 0.00x0.00 rel (-1.95,1.27) SMD
  pad   8 rect      size 2.40x0.74 drill 0.00x0.00 rel (1.95,1.27) SMD
  pad   9 rect      size 2.40x0.74 drill 0.00x0.00 rel (-1.95,2.54) SMD
  pad  10 rect      size 2.40x0.74 drill 0.00x0.00 rel (1.95,2.54) SMD
  bbox 8.63 x 7.41 mm
  courtyard 8.67 x 7.45 mm

```

## Still to compare once the drawings arrive (J5, J6, J9)
- pad size, recommended hole/drill, annular ring, pad pitch and row spacing;
- body outline/courtyard against the manufacturer keep-out; pin 1 and numbering direction; polarization/key orientation vs the silkscreen;
- mating direction vs the board edge and neighbours (J5/J6 mate vertically; J9 needs the shroud notch toward the keyed side);
- tail length vs the 1.6 mm board.

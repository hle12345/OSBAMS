# Connector footprint check — RC1.2 (2026-10-01)

**Status: OPEN.** The manufacturer drawings for these five parts were not available to the build (manufacturer sites are blocked; none were supplied). Only the numbers relayed by the user (pitch, circuits, A/B dimensions, tail length) could be compared, and those match; pad/drill/shield/courtyard/pin-1/orientation geometry could **not** be compared with an official drawing, so `conn_footprints` stays UNVERIFIED and critical. The EB21A footprint is verified and not part of this item.

## What was compared (relayed numbers vs the KiCad stock footprints)
| Part | Footprint | Relayed manufacturer data | Result |
|---|---|---|---|
| Molex 22-27-2031 (J5) | `Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical` | 3 circuits, 2.54 mm, PCB 1.60 mm, tail 3.56 mm, shrouded/polarized | pitch / circuits match |
| Molex 22-27-2041 (J6) | `Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` | 4 circuits, same family | pitch / circuits match |
| JST B4B-PH-K-S (J7) | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | 4 circuits, 2.0 mm, A = 6.0 mm (= 3 × 2.0), B = 9.9 mm | pitch and A match; B not checkable from the footprint |
| GCT USB4105-GF-A (J8) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | USB-C, horizontal, VBUS 5 A, GND 6.25 A | named for the family; geometry not compared |
| Samtec FTSH-105-01-L-DV-K (J9) | `PinHeader_2x05_P1.27mm_Vertical_SMD` | 10 pins, 1.27 mm, vertical SMT, keyed | generic SMD 2×5 footprint; keying/row spacing not compared |

## Extracted geometry of the footprints as placed (for the drawing comparison)
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

## Checks to perform against each official drawing (drawings needed: Molex 22-27-2031 and 22-27-2041, JST B4B-PH-K-S, GCT USB4105-GF-A, Samtec FTSH-105-01-L-DV-K)
- pad size and recommended hole/drill diameter; hole-to-pad annular ring; pad pitch and row spacing;
- body outline and courtyard vs the manufacturer's keep-out; connector overhang past the board edge (J8 overhangs ~0.8 mm by design);
- pin 1 location and the numbering direction; polarization/key orientation vs the silkscreen;
- mating direction vs the board edge and neighbours (J5/J6/J7 mate vertically; J8 mates horizontally to the right edge; J9 needs the shroud notch toward the keyed side);
- shield/NPTH holes and tail length vs the 1.6 mm board.

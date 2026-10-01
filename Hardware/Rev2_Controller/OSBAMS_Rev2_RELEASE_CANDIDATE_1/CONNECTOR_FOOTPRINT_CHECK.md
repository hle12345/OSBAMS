# Connector footprint check — RC1.2e (2026-10-01)

**Status: CLOSED for the mechanical geometry, one residual.** J7 (JST), J8 (GCT USB-C), J9 (Samtec land pattern) and the Molex J5/J6 mechanical geometry (official 22-27-2031 3D model, PRO/E STEP/IGES + TraceParts STEP, read locally) are verified against manufacturer data supplied (committed in `docs/rev2/pcb/evidence/`). **Residual:** the J5/J6 PCB hole and pad (drill 1.19, pad 1.74 × 2.19) are not in any supplied Molex file (3D models, product pages, spec PS-99020-0088-001); they are the KiCad library values citing Molex sales drawing 022272021_sd.pdf, plausible against the 0.905 mm square-pin diagonal, and covered by first-article F7. The 4-position 22-27-2041 3D model was not supplied (same series). J9 key side is a first-article check.

## Results
| Part | Footprint | Source | Result |
|---|---|---|---|
| JST B4B-PH-K-S (J7) | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | JST PH catalog ePH (p.1 through-hole layout, p.3 header table) | **PASS** — pitch 2.0 ±0.05 (pads at 0/2/4/6), recommended hole φ0.7 +0.1/0 (footprint drill 0.75 is inside that range; JST notes larger holes may be needed for hard PCB material), A = 6.0, B = 9.9 (outline x −1.95…7.95), body depth 4.5 with the pin row 1.7 mm from one edge (outline y −1.7…2.8), No. 1 circuit at the left viewed from the mounting surface (pin 1 at left, as placed), top-entry mating (cable/mating part comes from +Z; keep ≥ 8 mm above the board). Pad size 1.2 × 1.75 is a design choice (not on the drawing). |
| GCT USB4105-GF-A (J8) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | GCT drawing rev B | **PASS (footprint) + placement corrected.** Pad x positions ±0.25/0.75/1.25/1.75 (0.30 wide) and ±2.40/±3.20 (0.60 wide), pad length 1.15, A1…A12/B1…B12 order with A1 at the left viewed from the component side, shell slots 1.0 × 2.1 (hole 0.6 × 1.7) and 1.0 × 1.8 (hole 0.6 × 1.4) at ±4.32 (spacing 4.18), two NPTH φ0.65 at ±2.89 (5.78 apart), rear slot centre 2.60 from the PCB edge — all identical in the KiCad footprint. **Mismatch found and fixed:** the connector sat 0.275 mm too close to the board edge (the footprint's PCB-edge reference line was 0.275 mm outside the real edge); J8 moved from x = 96.600 to 96.325 mm so the shell slots are 2.60 mm from the edge and the front overhang is 0.6 mm as drawn. Signals: CC1/CC2 on A5/B5 with 5.1 kΩ, D± tied A6/B6 and A7/B7, SBU unused, all VBUS/GND pads and the four shell slots connected. |
| Samtec FTSH-105-01-L-DV-K (J9) | `OSBAMS_Rev2:FTSH-105-01-L-DV-K` (custom, RC1.2e) | Samtec recommended PCB layout rev H + product drawing rev FX | **PASS (land pattern) — changed in RC1.2e.** The generic KiCad footprint had pads 0.74 × 2.40 on a 6.30 mm span; the drawing gives 0.74 × 2.79 on 6.86 mm (rows 4.07 mm apart, 1.28 mm gap), -K has no locating hole. Pin 01/02/03 mapping reproduced by a +90° rotation (same handedness). Key side not resolved by the drawings → first-article F6. |
| Molex 22-27-2031 (J5), 22-27-2041 (J6) | `Molex_KK-254_AE-6410-03A/04A_1x0N_P2.54mm_Vertical` | Molex 3D models of 22-27-2031 (STEP/IGES) + TraceParts STEP, read locally | **PASS (mechanical) — hole/pad residual.** Pitch 2.54, square pin 0.64, tail 3.56, body 7.62 × 5.80, friction-lock wall on one long side spanning the pin row: all match the footprint (Fab 7.62 × 5.80, silk 7.84 × 6.02). Drill 1.19 / pad 1.74 × 2.19 are the KiCad library values (not in the supplied Molex files); first-article F7. 22-27-2041 model not supplied (same series, body 10.16 mm). |

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
== J9 OSBAMS_Rev2:FTSH-105-01-L-DV-K rot 0.0 layer F.Cu
  pad   1 rect      size 2.79x0.74 drill 0.00x0.00 rel (-2.04,-2.54) SMD
  pad   2 rect      size 2.79x0.74 drill 0.00x0.00 rel (2.04,-2.54) SMD
  pad   3 rect      size 2.79x0.74 drill 0.00x0.00 rel (-2.04,-1.27) SMD
  pad   4 rect      size 2.79x0.74 drill 0.00x0.00 rel (2.04,-1.27) SMD
  pad   5 rect      size 2.79x0.74 drill 0.00x0.00 rel (-2.04,0.00) SMD
  pad   6 rect      size 2.79x0.74 drill 0.00x0.00 rel (2.04,0.00) SMD
  pad   7 rect      size 2.79x0.74 drill 0.00x0.00 rel (-2.04,1.27) SMD
  pad   8 rect      size 2.79x0.74 drill 0.00x0.00 rel (2.04,1.27) SMD
  pad   9 rect      size 2.79x0.74 drill 0.00x0.00 rel (-2.04,2.54) SMD
  pad  10 rect      size 2.79x0.74 drill 0.00x0.00 rel (2.04,2.54) SMD
  bbox 8.21 x 6.91 mm
  courtyard 7.45 x 6.95 mm

```

## Still to compare once the dimensioned drawings arrive (J5, J6; J9 key side on the part)
- pad size, recommended hole/drill, annular ring, pad pitch and row spacing;
- body outline/courtyard against the manufacturer keep-out; pin 1 and numbering direction; polarization/key orientation vs the silkscreen;
- mating direction vs the board edge and neighbours (J5/J6 mate vertically; J9 needs the shroud notch toward the keyed side);
- tail length vs the 1.6 mm board.

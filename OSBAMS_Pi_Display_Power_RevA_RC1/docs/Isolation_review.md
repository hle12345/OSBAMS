# Isolation review and power budget — RC1

## Isolation
- Primary nets: `+12V_IN`, `+12V_F`, `12V_GND` (all x ≤ 45 mm). Isolated nets: `5V_ISO_RAW`, `5V_PI`, `PI_GND`, `PG_LED_A` (all x ≥ 55 mm).
- Copper-free lane x = 45…55 mm on **both layers** (10 mm), full board height, dashed silk line at x = 50. Checked by script: min primary↔secondary copper gap = **10.00 mm**, no overlaps (`reports/ERC_equivalent_connectivity_report.txt`).
- Both ground pours are separate zones (B.Cu); no stitching, no Y-cap, no ferrite or resistor between `PI_GND` and `12V_GND`. The only primary↔secondary path is through U1 (1.6 kVDC rated).
- U1 pins: primary pins at x = 27.14, secondary pins at x = 72.86; no copper under the module body inside the lane.
- **Not verified:** Mean Well's required clearance/creepage under and around the module, and whether copper under the module body is allowed at all. Footprint geometry is a placeholder. Gate stays OPEN.
- 12V_GND is the XDR-75-12 return shared with PCB #1 by design. The Pi side is floating: leakage/common-mode considerations → see `Proposals.md`.

## Voltage budget at the Pi pins (ESTIMATE — assumptions, not measurements)
Assumptions: RSDW output 5.00 V (tolerance/load regulation not verified, assume −1 %), F2 hot resistance 12 mΩ (verify datasheet), PCB copper 2 × 3 mΩ, J_OUT contact pair 5 mΩ per rail-pair ×2 (board + Pi end ×2 parallel), 250 mm 18 AWG pairs 2 × 2.6 mΩ, Pi header contact 5 mΩ per rail-pair.

| Load | Path R (≈) | Drop | V at Pi pins (with −1 % source) |
|---|---|---|---|
| 3 A | ≈ 41 mΩ | 0.12 V | ≈ 4.83 V |
| 4 A | ≈ 41 mΩ | 0.16 V | ≈ 4.79 V |
| 5 A | ≈ 41 mΩ | 0.21 V | ≈ 4.74 V ← **below 4.75 V limit** |

**Finding:** margin is thin. Largest contributors: F2 (≈12 mΩ) and connector contacts. If bench measurement confirms <4.75 V at the Pi pins at real load, options in order: shorter/16 AWG harness, more parallel contacts, replace F2 with a lower-resistance part or remove it (RSDW already has short-circuit/overload protection), then — only if still needed and within Pi limits — TRIM. None applied in RC1.
Input side: 40 W / (12 V × ~0.88) ≈ 3.8 A at full load; F1 5 A is adequate at 12 V (at 9 V it would not be — the bus is 12 V). Include this in the XDR-75-12 (6.3 A) budget alongside PCB #1.
TVS1 SMBJ15A: 15 V standoff, ≈24 V clamp; within the module's 36 V input range.

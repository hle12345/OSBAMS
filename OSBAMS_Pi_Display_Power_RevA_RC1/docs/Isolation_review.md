# Isolation review and power budget — RC1

## Isolation
- Primary nets: `+12V_IN`, `+12V_F`, `12V_GND` (all x ≤ 45 mm). Isolated nets: `5V_ISO_RAW`, `5V_PI`, `PI_GND`, `PG_LED_A` (all x ≥ 55 mm).
- Copper-free lane x = 45…55 mm on **both layers** (10 mm), full board height, dashed silk line at x = 50. Checked by script: min primary↔secondary copper gap = **10.00 mm**, no overlaps (`reports/ERC_equivalent_connectivity_report.txt`).
- Both ground pours are separate zones (B.Cu); no stitching, no Y-cap, no ferrite or resistor between `PI_GND` and `12V_GND`. The only primary↔secondary path is through U1 (1.6 kVDC rated).
- Y capacitor / bonding: none, by decision (see README).
- U1 pins: primary pins at x = 27.14, secondary pins at x = 72.86; no copper under the module body inside the lane.
- **Not verified:** Mean Well's required clearance/creepage under and around the module, and whether copper under the module body is allowed at all. Footprint geometry is a placeholder. Gate stays OPEN.
- 12V_GND is the XDR-75-12 return shared with PCB #1 by design. The Pi side is floating: leakage/common-mode considerations → see `Proposals.md`.

## Voltage budget
Moved to `Voltage_drop_budget.md` (script-generated, assumptions listed). Headline: typical 4.87 V at 5 A; stacked worst case 4.65 V — gate OPEN.
Input side: 40 W / (12 V × ~0.88) ≈ 3.8 A at full load; F1 5 A is adequate at 12 V (not at 9 V — the bus is 12 V). Include it in the XDR-75-12 (6.3 A) budget alongside PCB #1.
TVS1 SMBJ15A: 15 V standoff, ≈24 V clamp; within the module's 36 V input range.

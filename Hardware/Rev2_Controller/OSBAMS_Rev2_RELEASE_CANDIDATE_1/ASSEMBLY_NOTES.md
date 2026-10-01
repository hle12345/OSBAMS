# OSBAMS Rev.2 Controller — Assembly notes (2026-10-01)

**RC1 - REVIEW CANDIDATE - NOT FOR FABRICATION.**

## Assembly summary
- 99 SMT/SMD-only footprints (top side) and 12 through-hole footprints (including connectors, 2 x VO610A-1 DIP-4, 2 x 1N4148 DO-35, JP1, mounting hole/test-point features are not parts).
- Parts are on the **top side only**; no bottom-side assembly. Test points are bare 1.5 mm pads (no component).
- **THT parts needing hand/selective soldering:** J1-J4 (Adam Tech EB21A-02-C), J5 (Molex 22-27-2031), J6 (22-27-2041), J7 (JST B4B-PH-K-S), JP1, U4/U5 (VO610A-1 DIP-4), D11/D12 (1N4148 DO-35), J9/J8 mixed SMT+THT shield.
- **Consigned vs sourced:** default is PCBWay-sourced. Owned parts that can be consigned (BOM column `PCBWay Source / Consign`): 2 x VO610A-1 (exactly the two needed), 2 x 1N4148, EB21A-02-C (5 owned, 4 needed), 1.5SMBJ48A (2 owned, 3 needed), SMBJ15A. VJ0805Y104JXXAT (2 owned) are used on the probe board.
- **Do not populate:** R1/R2 on the probe board (DNP). Everything on the controller BOM is fitted in the baseline (I2C2 pull-ups fitted).

## Polarity / orientation
- Diodes: pad 1 = cathode on every diode footprint (checked against the library geometry and the netlist; see `DFM_DFA_REPORT.md`). D1, D2, D5-D7, D9 SMA/SMB bars face pad 1; D11/D12 DO-35 band at pad 1 side; LEDs D3/D4/D10 pad 1 = cathode.
- U1 pin 1 dot top-left; U2 (MSOP-10) pin 1 dot; U3, U9, U10 SOT-23-6 pin 1; U6 QFN-20 pin 1 + exposed pad to GND_HOST; U7 SOIC-8 pin 1.
- J1-J4: pin 1 square pad, wire entry toward the board edge. **Footprint is PROVISIONAL (VERIFY_MECHANICAL_DRAWING).**
- J5/J6/J7 are keyed (KK 254 / PH). J9 SWD is a shrouded keyed header. J8 USB-C front face overhangs the right edge by ~0.8 mm.

## CPL
`OSBAMS_Rev2_RC1_CPL.csv` (SMT) and `..._CPL_ALL.csv` use KiCad footprint-origin positions/rotations (mm, bottom-left origin, y up). **PCBWay's pick-and-place library rotation conventions differ for some packages (SOT-23-6, QFN-20, LQFP-64, SOIC-8, MSOP-10, diodes): verify every rotation in PCBWay's CAM preview before accepting.**

## First-article note
Build 2-3 boards. Bring-up order: power (+12V, 3V3, 3V3_A ripple), reset/SWD attach, 80 MHz clock, GPIO, I2C scan (INA228 0x40), UART echo through the isolator, feedback/E-stop/ARM readbacks, relay driver with the real K1 coil at 12.0 V.

# OSBAMS Rev.2: Minimal Change Request for PCBWay PCBA

**Status:** PLAN ONLY. Not released to PCBWay. Blocked by `PCBWAY_READINESS_GAPS.md`.
**Basis:** `REV1_HARDWARE_TRUTH_INVENTORY.md` (read it first; IDs like INV-B and §5 refer to it).
**Principle:** preserve the Rev.1 circuits that were operator-reported working. Change only what is wrong, missing, or needed for manufacture. Revise the existing KiCad project; do not start a new layout.
**Product basis:** 30–42 V Li-ion scooter packs · XT60 only · Agilent 6060B as the only external load (300 W) · 10 A ceiling · STM32 is the safety authority · Raspberry Pi 5 + 10.1" touchscreen is UI/application · EDU34450A = calibration reference only · EDUX1052G = validation/debug only. Not reintroduced: OWON, NiMH/Medicool, Dat Bike, XT90, MV/HV/EV-pack hardware, future cyclers.

"Working" below means operator-reported (FUND, RPT). No item is claimed HARDWARE_VALIDATED.

## KEEP: unchanged or nearly unchanged

| ID | Item | Why | Condition |
|---|---|---|---|
| K1 | Contactor-coil low-side driver: Q1 IRLZ44NPBF, R1, R2, D2 topology (PC8 → R → gate, pull-down, flyback) | MPNs consistent across SCH/INV/FW; default-low fail-safe is a firmware contract | Polarity fix F1; confirm R1 value (220 Ω SCH vs 100 Ω PL) by reading the installed part |
| K2 | Hardware E-stop in series with the coil supply (J3 loop; Eaton M22-PV-K02) | Safety architecture (HD §3); switch purchased (INV-B L11) | Add sense circuit (F5) |
| K3 | INA228 on the shared I²C bus, module via header (J4), Adafruit 5832, addr 0x40 | Operator-reported working; FUND wants a second populated module for Rev.2, not a redesign | Verify pin order/straps (V3) |
| K4 | Bourns RSA-20-50 (2.5 mΩ) shunt, off-board, Kelvin sense to INA228 | MPN = firmware constant = invoice | none |
| K5 | Littelfuse 0997015.WXN 15 A / 58 V fuse; 0FHM0001ZXJ-RED holder | Rated above 42 V; 15 A > 10 A ceiling and < 20 A shunt | Holder DC rating check (V5) |
| K6 | Mean Well XDR-75-12 12 V supply | Purchased; 74.88 W | Load budget (G-07) |
| K7 | 12 V input network: D3 reverse-protect Schottky (SB560-E3/73), D1 SMBJ15A TVS, C1 ECA-1EM100I | Parts bought and sized | **Polarity fix F1 is mandatory** |
| K8 | STM32L476RG on a Nucleo module via 2×4 header (J5); firmware pin map PB8/PB9, PC8, PA2/PA3, PA0, PC9, PA1 | FUND buys a spare Nucleo, so Rev.2 stays module-based | Extend header (I3); PCBWay does not assemble the module |
| K9 | UART/USB host link over the Nucleo ST-LINK VCP; programming via Nucleo ST-LINK | Demonstrated path | none |
| K10 | 80 × 80 mm outline, 4× M3 holes, 2-layer 1.6 mm, GND pour on B.Cu | Fits the current board; avoids a new layout | Re-pitch holes to the final enclosure (I7) |

## FIX: known problems

| ID | Problem | Change |
|---|---|---|
| **F1** | **Diode polarity: symbols have pin 1 = anode, footprints have pad 1 = cathode** (D1, D2, D3) | Rebuild the diode symbols with KiCad-standard K = pin 1 / A = pin 2 (or remap footprint pads), re-run netlist update, **confirm by schematic-vs-board net table that cathodes land on +12V (D1), +12V/COIL_V (D2), +12V rail side (D3)**. Add cathode-band marking to silkscreen. This is a hard BLOCKER: as-is, PCBWay would place diodes per the footprint and the board fails. |
| **F2** | **Temperature subsystem offline** (root cause unproven, Inventory §5) | **Do not choose a new sensor until the bench discriminators (V1) are done.** Hardware: keep U1 = TC74A5-3.3VAT (matches SCH/FW/INV-C), add local 100 nF at the VDD pin (≤ 3 mm), add a test point on SDA and SCL at the sensor, and add on-board I²C pull-ups (R-SDA/R-SCL, 4.7 kΩ to 3V3, with a DNP option) so the bus no longer depends on the Adafruit module. Move the sensor to a **remote pack-mounted probe connector** (keyed 4-pin: 3V3, GND, SDA, SCL) with a series damping resistor and ESD/clamp if the final cable is > 30 cm. TC74 is pack-**surface** sensing; a board-mounted TO-220 cannot measure the pack. Firmware (not PCB): slow I²C to ≤ 100 kHz or use a TC74-compatible timing, extend the TC74 init window to ≥ 300 ms, and keep the raw init status. |
| F3 | Passive footprints don't match purchased parts (C2/C3: 0805 bought, 5 mm disc footprint) | Make all small passives SMD 0805 or 0603 and assign MPNs; keep THT only for power/connector parts. PCBWay places SMD more cheaply than hand-inserted THT. |
| F4 | Netclass not applied; coil/12 V tracks 0.3 mm | Fix netclass patterns to `/+12V`, `/COIL_V`, `/COIL_SW`, `/12V_IN` (or use wildcards); re-route at the 1.2 mm class (or pour) once coil current is known (G-09). |
| F5 | E-stop sense (PA0), K1 feedback (PC9), ADC divider (PA1) exist in firmware and not in KiCad | Draw all three on the board and wire them to J5: (a) E-stop sense with the external pull-up the firmware assumes and a series R/ESD clamp; (b) the VO610A feedback stage with real values (after V2/V4); (c) 150 kΩ / 10 kΩ divider, series R, clamp to 3V3, RC filter, test point. Divider resistors need voltage-rated parts (≥ 100 V) and 0.1 % / 25 ppm if used for calibration. |
| F6 | ARM switch (C&K T102SHZQE) and F2 control fuse absent from KiCad | Draw ARM as a keyed 2-pin connector in the coil-enable path (position per V6) and add the control fuse/holder footprint on the 12 V input. |
| F7 | Relay identity conflict; Rev.1 Durakool unverified | Plan for the **Albright SW60 + aux contact** per FUND, only after its DC breaking rating at 42 V / 10 A and coil current are documented (G-02, G-09). Keep both feedback options (VO610A stage and an aux-contact input) footprinted so Rev.2 does not depend on one decision; DNP the unused one. |
| F8 | 5 V rail missing; Nucleo + Pi 5 + display power undefined | Define one 12→5 V converter MPN sized for Pi 5 + display + Nucleo (G-03). Add a fused 5 V output connector for the Pi and a Nucleo supply feed on J5/E5V per the chosen scheme; add a power-good test point. |
| F9 | Firmware limits exceed hardware | `OSBAMS_DEFAULT_MAX_CURRENT_MA` 18500 → 10000; add a power limit ≤ 300 W; review INA228 range (ADCRANGE 0 vs 1) and `INA228_IMAX_MA` against the 20 A shunt. Not PCB work; tracked here because the hardware ratings drive it. |
| F10 | UART header net names and 3V3 on pin 1 | Rename to host-side perspective (or label TX→host RX), remove 3V3 from the host header (3V3 contention with a Pi), add silkscreen. |

## IMPROVE: product/manufacturing changes that leave proven circuits alone

| ID | Improvement | Detail |
|---|---|---|
| I1 | Test points | Add through-hole/SMD TPs: +12V, +3V3, +5V, GND ×2, SDA, SCL, COIL_SW, GATE, ADC_IN (divider tap), K1_FB, ESTOP_SENSE, TC74 VDD. 1.5 mm pads, silk-labelled, accessible for EDUX1052G probing. |
| I2 | Keyed connectors | Replace the plain 2×4 header, 1×4 headers and terminal blocks with polarised parts (shrouded headers, pluggable terminal blocks with distinct pitch/colour per function). Pick **one** terminal-block series and match footprint to the purchased/BOM part (G-08). |
| I3 | Programming/debug header | Nucleo ST-LINK stays. Add a 1×6 SWD/UART service header (3V3, GND, SWDIO, SWCLK, NRST, spare) only if it does not conflict with Nucleo pins. If the MCU later moves on-board, this becomes mandatory. |
| I4 | Silkscreen | Board name/revision/date, designators outside component bodies, pin-1 and polarity marks (diodes, caps, TVS), net names at every connector, 12 V "coil path" and "do not connect pack here" warnings. Currently only reference text exists. |
| I5 | Analog/Kelvin review | Route INA228 IN+/IN− as a tight pair from the shunt Kelvin terminals (not on this board, so provide a keyed Kelvin connector with the pair adjacent). Keep the ADC divider away from the coil/switching traces; guard the divider tap; single-point GND bond between logic and pack-negative documented. |
| I6 | Protection review | Pack-side: place the 1.5SMBJ48A at the pack entry with a path that does not run through the INA228 module; confirm clamp (≈ 77 V class) stays below INA228 85 V and that the 58 V fuse rating is respected. 12 V side: keep SMBJ15A. USB ESD at the host connector if one is added. Reverse polarity on the pack is by XT60 keying + firmware polarity check; document it. |
| I7 | Mechanical | Mounting holes M3 on a rectangular pattern fitting the 24 × 16 × 12 in enclosure and DIN-rail standoffs; keep-out for 12 mm standoffs; board edge ≥ 5 mm from the nearest THT body to the edge; ≥ 3 mm for panelisation rails. |
| I8 | DFM/DFA | Fiducials (3 global), pad-to-pad and silk-to-pad rules per PCBWay capabilities, all SMD on one side where possible, THT limited to power/connectors; add MPN, Manufacturer, DNP, and `LCSC/Mouser` fields to every symbol; remove generic symbol/value-as-note text ("(confirmed…)"). |
| I9 | Serviceability | Socketed or pluggable sensor/probe, DNP-able pull-ups and divider, the Rev.1 schematic note says the E-stop loop is closed with a jumper for "run"; Rev.2 must not offer a bypass jumper on the E-stop loop (the E-stop contacts alone close it). |
| I10 | Documentation hygiene | One KiCad project in one folder (the repo has `OSBAMS PCB.kicad_pro` at root that differs from `Hardware/Schematic/OSBAMS PCB.kicad_pro`); update BOMX/PL to the real MPNs; add `MODULE_STATUS.md` (referenced but absent). |

## REMOVE: prototype-only items with no Rev.2 purpose

| ID | Item | Why |
|---|---|---|
| R1 | Adafruit INA260 (4226) and any INA260 references | Superseded by INA228 (36 V limit). Purchased in INV-A; do not use. |
| R2 | 5 A and 10 A fuses (0997005, 0997010) | Not the selected fuse; 10 A trips at the ceiling. |
| R3 | Stale BOMX rows: TC74A0-5.0VAT, 1N4007, Schneider XB4BS8445, Blue Sea 5504/6006, "TBD" placeholders | Contradicted by purchases/firmware. |
| R4 | The 5.0 V TC74A1-5.0VCTTR parts | SMD, A1 address (0x49), do not match the TO-220 footprint or firmware. Keep as spares only if SMD is adopted and the address is changed in firmware. |
| R5 | Prototype notes embedded in Value fields ("(confirmed…)") | Replace with real fields. |
| R6 | Unconnected `SPARE_GPIO` net on J5 pin 8 | Reuse for a defined signal (e.g. PA1/PC9) or leave a labelled NC. |
| R7 | OWON driver and NiMH profile in desktop code | Out of PCB scope; listed so product scope matches the hardware (no code changed here). |
| R8 | 1N4148 ×2 (purpose undocumented) | Keep only if V4 shows it belongs to the VO610A stage. |

## VERIFY PHYSICALLY: the repository cannot establish these

| ID | Check on the Rev.1 unit |
|---|---|
| V1 | TC74 package marking, supply at pin 5, idle SDA/SCL levels, `I2C1_Scan` and raw `TC74_Init` status, SCL timing on a scope (Inventory §5 bench list). |
| V2 | Photograph and record the VO610A stage: resistor values, pull-up, 1N4148 role, pack-side connection point. |
| V3 | INA228 module: pin order vs J4, ALERT/A0/A1 straps, onboard shunt state, wiring of IN+/IN−/VBUS. |
| V4 | Installed ADC divider: values, tolerances, where the tap and ground return connect. |
| V5 | Fuse holder datasheet (DC voltage/current rating), installed fuse value, any TVS on the pack bus. |
| V6 | Installed relay label (full marking), coil current/resistance, ARM switch position in the circuit, E-stop contact block (NC count). |
| V7 | Installed diode orientation (bands) for D1/D2/D3. |
| V8 | Installed R1/R2/C2/C3 values and package types; terminal-block and header part numbers. |
| V9 | Nucleo ↔ J5 wiring (which Nucleo pins), how the Nucleo is powered, USB vs UART host path. |
| V10 | Single ground-bond point and any pack-negative ↔ logic-GND connection. |

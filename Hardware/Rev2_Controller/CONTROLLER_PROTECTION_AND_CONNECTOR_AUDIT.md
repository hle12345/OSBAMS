# OSBAMS Rev.2 controller — protection and connector audit (RC1.2e)

**Status: RC1.2e review candidate — NOT RELEASED FOR FABRICATION. NOT READY.** Baseline audited: RC1.2d (ERC 0, DRC 0, unconnected 0). Result of this audit: **two board changes** (J9 land pattern, D15 differential clamp); the INA228 limits are now **read from the TI datasheet** (±40 V differential is a true absolute maximum); the ERJP08 voltage ratings are read locally (500 V limiting / 1000 V overload; the relayed 125 V / 500 V does not match the catalog row) and the SMF12CA values are read from the Littelfuse datasheet; the resistor pulse capability (X2) and the **J5/J6 Molex geometry (X1) remain open**. Evidence tags: none = VERIFIED_LOCAL (read by the build), **[UR]** = USER_RELAYED_MANUFACTURER, **[UV]** = UNVERIFIED (assumption/estimate). Surge and ESD are treated as separate problems.

**Definition used for the audit** (bench lithium-ion characterization, not an automotive or mains product): PACK_INA/INA228 VBUS normal 30–42 V, ceiling 44 V, INA228 absolute maximum / common mode 85 V (TI datasheet); Kelvin pair on the RSA-20-50 (2.5 mΩ): 10 A → 25 mV, 18.5 A (firmware trip) → 46.25 mV, 20 A → 50 mV, INA228 IN+ to IN− differential absolute maximum ±40 V (TI datasheet §6.1); PACK_ADC divider 75 k + 75 k / 10 k (16:1): 30 V → 1.875 V, 36 V → 2.250 V, 42 V → 2.625 V, 44 V → 2.750 V, then 1 k to PA1 (cross-check channel only). Credible events: hot-plug and contact bounce, load/relay interruption ≤ 18.5 A, ESD at accessible connectors, one Kelvin lead early/open, reversed wiring where reasonably protectable. Not in scope: automotive load dump, lightning, mains surge.

**Protection classification:** hot-plug and load-interruption = `MODELED_PASS`; INA228 limits = **closed, VERIFIED_LOCAL (TI datasheet read)**; SMF12CA = **closed, VERIFIED_LOCAL** (capacitance not published); ERJP08 single-pulse µs–ms survival = open; ESD = `ESD_PROTECTION_OPEN`. The network as a whole is `MODELED_PASS / DATASHEET_VERIFICATION_OPEN`, not a full PASS. Reversed pack at J6 is a **documented prohibited connection** (J6 is a polarized KK header; the harness must not be reversible); no board area is spent on −44 V miswiring.

## PASS

1. **J9 land pattern now matches the Samtec drawing** (details in appendix D). Samtec recommended PCB layout rev H: pads 0.74 × 2.79 mm, 1.27 mm pitch, 6.86 mm pad span, -K has no locating hole. RC1.2d used the generic KiCad pads 0.74 × 2.40 mm on a 6.30 mm span (0.39 mm too short, 0.56 mm too narrow a span). RC1.2e uses a custom footprint `OSBAMS_Rev2:FTSH-105-01-L-DV-K` built from the drawing; pin 1 / pin 2 / pin 3 positions were mapped to the drawing view by a 90° rotation (same handedness, no mirror).
2. **Hot-plug onto a live 44 V pack (appendix B1):** worst case over 3 harness inductances × 3 TVS capacitances — see the table: the 85 V limit holds with large margin because 44 V stays below the TVS knee (VBR min 53.3 V); the resistors limit ringing.
3. **Interruption of ≤ 18.5 A (appendix B3):** INA228 node ≤ 76.5 V even in the gross over-estimate where the whole interrupted current is forced into the sense TVS with no series resistor (limit 85 V); resistor energy ≈ ½·L·I² = 0.34 mJ for 2 µH (integrator ≤ 0.37 mJ).
4. **Normal-operation error of the new resistors** (appendix B7) stays inside the 0.1 % cross-check budget: R41 57 Ω into the VBUS input gives ≤ 0.007 % gain error (removed by calibration); Kelvin R42/R43/R11/R12 are matched and carry only bias/leakage.
5. **PA1 stays in range for every event that reaches the ADC divider** (appendix C): normal 1.875–2.750 V; clamped maximum ≈ 3.35 V; reversed pack ≈ −0.3 V with 0.27 mA injection.
6. **One-Kelvin-lead-open / late-connect is bounded** (appendix B5): with the INA228 powered and C26 intact, the 100 nF across the pins keeps the difference of a fast step at ≈ 1 % (≈ 0.4 V for 44 V) and the INA228's own differential input path holds it at ≪ 1 V afterwards; with D15 fitted the difference is also bounded to its clamp level (≤ about 15–20 V, limit 40 V) when the INA228 is unpowered / power-cycling or C26 has failed open — the cases where nothing else holds the open pin.
7. **Board checks after the RC1.2e changes:** ERC 0, DRC 0 (electrical and silkscreen), unconnected 0, netlist vs PCB 0 mismatches over 405 pads, diode polarity none wrong, host/controller isolation ≥ 1.0 mm on every layer (0.998 mm measured = polygon rounding, KiCad DRC enforces the exact rule), isolation-rule activity check passes. (Numbers in `NETLIST_CHECK.txt`, `ISOLATION_CHECK.txt`, `ISOLATION_RULE_CHECK.txt`, `DRC_REPORT.rpt`, `ERC_REPORT.rpt`.)

## CHANGE REQUIRED

**Made in RC1.2e**

| # | Change | Why | Effect on the board |
|---|---|---|---|
| C1 | J9 generic KiCad footprint → `OSBAMS_Rev2:FTSH-105-01-L-DV-K` (pads 0.74 × 2.79, rows 4.07 mm apart) | Samtec recommended layout rev H differs from the generic footprint (pad length 2.40 → 2.79 mm, pad span 6.30 → 6.86 mm) | J9 breakout re-routed: SWCLK and NRST moved into the 1.28 mm gap between the pad rows (x = 160.35), NRST via moved west to (155.8, 140.08); nothing else on the board moved (`design/rc12e_patch.py`) |
| C2 | **D15** (SMF12CA, bidirectional TVS, Diode_SMD:D_SMF) across INA_INP / INA_INN, placed at (119.25, 120.75) with 4 vias on the INA_INP/INA_INN copper | INA228 IN+ to IN− differential absolute maximum is ±40 V (TI §6.1); D5/D6 are ground-referenced 48 V TVS and cannot limit a difference. With the INA228 unpowered (or power-cycling) and one Kelvin lead open, nothing holds the open pin and it can drift 44 V away from the connected one; C26 failing open, or a one-sided ≈ 80 V ESD/clamp pulse that C26 does not fully absorb, create the same stress. D15 is a cheap backstop for these cases | +1 part (SMF12CA, SOD-123FL; pads identical to KiCad D_SMF), 2 pads, 4 vias, ≈ 8 mm of routing on F.Cu / B.Cu / In2.Cu; the rest of the routing is unchanged (`design/rc12e_merge.py` takes only the INA_INP/INA_INN copper from an incremental autoroute) |
| C3 | Evidence register: `rs_pulse_rating` reverted to **UNVERIFIED / critical** (catalog DC and ESD ratings are kept as the separate VERIFIED_LOCAL entry `rs_catalog_ratings`); `ina228_diff_max`, `ina228_cm`, pin map, SHUNT_CAL, ranges, offset, bias, supply and the new `ina228_zvbus_rdiff` are now VERIFIED_LOCAL from the TI datasheet (committed in `docs/rev2/pcb/evidence/`); new entries `tvs_diff` (UV, critical), `esd_connector`, `conn_samtec` (VERIFIED_LOCAL, land pattern), `conn_samtec_key` (UV) | Pulse capability of the 47 Ω / 10 Ω resistors has not been checked against the Panasonic pulse-data document | documents only |
| C4 | `REV2_CALCULATIONS.md` §2b result paragraph rewritten: it said PASS for the defined transient; it now says hot-plug and interruption bounds pass and the protection is **not closed** | the previous wording over-stated closure | documents only |

**Still required before the board is a fabrication candidate** (not done here because the data does not exist yet): see *REMAINING FABRICATION BLOCKERS*. One firmware item belongs to the first article: an INA228 reading outside ±163.84 mV (ADCRANGE 0) or an INA228 / ARM-sense cross-check mismatch must be treated as a sensor fault (load off), because an open Kelvin lead now produces a saturated or garbage shunt reading rather than a hardware failure. No firmware change is made in this round.


**ESD re-evaluation (ERJP08 row of the Panasonic catalog, read locally: 500 V limiting / 1000 V overload; the relayed "125 V / 500 V" does not match it — 125 is the row's terminal temperature in °C).** The existing order *connector → R41–R43 → TVS* makes the resistors carry an ESD pulse. At ±8 kV contact the model puts ≈ 1.3 kV across R41 (≈ 0.37 kV across R42/R43), above the 1000 V overload rating of the 47 Ω part (≈ 0.37 kV on the 10 Ω parts is inside both ratings), and the clamp node at ≈ 79–80 V (85 V limit) before the first-nanosecond overshoot; the ±15 kV air upper bound is ≈ 86–88 V and ≈ 1.9 mJ. The overload rating is a 5 s test, not a pulse rating, so this is not proof of failure — but nothing in the documents supports the event. **Recommendation: if J5/J6 pins can be touched bare, a fast low-capacitance TVS directly at the J5/J6 pins ahead of R41–R43 becomes a required RC1.3 change; if J5/J6 are always mated to a harness inside the enclosure, document that assumption and keep ESD as the first-article test F1.** No board change is made in RC1.2e. Status: `ESD_PROTECTION_OPEN`.

## FIRST-ARTICLE VALIDATION

| # | Test | Pass criterion |
|---|---|---|
| F1 | **ESD at the connectors** (IEC 61000-4-2, target ±8 kV contact / ±15 kV air on J5, J6 pins and shells, stepping 2 → 4 → 8 kV; INA228 and the MCU powered, a read-back of INA228 MANUFACTURER_ID / shunt voltage after every discharge, scope on INA_VBUS and across IN+/IN−) | No reset, no INA228 register upset, no permanent offset shift (> 10 µV at 0 A), resistors intact; if it fails, fall back to a fast connector-level TVS ahead of R41–R43 (RC1.3). Simulation cannot prove the first-nanosecond peak (appendix B4). |
| F2 | Shunt voltage at 0 A with D15 fitted, 25 °C and warm (≈ 60 °C), compared with D15 removed/lifted on a spare board | Offset change ≤ 10 µV (= 4 mA of shunt current) between D15 fitted and lifted; D5/D6/D15 leakage combined, cold and warm |
| F3 | One Kelvin lead open / connected late, 44 V current-limited source, scope across INA_INP − INA_INN and INA_INN to GND | |Vdiff| ≤ 20 V in steady state and during connect; shunt reading goes out of range and the firmware sensor-fault path trips |
| F4 | Hot-plug of the sense harness at 42–44 V with the real harness, 1 µs/div and 10 µs/div | INA_VBUS pin ≤ 60 V, INA_INP/INN pin ≤ 60 V, no step in INA228 calibration after 50 plugs |
| F5 | Resistor stress after F1, F4 and 20 bounce plugs: R41 / R42 / R43 resistance (4-wire) | within ±1 % of initial |
| F6 | J9: plug the FFSD/SWD ribbon on the bench board and check pin 1 (red stripe) against the silk triangle and the shroud key before powering | key slot on the shroud accepts the cable in one orientation only; pin 1 of the cable lands on pad 1 (SWD pinout continuity: pad 1 = VTref, 2 = SWDIO, 4 = SWCLK, 6 = SWO, 10 = NRST) |
| F7 | J5/J6: mate real Molex 22-27-2031/-2041 headers and KK crimp housings before reflow of the production batch: pin diameter / hole fit, pin pitch with a gauge, friction-lock ramp side vs pin 1 | headers seat flat, housings mate in the keyed direction only |
| F8 | IRLML0060 3.3 V gate check and buck input envelope (carried over from RC1.2: first-article, unchanged) | as in `BENCH_V1_V10_ONE_PAGE.pdf` |

## REMAINING FABRICATION BLOCKERS

| # | Blocker (X-numbers; the B-numbers in the appendix are event sections) | What closes it |
|---|---|---|
| X1 | **J5 / J6 (Molex 22-27-2031 / -2041) pad, drill, outline and pin-1/friction-lock geometry not verified.** The 022272041 drawing supplied is a 3D isometric with no dimensions (`Molex_022272041_3D_drawing_no_dimensions.pdf`); the 022272031 sheet was not supplied; a further Molex 022272041 product page (supplied later) only lists `022272041_sd.pdf`, `PS-99020-0088-001.pdf` and the footprint zip `SYM-22-27-2041-001.zip` — the drawing or that zip closes it. Product pages confirm circuits, 2.54 mm pitch, 3.56 mm tail, 1.60 mm board, partial shroud. | Dimensioned `022272031_sd.pdf` / `022272041_sd.pdf` or the Molex ECAD/footprint package, then compare drill 1.19 / pad 1.74 × 2.19 / body / ramp side |
| X2 | **Panasonic ERJ-P08F47R0V / ERJ-P08F10R0V pulse capability OPEN.** Voltage ratings: 500 V limiting / 1000 V overload, read locally from the ERJP08 row of the catalog (two copies); the catalog gives DC ratings and the ±3 kV 150 pF ESD test only — no pulse curve. Event energies per appendix B are ≈ 0.1 mJ per hot-plug, ≤ 0.37 mJ per 18.5 A interruption (gross over-estimate) and ≈ 0.53 mJ for an 8 kV contact ESD pulse into R41 (an upper-bound 15 kV air pulse is ≈ 1.9 mJ) — compared only with the catalog ESD-test energy (0.675 mJ), not with a pulse curve, so the margin for ESD is ≈ 20 % at 8 kV and negative at the 15 kV upper bound. The 47 Ω / 10 Ω values and suffixes stay provisional. | Panasonic pulse-data document AOA0000C331.pdf (single-pulse energy vs duration, repetition). Note: the independent audit and the user's relay quote 125 V / 500 V; the ERJP08 row of the catalog read here says 500 V / 1000 V (125 is the terminal temperature in °C) — unless AOA0000C331.pdf shows otherwise (appendix F) |
| X3 | **D15 (SMF12CA): CLOSED** — Littelfuse SMF datasheet read locally (VRWM 12 V, VBR 13.3–14.7 V, IR ≤ 2.5 µA, IPP 10.1 A, VC 19.9 V, 200 W / 1000 W; mounting pad layout 1.6 / 1.3 × 1.4 mm = the KiCad `D_SMF` pads). Residual, not a blocker: junction capacitance and leakage below 12 V are not in the datasheet (first-article F2); the datasheet names the case SOD-123FL (distributors say SOD-123F); D15 is DNP-capable. | — |
| X4 | INA228 ±40 V differential / 85 V CM and VBUS maxima: **CLOSED** — read from TI SLYS021A §6.1 (committed in the evidence folder). | — |
| X5 | Earlier open items carried unchanged: critical evidence-register entries not yet VERIFIED_LOCAL, STM32 / DG57CM / LMR14006Y items in `EVIDENCE_RISK_CLASSIFICATION.md`; Gerbers are exported by Joe from KiCad 10 after the checks are re-run locally; do not send the RC1.2x ZIPs to PCBWay yet. | see `PRE_PCBWAY_RELEASE_CHECKLIST.md` |

**NOT READY** for final local export until X1 (Molex J5/J6 dimensions) and X2 (ERJP08 pulse curve / AOA0000C331) are closed.

---

## Appendix A — network audited

```
J6.1 PACK_INA_CON ─ R41 47 Ω ─ PACK_INA ─┬─ D7 1.5SMBJ48A → GND
                                          └─ R13 10 Ω ─ INA_VBUS ─┬─ C28 100 nF → GND ─ INA228 VBUS
J5.1 SHUNT_INP_CON ─ R42 10 Ω ─ SHUNT_INP_RAW ─┬─ D5 1.5SMBJ48A → GND
                                               └─ R11 10 Ω ─ INA_INP ─┬─ C26 100 nF ─┬─ INA_INN ─ R12 10 Ω ─ SHUNT_INN_RAW ─┬─ D6 → GND
                                                                      └─ D15 SMF12CA ┘ (NEW, bidirectional)                └─ R43 10 Ω ─ SHUNT_INN_CON ─ J5.2
J6.2 PACK_ADC ─ R17 75 k ─ R18 75 k ─ ADC_TAP ─ R19 10 k → GND ; ADC_TAP ─ R20 1 k ─ PA1 (C29 100 nF, D8/D14 BAT54S clamps)
```
Topology evaluated against the alternatives: (a) *connector → R → TVS → filter → VBUS* (existing; right for slow surges, wrong for ESD because the series resistor sits between the connector and the clamp); (b) *symmetric Kelvin network + differential clamp* (adopted: D5/D6 stay, D15 added); (c) *fast low-capacitance ESD diode at the connector ahead of the resistors* (not added now — see appendix B4 and F1; it becomes the RC1.3 fallback if the ESD test fails, because it changes the connector area and needs a part that has not been selected from a datasheet).

## Appendix B — per-event calculations

Common inputs: pack source 44 V, source + harness resistance 0.3 Ω [UV], harness L 0.5/2/5 µH [UV], TVS junction capacitance 0.3/1/3 nF [UV]; 1.5SMBJ48A clamp curve from the Bourns datasheet points (58.9 V knee, 77.4 V at 19.4 A, 100.6 V at 97 A; the straight line between the rating points is an estimate). INA228 limits (TI datasheet §6.1): VBUS / IN± to GND 85 V, IN+ − IN− ±40 V, 5 mA into any pin.

### B1 Hot-plug of the sense harness onto a live 44 V pack

| path | source V | Rs upstream | TVS current (derived from the simulated node, not the 97 A rating) | clamp / node V | INA pin V (CM stress) | energy in Rs |
|---|---|---|---|---|---|---|
| VBUS (R41 47 Ω), no series R (reference) | 44 V | 0 Ω | 0.0 A | 48.3 V | 44.0 V | 0.00 µJ |
| VBUS (R41 47 Ω), worst of 9 L/C combinations | 44 V | 47 Ω | 0.00 A | 43.9 V | 43.9 V | 82.66 µJ |
| Kelvin line (R42/R43 10 Ω), no series R (reference) | 44 V | 0 Ω | 0.9 A | 59.8 V | 59.8 V | 0.00 µJ |
| Kelvin line (R42/R43 10 Ω), worst of 9 L/C combinations | 44 V | 10 Ω | 0.68 A | 59.5 V | 59.5 V | 2.84 µJ |

Result: with R41–R43 fitted the VBUS path never reaches the knee; the Kelvin path rings to 59.5 V (knee 58.9 V, TVS current 0.68 A); INA228 pin peak 59.5 V against 85 V; single-event energy in the resistors ≤ 83 µJ (the VBUS value is the ½·C28·V² = 97 µJ needed to charge C28, independent of R41). **PASS** (model; pulse capability of the resistors OPEN, blocker X2).
Differential stress: the two Kelvin lines rise together only if both leads connect at the same instant; any skew between them is the one-lead-early case of B5. D15 bounds the difference regardless of the cause.

### B2 Contact bounce

Bounce is a train of B1 events. The first closure charges C28 (VBUS path) through R41 + R13: ½·C·V² = 97 µJ, independent of the resistor value. C28 is discharged only by the INA228 VBUS input (ZVBUS ≥ 0.8 MΩ, TI datasheet) and TVS leakage, τ ≈ 80 ms, so during a ≈ 1 ms contact gap it droops by ≈ 0.55 V and each later bounce re-dissipates only ≈ ½·C·ΔV² = 15 nJ. Worst realistic total for one plug-in with 20 bounces ≈ 97 µJ; for deliberate repeated plugging once per second the average power is ≈ 0.10 mW against 660 mW (0.66 W at 70 °C, Panasonic catalog). Kelvin lines charge only ≈ 1 nF of TVS/pin capacitance per line (≈ 1 µJ). **PASS on average power; repetitive/single-pulse capability of the 1206 part = blocker X2.**

### B3 Interruption of load current (K1 opening, fuse clearing, 6060B turn-off), ≤ 18.5 A

The only energy source is the harness inductance carrying the interrupted current. The gross over-estimate forces the whole current into the sense branch (a thin sense harness cannot carry it):

| interrupted current | path | TVS current | clamp V | INA pin V | energy in Rs | resistor V (instant, gross) |
|---|---|---|---|---|---|---|
| 10.0 A | VBUS, Rs = 0 Ω | 3.8 A | 62.5 V | ≤ 62.5 V | 0 µJ | 0 V |
| 10.0 A | VBUS, Rs = 47 Ω | 1.3 A | 60.1 V | ≤ 60.1 V | 142 µJ | 470 V |
| 10.0 A | Kelvin line, Rs = 0 Ω | 10.0 A | 68.4 V | ≤ 68.4 V | 0 µJ | 0 V |
| 10.0 A | Kelvin line, Rs = 10 Ω | 9.4 A | 67.9 V | ≤ 67.9 V | 74 µJ | 100 V |
| 15.0 A | VBUS, Rs = 0 Ω | 8.3 A | 66.8 V | ≤ 66.8 V | 0 µJ | 0 V |
| 15.0 A | VBUS, Rs = 47 Ω | 5.9 A | 64.5 V | ≤ 64.5 V | 259 µJ | 705 V |
| 15.0 A | Kelvin line, Rs = 0 Ω | 14.9 A | 73.1 V | ≤ 73.1 V | 0 µJ | 0 V |
| 15.0 A | Kelvin line, Rs = 10 Ω | 14.3 A | 72.5 V | ≤ 72.5 V | 175 µJ | 150 V |
| 18.5 A | VBUS, Rs = 0 Ω | 11.5 A | 69.9 V | ≤ 69.9 V | 0 µJ | 0 V |
| 18.5 A | VBUS, Rs = 47 Ω | 8.9 A | 67.4 V | ≤ 67.4 V | 371 µJ | 870 V |
| 18.5 A | Kelvin line, Rs = 0 Ω | 18.4 A | 76.4 V | ≤ 76.4 V | 0 µJ | 0 V |
| 18.5 A | Kelvin line, Rs = 10 Ω | 17.7 A | 75.8 V | ≤ 75.8 V | 271 µJ | 185 V |

Without series resistors the clamp at 18.5 A is 76.5 V (margin 8.5 V to 85 V); with them the energy is ≈ ½·L·I² = 342 µJ (2 µH; the integrator gives up to 0.37 mJ in R41 at 18.5 A). The instantaneous R·I of the forced model (870 V on R41) is not a real resistor stress (a sense wire does not carry 18.5 A); the credible resistor stress is the B1 value. Common mode never exceeds the clamp (≤ 77 V < 85 V); differential stress is zero for an interruption that affects both leads equally. **PASS** for the INA228; resistor energy inside the catalog ESD-test energy (0.675 mJ), pulse curve OPEN (X2).

### B4 ESD at the connectors (IEC 61000-4-2, ±8 kV contact / ±15 kV air)

ESD and surge are different: a 30 A, ≈ 1 ns-rise, ≈ 100 ns pulse (4 kV basis I1 16.6 A / I2 9.3 A, ×2 for 8 kV, ed. 2 waveform) into a series resistor placed **between the connector and the clamp** means the resistor carries the pulse and develops its voltage; the TVS behind it only limits the node it protects. The table integrates the standard waveform (scaled for the gun's 330 Ω source into the path resistance instead of the 2 Ω target):

| zapped pin | path R | peak current | pin voltage ≈ V_clamp + I·R | energy in the series R | charge | node after R (clamp at that current) | INA228 pin after R13/R11 |
|---|---|---|---|---|---|---|---|
| PACK_INA (R41 47 Ω), ±4 kV contact | 47 Ω | 13.1 A | 689 V | 0.13 mJ | 0.51 µC | 71 V (estimate [UV]) | ≤ 71 V before C28/C26 filtering [UV] |
| Kelvin IN+ / IN− (R42/R43 10 Ω), ±4 kV contact | 10 Ω | 14.6 A | 218 V | 0.03 mJ | 0.57 µC | 73 V (estimate [UV]) | ≤ 73 V before C28/C26 filtering [UV] |
| PACK_INA (R41 47 Ω), ±8 kV contact | 47 Ω | 26.3 A | 1315 V | 0.53 mJ | 1.03 µC | 79 V (estimate [UV]) | ≤ 79 V before C28/C26 filtering [UV] |
| Kelvin IN+ / IN− (R42/R43 10 Ω), ±8 kV contact | 10 Ω | 29.1 A | 372 V | 0.14 mJ | 1.14 µC | 80 V (estimate [UV]) | ≤ 80 V before C28/C26 filtering [UV] |
| PACK_INA (R41 47 Ω), ±15 kV air (upper bound: contact waveform scaled by voltage; the air-discharge current is not specified by the standard) | 47 Ω | 49.3 A | 2402 V | 1.87 mJ | 1.93 µC | 86 V (estimate [UV]) | ≤ 86 V before C28/C26 filtering [UV] |
| Kelvin IN+ / IN− (R42/R43 10 Ω), ±15 kV air (upper bound: contact waveform scaled by voltage; the air-discharge current is not specified by the standard) | 10 Ω | 54.6 A | 634 V | 0.49 mJ | 2.14 µC | 88 V (estimate [UV]) | ≤ 88 V before C28/C26 filtering [UV] |

Findings: (1) the 8 kV discharge into R41 puts ≈ 1315 V across the pin–resistor–TVS path for tens of ns and ≈ 0.53 mJ into R41 — ≈ 80 % of the resistor's catalog ESD-test energy (0.675 mJ, ±3 kV / 150 pF; a different pulse shape) — little margin; the ERJP08's limiting element voltage is 500 V and its maximum overload voltage 1000 V (catalog row, read locally), so ≈ 1.3 kV across R41 is **above the documented 1000 V overload rating** (R42/R43 at ≈ 0.37 kV are inside it) (a 5 s overload test, not a pulse rating, but no pulse curve supports the event) (X2). (2) The node behind R41 is clamped at ≈ 79 V — 6 V under the INA228 85 V limit **before** the first-nanosecond TVS turn-on overshoot (a few nH of loop inductance × 30 A/ns can add > 100 V for ≈ 1 ns; C28 + R13 attenuate it, but that cannot be shown here). (3) An ESD pulse on one Kelvin pin produces a one-sided ≈ 80 V node. With C26 intact the 100 nF couples it to the other pin and the **differential** stays ≈ 1 % of that (≈ 1 V); if C26 is open, the pulse is a ≈ 80 V difference against the ±40 V limit, and D15 limits it to its clamp level (VC 19.9 V at 10.1 A) plus the R11/R12 drop. (4) PACK_ADC (J6.2) has no clamp ahead of its 160 kΩ chain; 8 kV ESD there peaks at ≈ 50 mA through the resistors and the BAT54S clamps, which is not a surge problem but the 0603 thin-film resistor body voltage is unknown (first-article F1 includes J6.2).

**Conclusion: ESD survival cannot be proven by simulation** (first-nanosecond peak, parasitic inductance, TVS turn-on, resistor-body withstand). It stays a **first-article test (F1)**. If it fails, the likely fix is a fast low-capacitance TVS directly at the J5/J6 pins ahead of R41–R43 (RC1.3) so that the resistors no longer carry the pulse.

### B5 One Kelvin lead early / open / late-connect (the case that needs the differential clamp)

Setup: both leads normally sit at pack potential (≤ 44 V common mode) and differ by ≤ 50 mV. Case A: IN+ lead connected, IN− lead open or not yet plugged. Case B is the mirror (IN− connected, IN+ open: difference −44 V, the limit is ±40 V so it is symmetric).

**What holds the open pin, by regime** (this decides whether D15 is needed):
1. *INA228 powered, C26 intact.* A fast step on IN+ is passed to the open IN− pin by C26 (capacitor divider C26 / (C26 + ≈ 1 nF of D6/pin capacitance) ≈ 99 %), so the **difference is only ≈ 0.4 V** for a 44 V step; afterwards the INA228's differential input path (R_DIFF 92 kΩ typical, **TI datasheet, read locally — specified for active mode with |VIN+ − VIN−| < 164 mV only**) pulls IN− toward IN+ (τ ≈ R_DIFF × 100 nF ≈ 9 ms), leaving only leakage × R_DIFF ≈ 0.1 V per µA. **No hazard in this regime; D15 not needed.**
2. *INA228 unpowered or power-cycling (3V3_A off, or the Kelvin harness plugged before the controller is switched on).* There is no sampling path; the open pin is held only by C26 and leakage to ground (D6 ≤ 1 µA at 48 V, 25 °C; RDIFF is specified for active mode only, so nothing in the datasheet holds the open pin here). The difference then **grows as the leakage discharges the node**; the INA228 would be powered up with up to 44 V across its inputs:

| leakage pulling IN− toward ground | time for the difference to reach 40 V (Q = C26 × 44 V = 4.4 µC) |
|---|---|
| 1000 nA | 4 s |
| 100 nA | 44 s |
| 10 nA | 440 s |
3. *C26 failed open / not fitted / badly derated* (a cracked MLCC is a classic field failure): regime 1 loses its capacitive coupling; a one-sided clamp event (≈ 80 V node, B4) is then a ≈ 80 V difference for its duration (the independent audit gives 60–83 V when the other lead is open; that figure ignores C26, which is why it is regime 3, not regime 1).

**Conclusion on the question "is a differential clamp required?":** not required for a powered INA228 with an intact C26; **recommended as a backstop** for regimes 2 and 3 because the failure it prevents (a destroyed INA228 and an unreadable shunt) is expensive and the cost is one 2-pad part. It stays UNVERIFIED (datasheet not read) and can be left unpopulated without any other change if the INA228 datasheet shows the unpowered input state is safe — the decision-determining datasheet fact is INA228 input behaviour at VS = 0.

**With D15 (bidirectional; Littelfuse datasheet read locally: VRWM 12 V, VBR 13.3–14.7 V at 1 mA, IR ≤ 2.5 µA at 12 V, VC 19.9 V at IPP 10.1 A).** In every regime the difference cannot exceed the D15 clamp; in regime 2 the open node settles where the leakage currents balance, ≈ 5–15 V [UV], far below ±40 V; common mode stays ≤ 44 V (limit 85 V).

| event | source V | series R in the D15 loop | D15 current | difference across IN+/IN− | CM stress | PASS? |
|---|---|---|---|---|---|---|
| late connect of IN+ at 44 V, IN− open — first edge (C26 couples: D15 nearly idle) | 44 V | 20.0 Ω (R42 + R11) | ≤ 1.4 A for ≈ 20 ns (charging D6/pin capacitance) | ≈ 0.4 V with C26 intact; bounded by ≈ 16–20 V either way | ≤ 44 V | yes |
| late connect at 30 V — first edge (C26 couples: D15 nearly idle) | 30 V | 20.0 Ω (R42 + R11) | ≤ 0.7 A for ≈ 20 ns (charging D6/pin capacitance) | ≈ 0.3 V with C26 intact; bounded by ≈ 16–20 V either way | ≤ 30 V | yes |
| IN− lead stays open, steady state | 44 V | — | leakage only (nA–µA) | ≤ ≈ 15 V (clamp) | ≤ 44 V | yes (UV: D15 data) |
| IN− lead plugged in late (while the INA pins sit 15–30 V apart) | 44 V | R43 + R12 (20 Ω) + R42 + R11 (20 Ω) = 40 Ω | ≈ (30 V − 16 V)/40 Ω ≈ 0.35 A for ≈ 4 µs while C26 discharges | falls to 50 mV in ≈ 5 τ = 20 µs | ≤ 44 V | yes |

D15 power (late-connect rows apply when C26 is intact or not; with C26 intact D15 is nearly idle): ≤ 0.35 A × 16 V × 4 µs ≈ 22 µJ per event, far below the SMF12CA ratings (200 W 10/1000 µs, 1000 W 8/20 µs, IPP 10.1 A). **Recovery:** when the lead is reconnected the INA228 pins return to the 50 mV level in ≈ 5τ = 20 µs (Kelvin filter 40 Ω × 100 nF); the INA228 conversion time ≥ 50 µs, so the first conversion after reconnection is already valid.

**Measurement error caused by D15** (normal operation, Vshunt ≤ 50 mV): leakage of D15 below its stand-off voltage is not given by the datasheet; bound using the 12 V stand-off leakage (≤ 2.5 µA) as if it flowed at 50 mV: error = I × (R11 + R42 + R12 + R43 + lead resistance) = 2.5 µA × 40 Ω = 100 µV = 0.4 % of 25 mV (10 A) — a **gross over-estimate**: TVS leakage at 0.4 % of the standoff voltage is orders of magnitude lower (nA-class). It would be a constant additive offset removable by the zero calibration, validated in F2. D15 capacitance (not in the datasheet; SOD-123FL TVS of this size are tens of pF [UV]) is ≪ C26 and does not change the Kelvin filter. **Decision: D15 added as a backstop (see the conclusion above); it is the only RC1.2e change that is a judgement call rather than a measured defect.**

### B6 Reversed wiring (where reasonably protectable)

| mistake | what happens | protectable? |
|---|---|---|
| Kelvin leads swapped (IN+ on the load side) | the shunt voltage is negative (−25 mV at 10 A); INA228 reads a negative current; no overstress (both within ±50 mV, ±163.84 mV range) | not a hazard; firmware sign check at first article |
| Pack polarity reversed at J6 (PACK_INA lead on pack −, GND lead on pack +, −44 V) | D7 conducts forward (≈ −1 V clamp): R41 carries 44 V / 47 Ω = **0.94 A continuous = 41 W** in a 0.66 W resistor (it fails open as a fuse, possibly charring), and the INA228 VBUS pin is driven to ≈ −1 V through R13 (10 Ω): ≈ 50 mA into the pin protection diode (absolute maximum 5 mA per pin — about 10× exceeded; the INA228 abs-min is −0.3 V and the absolute maximum pin current is 5 mA (TI datasheet)) | **not reasonably protectable** on this board without a series blocking element in a 44 V sense line (diode drop and leakage error, parts not selected). Accepted limitation, documented: J6 is a polarized KK header with a labelled harness; verify polarity at the bench before connecting the pack. |
| Pack polarity reversed at J5 (Kelvin) | D5/D6 conduct forward clamping the INA pins at ≈ −1 V; the 20 Ω per line limit the current to ≈ 2 A peak decaying — D15 also conducts (bidirectional, difference ≤ 20 V). Both leads reversed equally leaves the difference at ≈ 50 mV. Abs-min of IN± (−0.3 V) is exceeded for the duration | not reasonably protectable; same limitation |

### B7 Leakage-induced error, filter settling and recovery (normal operation)

| item | value | note |
|---|---|---|
| D5/D6 leakage mismatch × R42/R43 | ≤ 1 µA × 10 Ω = 10 µV = 4 mA-equivalent (0.04 % of 10 A) at 25 °C | Bourns IR ≤ 1.0 µA at 48 V, 25 °C (read locally); temperature dependence not specified [UV] → F2 |
| D7 leakage × R41 | ≤ 1 µA × 47 Ω = 47 µV on 44 V (1.1 ppm) | |
| INA228 bias (2.5 nA max, TI datasheet) × 20 Ω per Kelvin line | ≈ nV, cancels with matched 1 % resistors | |
| D15 leakage × 40 Ω loop | ≤ 100 µV worst-case bound (2.5 µA max at 12 V × 40 Ω = 0.4 % of 25 mV); expected ≪ (leakage at 50 mV is not specified) | F2 |
| VBUS divider error from 57 Ω into the input | ≈ 0.007 % (3 mV at 44 V), fixed ratio, removed by calibration against the EDU34450A | |
| Kelvin filter 2 × 20 Ω + C26 | τ = 4.0 µs, fc 40 kHz; 5τ = 20 µs | INA228 conversion ≥ 50 µs |
| VBUS filter 57 Ω + C28 | τ = 5.7 µs, 5τ = 28 µs | |
| PA1 filter (150 k ∥ 10 k + 1 k) × C29 100 nF | τ = 1.04 ms, 5τ = 5.2 ms | slow by design (cross-check channel) |
| Recovery after a clamp event | ≤ 5τ above: 20–30 µs for the INA228 pins, ≈ 5 ms for PA1 | a transient does not leave the ADC reading stale for longer than one 10 ms logging step |

## Appendix C — PA1 (cross-check channel) min / max

| event | ADC_TAP | PA1 | note |
|---|---|---|---|
| normal, 30 V | 1.875 V | 1.875 V | no current through R20 (1 k) |
| normal, 36 V | 2.250 V | 2.250 V | no current through R20 (1 k) |
| normal, 42 V | 2.625 V | 2.625 V | no current through R20 (1 k) |
| normal, 44 V | 2.750 V | 2.750 V | no current through R20 (1 k) |
| 48 V (above the ceiling, still inside the divider range) | 3.000 V | 3.000 V | |
| overvoltage on PACK_ADC, 100 V | unclamped 6.25 V | ≈ 3.35 V (VCLAMP + Vf of the BAT54S upper diode [UV]) | clamp current ≈ (6.25 − 3.35)/161 kΩ ≈ 0.02 mA through the 75 k + 75 k chain |
| reversed pack −44 V on PACK_ADC | −2.75 V | ≈ −0.3 V (lower BAT54S diode) | injection ≈ (44 − 0.3)/161 kΩ = 0.27 mA, inside the STM32 injection limit [UV] |
| controller unpowered, pack at 44 V | tap 2.75 V | ADC_SENSE → D8 → VCLAMP → R37 (10 k) | 3V3 stays at ≈ 0 V (D14 blocks, R4 bleeder) — design from RC1.1, unchanged |
| PACK_ADC lead open | 0 V | 0 V | INA228 vs ARM-sense cross-check flags a mismatch (firmware) |
| ESD on PACK_ADC | — | clamps conduct | first-article F1; only 160 kΩ in series, no pre-clamp (see B4) |

Leakage: BAT54S reverse leakage into the 9.4 kΩ source impedance is ≈ 0.01 % (RC1.1 calculation); it is not changed by D15. Accuracy of the divider itself is independent of the protection events.

## Appendix D — J9 Samtec FTSH-105-01-L-DV-K verification

| item | Samtec drawing (read locally) | RC1.2d generic footprint | RC1.2e footprint |
|---|---|---|---|
| pitch | 1.27 × 1.27 mm | 1.27 | 1.27 |
| pad size | 0.74 × 2.79 mm (rec. layout rev H, sheet 1) | 0.74 × 2.40 | 0.74 × 2.79 |
| pad span (overall) | 0.270 in = 6.86 mm | 6.30 mm | 6.86 mm |
| row spacing (centre to centre) | 6.86 − 2.79 = 4.07 mm (gap between rows 1.28 mm) | 3.90 mm | 4.07 mm |
| locating hole 'A' (table 1) | -K: N/A (no PCB hole) | none | none |
| body | 5 × 1.27 = 6.35 mm long (+0.13/−0.36), 3.43 mm wide, tail-to-tail 5.84 mm (product drawing rev FX) | — | Fab outline 6.35 × 3.43; courtyard 7.4 × 6.9 mm |
| pin numbering | pin 01 bottom-left, 02 directly above, 03 to the right of 01 (drawing view) | pin 1 top-left, 2 top-right, 3 below pin 1 | same as the generic frame; rotating the footprint +90° (CCW) gives the Samtec view, same handedness (no mirror) |
| key | -K = keying part FTSH-50-CN-xx in the shroud, centred on the shroud, positions 05–25, lead style -01 only | not keyed | **side not resolved by the drawings** → F6 |

On the board J9 sits at (160, 140) with rotation 0: pin 1 top-left (silk triangle + "1" at the left of pad 1), pad 2 top-right, rows running along y. The SWD cable plugs vertically from the top; its pin 1 (red stripe) goes to the triangle. Checked: courtyard does not overlap any neighbour (DRC), pads clear the GND pour by the 0.25 mm rule, J9's silk is two short bars outside the pad rows (no silk over pads). Pad-to-neighbour clearance fixed by moving two traces into the 1.28 mm row gap. **J9 land pattern: CLOSED. Key side: first-article F6.**

## Appendix E — J5 / J6 Molex status

What the supplied 022272041 file is: a 3D isometric of the 4-circuit header (square posts, polarizing/friction-lock shroud with a ramp on one long side) with the title block "MATERIAL NO.: 022272041, CIRCUIT SIZE: 4" — no dimensions, no hole pattern, no ramp-vs-pin-1 information. The PK-6410-002-001 file is a packaging drawing (polybag/carton quantities) and contains no part geometry. The product pages (supplied earlier) give circuits, 2.54 mm pitch, 3.56 mm tail, 1.60 mm board, partially shrouded, 4 A/contact. These all agree with the KiCad KK-254 footprints (pitch, pin count, vertical, through-hole), but pad size 1.74 × 2.19, drill 1.19, courtyard and the friction-lock side relative to pin 1 are unverified. **J5/J6: OPEN (X1). No board change is justified until a dimensioned drawing exists; if the dimensions then agree, no RC1.2f is needed.**

## Appendix F — cross-reference to the independent audit on this branch (`audit/CONTROLLER_AUDIT_REPORT.md`, written by a separate session)

That session had the INA228 datasheet and the Panasonic ERJP08 sheet AOA0000C331.pdf. **The INA228 datasheet has since reached this session and was read locally (rows below marked accordingly)**; the Panasonic and Littelfuse values remain `USER_RELAYED_MANUFACTURER` until those PDFs are committed and read. What that audit reports, and how it compares:

| item | independent audit (from the PDFs it had) | this audit | consequence |
|---|---|---|---|
| INA228 absolute maxima | VBUS/VCM −0.3…85 V, differential ±40 V, 5 mA into any pin, HBM ±2 kV | **read locally from TI SLYS021A §6.1**: differential ±40 V, CM and VBUS −0.3…85 V, VS 6 V, 5 mA into any pin, HBM ±2 kV / CDM ±1 kV | **agree and closed (VERIFIED_LOCAL)** |
| INA228 R_DIFF, Z_VBUS, bias | R_DIFF 92 kΩ, Z_VBUS 0.8/1/1.2 MΩ, I_B 0.1/2.5 nA | same values read locally; R_DIFF is specified for active mode (|VIN+ − VIN−| < 164 mV) only | VBUS gain error 0.0071 % with 0.8 MΩ (calibrated out); R_DIFF holds an open pin only while the INA228 is active (B5 regime 1), which is why D15 stays as a backstop for unpowered / shutdown / C26-open |
| Panasonic ERJP08 voltage ratings | limiting element voltage 125 V, maximum overload 500 V | **500 V limiting / 1000 V overload** in the ERJP08 row of the Panasonic catalog (24-Feb-22 copy and the later series catalog `3750967.pdf`, both read locally; the 125 in that row is the rated terminal-part temperature, °C) | **corrected back**: ≈ 1.3 kV across R41 at 8 kV contact is still above the 1000 V overload rating (31 % over); R42/R43 inside; energy alone cannot close ESD. AOA0000C331.pdf itself not read |
| One-sided event with the other lead open | 60–83 V differential (IN− held only by R_DIFF) | ≈ 1 % with C26 intact (B4, B5), ≈ 80 V if C26 is open | different conclusion because that audit does not include the 100 nF C26 across the pins; D15 covers the C26-open and INA-unpowered cases |
| ESD at the INA pin | 8 kV: 77.9 V; 15 kV air: 83.4 V (87.0 V at +60 K) | 8 kV: 79 V; 15 kV air (upper bound): 86 V | agree: no margin at 15 kV air, and the first-nanosecond spike is not resolved by either model |
| Lower-clamp TVS | suggests 1.5SMBJ45A (clamp ≈ 5–6 V lower, but only 1 V standoff headroom over 44 V and higher leakage) | not adopted | evaluate only after the ESD decision; the headroom is thin |
| Samtec J9 / Molex J5, J6 | land pattern not available (J9 "likely wrong"); Molex PDFs missing | J9 replaced from the rev-H land pattern; Molex still open | consistent; J9 flagged by that audit is closed by this round |

## Appendix G — what was and was not changed

Changed: J9 footprint (+ J9 breakout routing), D15 + 4 vias on INA_INP/INA_INN, evidence register, calculation text, this report, checklist/risk/connector documents. **Not changed:** every other footprint and track, the isolation geometry and rules, netclasses, BOM except one added line (D15 SMF12CA), the Pi/display branch (untouched).

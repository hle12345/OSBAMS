# 5 V distribution voltage-drop budget (RC1.1)

Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT (2 contacts/rail) -> 16 AWG trunk (<=150 mm) -> splice -> 22 AWG branch leads (~50 mm) -> Harwin M20 contacts (2 per rail) -> Pi 5V pins` and the matching return.
Target: **>= 4.85 V at the Pi header at 5 A, worst case**; **<= 5.25 V no-load / high-line** (Pi floor 4.75 V).

## Inputs and status (`datasheet_inputs.json`)

| Input | Value | Status | Source |
|---|---|---|---|
| f2_resistance_cold_mohm | 7.7 | owner_cited | Littelfuse 0451008.MRL, 7.7 mOhm DC cold resistance (owner-cited; DigiKey lists active) |
| f2_hot_factor | 1.0 | unverified | Fuse resistance rises when loaded; main table uses cold value as instructed, sensitivity row applies 1.3x (ASSUMED) |
| j_out_contact_max_mohm | 10.0 | owner_cited | Molex Micro-Fit 3.0 family: 10 mOhm max contact resistance (owner-cited) |
| j_out_contact_typ_mohm | 5.24 | owner_cited | Molex wire-to-board test data, ~5.24 mOhm initial in one configuration (owner-cited; includes wire) |
| j_out_rating_a | 8.5 | owner_cited | Molex 43045-0400, 8.5 A max per contact (owner-cited) |
| rsdw_trim_range_pct | 10.0 | owner_cited | RSDW40F-05 output trim +-10 % (owner-cited, RS Components datasheet A700000011914648) |
| rsdw_trim_network | {'Vref': 1.24, 'R1_kohm': 15.47, 'R2_kohm': 5.1, 'R3_kohm': 33.0, 'trim_up': 'resistor from TRIM to -Vout'} | owner_cited | 5 V model trim network + trim-up formula (owner-cited from Mean Well spec): a = Vref*R1/(Vout-Vref); Rt = a*R2/(R2-a) - R3; trim-up resistor TRIM -> -Vout. Identical to the topology assumed earlier. |
| rsdw_tolerance_pct | 1.0 | owner_cited | RSDW40F-05 output accuracy +-1 % (Mean Well RSDW40/RDDW40 spec, owner-cited; assumed to hold at trimmed setpoints - confirm) |
| rsdw_footprint_drawing | False | unverified | Pin X/Y positions, pin pitch/rows, drill and keepout needed from the Mean Well drawing. Footprint remains the placeholder. |
| pi_end_connector_mpn | Harwin M20-1070500 housing + M20-1160042 gold crimp contacts | owner_cited | Harwin M20: 3 A/contact, 20 mOhm max initial, 22-30 AWG crimp (owner-cited). Housing pin count/layout to be confirmed from the Harwin drawing. |
| pi_end_contact_max_mohm | 20.0 | owner_cited | Harwin M20 series 20 mOhm max initial per contact (owner-cited) |
| pi_end_contact_typ_mohm | 12.0 | unverified | ASSUMED typical (Harwin quotes max only) |
| erc_clean_kicad10 | False | unverified | Run ERC in KiCad 10 locally |
| rsdw_body_pins_owner | {'body_mm': [50.8, 25.4], 'pin_dia_mm': 1.0, 'pinout': '1 +VIN, 2 -VIN, 3 ON/OFF, 4 +VOUT, 5 -VOUT, 6 TRIM'} | owner_cited | Mean Well drawing as described by owner. Pin X/Y coordinates were NOT supplied. |
| pi_end_contact_rating_a | 3.0 | owner_cited | Harwin M20 3 A per contact (owner-cited) |
| branch_wire | {'awg': 22, 'mohm_per_m': 53.0, 'length_m': 0.05, 'splice_mohm': 1.0} | unverified | 22 AWG 53 mOhm/m @20C (standard table), 50 mm branch, 1 mOhm per crimp splice ASSUMED |
| pi_end_pin_map_confirmed | False | unverified | Housing size/pin map + anti-reversal keying not yet confirmed (see docs/Pi_end_connector_requirements.md: a 180-degree reversed 2x5 housing swaps +5 V and GND) |
| bench_pi_voltage | False | unverified | Bench measurement at Pi header under real load |

`owner_cited` = supplied by the project owner with a source; the build environment cannot reach Mean Well, Molex, Littelfuse or Harwin, so re-check against the PDFs. Assumptions: typical Harwin 12 mOhm, branch wire/splice values, hot-fuse 1.3x sensitivity.

Source accuracy +-1 % (was assumed +-2 %). PCB copper 2.2 mOhm; F2 7.7 mOhm cold; J_OUT 10.0 mOhm max/contact; Harwin M20 20 mOhm max/contact, 2 contacts per rail.

## Results at the Pi 5V pins

| Case | R typ / max (mOhm) | setpoint | 5 A typ / worst (V) | 3 A worst (V) | no-load max (V) |
|---|---|---|---|---|---|
| Untrimmed (5.00 V) | 33.7 / 46.5 | 5.000 | 4.83 / 4.72 | 4.81 | 5.050 |
| Trimmed to 5.14 V (selected) | 33.7 / 46.5 | 5.140 | 4.97 / 4.86 | 4.95 | 5.191 |
| Trimmed, 3 Pi GND contacts | 31.0 / 42.5 | 5.140 | 4.98 / 4.88 | 4.96 | 5.191 |
| Hot F2 (x1.3), trimmed | 36.0 / 48.8 | 5.140 | 4.96 / 4.84 | 4.94 | 5.191 |

Feasibility window: one setpoint can meet both limits only if worst-case path R <= 59.2 mOhm; this design is 46.5 mOhm -> **feasible, margin 12.7 mOhm**. Untrimmed, the 5 A worst case is below the Pi floor, so **trim is required**.
Contact loading at 5 A: 2.5 A per Harwin 5 V contact vs 3 A rating (83 %) - **no derating headroom**; the Pi has only two 5 V pins (2 and 4), so this cannot be improved by adding 5 V contacts. At 8 A the contacts and Pi header pins would be overloaded (4 A each): keep real load <= ~5 A. See the Pi_end note.

## Trim-up resistor (Mean Well formula, owner-cited)

Vref = 1.24 V, R1 = 15.47 k, R2 = 5.1 k, R3 = 33.0 k; nominal Vout = 5.001 V. `a = Vref*R1/(Vout - Vref)`, `Rt = a*R2/(R2 - a) - R3`, Rt from TRIM to -Vout (board pad **R3**; R2 pad is trim-down and is not used).

| Setpoint | +% | Rt (R3 pad), calc | E96 | Vout with E96 | worst-case Pi @5A | no-load max |
|---|---|---|---|---|---|---|
| 5.12 V | +2.4 % | 128.7 kOhm | 130.0 kOhm | 5.119 V | 4.84 V | 5.170 V |
| 5.14 V | +2.8 % | 105.3 kOhm | 105.0 kOhm | 5.140 V | 4.86 V | 5.192 V |
| 5.16 V | +3.2 % | 87.9 kOhm | 88.7 kOhm | 5.159 V | 4.87 V | 5.211 V |

**Selected setpoint 5.14 V -> Rt = 105.3 kOhm, E96 105.0 kOhm (gives 5.140 V). R3 stays DNP until you approve the resistor.** The +-1 % accuracy is assumed to hold at the trimmed setpoint (confirm). R3 pad is 0603; use a 0.1 % or 1 % resistor.

## Remaining RC2 gates

1. Housing size / pin map and anti-reversal keying at the Pi end (`Pi_end_connector_requirements.md`).
2. RSDW40F-05 pin X/Y, drill and keepout from the Mean Well drawing (body 50.8 x 25.4 mm, pin dia ~1.0 mm are recorded; coordinates not supplied).
3. KiCad 10 ERC.  4. Bench voltage at the Pi header under real load.

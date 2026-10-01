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
| rsdw_trim_network | {'Vref': 1.24, 'R1_kohm': 15.47, 'R2_kohm': 5.1, 'R3_kohm': 33.0, 'trim_up': 'resistor from TRIM to -Vout'} | verified | spec p.4: Rtrim-up = a*R2/(R2-a) - R3, a = Vref/(Vo'-Vref)*R1; 5 V model Vref 1.24 V, R1 15.47k, R2 5.1k, R3 33k; trim-up resistor TRIM to -Vo; range +-10 %. Datasheet example 5.5 V -> 5.476 kOhm reproduced. |
| rsdw_tolerance_pct | 1.0 | verified | RSDW40/RDDW40 spec 2022-05-24: VOLTAGE ACCURACY +-1 % (at normal input 24 V, rated load, 25 C) |
| rsdw_footprint_drawing | True | verified | spec p.5 mechanical drawing (Bottom View): pins 4/5/6 at 2.54/12.7/22.86 mm across, 2.54 mm from one end; pins 1/2/3 at 5.08/10.16/20.32 mm across, 2.54 mm from the other end (45.72 mm between rows); body 50.8x25.4x10.5; pin dia 1+-0.1; tol +-0.35. Implemented in build_pcb.py (mirrored for PCB top view). |
| pi_end_connector_mpn | Harwin M20-1070500 housing + M20-1160042 contacts | owner_cited | Contact verified from uploaded datasheet; housing M20-1070500 datasheet NOT supplied (pin count/layout unconfirmed) |
| pi_end_contact_max_mohm | 20.0 | owner_cited | Harwin M20 20 mOhm max initial (owner-cited; not in the uploaded M20-1160042 datasheet - need the M20 series spec) |
| pi_end_contact_typ_mohm | 12.0 | unverified | ASSUMED typical (Harwin quotes max only) |
| erc_clean_kicad10 | False | unverified | Run ERC in KiCad 10 locally |
| rsdw_body_pins_owner | {'body_mm': [50.8, 25.4], 'pin_dia_mm': 1.0, 'pinout': '1 +VIN, 2 -VIN, 3 ON/OFF, 4 +VOUT, 5 -VOUT, 6 TRIM'} | owner_cited | Mean Well drawing as described by owner. Pin X/Y coordinates were NOT supplied. |
| pi_end_contact_rating_a | 3.0 | verified | Harwin M20-1160042 datasheet (TraceParts, 2025-11-18): current rating (signal) 3 A; 22-30 AWG; mating pin 0.64 mm square; gold contact. NOTE: the 20 mOhm figure is NOT in this file. |
| branch_wire | {'awg': 22, 'mohm_per_m': 53.0, 'length_m': 0.05, 'splice_mohm': 1.0} | unverified | 22 AWG 53 mOhm/m @20C (standard table), 50 mm branch, 1 mOhm per crimp splice ASSUMED |
| pi_end_pin_map_confirmed | False | unverified | Housing size/pin map + anti-reversal keying not yet confirmed (see docs/Pi_end_connector_requirements.md: a 180-degree reversed 2x5 housing swaps +5 V and GND) |
| bench_pi_voltage | False | unverified | Bench measurement at Pi header under real load |
| rsdw_line_reg_pct | 0.2 | verified | spec: line regulation +-0.2 % (single output) |
| rsdw_load_reg_pct | 0.5 | verified | spec: load regulation +-0.5 % (0-100 % load) |
| rsdw_tempco_pct_per_c | 0.05 | verified | spec: temperature coefficient 0.05 %/C (0~55 C) |
| delta_t_c | 15.0 | unverified | ASSUMED module temperature rise above 25 C in the enclosure; measure |
| rsdw_remote_onoff | open = ON | verified | spec: Power ON: R.C ~ -Vin >3~12 Vdc or open circuit; OFF < 1.2 V or short. Pin 3 left open = enabled. |
| rsdw_input_fuse_recommendation | 24Vin models: 8 A delay (time-lag) type | verified | spec INPUT PROTECTION: 'Fuse recommended. 24Vin models: 8A delay time Type'. F1 is 5 A fast-acting - see docs/Datasheet_findings.md |
| rsdw_ripple_mvpp | 100 | verified | spec: single output 3.3-15 Vo: 100 mVp-p (20 MHz, 0.1 uF + 47 uF) |
| rsdw_input_fuse_recommendation_resolved | False | unverified | Decision needed: F1 (5 A fast-acting, locked) vs Mean Well recommended 8 A delay type |

`owner_cited` = supplied by the project owner with a source; the build environment cannot reach Mean Well, Molex, Littelfuse or Harwin, so re-check against the PDFs. Assumptions: typical Harwin 12 mOhm, branch wire/splice values, hot-fuse 1.3x sensitivity.

Source tolerance from the datasheet: accuracy +-1 % + line +-0.2 % + load +-0.5 % (low corner at 5 A = -1.51 %, no-load high corner = +1.70 %, at 25 C). PCB copper 2.2 mOhm; F2 7.7 mOhm cold; J_OUT 10.0 mOhm max/contact; Harwin M20 20 mOhm max/contact, 2 contacts per rail.

## Results at the Pi 5V pins

| Case | R typ / max (mOhm) | setpoint | 5 A typ / worst (V) | 3 A worst (V) | no-load max (V) |
|---|---|---|---|---|---|
| Untrimmed (5.00 V) | 33.7 / 46.5 | 5.000 | 4.83 / 4.69 | 4.78 | 5.085 |
| Trimmed to 5.161 V (window-limited) | 33.7 / 46.5 | 5.161 | 4.99 / 4.85 | 4.94 | 5.249 |
| Trimmed, 3 Pi GND contacts | 31.0 / 42.5 | 5.161 | 5.01 / 4.87 | 4.96 | 5.249 |
| Hot F2 (x1.3), trimmed | 36.0 / 48.8 | 5.161 | 4.98 / 4.84 | 4.94 | 5.249 |

Feasibility window: one setpoint can meet both limits only if worst-case path R <= 46.8 mOhm; this design is 46.5 mOhm -> **feasible, margin 0.4 mOhm**. Untrimmed, the 5 A worst case is below the Pi floor, so **trim is required**.
Contact loading at 5 A: 2.5 A per Harwin 5 V contact vs 3 A rating (83 %) - **no derating headroom**; the Pi has only two 5 V pins (2 and 4), so this cannot be improved by adding 5 V contacts. At 8 A the contacts and Pi header pins would be overloaded (4 A each): keep real load <= ~5 A. See the Pi_end note.

## Tolerance scenarios (does one setpoint satisfy both limits?)

| Tolerance scenario | low / high corner | setpoint needed | max setpoint allowed (<=5.25 V) | margin | feasible |
|---|---|---|---|---|---|
| Datasheet stack at 25 C (accuracy+line+load) | -1.51 % / +1.70 % | 5.160 V | 5.162 V | +2 mV | yes |
| Stack + temperature drift (0.75 % for dT=15 C) | -2.26 % / +2.45 % | 5.200 V | 5.124 V | -76 mV | NO |
| Unit calibrated at 25 C (accuracy term removed) + temp drift | -1.26 % / +1.45 % | 5.147 V | 5.175 V | +28 mV | yes |

The +-1 % accuracy alone (as first assumed) hides the line/load terms and the 0.05 %/C coefficient. At 25 C the design closes by only a few mV; with realistic temperature rise it does **not** close by the stated criteria unless each unit is calibrated (measure the untrimmed output, then select Rt) and/or path resistance is reduced.

## Trim-up resistor (Mean Well formula, verified)

Vref = 1.24 V, R1 = 15.47 k, R2 = 5.1 k, R3 = 33.0 k; nominal Vout = 5.001 V. `a = Vref*R1/(Vout - Vref)`, `Rt = a*R2/(R2 - a) - R3`, Rt from TRIM to -Vout (board pad **R3**; R2 pad is trim-down and is not used).

| Setpoint | +% | Rt (R3 pad), calc | E96 | Vout with E96 | worst-case Pi @5A | no-load max |
|---|---|---|---|---|---|---|
| 5.141 V | +2.8 % | 104.3 kOhm | 105.0 kOhm | 5.140 V | 4.83 V | 5.228 V |
| 5.161 V | +3.2 % | 87.1 kOhm | 86.6 kOhm | 5.162 V | 4.85 V | 5.249 V |
| 5.181 V | +3.6 % | 73.8 kOhm | 73.2 kOhm | 5.182 V | 4.87 V | 5.270 V |

**Window-limited setpoint 5.161 V -> Rt = 87.1 kOhm, E96 86.6 kOhm (gives 5.162 V). R3 stays DNP until you approve the resistor.** The +-1 % accuracy is assumed to hold at the trimmed setpoint (confirm). R3 pad is 0603; use a 0.1 % or 1 % resistor.

## Remaining RC2 gates

1. Housing size / pin map and anti-reversal keying at the Pi end (`Pi_end_connector_requirements.md`).
2. RSDW40F-05 pin X/Y, drill and keepout from the Mean Well drawing (body 50.8 x 25.4 mm, pin dia ~1.0 mm are recorded; coordinates not supplied).
3. KiCad 10 ERC.  4. Bench voltage at the Pi header under real load.

# 5 V voltage-drop budget — detail and trim table (RC2)

Scenario tables (Pi / display loads, element drops, setpoint window) are in `Power_budget_report.md`; this file keeps the datasheet-input table, the tolerance scenarios and the trim-resistor table. In RC2 the display is fed from J_DISP, so the display current does not pass through the Pi path modelled below.

Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT (2 contacts/rail) -> 18 AWG harness (<=150 mm) -> keyed interposer Micro-Fit J1 (2 contacts/rail) -> interposer copper -> 2x20 stacking socket -> Pi pins (+5 V: 2 and 4; GND: 6, 9, 14, 20)` and the matching return. The Harwin M20 fan-out is no longer in the path.
Target: **>= 4.85 V at the Pi header at 5 A, worst case**; **<= 5.25 V no-load / high-line** (Pi floor 4.75 V).

## Inputs and status (`datasheet_inputs.json`)

| Input | Value | Status | Source |
|---|---|---|---|
| f2_resistance_cold_mohm | 7.7 | verified | Littelfuse 451/453 datasheet (uploaded): 0451008 nominal cold resistance 0.0077 ohm |
| f2_hot_factor | 1.0 | unverified | Fuse resistance rises when loaded; main table uses cold value as instructed, sensitivity row applies 1.3x (ASSUMED) |
| j_out_contact_max_mohm | 10.0 | owner_cited | Molex Micro-Fit 3.0 family: 10 mOhm max contact resistance (owner-cited) |
| j_out_contact_typ_mohm | 5.24 | owner_cited | Molex wire-to-board test data, ~5.24 mOhm initial in one configuration (owner-cited; includes wire) |
| j_out_rating_a | 8.5 | owner_cited | Molex 43045-0400, 8.5 A max per contact (owner-cited) |
| rsdw_trim_range_pct | 10.0 | owner_cited | RSDW40F-05 output trim +-10 % (owner-cited, RS Components datasheet A700000011914648) |
| rsdw_trim_network | {'Vref': 1.24, 'R1_kohm': 15.47, 'R2_kohm': 5.1, 'R3_kohm': 33.0, 'trim_up': 'resistor from TRIM to -Vout'} | verified | spec p.4: Rtrim-up = a*R2/(R2-a) - R3, a = Vref/(Vo'-Vref)*R1; 5 V model Vref 1.24 V, R1 15.47k, R2 5.1k, R3 33k; trim-up resistor TRIM to -Vo; range +-10 %. Datasheet example 5.5 V -> 5.476 kOhm reproduced. |
| rsdw_tolerance_pct | 1.0 | verified | RSDW40/RDDW40 spec 2022-05-24: VOLTAGE ACCURACY +-1 % (at normal input 24 V, rated load, 25 C) |
| rsdw_footprint_drawing | True | verified | spec p.5 mechanical drawing (Bottom View): pins 4/5/6 at 2.54/12.7/22.86 mm across, 2.54 mm from one end; pins 1/2/3 at 5.08/10.16/20.32 mm across, 2.54 mm from the other end (45.72 mm between rows); body 50.8x25.4x10.5; pin dia 1+-0.1; tol +-0.35. Implemented in build_pcb.py (mirrored for PCB top view). |
| pi_end_connector_mpn | Keyed interposer (OSBAMS_Pi_Power_Interposer_RevA) with Micro-Fit 430450400 + 2x20 stacking socket | owner_cited | Owner decision. Harwin M20 no longer in the power path (superseded). |
| pi_end_contact_max_mohm | 20.0 | owner_cited | Harwin M20 20 mOhm max initial (owner-cited; not in the uploaded M20-1160042 datasheet - need the M20 series spec) |
| pi_end_contact_typ_mohm | 12.0 | unverified | ASSUMED typical (Harwin quotes max only) |
| erc_clean_kicad10 | True | verified | KiCad 10.0.6 (container) ERC 0 / DRC 0 incl. schematic parity on both projects, reports in reports/*_kicad10.rpt (build_k10.py). Owner re-runs locally before the Gerber export. |
| rsdw_body_pins_owner | {'body_mm': [50.8, 25.4], 'pin_dia_mm': 1.0, 'pinout': '1 +VIN, 2 -VIN, 3 ON/OFF, 4 +VOUT, 5 -VOUT, 6 TRIM'} | owner_cited | Mean Well drawing as described by owner. Pin X/Y coordinates were NOT supplied. |
| pi_end_contact_rating_a | 3.0 | verified | Harwin M20-1160042 datasheet (TraceParts, 2025-11-18): current rating (signal) 3 A; 22-30 AWG; mating pin 0.64 mm square; gold contact. NOTE: the 20 mOhm figure is NOT in this file. |
| branch_wire | {'awg': 22, 'mohm_per_m': 53.0, 'length_m': 0.05, 'splice_mohm': 1.0} | unverified | 22 AWG 53 mOhm/m @20C (standard table), 50 mm branch, 1 mOhm per crimp splice ASSUMED |
| pi_end_pin_map_confirmed | True | verified | Interposer: +5 V on Pi pins 2,4; GND on 6,9,14,20; all 40 positions socketed (no offset); 180-degree reversal blocked by key standoffs (3D check pending) |
| bench_pi_voltage | False | unverified | First-article validation (not an RC2 gate): loaded Pi voltage + harness temperature rise |
| rsdw_line_reg_pct | 0.2 | verified | spec: line regulation +-0.2 % (single output) |
| rsdw_load_reg_pct | 0.5 | verified | spec: load regulation +-0.5 % (0-100 % load) |
| rsdw_tempco_pct_per_c | 0.05 | verified | spec: temperature coefficient 0.05 %/C (0~55 C) |
| delta_t_c | 15.0 | unverified | ASSUMED module temperature rise above 25 C in the enclosure; measure |
| rsdw_remote_onoff | open = ON | verified | spec: Power ON: R.C ~ -Vin >3~12 Vdc or open circuit; OFF < 1.2 V or short. Pin 3 left open = enabled. |
| rsdw_input_fuse_recommendation | 24Vin models: 8 A delay (time-lag) type | verified | spec INPUT PROTECTION: 'Fuse recommended. 24Vin models: 8A delay time Type'. F1 is 5 A fast-acting - see docs/Datasheet_findings.md |
| rsdw_ripple_mvpp | 100 | verified | spec: single output 3.3-15 Vo: 100 mVp-p (20 MHz, 0.1 uF + 47 uF) |
| f1_mpn | 0407008.WR | verified | Littelfuse 407 Series datasheet (rev 09/14/20, uploaded): 1206 time-lag, amp code 008., part number 0407 008. W R (W = 3000 pcs, R = reel). Replaces 0453008.MRL, which is very fast-acting (451/453 datasheet). |
| f1_resistance_mohm | 9.0 | verified | 407 datasheet nominal resistance 0.009 ohm (measured <10 % rated current); hot value from 0.097 V drop at 8 A = 12.1 mOhm |
| interposer_socket_mpn | SSW-120-01-L-D | user_relayed_manufacturer | Samtec SSW-120-01-L-D (user-relayed from the Samtec product page): 40 pos, 2 rows, 2.54 mm, vertical THT, 10 uin Au mating, tin post, post 2.64 mm, insulation 8.51 mm, 4.7 A per contact (Samtec basis: 2 pins powered), -55..+125 C. Dimensions also verified from catalog F-226 (uploaded). Not read locally from the product page. |
| interposer_socket_contact_mohm | 20.0 | unverified | CONSERVATIVE PLACEHOLDER - no initial contact resistance is published for this ordering code (Samtec spec gives delta 15 mOhm max after tests only). Treated as a FIRST-ARTICLE MEASURED parameter: measure it on the assembled interposer; do not substitute a lower value on paper. |
| interposer_key_3d_check | True | verified | PLAN-VIEW check PASS against the official drawing (reports/Pi5_keying_check.txt): correct orientation posts hang beyond the Pi edge; reversed they land on bare PCB (1.6 mm and 3.3 mm clear of components for a 5 mm post). Height/engagement check (post length vs seated gap G) still pending the SSW-120 drawing; optional STEP confirmation. |
| f1_spec | {'rating_a': 8, 'max_voltage_v': 24, 'interrupt': '60 A @ 24 VDC', 'nominal_resistance_mohm': 9.0, 'melting_i2t_a2s': 24.12, 'vdrop_at_rated_v': 0.097, 'power_at_rated_w': 0.8, 'continuous_derate': '<=80 % of rating (6.4 A), plus temperature re-rating curve', 'time_lag': '100 %: 4 h min; 200 %: 1-120 s; 300 %: 0.1-3 s; 800 %: 2-50 ms', 'land_pattern_mm': 'pad 1.0 x 1.8, gap 1.5, span 3.5; body 3.2 x 1.6'} | verified | 407 datasheet electrical specs by item |
| f2_spec | {'mpn': '0451008.MRL', 'rating_a': 8, 'max_voltage_v': 125, 'nominal_cold_resistance_mohm': 7.7, 'melting_i2t_a2s': 20.23, 'interrupt': 'PSE: 100 A @ 100 VAC', 'land_pattern': 'pad 1.96 x 3.15, outer span 6.86 mm - matches the KiCad library footprint used', 'class': 'very fast-acting'} | verified | Littelfuse 451/453 datasheet (uploaded) - confirms owner's 7.7 mOhm |
| pi_hat_plus_guidance | {'power_hat_min': '3 A @ 5.1 V (strongly recommend 5 A @ 5.1 V)', 'standby': '5 V rail powered, 3.3 V unpowered', 'mech': '65 x 56.5 board, holes 3.5 mm from edges (58 x 49 pattern), header centred between the end holes on the hole-row axis; at least one hole aligned; stacking header + spacers; >=15 mm (16 ideal) board-to-board over an Active Cooler; do not foul PoE header or camera/display/PCIe flex connectors'} | verified | Raspberry Pi HAT+ specification RP-008281-DS-1 (uploaded), ch. 6-7, Fig. 2 |
| interposer_socket_current_a | 4.7 | verified | Samtec SSW/TSW spec 3.1: 4.7 A, one pin powered per row. We power +5 V pins 2 and 4 side by side and GND pins in both rows, so derate (catalog curve needed). The Pi header pins/traces (~3 A per pin class) remain the practical limit. |
| pi5_mechanical_drawing_step | True | verified | Official Raspberry Pi 5 mechanical drawing RP-008347-DS-1 (uploaded): 85 x 56 mm, mounting holes dia 2.7 at (3.5,3.5)/(61.5,3.5)/(3.5,52.5)/(61.5,52.5), header on the hole-row axis 3.5 mm from the top edge, centred at x = 32.5, component outlines near the header. STEP not supplied (not needed for the plan-view check). |
| interposer_socket_family | Samtec SSW vertical through-hole socket, 0.100 in / 2.54 mm pitch, 0.025 in square post, 2x20 dual row | verified | Samtec SSW/TSW product specification rev C (2023-02-08, uploaded; two identical copies): current 4.7 A with ONE PIN POWERED PER ROW; 465 VAC; gold -55..+125 C; durability 1000 cycles; normal force >= 30 g (gold); contact resistance is specified only as a CHANGE (LLCR delta 15 mOhm max after tests), no absolute initial value; standoffs recommended. Prints, footprints and lead styles are on the Samtec product page, NOT in this spec. | Catalog F-226 (uploaded): 4.7 A per pin with 2 pins powered (= one per row in a double-row part; same basis as the spec), 465 VAC/655 VDC, -55..+125 C gold, max 100 cycles with 10 uin Au, phosphor bronze over 50 uin Ni. |
| pi5_envelope_docs | {'board_mm': '85 x 56 (bumper 89.6 x 60.6 implies +4.6 mm per side)', 'official_case_mm': '98.5 x 70.3 x 33 (approx, reference only)', 'pcie_ffc': '16-pin 0.5 mm FFC; 5 V pins 1,2 rated 500 mA each (1 A total), not a power path', 'power_states': 'STANDBY = +5 V rail powered, other rails off'} | verified | Raspberry Pi RP-008159 (case), RP-008144 (bumper), RP-008298 (PCIe connector) briefs - envelope info only; NOT the header/component geometry needed for the 180-degree key check |
| pi_m2_hat_reference | M.2 HAT+ ships with a 16 mm stacking header + threaded spacers so it fits over the Active Cooler | verified | Raspberry Pi M.2 HAT+ product brief RP-009234-MM-1 (uploaded) |
| interposer_socket_dims | {'body_height_mm': 8.51, 'tail_length_mm': 2.64, 'pitch_mm': 2.54, 'rows': 2, 'positions': 40, 'insertion_depth_mm': [3.68, 6.35], 'pi_header_plastic_mm': 2.5, 'pi_pin_tip_height_mm': 9.0} | verified | Samtec SSW/SSQ through-hole catalog page F-226 (uploaded): straight-pin body height 8.51 mm (.335 in); lead style -01 tail A = 2.64 mm (.104 in) (-02 4.93, -03 10.00, -04 14.83, -06 3.15); double row width 4.95 mm; mating insertion depth 3.68-6.35 mm; Pi header plastic 2.5 mm is a standard-header ASSUMPTION; pin tip ~9 mm from the Pi 5 drawing. |
| display_power_feed | J_DISP direct feed (Molex 430450200) from the 5V_PI node after F2 | verified | Design decision (Waveshare_integration.md): the interposer covers the Pi header, so the display cannot use Pi pins; display current stays out of the harness/interposer/socket. Waveshare datasheet itself not available: display current is a first-article measurement. |
| waveshare_current_a | 0.8 | user_relayed_manufacturer | 0.8 A typical (manufacturer); maximum NOT published. 1.0 A is used as a design scenario only; first article measures the actual current. |
| harness_terminal | Molex 43030-0038 (18 AWG / 0.75 mm2, tin) with 18 AWG UL1061-type wire, insulation OD <= 1.85 mm; housings 43025-0200 / 43025-0400 | verified | Molex ATS-638280200 (Hand Crimp Tool 63828-0200 application tooling spec, rev D, uploaded): 43030-0038/-0039/-0040 = 18 AWG / 0.75 mm2; insulation OD 1.60-1.85 mm (IPC) / 0.90-1.85 mm (terminal); strip 2.54-2.92 mm; conductor crimp height 1.00-1.10 mm (18 AWG) / 0.85-0.95 mm (0.75 mm2); pull force >= 89 N; locator 63828-0275. The 24-20 AWG / 30-26 AWG rows of the 43030 series table are user-relayed (not in the uploaded file): no 16 AWG 43030 terminal. |
| harness_wire_awg | 18 | verified | Follows from harness_terminal: 16 AWG does not fit any 43030 terminal; 18 AWG (20.9 mOhm/m at 20 C, x1.2 hot) is used in the budget |
| waveshare_input_range_v | [4.75, 5.0, 5.3] | user_relayed_manufacturer | Waveshare 10.1-DSI-TOUCH-A (SKU 30052) specification as relayed by the owner: input 4.75 / 5.00 / 5.30 V (min/nom/max); 0.8 A typical, maximum not published; supply should provide >= ~0.8 A or start-up abnormalities may occur; 0-60 C operating. Package cables: MX1.25 2PIN to 2.54 3PIN and MX1.25 2PIN to MX1.25 4PIN. Not read locally. |
| tvs1_smbj15a | {'vrwm_v': 15.0, 'vbr_min_v': 16.7, 'vbr_max_v': 18.5, 'vbr_test_ma': 1, 'vc_max_v': 24.4, 'ipp_a': 24.6, 'ppp_w': 600, 'ir_ua': 1, 'package': 'DO-214AA / SMB', 'tj_c': [-65, 150]} | user_relayed_manufacturer | Littelfuse SMBJ series datasheet, SMBJ15A row (user-relayed; not read locally). Unidirectional A part. |

`owner_cited` = supplied by the project owner with a source; the build environment cannot reach Mean Well, Molex, Littelfuse or Harwin, so re-check against the PDFs. Assumptions: socket contact resistance (SSW-120-01-L-D, no initial value published) is a conservative 20 mOhm PLACEHOLDER to be MEASURED on first articles - not lowered on paper, interposer copper 2 mOhm/rail, hot-fuse 1.3x sensitivity.

Source tolerance from the datasheet: accuracy +-1 % + line +-0.2 % + load +-0.5 % (low corner at 5 A = -1.51 %, no-load high corner = +1.70 %, at 25 C). PCB copper 2.2 mOhm; F2 7.7 mOhm cold; J_OUT 10.0 mOhm max/contact; SSW-120-01-L-D socket contact 20 mOhm (placeholder, first-article measured), 2 contacts on +5 V and 4 on GND.

## Results at the Pi 5V pins

| Case | R typ / max (mOhm) | setpoint | 5 A typ / worst (V) | 3 A worst (V) | no-load max (V) |
|---|---|---|---|---|---|
| Untrimmed (5.00 V) | 37.1 / 52.7 | 5.000 | 4.81 / 4.66 | 4.77 | 5.085 |
| Trimmed to 5.192 V (window-limited) | 37.1 / 52.7 | 5.192 | 5.01 / 4.85 | 4.96 | 5.280 |
| Trimmed, only 2 GND contacts (no 14/20) | 40.1 / 57.7 | 5.192 | 4.99 / 4.83 | 4.94 | 5.280 |
| Socket contact 25 mOhm (placeholder + 5), trimmed | 39.4 / 56.4 | 5.192 | 5.00 / 4.83 | 4.94 | 5.280 |
| Hot F2 (x1.3), trimmed | 39.5 / 55.0 | 5.192 | 4.99 / 4.84 | 4.95 | 5.280 |

Feasibility window (25 C stack): one setpoint can meet both limits only if worst-case path R <= 46.8 mOhm; this design is 52.7 mOhm -> **NOT feasible without per-unit calibration** (margin -5.8 mOhm). Untrimmed, the 5 A worst case is below the Pi floor, so **trim is required**.

Required stacking-socket contact resistance (max, per contact; 2 contacts on +5 V, 4 on GND) for a single fixed setpoint to satisfy both limits:

| Tolerance scenario | max socket contact (mOhm) |
|---|---|
| 25 C stack | 12.2 |
| stack + 15 C drift | not achievable (even 0 mOhm contacts) |
| calibrated unit + 15 C drift | 19.0 |

Contact loading at 5 A: 2.5 A per Pi 5 V pin/socket contact. Samtec SSW rates 4.7 A with one pin powered per row; that is NOT 4.7 A per contact with all adjacent power contacts loaded - here two +5 V pins share ~5 A (2.5 A each, 53 % of 4.7 A, comfortable) and the Pi header pin is the nominal ~3 A-class limit (83 %) - **no derating headroom**; the Pi has only two 5 V pins (2 and 4), so this cannot be improved by adding 5 V contacts. At 8 A the contacts and Pi header pins would be overloaded (4 A each): keep real load <= ~5 A. See the Pi_end note.

## Tolerance scenarios (does one setpoint satisfy both limits?)

| Tolerance scenario | low / high corner | setpoint needed | max setpoint allowed (<=5.25 V) | margin | feasible |
|---|---|---|---|---|---|
| Datasheet stack at 25 C (accuracy+line+load) | -1.51 % / +1.70 % | 5.192 V | 5.162 V | -30 mV | NO |
| Stack + temperature drift (0.75 % for dT=15 C) | -2.26 % / +2.45 % | 5.232 V | 5.124 V | -107 mV | NO |
| Unit calibrated at 25 C (accuracy term removed) + temp drift | -1.26 % / +1.45 % | 5.179 V | 5.175 V | -4 mV | NO |

The +-1 % accuracy alone (as first assumed) hides the line/load terms and the 0.05 %/C coefficient. At 25 C the design closes by only a few mV; with realistic temperature rise it does **not** close by the stated criteria unless each unit is calibrated (measure the untrimmed output, then select Rt) and/or path resistance is reduced.

## Trim-up resistor (Mean Well formula, verified)

Vref = 1.24 V, R1 = 15.47 k, R2 = 5.1 k, R3 = 33.0 k; nominal Vout = 5.001 V. `a = Vref*R1/(Vout - Vref)`, `Rt = a*R2/(R2 - a) - R3`, Rt from TRIM to -Vout (board pad **R3**; R2 pad is trim-down and is not used).

| Setpoint | +% | Rt (R3 pad), calc | E96 | Vout with E96 | worst-case Pi @5A | no-load max |
|---|---|---|---|---|---|---|
| 5.172 V | +3.4 % | 79.4 kOhm | 78.7 kOhm | 5.173 V | 4.83 V | 5.261 V |
| 5.192 V | +3.8 % | 67.6 kOhm | 68.1 kOhm | 5.191 V | 4.85 V | 5.279 V |
| 5.212 V | +4.2 % | 58.1 kOhm | 57.6 kOhm | 5.213 V | 4.87 V | 5.302 V |

**Window-limited setpoint 5.192 V -> Rt = 67.6 kOhm, E96 68.1 kOhm (gives 5.191 V). R3 stays DNP until you approve the resistor.** The +-1 % accuracy is assumed to hold at the trimmed setpoint (confirm). R3 pad is 0603; use a 0.1 % or 1 % resistor.

## F1 (input fuse)

F1 = 0407008.WR (Littelfuse 407, 1206 time-lag, 8 A, 24 V max, interrupt 60 A @ 24 VDC; datasheet-verified). Nominal resistance 9 mOhm (cold), 12.1 mOhm hot at 8 A (0.097 V drop). At the 5 A design load (2.3 A in): 28 mV drop, 0.07 W; at the module's full 8 A load (3.9 A in): 48 mV, 0.19 W, 49 % of rating (datasheet: run continuously <= 80 % = 6.4 A, plus temperature re-rating). Inrush check (ASSUMED 122 uF, 10 mOhm loop, 14.4 V): I2t ~ 1.26 A2s vs fuse melting I2t 24.12 A2s = 5 % - comfortable; confirm by scope. Input-side drop does not enter the 5 V budget (module UVLO 8 V). Note: 24 V max rating is ample for the 12 V bus (<=14.4 V); the SMBJ15A clamps ~24 V only in a surge.

## Status

1. KiCad 10 ERC/DRC: run in the build container (reports in `reports/`), re-run locally by the owner.
2. First article (not a gate): per-unit trim calibration, **measured socket and connector contact resistances**, loaded Pi voltage and harness/connector temperature rise (`First_article_checklist.md`).

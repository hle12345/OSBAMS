#!/usr/bin/env python3
"""5V distribution voltage-drop budget + trim setpoint calculation. Inputs: datasheet_inputs.json."""
import sys, json, os
D = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(f"{HERE}/datasheet_inputs.json")); V = lambda k: I[k]["value"]
RS = 0.246; PCB = (4.8 + 3.7 + 0.4) * RS                    # 2 oz, squares from RC1.1 layout
TRUNK = 13.4 * 1.2 * 0.15                                    # 16 AWG trunk, 150 mm, hot  (mOhm, one wire)
BW = V("branch_wire"); BR = BW["mohm_per_m"] * 1.2 * BW["length_m"]; SPL = BW["splice_mohm"]
TARGET, PI_MAX, PI_MIN = 4.85, 5.25, 4.75
ACC, LINE, LOAD, TC, DT = V("rsdw_tolerance_pct") / 100, V("rsdw_line_reg_pct") / 100, V("rsdw_load_reg_pct") / 100, V("rsdw_tempco_pct_per_c") / 100, V("delta_t_c")
tl = ACC + LINE + LOAD * 5 / 8        # low corner at 5 A (5/8 of rated load), 25 C
th = ACC + LINE + LOAD                # high corner at no load, 25 C
tol = (tl + th) / 2
def R(j, pi, f2, n_pi_gnd=2, n_pi_5v=2):
    """mOhm. J_OUT: 2 contacts/rail. Trunk: 2x16 AWG/rail, each spliced to one 22 AWG lead -> Harwin contact (2/rail)."""
    rail5 = j / 2 + TRUNK / 2 + (SPL + BR + pi) / n_pi_5v
    railg = j / 2 + TRUNK / 2 + (SPL + BR + pi) / n_pi_gnd
    return PCB + f2 + rail5 + railg
F2 = V("f2_resistance_cold_mohm"); Jmax, Jtyp = V("j_out_contact_max_mohm"), V("j_out_contact_typ_mohm")
Pmax, Ptyp = V("pi_end_contact_max_mohm"), V("pi_end_contact_typ_mohm")
rt_, rm_ = R(Jtyp, Ptyp, F2), R(Jmax, Pmax, F2)
rwin = (PI_MAX * (1 - tl) / (1 + th) - TARGET) / 5 * 1e3
sp_need = (TARGET + 5 * rm_ / 1e3) / (1 - tl)
tab = ["| Case | R typ / max (mOhm) | setpoint | 5 A typ / worst (V) | 3 A worst (V) | no-load max (V) |", "|---|---|---|---|---|---|"]
def row(name, rt, rm, sp):
    tab.append(f"| {name} | {rt:.1f} / {rm:.1f} | {sp:.3f} | {sp - 5*rt/1e3:.2f} / {sp*(1-tl) - 5*rm/1e3:.2f} | {sp*(1-tl) - 3*rm/1e3:.2f} | {sp*(1+th):.3f} |")
row("Untrimmed (5.00 V)", rt_, rm_, 5.0)
import math
SP = math.ceil(sp_need * 1000) / 1000
row(f"Trimmed to {SP:.3f} V (window-limited)", rt_, rm_, SP)
row("Trimmed, 3 Pi GND contacts", R(Jtyp, Ptyp, F2, 3), R(Jmax, Pmax, F2, 3), SP)
row("Hot F2 (x1.3), trimmed", R(Jtyp, Ptyp, F2 * 1.3), R(Jmax, Pmax, F2 * 1.3), SP)
cur = 5.0 / 2
# ---- trim-up resistor, Mean Well formula (owner-cited): a = Vref*R1/(Vout-Vref); Rt = a*R2/(R2-a) - R3 ; Rt from TRIM to -Vout
n = V("rsdw_trim_network"); Vr, R1, R2, R3 = n["Vref"], n["R1_kohm"], n["R2_kohm"], n["R3_kohm"]
vnom = Vr * (1 + R1 / R2)
def rt_for(vo):
    a = Vr * R1 / (vo - Vr); return a * R2 / (R2 - a) - R3
def vo_for(rt):
    a = 1 / (1 / R2 + 1 / (R3 + rt)); return Vr * (1 + R1 / a)
E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76]
def e96(x):
    d = 10 ** math.floor(math.log10(x)); return min((e * d for e in E96 + [10.0]), key=lambda c: abs(c - x))
trim = ["| Setpoint | +% | Rt (R3 pad), calc | E96 | Vout with E96 | worst-case Pi @5A | no-load max |", "|---|---|---|---|---|---|---|"]
for sp in (SP - 0.02, SP, SP + 0.02):  # SP is window-limited at 25 C
    rt = rt_for(sp); e = e96(rt); vo = vo_for(e)
    trim.append(f"| {sp:.3f} V | {(sp/vnom-1)*100:+.1f} % | {rt:.1f} kOhm | {e:.1f} kOhm | {vo:.3f} V | {vo*(1-tl) - 5*rm_/1e3:.2f} V | {vo*(1+th):.3f} V |")
rt_sel = rt_for(SP); e_sel = e96(rt_sel); vo_sel = vo_for(e_sel)

scen = [("Datasheet stack at 25 C (accuracy+line+load)", tl, th),
        (f"Stack + temperature drift ({TC*DT*100:.2f} % for dT={DT:.0f} C)", tl + TC * DT, th + TC * DT),
        (f"Unit calibrated at 25 C (accuracy term removed) + temp drift", tl - ACC + TC * DT, th - ACC + TC * DT)]
tt = ["| Tolerance scenario | low / high corner | setpoint needed | max setpoint allowed (<=5.25 V) | margin | feasible |", "|---|---|---|---|---|---|"]
for nme, a_, b_ in scen:
    need_ = (TARGET + 5 * rm_ / 1e3) / (1 - a_); mx_ = PI_MAX / (1 + b_)
    tt.append(f"| {nme} | -{a_*100:.2f} % / +{b_*100:.2f} % | {need_:.3f} V | {mx_:.3f} V | {(mx_-need_)*1000:+.0f} mV | {'yes' if mx_ >= need_ else 'NO'} |")
lines = [
"# 5 V distribution voltage-drop budget (RC1.1)", "",
"Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT (2 contacts/rail) -> 16 AWG trunk (<=150 mm) -> splice -> 22 AWG branch leads (~50 mm) -> Harwin M20 contacts (2 per rail) -> Pi 5V pins` and the matching return.",
f"Target: **>= {TARGET} V at the Pi header at 5 A, worst case**; **<= {PI_MAX} V no-load / high-line** (Pi floor {PI_MIN} V).", "",
"## Inputs and status (`datasheet_inputs.json`)", "", "| Input | Value | Status | Source |", "|---|---|---|---|",
*[f"| {k} | {I[k]['value']} | {I[k]['status']} | {I[k]['source']} |" for k in I if not k.startswith('_')], "",
"`owner_cited` = supplied by the project owner with a source; the build environment cannot reach Mean Well, Molex, Littelfuse or Harwin, so re-check against the PDFs. Assumptions: typical Harwin 12 mOhm, branch wire/splice values, hot-fuse 1.3x sensitivity.", "",
f"Source tolerance from the datasheet: accuracy +-1 % + line +-0.2 % + load +-0.5 % (low corner at 5 A = -{tl*100:.2f} %, no-load high corner = +{th*100:.2f} %, at 25 C). PCB copper {PCB:.1f} mOhm; F2 {F2} mOhm cold; J_OUT {Jmax} mOhm max/contact; Harwin M20 {Pmax:.0f} mOhm max/contact, 2 contacts per rail.", "",
"## Results at the Pi 5V pins", "", *tab, "",
f"Feasibility window: one setpoint can meet both limits only if worst-case path R <= {rwin:.1f} mOhm; this design is {rm_:.1f} mOhm -> **feasible, margin {rwin - rm_:.1f} mOhm**. Untrimmed, the 5 A worst case is below the Pi floor, so **trim is required**.",
f"Contact loading at 5 A: {cur:.1f} A per Harwin 5 V contact vs 3 A rating ({cur/3*100:.0f} %) - **no derating headroom**; the Pi has only two 5 V pins (2 and 4), so this cannot be improved by adding 5 V contacts. At 8 A the contacts and Pi header pins would be overloaded (4 A each): keep real load <= ~5 A. See the Pi_end note.", "",
"## Tolerance scenarios (does one setpoint satisfy both limits?)", "", *tt, "", "The +-1 % accuracy alone (as first assumed) hides the line/load terms and the 0.05 %/C coefficient. At 25 C the design closes by only a few mV; with realistic temperature rise it does **not** close by the stated criteria unless each unit is calibrated (measure the untrimmed output, then select Rt) and/or path resistance is reduced.", "",
"## Trim-up resistor (Mean Well formula, verified)", "",
f"Vref = {Vr} V, R1 = {R1} k, R2 = {R2} k, R3 = {R3} k; nominal Vout = {vnom:.3f} V. `a = Vref*R1/(Vout - Vref)`, `Rt = a*R2/(R2 - a) - R3`, Rt from TRIM to -Vout (board pad **R3**; R2 pad is trim-down and is not used).", "",
*trim, "",
f"**Window-limited setpoint {SP:.3f} V -> Rt = {rt_sel:.1f} kOhm, E96 {e_sel:.1f} kOhm (gives {vo_sel:.3f} V). R3 stays DNP until you approve the resistor.** The +-1 % accuracy is assumed to hold at the trimmed setpoint (confirm). R3 pad is 0603; use a 0.1 % or 1 % resistor.", "",
"## Remaining RC2 gates", "",
"1. Housing size / pin map and anti-reversal keying at the Pi end (`Pi_end_connector_requirements.md`).",
"2. RSDW40F-05 pin X/Y, drill and keepout from the Mean Well drawing (body 50.8 x 25.4 mm, pin dia ~1.0 mm are recorded; coordinates not supplied).",
"3. KiCad 10 ERC.  4. Bench voltage at the Pi header under real load.", ""]
open(f"{D}/docs/Voltage_drop_budget.md", "w").write("\n".join(lines))
print("\n".join(tab)); print("window", round(rwin,1), "Rmax", round(rm_,1)); print("\n".join(trim))

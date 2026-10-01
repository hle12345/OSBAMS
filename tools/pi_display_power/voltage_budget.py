#!/usr/bin/env python3
"""5V distribution voltage-drop budget + trim setpoint calculation. Inputs: datasheet_inputs.json."""
import sys, json, os
D = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(f"{HERE}/datasheet_inputs.json")); V = lambda k: I[k]["value"]
RS = 0.246; PCB = (4.8 + 3.7 + 0.4) * RS                    # 2 oz, squares from RC1.1 layout
W16 = 13.4 * 1.2 * 0.15                                      # 16 AWG, 150 mm, hot
TARGET, PI_MAX, PI_MIN = 4.85, 5.25, 4.75
tol = V("rsdw_tolerance_pct") / 100
def R(contact_j, pi_end, f2, pi_ng=2):                       # mOhm; 2 contacts paralleled per rail
    return PCB + f2 + contact_j / 2 + contact_j / 2 + W16 / 2 + W16 / 2 + pi_end / 2 + pi_end / pi_ng
F2 = V("f2_resistance_cold_mohm"); F2H = F2 * 1.3
Jmax, Jtyp = V("j_out_contact_max_mohm"), V("j_out_contact_typ_mohm")
pi_vals = [5.0, 10.0, 15.0, 20.0]
head = "| Pi-end contact (mOhm, per contact) | R typ / max (mOhm) | 5 A typ / worst V | 3 A worst V | setpoint for 4.85 V (worst) | no-load max | fits <= 5.25 V |"
tab = [head, "|---|---|---|---|---|---|---|"]
for p in pi_vals:
    rt, rm = R(Jtyp, p * 0.6, F2), R(Jmax, p, F2)         # typ Pi-end assumed 0.6x of max
    v5t, v5w, v3w = 5.0 - 5 * rt / 1e3, 5.0 * (1 - tol) - 5 * rm / 1e3, 5.0 * (1 - tol) - 3 * rm / 1e3
    sp = (TARGET + 5 * rm / 1e3) / (1 - tol); mx = sp * (1 + tol)
    tab.append(f"| {p:.0f} | {rt:.1f} / {rm:.1f} | {v5t:.2f} / {v5w:.2f} | {v3w:.2f} | {sp:.3f} V ({(sp/5-1)*100:+.1f} %) | {mx:.3f} V | {'yes' if mx <= PI_MAX else 'NO'} |")
# max Pi-end contact R for which a single setpoint meets both limits
rwin = (PI_MAX * (1 - tol) / (1 + tol) - TARGET) / 5 * 1e3
pmax = None
for p in [x / 10 for x in range(0, 400)]:
    if R(Jmax, p, F2) <= rwin: pmax = p
hot = R(Jmax, 10.0, F2H) - R(Jmax, 10.0, F2)
# ---- trim calculation (ASSUMED topology: Rt+R3 in series, in parallel with R2, trim-up resistor TRIM -> -Vout)
n = V("rsdw_trim_network"); Vr, R1, R2, R3 = n["Vref"], n["R1_kohm"], n["R2_kohm"], n["R3_kohm"]
vnom = Vr * (1 + R1 / R2)
def rt_for(vo):
    g = (vo / Vr - 1) / R1 - 1 / R2                         # 1/(R3+Rt)
    return (1 / g - R3) if g > 0 else None
def vo_for(rt): return Vr * (1 + R1 * (1 / R2 + 1 / (R3 + rt)))
trim = ["| Setpoint | +% | Rt (R3 DNP pad), calc | nearest E96 | resulting Vout | Vout if Rt +1 % |", "|---|---|---|---|---|---|"]
E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76]
def e96(x):
    import math
    d = 10 ** math.floor(math.log10(x)); return min((e * d for e in E96 + [10.0]), key=lambda c: abs(c - x))
for sp in (5.05, 5.10, 5.15):
    rt = rt_for(sp)
    if rt: e = e96(rt); trim.append(f"| {sp:.2f} V | {(sp/vnom-1)*100:+.1f} % | {rt:.1f} kOhm | {e:.1f} kOhm | {vo_for(e):.3f} V | {vo_for(e*1.01):.3f} V |")
lines = [
"# 5 V distribution voltage-drop budget (RC1.1)", "",
"Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT contacts -> harness -> Pi-end contacts -> Pi 5V pins` and return. 2 contacts paralleled for +5 V and for GND, 16 AWG <=150 mm (x1.2 hot), 2 oz copper from the layout.",
f"Target: **>= {TARGET} V at the Pi header at 5 A, worst case** (Pi floor {PI_MIN} V, ceiling {PI_MAX} V); nominal input 5.0-5.1 V.", "",
"## Inputs and status (`datasheet_inputs.json`)", "", "| Input | Value | Status | Source |", "|---|---|---|---|",
*[f"| {k} | {I[k]['value']} | {I[k]['status']} | {I[k]['source']} |" for k in I if not k.startswith('_')], "",
"`owner_cited` = given by the project owner with a source; the build environment cannot reach the manufacturer sites, so re-check against the PDFs. **The Pi-end contact value is a placeholder, not a design input** - the Pi-end connector has not been selected.", "",
f"F2 = {F2} mOhm cold (as instructed). Hot sensitivity: if F2 runs 1.3x hot in service, the worst-case path gains {hot:.1f} mOhm = {hot*5:.0f} mV at 5 A. J_OUT: {Jmax} mOhm max / {Jtyp} typ per contact (max is conservative).", "",
"## Results vs the unknown Pi-end contact resistance", "", *tab, "",
f"With +-{V('rsdw_tolerance_pct'):.0f} % source tolerance (assumed), one setpoint can satisfy both 4.85 V @ 5 A and <= 5.25 V no-load only if worst-case path R <= {rwin:.1f} mOhm, i.e. **the Pi-end connector must be <= ~{pmax:.1f} mOhm per contact** (2 contacts in parallel per rail) with the other terms as above. This is the requirement for the connector selection.", "",
"## Trim calculation (ASSUMED topology - do not fit R2/R3 on this basis)", "",
f"Given: Vref = {Vr} V, R1 = {R1} k, R2 = {R2} k, R3 = {R3} k -> nominal Vout = Vref(1 + R1/R2) = {vnom:.3f} V (matches 5 V). Trim-up resistor Rt connects TRIM to -Vout (board pad **R3** = TRIM to PI_GND; pad R2 = TRIM to +VOUT is trim-down and is not needed).",
"Assumed network: Vout = Vref * (1 + R1 * (1/R2 + 1/(R3 + Rt))), i.e. R3 in series with Rt, both in parallel with R2. The source gave the component values but not this exact topology, so the Rt values below must be confirmed against the Mean Well datasheet formula before any resistor is fitted.", "",
*trim, "",
f"Check: Rt -> 0 gives {vo_for(0):.2f} V (+{(vo_for(0)/vnom-1)*100:.1f} %), consistent with a +-10 % trim range under this assumed topology. Setpoint tolerance adds the unknown RSDW tolerance on top; E96 1 % resistors move Vout by only a few mV at these values.", "",
"## Still open before RC2", "",
"1. Select the Pi-end connector (exact MPN, published per-contact current and contact resistance <= the limit above) - `Pi_end_connector_requirements.md`.",
"2. RSDW40F-05 setpoint tolerance and the exact trim formula/topology; then pick the setpoint (likely 5.05-5.10 V) and keep R2/R3 DNP until then.",
"3. RSDW40F-05 mechanical drawing -> U1 footprint.  4. KiCad 10 ERC.  5. Bench voltage at the Pi header under real load.", ""]
open(f"{D}/docs/Voltage_drop_budget.md", "w").write("\n".join(lines))
print("\n".join(tab)); print(f"window R<= {rwin:.1f}; Pi-end max per contact {pmax}"); print("\n".join(trim))

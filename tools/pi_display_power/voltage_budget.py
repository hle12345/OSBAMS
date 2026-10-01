#!/usr/bin/env python3
"""5V distribution voltage-drop budget. Inputs come from datasheet_inputs.json; unverified items are flagged in the output."""
import sys, json, os
D = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(f"{HERE}/datasheet_inputs.json")); V = lambda k: I[k]["value"]
tag = lambda k: "verified" if I[k]["verified"] else "UNVERIFIED"
RS = 0.246                                        # 2 oz copper, mOhm/sq
SQ = 4.8 + 3.7 + 0.4                              # 5V path + GND return squares measured on RC1.1 layout
PCB = SQ * RS
WIRE = {"18 AWG": 21.4, "16 AWG": 13.4}           # mOhm/m @20C; x1.2 for ~50C
TARGET, PI_MAX, PI_MIN = 4.85, 5.25, 4.75
def R(which, awg="16 AWG", L=0.15, pi_end=None, f2=None, n5=2, ng=2, pi_ng=2, fuse=True):
    j = V("j_out_contact_max_mohm") if which else V("j_out_contact_typ_mohm")
    p = pi_end if pi_end is not None else (V("pi_end_contact_max_mohm") if which else V("pi_end_contact_typ_mohm"))
    f = f2 if f2 is not None else (V("f2_resistance_max_mohm") if which else V("f2_resistance_typ_mohm"))
    w = WIRE[awg] * 1.2 * L
    return PCB + (f if fuse else 0) + j / n5 + j / ng + w / n5 + w / ng + p / n5 + p / pi_ng
tol = V("rsdw_tolerance_pct") / 100
vmin = lambda k=1.0: 5.0 * k * (1 - tol); vmax = lambda k=1.0: 5.0 * k * (1 + tol)
rows = []
def case(name, rt, rm, k=1.0):
    rows.append((name, rt, rm, k, 5.0 * k - 3 * rt / 1000, vmin(k) - 3 * rm / 1000, 5.0 * k - 5 * rt / 1000, vmin(k) - 5 * rm / 1000, vmax(k)))
rt, rm = R(0), R(1);                       case("A  RC1.1 baseline (16 AWG/150 mm, Pi-end 20 mOhm max, F2 15 max)", rt, rm)
case("B  A + Pi-end terminal <= 10 mOhm (selection requirement)", R(0, pi_end=None) - 0, R(1, pi_end=10.0))
case("C  B + F2 <= 8 mOhm (lower-resistance fuse)", R(0), R(1, pi_end=10.0, f2=8.0))
case("D  C + 4 Pi GND pins", R(0), R(1, pi_end=10.0, f2=8.0, pi_ng=4))
# required trim for target in the stacked worst case, and feasibility vs 5.25 V
def need(rmax):
    k = (TARGET + 5 * rmax / 1000) / (5.0 * (1 - tol)); return k
out = ["| Case | R typ / max (mOhm) | V@Pi 3 A typ / worst | V@Pi 5 A typ / worst | max src (no load) |", "|---|---|---|---|---|"]
for n, a, b, k, t3, w3, t5, w5, mx in rows: out.append(f"| {n} | {a:.1f} / {b:.1f} | {t3:.2f} / {w3:.2f} | {t5:.2f} / {w5:.2f} | {mx:.2f} |")
feas = ["| Worst-case R (mOhm) | Setpoint needed for 4.85 V @5 A (worst) | No-load max at that setpoint | Fits <= 5.25 V? |", "|---|---|---|---|"]
for lab, r in [("A", R(1)), ("B", R(1, pi_end=10.0)), ("C", R(1, pi_end=10.0, f2=8.0)), ("D", R(1, pi_end=10.0, f2=8.0, pi_ng=4))]:
    k = need(r); sp = 5.0 * k; mx = sp * (1 + tol)
    feas.append(f"| {lab}: {r:.1f} | {sp:.3f} V ({(k-1)*100:+.1f} %) | {mx:.3f} V | {'yes' if mx <= PI_MAX else 'NO'} |")
rmax_window = (PI_MAX * (1 - tol) / (1 + tol) - TARGET) / 5 * 1000   # largest worst-case R for which one setpoint meets both 4.85 V@5A and <=5.25 V no-load
w_fixed20 = R(1, fuse=False); w_fixed10 = R(1, pi_end=10.0, fuse=False)
lines = [
"# 5 V distribution voltage-drop budget (RC1.1)", "",
"Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT contacts -> harness -> Pi-end contacts -> Pi 5V pins` and return. 2 contacts paralleled per rail, 16 AWG <=150 mm (x1.2 hot), 2 oz copper from the measured layout.",
f"Target: **>= {TARGET} V at the Pi header at 5 A, worst case** (Pi floor {PI_MIN} V, ceiling {PI_MAX} V).", "",
"## Inputs and their status (`datasheet_inputs.json`)", "", "| Input | Value | Status | Source |", "|---|---|---|---|",
*[f"| {k} | {I[k]['value']} | {tag(k)} | {I[k]['source']} |" for k in I if not k.startswith('_')], "",
"**Clarification on the 20 mOhm:** that figure is the *Pi-end* 2.54 mm crimp terminal + header pin, not Micro-Fit. The Molex 10 mOhm max applies to the J_OUT mating contacts, which RC1.1 already budgeted at 10 mOhm max. The Micro-Fit data therefore does not lower the Pi-end term; it only becomes 10 mOhm if the chosen Pi-end terminal is *specified* at <=10 mOhm (case B). Molex quotes a maximum only, and as you note the measured value includes wire resistance, so the max-stack below is conservative.", "",
"## Results at the Pi 5V pins", "", *out, "",
"## Is 4.85 V achievable in the stacked worst case? (setpoint window)", "", *feas, "",
f"With +-{V('rsdw_tolerance_pct'):.0f} % source tolerance, a setpoint that gives {TARGET} V at 5 A *and* stays <= {PI_MAX} V at no load exists only if worst-case R <= **{rmax_window:.1f} mOhm** (non-fuse terms: {w_fixed20:.1f} mOhm with a 20 mOhm Pi-end terminal -> F2 <= {rmax_window - w_fixed20:.1f} mOhm; {w_fixed10:.1f} mOhm with a 10 mOhm Pi-end terminal -> F2 <= {rmax_window - w_fixed10:.1f} mOhm). So the Pi-end terminal must be a <=~10 mOhm part and F2 must be a low-resistance part for any trim setting to satisfy both limits.",
"Preferred 4.9-5.0 V at 5 A needs either a tighter RSDW tolerance than assumed or lower resistance than any configuration above - to be settled from the RSDW datasheet, not assumed.", "",
"## What must be verified before RC2 (blocking)", "",
"1. F2 exact cold resistance and 5 A voltage drop - Littelfuse 0451008.MRL datasheet; if it exceeds the F2 limit above, choose a lower-resistance suitable Nano2 (keep over-current protection; the 451/453 family goes to 20 A) and re-check I2t/ratings against U1's overload limit.",
"2. RSDW40F-05 setpoint tolerance, trim range, formula and resistor topology (which of R2/R3, value) - Mean Well datasheet. Use trim only if explicitly permitted; R2/R3 stay DNP.",
"3. RSDW40F-05 mechanical drawing -> U1 footprint.",
"4. Pi-end terminal contact resistance (<=10 mOhm class selection) and a measured harness.",
"5. Bench: voltage at the Pi header under real Pi 5 + Waveshare load.", ""]
open(f"{D}/docs/Voltage_drop_budget.md", "w").write("\n".join(lines))
print("\n".join(out)); print(); print("\n".join(feas)); print(f"window: worst-case R <= {rmax_window:.1f} mOhm")

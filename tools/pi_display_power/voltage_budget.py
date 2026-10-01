#!/usr/bin/env python3
"""5V distribution voltage-drop budget. ALL resistances are ASSUMPTIONS until replaced with datasheet / measured values."""
import sys, itertools
D = sys.argv[1]
# per-element (typ, max) in mOhm; contacts are per mated contact; parallel contacts divide
A = dict(
  v_src=(5.00, 4.90),               # nominal, worst-case-low output (setpoint + load regulation, ASSUMED +-2 %; RSDW tolerance NOT verified)
  fuse=(8.0, 15.0),                 # F2 0451008 hot resistance, ASSUMED (datasheet not accessible)
  j_out=(5.0, 10.0),                # Micro-Fit mated contact, ASSUMED (Molex spec not accessible)
  pi_end=(8.0, 20.0),               # 2.54 mm crimp terminal + Pi header pin, ASSUMED
)
# PCB copper from the actual layout (2 oz = 0.246 mOhm/sq): 5V path squares and GND return squares
RS = 0.246
PCB = {"RC1 layout (old)": (6.0, 6.0), "RC2 layout (this board)": (4.8 + 3.7, 0.4)}  # (5V squares, GND squares)
WIRE_MOHM_M = {"18 AWG": 21.4, "16 AWG": 13.4}   # 20 C; x1.2 for ~50 C applied below
def total(layout, awg, length_m, n5=2, ngnd=2, fuse=True, which=0, pi_ngnd=None):
    sq5, sqg = PCB[layout]; pcb = (sq5 + sqg) * RS
    w = WIRE_MOHM_M[awg] * 1.2 * length_m
    r = pcb + (A["fuse"][which] if fuse else 0) + A["j_out"][which] / n5 + A["j_out"][which] / ngnd \
        + w / n5 + w / ngnd + A["pi_end"][which] / n5 + A["pi_end"][which] / (pi_ngnd or ngnd)
    return r
rows = []
cases = [
 ("RC1: 18 AWG 250 mm, 2+2 Pi pins", "RC1 layout (old)", "18 AWG", 0.25, 2, 2, 1.00, True),
 ("RC1.1: 16 AWG 150 mm, 2+2 Pi pins, wide copper", "RC2 layout (this board)", "16 AWG", 0.15, 2, 2, 1.00, True),
 ("RC1.1 + 4 Pi GND pins (6,9,14,20 via splice)", "RC2 layout (this board)", "16 AWG", 0.15, 2, 4, 1.00, True),
 ("RC1.1, F2 deleted (NOT recommended w/o protection analysis)", "RC2 layout (this board)", "16 AWG", 0.15, 2, 2, 1.00, False),
 ("RC1.1 + trim to 5.10 V (only if Mean Well confirms)", "RC2 layout (this board)", "16 AWG", 0.15, 2, 2, 1.02, True),
]
out = ["| Case | R typ (mOhm) | R max (mOhm) | V@Pi 3 A typ / worst | V@Pi 5 A typ / worst |", "|---|---|---|---|---|"]
csvr = ["case,R_typ_mohm,R_max_mohm,V3_typ,V3_worst,V5_typ,V5_worst"]
for name, lay, awg, L, n5, ng, trim, fuse in cases:
    rt = total(lay, awg, L, n5, ng, fuse, 0, ng if ng != 2 else None) if False else total(lay, awg, L, n5, 2, fuse, 0, ng)
    rm = total(lay, awg, L, n5, 2, fuse, 1, ng)
    vt, vw = A["v_src"][0] * trim, A["v_src"][1] * trim
    v = lambda i: (vt - i * rt / 1000, vw - i * rm / 1000)
    v3, v5 = v(3), v(5)
    out.append(f"| {name} | {rt:.1f} | {rm:.1f} | {v3[0]:.2f} / {v3[1]:.2f} | {v5[0]:.2f} / {v5[1]:.2f} |")
    csvr.append(f'"{name}",{rt:.1f},{rm:.1f},{v3[0]:.3f},{v3[1]:.3f},{v5[0]:.3f},{v5[1]:.3f}')
# sensitivity of the RC1.1 baseline (5 A, worst-case) to each element
base = total("RC2 layout (this board)", "16 AWG", 0.15, 2, 2, True, 1, 2)
sens = []
def bump(key, new):
    old = A[key]; A[key] = (old[0], new); r = total("RC2 layout (this board)", "16 AWG", 0.15, 2, 2, True, 1, 2); A[key] = old; return r
sens.append(("F2 max 15 -> 8 mOhm", base - bump("fuse", 8.0)))
sens.append(("J_OUT contact max 10 -> 5 mOhm", base - bump("j_out", 5.0)))
sens.append(("Pi-end contact max 20 -> 10 mOhm", base - bump("pi_end", 10.0)))
sens.append(("Harness 18 AWG/250 mm -> 16 AWG/150 mm", total("RC2 layout (this board)", "18 AWG", 0.25, 2, 2, True, 1, 2) - base))
sens.append(("PCB copper RC1 -> RC1.1", total("RC1 layout (old)", "16 AWG", 0.15, 2, 2, True, 1, 2) - base))
pt = 0.0
lines = [
"# 5 V distribution voltage-drop budget (RC1.1)", "",
"Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT contacts -> harness -> Pi-end contacts -> Pi 5V pins` and the matching return.",
"**Every resistance below is an assumption** (Littelfuse, Molex and Mean Well datasheets were not reachable from the build environment). Replace the values in `tools/pi_display_power/voltage_budget.py` with datasheet/measured numbers and re-run.", "",
"## Assumptions", "",
f"- Source: 5.00 V nominal; worst-case low {A['v_src'][1]:.2f} V (+-2 % setpoint+regulation, not verified).",
f"- F2 hot resistance typ/max {A['fuse'][0]:.0f}/{A['fuse'][1]:.0f} mOhm; J_OUT mated contact {A['j_out'][0]:.0f}/{A['j_out'][1]:.0f} mOhm; Pi-end 2.54 mm crimp+header {A['pi_end'][0]:.0f}/{A['pi_end'][1]:.0f} mOhm per contact.",
"- Two contacts in parallel per rail (as specified); wire resistance derated x1.2 for ~50 C.",
f"- PCB copper (2 oz, {RS} mOhm/sq): 5 V path ~{PCB['RC2 layout (this board)'][0]:.1f} squares, GND return ~{PCB['RC2 layout (this board)'][1]:.1f} squares measured from the RC1.1 layout (RC1 assumed 6+6 mOhm-equivalent).",
"- Raspberry Pi 5 input: 5 V nominal; spec floor 4.75 V; low-voltage warning ~4.63 V (verify against Raspberry Pi documentation). Raspberry Pi recommends 5 V/5 A and says to allow for cable/connector loss.", "",
"## Results (voltage at the Pi 5V pins)", "", *out, "",
"Typ = nominal source and typical resistances. Worst = low source and maximum resistances stacked (deliberately pessimistic corner).", "",
"## What each lever buys (RC1.1 baseline, 5 A, worst case)", "", "| Change | Saves |", "|---|---|",
*[f"| {n} | {d * 5:.0f} mV |" for n, d in sens], "",
"## Reading the numbers",
"- **Typical case clears 4.85 V at 5 A (4.87 V); the stacked worst case does not (4.65 V, below the 4.75 V floor).** No single lever closes that corner: it needs low-resistance Pi-end contacts (-50 mV), a lower-resistance F2 (-35 mV) and trim together. Treat the worst-case corner as unproven until measured.",
"- The two largest terms are the *Pi-end* and J_OUT contacts, not copper or wire.",
"- Done in RC1.1, in your order: (1) fuse - kept F2 (see below); (2) 2+2 parallel contacts (unchanged); (3) harness changed to 16 AWG, <=150 mm; (4) PCB copper re-laid with wide pours (~5 mm bars, GND return through a full-width plane) - small gain; (5) trim *not* applied, but DNP pads R2/R3 added so a trim network can be fitted without a respin once Mean Well's trim formula and range are confirmed.",
"- **F2:** no lower-resistance 8 A Nano2 alternative can be selected without the Littelfuse datasheet. F2 is *not* removed. Its job is to protect the harness/connector if U1 fails short or its overload limit is higher than assumed; an 18 AWG or 16 AWG short run tolerates 8 A, so the fuse is protecting against >8 A fault current that U1's own limiting should already cap. Removal is a protection-analysis decision for you, not a voltage-margin shortcut.",
"- **Biggest lever that needs no new board:** choose Pi-end terminals/housing with low contact resistance (measure them), and keep +5 V on both Pi 5V pins (2,4). Adding GND pins (6,9,14,20) via a splice is shown as an option; it helps the return only.",
"- **Trim:** if Mean Well confirms the RSDW trim range, +2 % (5.10 V) gives ~4.97 V typical and ~4.75 V stacked-worst-case at 5 A (still marginal); no-load worst-case source is ~5.00 x 1.02 x 1.02 = ~5.20 V (< 5.25 V). Do not fit R2/R3 until the formula is confirmed - a wrong value could over-volt the Pi.",
"- **Gate:** a bench measurement *at the Pi header pins* under real Pi 5 + Waveshare load (and a stress test at 5 A) is still required before release.", ""]
open(f"{D}/docs/Voltage_drop_budget.md", "w").write("\n".join(lines))
open(f"{D}/docs/Voltage_drop_budget.csv", "w").write("\n".join(csvr) + "\n")
print("\n".join(out)); print("\n".join(f"{n}: {d*5:.0f} mV" for n, d in sens))

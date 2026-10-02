#!/usr/bin/env python3
"""Voltage-drop report for the combined Pi Power Carrier (RevB), recomputed from the layout and datasheet_inputs.json. usage: power_budget_carrier.py <project dir>"""
import sys, os, json, math
D = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from parts_carrier import *
I = json.load(open(f"{HERE}/datasheet_inputs.json")); V = lambda k: I[k]["value"]
RS = 0.246                                                    # mOhm per square, 2 oz (70 um) copper
F2 = V("f2_resistance_cold_mohm"); F2H = 1.3
J = V("j_out_contact_max_mohm"); JT = V("j_out_contact_typ_mohm"); SOCK = V("interposer_socket_contact_mohm"); HOTCU = 1.2
ACC, LINE, LOAD, TC, DT = V("rsdw_tolerance_pct") / 100, V("rsdw_line_reg_pct") / 100, V("rsdw_load_reg_pct") / 100, V("rsdw_tempco_pct_per_c") / 100, V("delta_t_c")
TARGET, PI_MAX, PI_MIN, DISP_MIN, DISP_MAX = 4.85, 5.25, 4.75, 4.75, 5.30
# ---- copper paths measured on this layout (length / width in mm -> squares)
sq = lambda l, w: l / w
pin4_f2 = sq(6.34 + 2.79, 2.5)                                  # U1 pin 4 -> F2 pad 1 (5V_ISO_RAW track)
zone_pi = sq(4.0, 9.8) + sq(7.0, 4.8)                           # F2 pad 2 -> Pi pins 2,4 (5V_PI pour, both pins in the same zone)
gnd_pi = sq(14.0, 40.0)                                         # U1 pin 5 -> Pi GND pins 6,9,14,20 (PI_GND B.Cu pour, 40 mm wide)
band = sq(49.6, 3.1) + sq(6.9, 2.5) + sq(2.0, 4.5)             # display branch: 5V band + track + stripe to J_DISP
gnd_disp = sq(28.0, 40.0)                                       # J_DISP GND pad -> U1 pin 5 through the PI_GND pour
PINJ = 2 * 0.5                                                  # U1 pins 4 and 5: solder joint + PTH barrel ~0.5 mOhm each (estimate)
HDR_PIN = 1.0                                                   # Pi-side header pin + solder joint per contact (estimate)
DLEAD = 2 * 0.2 * 33.0                                          # display lead 20 AWG 200 mm, both wires (33 mOhm/m)
shared = [("PCB: U1 pin 4 -> F2 (2.5 mm track, %.1f squares)" % pin4_f2, pin4_f2 * RS, pin4_f2 * RS * HOTCU),
          ("U1 pins 4 + 5 solder joints / PTH barrels (estimate)", PINJ, PINJ * 1.0),
          ("F2 0451008.MRL (7.7 mOhm cold; 1.3x hot)", F2, F2 * F2H)]
branch = [("PCB: F2 -> Pi pins 2,4 (5V_PI pour, %.1f squares)" % zone_pi, zone_pi * RS, zone_pi * RS * HOTCU),
          ("PCB: Pi GND pins 6,9,14,20 -> U1 pin 5 (PI_GND pour, %.2f squares)" % gnd_pi, gnd_pi * RS, gnd_pi * RS * HOTCU),
          (f"SSW-120-01-L-D socket contacts ({SOCK:g} mOhm/contact max, typ 0.6x; 2 on +5 V, 4 on GND)", SOCK * 0.6 / 2 + SOCK * 0.6 / 4, SOCK / 2 + SOCK / 4),
          (f"Pi header pins + solder joints ({HDR_PIN:g} mOhm/contact estimate; 2 on +5 V, 4 on GND)", HDR_PIN / 2 + HDR_PIN / 4, HDR_PIN / 2 + HDR_PIN / 4)]
disp = [("PCB: 5V_PI band + track to J_DISP (%.1f squares)" % band, band * RS, band * RS * HOTCU), ("PCB: J_DISP GND -> U1 pin 5 (%.2f squares)" % gnd_disp, gnd_disp * RS, gnd_disp * RS * HOTCU),
        ("J_DISP Micro-Fit contacts (1 on +5 V, 1 on GND; 5.24 typ / 10 max per contact)", 2 * JT, 2 * J), ("Display lead 20 AWG, 200 mm, both wires (hot 1.2x)", DLEAD / HOTCU, DLEAD)]
S = lambda L, i: sum(e[i] for e in L)
Rs_t, Rs_m, Rb_t, Rb_m, Rd_t, Rd_m = S(shared, 1), S(shared, 2), S(branch, 1), S(branch, 2), S(disp, 1), S(disp, 2)
tl = lambda i: LINE + LOAD * i / 8; th = LINE
# ---- trim resistor sensitivity (Mean Well formula, Vref 1.24 V, R1 15.47k, R2 5.1k, R3 33k)
n = V("rsdw_trim_network"); Vr, R1, R2, R3 = n["Vref"], n["R1_kohm"], n["R2_kohm"], n["R3_kohm"]
vo_for = lambda rt: Vr * (1 + R1 / (1 / (1 / R2 + 1 / (R3 + rt))))
E96 = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76,10.0]
rt_nom = 71.5; d1 = abs(vo_for(rt_nom * 1.01) - vo_for(rt_nom)) * 1000; step = abs(vo_for(73.2) - vo_for(71.5)) * 1000      # 1 % tolerance, one E96 step (71.5k -> 75.0k)
def vo_sp(sp, dt=DT): return sp
# ---- RC2 reference (separate Power board + interposer + 18 AWG harness), same constants as power_budget_rc2.py
rc2_s_t, rc2_s_m, rc2_b_t, rc2_b_m = 9.9, 12.2, 26.6, 42.8
SP = 5.185
def v_pi(ip, idp, sp=SP, worst=True, rs=None, rb=None):
    it = ip + idp; rs = rs if rs is not None else (Rs_m if worst else Rs_t); rb = rb if rb is not None else (Rb_m if worst else Rb_t)
    vm = sp * (1 - tl(it) - TC * DT) if worst else sp * (1 - LOAD * it / 8)
    return vm - it * rs / 1e3 - ip * rb / 1e3
def v_disp(ip, idp, sp=SP, worst=True):
    it = ip + idp; rs = Rs_m if worst else Rs_t; rd = Rd_m if worst else Rd_t
    vm = sp * (1 - tl(it) - TC * DT) if worst else sp * (1 - LOAD * it / 8)
    return vm - it * rs / 1e3 - idp * rd / 1e3
L = ["# Voltage-drop report — Pi Power Carrier RevB (combined board)", "",
     "Recomputed from scratch for the combined board: no J_OUT, no 4-wire harness, no interposer J1. Path: `RSDW40F-05 pins 4/5 -> F2 -> 5V_PI pour -> SSW-120-01-L-D -> Pi header pins 2,4 (+5 V) and 6,9,14,20 (GND)`; display branch `5V_PI node -> band -> J_DISP -> display lead`. Copper lengths/widths are measured on this layout (2 oz, 0.246 mOhm/square, x1.2 hot). Inputs: `datasheet_inputs.json` (source and status per value; user-relayed Samtec/Waveshare data marked there).", "",
     f"Targets: Pi pins >= {TARGET} V (preferred) with the {PI_MIN} V design floor, no-load <= {PI_MAX} V; Waveshare input {DISP_MIN}-{DISP_MAX} V (4.75 / 5.00 / 5.30, **0.8 A typical, maximum not published**; 1.0 A is a design scenario, not a manufacturer maximum). Calibrated unit: setpoint {SP:.3f} V (25 C, no load); line {LINE*100:.1f} %, load {LOAD*100:.1f} % over 0-8 A, temperature {TC*100:.2f} %/C x {DT:.0f} C = {TC*DT*100:.2f} %.", "",
     "## 1. Element drops", "", "| Element | carries | R typ (mOhm) | R worst (mOhm) | drop @5 A typ / worst (mV) |", "|---|---|---|---|---|"]
for lst, who, cur in ((shared, "Pi + display", 6), (branch, "Pi only", 5), (disp, "display only", 1)):
    for nme, a, b_ in lst: L.append(f"| {nme} | {who} | {a:.2f} | {b_:.2f} | {cur*a:.0f} / {cur*b_:.0f} (at {cur} A) |")
L += [f"| **Shared (module pins, track, F2)** | | **{Rs_t:.1f}** | **{Rs_m:.1f}** | |", f"| **Pi branch (pour, socket, header)** | | **{Rb_t:.1f}** | **{Rb_m:.1f}** | |", f"| **Total to the Pi pins** | | **{Rs_t+Rb_t:.1f}** | **{Rs_m+Rb_m:.1f}** | **{5*(Rs_t+Rb_t):.0f} / {5*(Rs_m+Rb_m):.0f}** |",
      f"| **Display branch (after the shared part)** | | **{Rd_t:.1f}** | **{Rd_m:.1f}** | |", "",
      f"**Versus RC2** (separate power board + interposer + 18 AWG harness): total to the Pi pins {rc2_s_t+rc2_b_t:.1f} / {rc2_s_m+rc2_b_m:.1f} mOhm typ/worst -> carrier {Rs_t+Rb_t:.1f} / {Rs_m+Rb_m:.1f} mOhm: **{(rc2_s_m+rc2_b_m)-(Rs_m+Rb_m):.1f} mOhm less in the worst case ({((rc2_s_m+rc2_b_m)-(Rs_m+Rb_m))*5:.0f} mV at 5 A)** (removed: J_OUT and J1 Micro-Fit contacts 4 x 10 mOhm, 4 x 18 AWG wires, interposer copper). The J_IN and the contact-resistance items that remain are the SSW socket and the Pi header pins (the only mating interface to the Pi).", "",
      "## 2. Cases (calibrated unit)", "", "| Case | Pi load (A) | Display (A) | Total through F2 (A) | Pi pins typ (V) | Pi pins worst (V) | margin to 4.85 V (worst) | margin to 4.75 V (worst) | J_DISP typ / worst (V) |", "|---|---|---|---|---|---|---|---|---|"]
for nm_, ip, idp in (("no load", 0, 0), ("1 A", 1, 0), ("3 A", 3, 0), ("5 A Pi", 5, 0), ("5 A Pi + 0.8 A display (typical)", 5, 0.8), ("5 A Pi + 1.0 A display (design scenario)", 5, 1.0)):
    w = v_pi(ip, idp); L.append(f"| {nm_} | {ip:g} | {idp:g} | {ip+idp:g} | {v_pi(ip, idp, worst=False):.3f} | {w:.3f} | {w-TARGET:+.3f} | {w-PI_MIN:+.3f} | {v_disp(ip, idp, worst=False):.3f} / {v_disp(ip, idp):.3f} |")
w = v_pi(5, 1.0); w2 = v_pi(5, 1.0, rs=rc2_s_m, rb=rc2_b_m)
nl = SP * (1 + th + TC * DT)
SPMIN = (TARGET + 5 * Rb_m / 1e3 + 6 * Rs_m / 1e3) / (1 - tl(6) - TC * DT); SPMAX = PI_MAX / (1 + th + TC * DT); SPMIN_t = (TARGET + 5 * Rb_t / 1e3 + 6 * Rs_t / 1e3) / (1 - tl(6) - TC * DT)
SPMIN_f = (PI_MIN + 5 * Rb_m / 1e3 + 6 * Rs_m / 1e3) / (1 - tl(6) - TC * DT)
L += ["", f"**No-load maximum:** {nl:.3f} V (setpoint x (1 + line + temperature)) -> {'below' if nl <= PI_MAX else 'ABOVE'} the {PI_MAX} V Pi maximum and below the Waveshare {DISP_MAX} V limit by {(DISP_MAX-nl)*1000:.0f} mV.",
      f"**Worst case, 5 A Pi + 1.0 A display:** {w:.3f} V at the Pi pins ({(w-TARGET)*1000:+.0f} mV vs the 4.85 V preferred target, {(w-PI_MIN)*1000:+.0f} mV vs the 4.75 V floor); RC2 with the same load and setpoint: {w2:.3f} V -> **carrier improves the worst case by {(w-w2)*1000:.0f} mV**.", "",
      f"## 3. Setpoint (trim) window, calibrated unit, 5 A Pi + 1.0 A display", "",
      f"| Window | lower (V) | upper (V) | width (mV) |", "|---|---|---|---|",
      f"| worst path, 4.85 V preferred target | {SPMIN:.3f} | {SPMAX:.3f} | {(SPMAX-SPMIN)*1000:.0f} |", f"| worst path, 4.75 V design floor | {SPMIN_f:.3f} | {SPMAX:.3f} | {(SPMAX-SPMIN_f)*1000:.0f} |", f"| typical path, 4.85 V target | {SPMIN_t:.3f} | {SPMAX:.3f} | {(SPMAX-SPMIN_t)*1000:.0f} |", "",
      f"RC2 worst-path window for comparison: {((TARGET + 5*rc2_b_m/1e3 + 6*rc2_s_m/1e3)/(1 - tl(6) - TC*DT)):.3f} V ... {SPMAX:.3f} V (CLOSED, negative width). Carrier: **{'open' if SPMAX > SPMIN else 'closed'}** against the preferred target in the stacked worst case.", "",
      f"Trim tolerance: a 1 % resistor on the trim-up pad (71.5 k nominal) moves the output by **{d1:.1f} mV**; one E96 step (71.5 k -> 73.2 k) is **{step:.0f} mV**. The calibration therefore resolves the setpoint to about ±{step/2:.0f} mV plus the {d1:.1f} mV tolerance: usable window for the worst-path target = {((SPMAX-SPMIN)*1000 - step - 2*d1):.0f} mV after quantisation and tolerance ({'workable' if (SPMAX-SPMIN)*1000 - step - 2*d1 > 0 else 'too narrow for the worst-path target; the typical window ({:.0f} mV) is workable and the 4.75 V floor window ({:.0f} mV) has ample room'.format((SPMAX-SPMIN_t)*1000, (SPMAX-SPMIN_f)*1000)}).", "",
      "## 4. Waveshare display input", "", "| Case | Display connector (V) | Range 4.75-5.30 V |", "|---|---|---|"]
for nm_, ip, idp in (("lowest: worst path, 5 A Pi + 1.0 A display", 5, 1.0), ("5 A Pi + 0.8 A display (typical current)", 5, 0.8)):
    v = v_disp(ip, idp); L.append(f"| {nm_} | {v:.3f} | {'inside' if DISP_MIN <= v <= DISP_MAX else 'OUTSIDE'} (+{(v-DISP_MIN)*1000:.0f} mV to the lower limit) |")
L += [f"| highest: no load, high line, +{DT:.0f} C | {nl:.3f} | {'inside' if nl <= DISP_MAX else 'ABOVE'} ({(DISP_MAX-nl)*1000:+.0f} mV to the upper limit) |", "",
      "## 5. Current per contact (SSW-120-01-L-D: 4.7 A per contact with two pins powered, Samtec basis)", "", "| Contact group | Pi current | per contact | rating | utilisation |", "|---|---|---|---|---|",
      f"| +5 V: Pi pins 2, 4 | 5.0 A | 2.50 A | 4.7 A | {2.5/4.7*100:.0f} % |", f"| GND: Pi pins 6, 9, 14, 20 | 5.0 A | 1.25 A | 4.7 A | {1.25/4.7*100:.0f} % |",
      "| J_DISP Micro-Fit contact | 1.0 A | 1.00 A | 8.5 A (owner-cited) | 12 % |", "| J_IN Micro-Fit contact (12 V, full module load ~3.9 A over 1 contact per rail) | 3.9 A | 3.9 A | 8.5 A (owner-cited) | 46 % |", "",
      f"Power dissipation at 5 A + 1 A (worst): F2 {6**2*F2*F2H/1e3*1e3:.0f} mW; SSW +5 V pin {2.5**2*SOCK:.0f} mW each; SSW GND pin {1.25**2*SOCK:.0f} mW each; J_DISP contact {1.0*J:.0f} mW; copper negligible. The module (~3.5 W) dominates. First article measures the real temperatures.", "",
      "## 6. What is estimated", "", "Copper squares are measured on this layout but the plated-through-hole barrels, solder joints and the Pi-side pin resistance are estimates (0.5 mOhm per module pin, 1 mOhm per Pi header contact). The SSW contact resistance (20 mOhm max) is a conservative limit — Samtec publishes no initial value for this code — and is **measured at first article**. The display current maximum is unpublished. All are bench items (`First_article_checklist.md`).", ""]
open(f"{D}/docs/Voltage_drop_report.md", "w").write("\n".join(L)); print("\n".join(L[18:44]))

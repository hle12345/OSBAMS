#!/usr/bin/env python3
"""RC2 5 V power-budget report: element-by-element drops and load scenarios from the same inputs as voltage_budget.py (datasheet_inputs.json). usage: power_budget_rc2.py <project dir>"""
import sys, os, json, math
D = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
I = json.load(open(f"{HERE}/datasheet_inputs.json")); V = lambda k: I[k]["value"]
RS = 0.246; PCB = (4.8 + 3.7 + 0.4) * RS; TRUNK = 13.4 * 1.2 * 0.15; IPCU = 2.0           # same constants as voltage_budget.py
F2 = V("f2_resistance_cold_mohm"); F2H = 1.3; J = V("j_out_contact_max_mohm"); JT = V("j_out_contact_typ_mohm"); SOCK = V("interposer_socket_contact_mohm")
ACC, LINE, LOAD, TC, DT = V("rsdw_tolerance_pct") / 100, V("rsdw_line_reg_pct") / 100, V("rsdw_load_reg_pct") / 100, V("rsdw_tempco_pct_per_c") / 100, V("delta_t_c")
TARGET, PI_MAX, PI_MIN = 4.85, 5.25, 4.75
# element table: mOhm for the +5 V rail and the return rail (series), typical / worst
shared = [("PCB copper (2 oz, +5 V and GND paths, from layout squares)", PCB, PCB),
          ("F2 output fuse 0451008.MRL (7.7 mOhm cold; 1.3x hot)", F2, F2 * F2H)]
branch = [("J_OUT Micro-Fit 430450400 (2 contacts/rail, 5.24 typ / 10 max mOhm per contact)", 2 * JT / 2, 2 * J / 2),
          ("Harness 16 AWG, 150 mm, 2 wires/rail (hot 1.2x)", 2 * TRUNK / 2 / 1.2, 2 * TRUNK / 2),
          ("Interposer J1 Micro-Fit (2 contacts/rail)", 2 * JT / 2, 2 * J / 2),
          ("Interposer copper (estimate 2 mOhm/rail)", 2 * IPCU, 2 * IPCU),
          (f"SSW-120 socket contacts ({SOCK:g} mOhm/contact max; 2 on +5 V, 4 on GND; typ = 0.6x)", SOCK * 0.6 / 2 + SOCK * 0.6 / 4, SOCK / 2 + SOCK / 4)]
el = shared + branch; Rs_t, Rs_m = sum(e[1] for e in shared), sum(e[2] for e in shared); Rb_t, Rb_m = sum(e[1] for e in branch), sum(e[2] for e in branch)
Rt, Rm = sum(e[1] for e in el), sum(e[2] for e in el)
tl = lambda i: LINE + LOAD * i / 8          # low corner of the module output (line + load) at total load i, calibrated unit (accuracy term removed by calibration)
th = LINE                                    # no-load high corner
SP = 5.185                                   # per-unit calibrated setpoint (see Trim_calibration_procedure.md)
def vpi(ip, idisp, sp=SP, worst=True, dt=DT):
    it = ip + idisp; rs = Rs_m if worst else Rs_t; rb = Rb_m if worst else Rb_t
    vm = sp * (1 - tl(it) - TC * dt) if worst else sp * (1 - LOAD * it / 8)
    return vm - it * rs / 1e3 - ip * rb / 1e3
L = ["# 5 V power-budget report (RC2)", "",
     "Topology (RC2): `RSDW40F-05 +VOUT -> PCB copper -> F2 -> [5V_PI node]`; from the node two branches: (a) **Pi branch**: J_OUT -> 16 AWG harness -> interposer J1 -> interposer copper -> SSW-120 socket -> Pi pins 2/4 (+5 V) and 6/9/14/20 (GND); (b) **display branch**: J_DISP (Micro-Fit 430450200) -> display lead. The display is fed directly from the board because the interposer covers the Pi header (see `Waveshare_integration.md`), so display current does not pass through the harness, the interposer or the socket. Both loads share only the PCB copper and F2.", "",
     f"Inputs: `datasheet_inputs.json` (source/status per value, see `Parts_and_sources.md`). Targets: **Pi pins >= {TARGET} V at the maximum intended Pi load, worst case**; **<= {PI_MAX} V at no load / high line**; Pi under-voltage region begins near {PI_MIN} V or lower (design floor {PI_MIN} V). Calibrated unit: module setpoint **{SP:.3f} V** (25 C, no load); line {LINE*100:.1f} %, load {LOAD*100:.1f} % over 0-8 A, temperature {TC*100:.2f} %/C x {DT:.0f} C = {TC*DT*100:.2f} %.", "",
     "## 1. Element drops", "",
     "| Element | carries | R typ (mOhm) | R worst (mOhm) | drop @3 A typ / worst (mV) | drop @5 A typ / worst (mV) |", "|---|---|---|---|---|---|"]
for n, a_, b_ in shared: L.append(f"| {n} | Pi + display | {a_:.1f} | {b_:.1f} | {3*a_:.0f} / {3*b_:.0f} | {5*a_:.0f} / {5*b_:.0f} |")
for n, a_, b_ in branch: L.append(f"| {n} | Pi only | {a_:.1f} | {b_:.1f} | {3*a_:.0f} / {3*b_:.0f} | {5*a_:.0f} / {5*b_:.0f} |")
L += [f"| **Shared (PCB + fuse)** | | **{Rs_t:.1f}** | **{Rs_m:.1f}** | **{3*Rs_t:.0f} / {3*Rs_m:.0f}** | **{5*Rs_t:.0f} / {5*Rs_m:.0f}** |",
      f"| **Pi branch (connectors, harness, interposer, socket)** | | **{Rb_t:.1f}** | **{Rb_m:.1f}** | **{3*Rb_t:.0f} / {3*Rb_m:.0f}** | **{5*Rb_t:.0f} / {5*Rb_m:.0f}** |",
      f"| **Total to the Pi pins** | | **{Rs_t+Rb_t:.1f}** | **{Rs_m+Rb_m:.1f}** | **{3*(Rs_t+Rb_t):.0f} / {3*(Rs_m+Rb_m):.0f}** | **{5*(Rs_t+Rb_t):.0f} / {5*(Rs_m+Rb_m):.0f}** |", "",
      "Fuse drop (F2) and connector/contact drop (J_OUT + J1 + SSW socket) are separate rows. F1 (input side, 0407008.WR, 9 mOhm / 12.1 mOhm hot) is upstream of the module (under-voltage lock-out 8 V, bus 12 V) and does not enter the 5 V budget. The display branch (J_DISP contact + lead) depends on the display connector/lead, which is chosen with the display data (`Waveshare_integration.md`): allow <= 50 mV for it.", "",
      "## 2. Voltage at the Pi pins, by scenario (calibrated unit)", "",
      "| Pi load (A) | Display load (A) | Total through F2 (A) | Pi pins typical (V) | Pi pins worst path (V) | Margin to 4.85 V (worst) | Display terminal J_DISP worst (V, before its lead) |", "|---|---|---|---|---|---|---|"]
for ip, idp in ((0, 0), (1, 0), (3, 0), (5, 0), (3, 1), (4, 1), (5, 1)):
    it = ip + idp; vd = SP * (1 - tl(it) - TC * DT) - it * Rs_m / 1e3 - idp * 0.010 * 0
    L.append(f"| {ip:g} | {idp:g} | {it:g} | {vpi(ip, idp, worst=False):.3f} | {vpi(ip, idp):.3f} | {vpi(ip, idp)-TARGET:+.3f} | {vd:.3f} |")
SPMIN = max((TARGET + 5 * (Rb_m) / 1e3 + 5 * Rs_m / 1e3) / (1 - tl(5) - TC * DT), (TARGET + 5 * Rb_m / 1e3 + 6 * Rs_m / 1e3) / (1 - tl(6) - TC * DT)); SPMAX = PI_MAX / (1 + th + TC * DT)
SPMIN_t = (TARGET + 5 * Rb_t / 1e3 + 6 * Rs_t / 1e3) / (1 - tl(6) - TC * DT)
wmin = vpi(5, 1)
L += ["", f"Lowest voltage anywhere in the table (every resistance at its maximum, F2 hot, +{DT:.0f} C, 5 A Pi + 1 A display): **{wmin:.3f} V**: {'meets' if wmin >= TARGET else 'MISSES'} the {TARGET} V owner target by {(wmin-TARGET)*1000:+.0f} mV and clears the {PI_MIN} V design floor by {(wmin-PI_MIN)*1000:+.0f} mV. The {TARGET} V target is the conservative owner target; the {PI_MIN} V floor is the under-voltage design limit.", "",
     "The 5 A + 1 A row is the maximum intended load (Pi 5 at its 5 A supply rating plus ~1 A display; owner note in `docs/rev2/pcb/PI_POWER_ARCHITECTURE.md`: Pi 5 5 V / up to 5 A, display ~0.8-1 A - the actual Waveshare model rating must still be confirmed).", "",
      f"**Setpoint window (calibrated unit, worst path, hot F2, 5 A Pi + 1 A display):** the module output measured at 25 C, no load, must lie in **{SPMIN:.3f} V ... {SPMAX:.3f} V** (lower bound: 4.85 V at the Pi pins; upper bound: 5.25 V at no load / high line / +{DT:.0f} C): width {(SPMAX-SPMIN)*1000:.0f} mV {'(CLOSED: no setpoint satisfies both limits with every resistance at its maximum)' if SPMAX <= SPMIN else ('(effectively closed: narrower than one E96 trim step, ~20 mV)' if (SPMAX-SPMIN) < 0.02 else '(open)')}. With **typical** resistances the window is {SPMIN_t:.3f} V ... {SPMAX:.3f} V ({(SPMAX-SPMIN_t)*1000:.0f} mV wide). The worst-path window stacks every contact at its maximum with F2 hot at once; it shows the limit, not the expected case. **Calibration is therefore done on the assembled system** (measure the real drop, then choose the trim resistor; `Trim_calibration_procedure.md`, `First_article_checklist.md`); worst-path closure is checked by measuring the socket and connector contact resistances on the first articles.", "",
      f"No-load worst case: **{SP*(1+th+TC*DT):.3f} V** (setpoint {SP:.3f} V x (1 + line {LINE*100:.1f} % + temperature {TC*DT*100:.2f} %)) -> {'below' if SP*(1+th+TC*DT) <= PI_MAX else 'ABOVE'} the {PI_MAX} V Pi maximum.", "",
      "## 3. Scenarios and acceptance (measured at first article)", "",
      "The Pi 5 and display currents are not taken from datasheets in this build; they are measured. The hardware limit is **5.0 A into the Pi pins** (2 x 5 V pins, J_OUT/J1 contacts, harness) and **6.0 A total through F2 / the module (8 A)**.", "",
      "| Scenario | What is loaded | Required measurement | Pass if |", "|---|---|---|---|",
      "| Pi only, idle / boot | Pi 5 alone | I_5V at pins, V at pins | V >= 4.85 V at the measured current |",
      "| Pi only, stress | CPU+GPU+RAM stress, Active Cooler if fitted | I_5V peak/continuous, V at pins, throttling flag | V >= 4.85 V; no under-voltage / throttle flag |",
      "| Pi + Waveshare display | stress + display at full brightness + touch | I_Pi, I_display, V at Pi pins and at the display input | I_Pi <= 5.0 A, total <= 6.0 A, V_Pi >= 4.85 V, display input >= its minimum |",
      "| Pi + display + USB peripherals | the above + intended USB load | I_Pi (incl. USB) | I_Pi <= 5.0 A; otherwise reduce the USB load - the Pi branch is not rated beyond 5 A |", "",
      f"Contact loading at 5 A Pi load: {5/2:.1f} A per Pi 5 V pin (2 pins), {5/4:.2f} A per GND pin (4 pins); Samtec SSW 4.7 A per pin with two pins powered (53 % on +5 V). Micro-Fit 8.5 A per contact (owner-cited): J_OUT and J1 carry 2.5 A per +5 V contact (29 %); J_DISP carries 1 A.", "",
      "## 4. Sensitivities (Pi pins at 5 A Pi + 1 A display, worst path)", "", "| Case | Pi pins (V) |", "|---|---|"]
L += [f"| Baseline | {vpi(5, 1):.3f} |", f"| Only 2 GND socket pins used (no pins 14/20) | {vpi(5, 1) - 5*(SOCK/2 - SOCK/4)/1e3:.3f} |", f"| Socket contact 25 mOhm instead of {SOCK:g} | {vpi(5, 1) - 5*5*0.75/1e3:.3f} |",
      f"| Module 5 C hotter (dT {DT+5:.0f} C) | {vpi(5, 1, dt=DT+5):.3f} |", f"| Uncalibrated unit (accuracy +-1 % included, same setpoint) | {vpi(5, 1) - SP*ACC:.3f} |", "",
      "The uncalibrated row shows why **per-unit trim calibration is required**: without it the 5 A worst case falls below 4.85 V and no fixed setpoint can satisfy both the 4.85 V and 5.25 V limits.", ""]
open(f"{D}/docs/Power_budget_report.md", "w").write("\n".join(L)); print("\n".join(L[16:44]))

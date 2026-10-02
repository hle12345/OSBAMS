#!/usr/bin/env python3
"""Independent audit of the OSBAMS Rev.2 pack-sense protection (read-only; nothing here is committed to either branch).
Inputs are manufacturer values from the uploaded datasheets: Bourns 1.5SMBJ (VBR, VC@IPP), TI INA228 (abs max), Panasonic ERJP08."""
import math
# ---- TVS clamp model (piecewise-linear through the datasheet rating points; ENGINEERING ESTIMATE, not a datasheet curve)
TVS = {"1.5SMBJ48A": dict(vbr_max=58.9, vbr_min=53.3, p1=(19.4, 77.4), p2=(97.0, 100.6), vrwm=48.0),
       "1.5SMBJ45A": dict(vbr_max=55.3, vbr_min=50.0, p1=(20.6, 72.7), p2=(103.0, 94.5), vrwm=45.0)}
def vclamp(name, i, dT=0.0):
    t = TVS[name]; (i1, v1), (i2, v2) = t["p1"], t["p2"]
    v = t["vbr_max"] + (v1 - t["vbr_max"]) / i1 * i if i <= i1 else v1 + (v2 - v1) / (i2 - i1) * (i - i1)
    return v + 0.001 * t["vbr_max"] * dT      # datasheet: dVBR = 0.1 % x VBR x dT
INA_ABS, INA_DIFF, INA_IMAX = 85.0, 40.0, 5e-3
out = []
P = out.append
P("# Pack-sense protection audit (independent recomputation)\n")
P("INA228 limits (TI datasheet, verified): VBUS and IN+/IN- common-mode -0.3..85 V; differential (IN+ - IN-) +-40 V; input current into any pin 5 mA; HBM +-2 kV; ZVBUS 0.8-1.2 Mohm; IB 0.1 nA typ / 2.5 nA max; RDIFF 92 kohm.\n")
P("## 1. Credible events (as defined in the brief)\n")
P("| Event | model | node clamp V (1.5SMBJ48A) | margin to 85 V | node V (1.5SMBJ45A) | margin |\n|---|---|---|---|---|---|")
rows = []
for name, I, lab in [("interrupt 18.5 A (firmware trip bound), Rs=0", 18.5, "interruption"), ("interrupt 20 A", 20.0, "interruption")]:
    a, b = vclamp("1.5SMBJ48A", I), vclamp("1.5SMBJ45A", I); P(f"| {name} | I_TVS = {I} A | {a:.1f} | {85-a:+.1f} | {b:.1f} | {85-b:+.1f} |")
def esd(vgen, rgun=330.0, rs=47.0, name="1.5SMBJ48A", dT=0.0):
    i = 0.0
    for _ in range(50): i = max(0.0, (vgen - vclamp(name, i, dT)) / (rgun + rs))     # iterate: TVS current limited by the gun + series R upstream of the clamp
    return i, vclamp(name, i, dT)
for lab, v in (("ESD 8 kV contact (IEC 61000-4-2)", 8000.0), ("ESD 15 kV air (IEC 61000-4-2)", 15000.0)):
    ia, va = esd(v); ib, vb = esd(v, name="1.5SMBJ45A")
    P(f"| {lab}, 330 ohm gun + 47 ohm upstream | I_TVS = {ia:.0f} A (48A) / {ib:.0f} A (45A) | {va:.1f} | {85-va:+.1f} | {vb:.1f} | {85-vb:+.1f} |")
for lab, v in (("ESD 15 kV air, +60 K hot (VBR tempco)", 15000.0),):
    ia, va = esd(v, dT=60); ib, vb = esd(v, name="1.5SMBJ45A", dT=60)
    P(f"| {lab} | {ia:.0f} A / {ib:.0f} A | {va:.1f} | {85-va:+.1f} | {vb:.1f} | {85-vb:+.1f} |")
P("\nESD note: these are *DC-level clamp* values. The first-nanosecond spike (L di/dt of the TVS leads and the trace to the INA pin: 5 nH x 30 A / 1 ns = 150 V) is NOT in the clamp curve and cannot be resolved by a datasheet model; only a TLP/IEC-gun test at the connector can demonstrate the INA228 pin stays below 85 V. The 47 ohm upstream resistor barely helps against ESD (330 ohm gun impedance dominates).\n")
# ---- hot-plug RLC with TVS (explicit Euler)
def hotplug(L, Ctvs, Rs, Rpin, Cpin, Rsrc=0.3, V0=44.0, name="1.5SMBJ48A"):
    dt = 5e-11; il = 0.0; vc = 0.0; vp = 0.0; vmax = 0.0; ipk = 0.0; vpmax = 0.0; e_rs = 0.0
    for _ in range(int(40e-6 / dt)):
        itvs = max(0.0, (vc - TVS[name]["vbr_max"]) / 0.95) if vc > TVS[name]["vbr_min"] else 0.0   # conduction beyond VBR, ~0.95 ohm slope of the 10/1000 point
        ipin = (vc - vp) / Rpin
        il += dt * (V0 - (Rsrc + Rs) * il - vc) / L
        vc += dt * (il - itvs - ipin) / Ctvs
        vp += dt * ipin / Cpin
        vmax = max(vmax, vc); vpmax = max(vpmax, vp); ipk = max(ipk, itvs); e_rs += il * il * Rs * dt
    return vmax, vpmax, ipk, e_rs
for title, Rs, Rpin, Cpin, lab in (("VBUS path: 47 ohm upstream, 10 ohm to the pin, 100 nF at VBUS", 47.0, 10.0, 100e-9, "R41"),
                                   ("Kelvin path: 10 ohm upstream, 10 ohm to the pin, ~1 nF pin/filter capacitance (no 100 nF)", 10.0, 10.0, 1e-9, "R42/R43")):
    P(f"## 2. Hot-plug onto a live 44 V pack - {title}\n")
    P("| L (uH) | C_tvs (nF) | TVS node peak V | INA pin peak V | TVS peak A | energy in upstream R (uJ) | margin to 85 V (node) |\n|---|---|---|---|---|---|---|")
    worst = 0
    for L in (0.5e-6, 2e-6, 5e-6, 10e-6):
        for C in (0.3e-9, 1e-9, 3e-9):
            v, vp, i, e = hotplug(L, C, Rs, Rpin, Cpin); worst = max(worst, v)
            P(f"| {L*1e6:g} | {C*1e9:g} | {v:.1f} | {vp:.1f} | {i:.2f} | {e*1e6:.0f} | {85-v:+.1f} |")
    P(f"\nWorst {lab} combination: node {worst:.1f} V (limit 85 V).\n")
    if lab == "R42/R43": worst_k = worst
worst = worst_k
# ---- differential stress
P("## 3. INA228 IN+/IN- differential stress (limit +-40 V)\n")
P("One-sided transient: IN+ driven to the clamp level while IN- is at the pack voltage (both leads connected) or near 0 V (IN- lead not yet connected / broken, so IN- is held only by the 92 kohm differential impedance).\n")
P("| clamp level on IN+ | IN- at 44 V | IN- at ~0 V |\n|---|---|---|")
for lab, v in (("interrupt 18.5 A bound (76.5 V)", 76.5), ("ESD 8 kV contact (~77.9 V)", 77.9), ("ESD 15 kV air (~83.4 V)", 83.4), ("hot-plug worst (model)", worst)):
    P(f"| {lab} | {v-44:+.1f} V ({'OK' if abs(v-44)<=INA_DIFF else 'EXCEEDS'}) | {v:+.1f} V ({'OK' if abs(v)<=INA_DIFF else 'EXCEEDS'}) |")
P("\nBoth leads connected and live: a one-sided event stays under 40 V with 1-6 V margin at the ESD levels. If an IN- lead is open or connects later, a one-sided transient exceeds the +-40 V absolute maximum for as long as the 92 kohm / pin-capacitance time constant holds IN- down. A symmetric (common-mode) transient does not stress the differential limit. -> add a differential clamp across IN+/IN- on the INA side of R11/R12 (see recommendations).\n")
# ---- leakage / gain errors
P("## 4. Leakage and gain errors (steady state)\n")
P("| item | value |\n|---|---|")
P(f"| VBUS gain error from 57 ohm in series with ZVBUS 0.8-1.2 Mohm | {57/1.2e6*100:.4f} - {57/0.8e6*100:.4f} % (fixed ratio; calibration against the reference meter removes it, its Z spread {(57/0.8e6-57/1.2e6)*100:.4f} % does not) |")
P(f"| TVS leakage (1 uA max at VRWM, 25 C) x 47 ohm on PACK_INA | {1e-6*47*1e6:.0f} uV (1.1 ppm of 44 V) |")
P(f"| TVS leakage (1 uA max) x (10+10 ohm) on each Kelvin line | {1e-6*20*1e6:.0f} uV worst-case line-to-line mismatch = {1e-6*20/0.0025*1e3:.0f} mA shunt-current equivalent (shunt 50 mV/20 A = 2.5 mohm), 0.04 % of 20 A |")
P(f"| INA228 bias current (2.5 nA max) x 20 ohm | {2.5e-9*20*1e9:.0f} nV (negligible) |")
P("\nLeakage rises with temperature and with proximity to VRWM; the Bourns file gives only 1 uA max at VRWM/25 C (no temperature curve), so the real figure is a first-article measurement (INA228 shunt reading at 0 A, cold and warm).\n")
P("## 5. Panasonic ERJP08 (1206) - from the uploaded datasheet (28-Mar-26)\n")
P("0.66 W @ 70 C, limiting element voltage 125 V, max overload voltage 500 V, TCR +-200 ppm/K for R>=10 ohm (R<10: -100..+600), AEC-Q200. 47 ohm: RCWV = min(sqrt(0.66 x 47), 125) = 5.6 V; 10 ohm: 2.6 V. Overload test = 2.5 x RCWV for 5 s (about 4.1 W / 20 J into 47 ohm). Orderable pattern ERJP08 F 47R0 V = 1 % (F, four-digit code), embossed 4 mm carrier, 5000 pcs; ERJP08F10R0V is at the lower limit of the +-1 % range (10 ohm to 1 Mohm). **The datasheet contains no pulse-energy / pulse-limiting curve** (only the ESD test: 3 kV / 150 pF, 0.68 mJ, resistance change plotted), so the resistor pulse rating stays OPEN even though the credible pulses are only 0.3-0.4 mJ (hot-plug/interruption) - request the Panasonic pulse-limiting-voltage / surge curve or test the part.\n")
print("\n".join(out)); open(__file__.replace("protection_audit.py", "protection_audit_results.md"), "w").write("\n".join(out) + "\n")

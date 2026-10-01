#!/usr/bin/env python3
"""RC1.3 pack-sense protection calculations (INA228 differential clamp + connector-entry fast ESD stage).
Verified inputs : INA228 limits, Bourns 1.5SMBJ48A (VBR, VC@IPP), Panasonic ERJP08 (no pulse curve).
Assumed inputs  : 1.5SMBJ12CA (datasheet NOT supplied; every number from it is an engineering estimate flagged ASSUMED). The connector-entry diode is the same
                  verified 1.5SMBJ48A; the other Rdyn rows are sensitivity cases for alternative parts."""
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
out = []; P = out.append
INA_ABS, INA_DIFF = 85.0, 40.0
# ---- clamp models: V = VBR_max + Rdyn*I up to the rating point, then linear to the second point
def v48(i, dT=0.0):                       # Bourns 1.5SMBJ48A (verified points: VBR max 58.9; 77.4 V @ 19.4 A; 100.6 V @ 97 A)
    v = 58.9 + (77.4 - 58.9) / 19.4 * i if i <= 19.4 else 77.4 + (100.6 - 77.4) / (97 - 19.4) * (i - 19.4)
    return v + 0.001 * 58.9 * dT
def v12ca(i, dT=0.0):                     # 1.5SMBJ12CA ASSUMED: VBR max 14.7 V, VC 19.9 V @ 75.4 A (typical 1.5 kW series figures)
    return 14.7 + (19.9 - 14.7) / 75.4 * i + 0.001 * 14.7 * dT
def make_esd(rdyn):                       # connector-entry ESD diode ASSUMED: VBR max 58.9 V (48 V class), dynamic resistance rdyn
    return lambda i, dT=0.0: 58.9 + rdyn * i + 0.001 * 58.9 * dT
ESD_CANDS = (("SMF48A-class 200 W SOD-123FL, Rdyn 7.1 ohm (sensitivity case; derived from 77.4 V @ 2.6 A, NOT a datasheet curve)", make_esd(7.1)),
             ("SMBJ48A-class, Rdyn 2.4 ohm", make_esd(2.4)),
             ("**1.5SMBJ48A, Rdyn 0.95 ohm (verified curve) = D15-D19 as built**", make_esd(0.95)),
             ("hypothetical low-Rdyn 0.3 ohm", make_esd(0.3)))
RG = 330.0
def solve(vg, esd_fn, rseries, dT=0.0):
    """node voltage Vn at the connector: gun (Vg via 330 ohm) feeds [ESD diode] || [rseries + D(48A)]. returns dict"""
    lo, hi = 0.0, 3000.0
    for _ in range(200):
        vn = (lo + hi) / 2
        itot = max(0.0, (vg - vn) / RG)
        ie = max(0.0, (vn - 58.9 - 0.001 * 58.9 * dT) / (esd_fn(1.0, dT) - esd_fn(0.0, dT))) if esd_fn else 0.0
        ir = 0.0
        for _ in range(60): ir = max(0.0, (vn - v48(ir, dT)) / rseries)
        if ie + ir > itot: hi = vn
        else: lo = vn
    vn = (lo + hi) / 2; itot = (vg - vn) / RG
    ie = max(0.0, (vn - 58.9 - 0.001 * 58.9 * dT) / (esd_fn(1.0, dT) - esd_fn(0.0, dT))) if esd_fn else 0.0
    ir = max(0.0, itot - ie); vd = v48(ir, dT)
    tau = (RG + (vn / max(itot, 1e-9)) * 0 + 5.0) * 150e-12
    er = ir * ir * rseries * tau / 2                  # exponential decay, tau ~ (330+few) ohm x 150 pF
    return dict(vn=vn, itot=itot, ie=ie, ir=ir, vr=ir * rseries, vd=vd, er=er)

P("# RC1.3 protection calculations (INA228 differential clamp + connector-entry ESD stage)\n")
P("Status of inputs: **verified** = INA228 limits, 1.5SMBJ48A, ERJP08 (uploaded datasheets). **ASSUMED** = 1.5SMBJ12CA only (no datasheet supplied; replace with datasheet values before release). The connector-entry diodes D15-D19 are the verified 1.5SMBJ48A; the other connector-entry rows below are sensitivity cases only. Architecture: connector -> fast ESD diode -> pulse-rated series resistor (R41/R42/R43) -> surge TVS (1.5SMBJ48A) -> filter (R11/R12/R13 + C26/C28) -> INA228.\n")
P("ESD target: IEC 61000-4-2 +-8 kV contact / +-15 kV air - a **design / first-article target, not a certification claim**. Generator model: 330 ohm / 150 pF discharge, source current Vg/330 into the clamp network (8 kV: 24 A; 15 kV: 45 A). DC-level clamp analysis only: the first-nanosecond L di/dt spike is not resolvable by a datasheet model (needs TLP / gun test).\n")

for title, rs, lab in (("VBUS lead (J6.1): R41 = 47 ohm, then D7 1.5SMBJ48A, then R13 10 ohm to the INA228 VBUS pin", 47.0, "R41"),
                       ("Kelvin line (J5.1 / J5.2): R42, R43 = 10 ohm, then D5/D6 1.5SMBJ48A, then R11/R12 10 ohm to the pin", 10.0, "R42/R43")):
    P(f"## 1. ESD on the {title}\n")
    P("| connector-entry device | event | connector node V | ESD diode A | series R A | V across series R | peak P in R (W) | R pulse energy (uJ) | D5/D7 clamp V | margin to 85 V | VBUS-pin V (pin 5 mA bound) |\n|---|---|---|---|---|---|---|---|---|---|---|")
    cases = [("none (RC1.2: series R first)", None)] + [(n, f) for n, f in ESD_CANDS]
    for n, f in cases:
        for ev, vg, dT in (("8 kV contact", 8000.0, 0), ("15 kV air", 15000.0, 0), ("15 kV air, +60 K", 15000.0, 60)):
            r = solve(vg, f, rs, dT)
            P(f"| {n} | {ev} | {r['vn']:.0f} | {r['ie']:.1f} | {r['ir']:.2f} | {r['vr']:.0f} V | {r['vr']*r['ir']:.0f} | {r['er']*1e6:.1f} | {r['vd']:.1f} | {85-r['vd']:+.1f} | <= {r['vd']:.1f} (pin current = (V_D - pin clamp)/10 ohm) |")
    P("")
P("Reading the table: without a connector-entry device (RC1.2) the series resistor carries almost the whole gun current (21-44 A) and drops 0.2-1.9 kV across a 1206 anti-surge part whose datasheet gives only 125 V limiting-element voltage / 500 V overload voltage and **no pulse curve**, and the RC1.2 pin clamp reached 83-87 V (15 kV air: 85 V limit exceeded at +60 K): the RC1.2 ESD behaviour of R41/R42/R43 and the INA228 VBUS/CM margin was undemonstrated. With a connector-entry 1.5SMBJ48A (as built, Rdyn ~0.95 ohm) the connector node is held at ~80-104 V, the series resistor sees 19-41 V (Kelvin 10 ohm) / 22-41 V (VBUS 47 ohm) instead of 0.2-1.9 kV, the resistor pulse energy drops from 136-2440 uJ to 0.3-3.3 uJ, and the surge clamp D5/D7 stays near 60-66 V (margin >= 19 V to 85 V). The result depends strongly on the entry device's dynamic resistance: a 200 W SOD-123FL 48 V part (~7 ohm) would leave 93-269 V across the resistor and 76-79 V at the Kelvin pin (margin 6-9 V), which is why the SMF48A candidate used in the first RC1.3 draft was replaced. No purpose-built >= 48 V ESD diode with a verified Rdyn <= 1 ohm was identified in the supplied files. DC-level clamp analysis only; the first-nanosecond spike and the ERJP08 pulse survival remain first-article test items.\n")

# ---- differential stress with the clamp
P("## 2. INA228 IN+/IN- differential stress with D20 (1.5SMBJ12CA, ASSUMED) across SHUNT_INP_RAW / SHUNT_INN_RAW\n")
P("D20 sits on the connector side of R11/R12 so the INA228 pins only ever see the clamp level minus the pin-current drop (<= 5 mA x 10 ohm = 50 mV).\n")
P("| one-sided event on IN+ | IN+_RAW before D20 (D5 clamp, V) | IN- condition | I through D20 (A) | differential at pins (V) | limit | margin |\n|---|---|---|---|---|---|---|")
for lab, vin in (("ESD 8 kV contact", 77.9), ("ESD 15 kV air", 83.4), ("hot-plug / interruption (D5 at 20 A)", v48(20.0)), ("hot-plug node (RLC model, 59.5 V)", 59.5)):
    for cond, vm, rloop in (("IN- lead connected, pack at 44 V", 44.0, 10.0), ("IN- lead connected, pack at 0 V", 0.0, 10.0), ("IN- lead open (floating)", None, None)):
        if vm is None:
            i = 0.0                                              # only INA228 92 kohm / node capacitance: node charges until D20 conducts
            vd = v12ca(0.05)                                     # clamp conducts at mA level into the 1 nF node capacitance
            P(f"| {lab} | {vin:.1f} | {cond} | ~0.01-0.05 (node charge) | {vd:.1f} | 40 | {INA_DIFF-vd:+.1f} |")
        else:
            i = 0.0
            for _ in range(50): i = max(0.0, (vin - vm - v12ca(i)) / (rloop + 10.0))   # R43 10 ohm + cable on the IN- side, R42 absorbed in D5 node level
            P(f"| {lab} | {vin:.1f} | {cond} | {i:.1f} | {v12ca(i):.1f} | 40 | {INA_DIFF-v12ca(i):+.1f} |")
P("\nWithout D20 (RC1.2) the same one-sided events put 77.9 / 83.4 V (IN- near 0 V or open) or 33.9 / 39.4 V (IN- at 44 V) across the 40 V differential limit: the open-lead and 0 V cases exceeded the absolute maximum by 38-43 V. With D20 the differential is held to ~15-17 V (hot: +6 % of VBR at +60 K = ~+1 V) in every case, leaving > 22 V margin. Common-mode level (pin to GND) is unchanged: 53-84 V, within 85 V - that margin is unchanged from the audit and still depends on the 1.5SMBJ48A + R-chain for the first-nanosecond spike.\n")

# ---- leakage / capacitance / recovery
P("## 3. Normal-operation error, leakage, capacitance, recovery (0-50 mV differential, common mode up to 44 V)\n")
Ish = 50e-3
P("| item | assumption | result |\n|---|---|---|")
for nm, ileak in (("flat worst-case bound: 5 uA at VRWM 12 V applied at all voltages", 5e-6), ("ohmic scaling 5 uA/12 V x 0.05 V (leakage at 50 mV differential, 25 C)", 5e-6 / 12 * 0.05), ("ohmic scaling x 10 for +85 C", 5e-6 / 12 * 0.05 * 10)):
    rloop = 10 + 10 + 10 + 10      # R42 + R43 + (R11 + R12 between filter and pin are outside the clamp) - clamp drawn through R42/R43 + cable
    dv = ileak * (10 + 10)        # leakage flows through R42 + R43 (clamp is downstream of them)
    P(f"| D20 leakage current: {nm} | I = {ileak*1e9:.3g} nA | differential error = I x (R42+R43) = {dv*1e6:.3g} uV = {dv/Ish*1e6:.0f} ppm of 50 mV (and unchanged scale: removed by zero-current offset trim) |")
P("| D20 leakage at a CM of 44 V | the clamp is differential: both terminals at the same potential -> no voltage across it | 0 (no common-mode leakage) |")
dC = 2e-9
tau_rc12 = (10 + 10 + 10 + 10) * 100e-9           # R42+R43+R11+R12 = 40 ohm x C26
tau_rc13 = (10 + 10 + 10 + 10) * (100e-9 + dC)
P(f"| D20 capacitance (ASSUMED 2 nF, 0 V bias; falls with bias) | in parallel with C26 100 nF | differential filter tau {tau_rc12*1e6:.2f} -> {tau_rc13*1e6:.2f} us (+{(tau_rc13/tau_rc12-1)*100:.0f} %), fc {1/(2*math.pi*tau_rc12)/1e3:.1f} -> {1/(2*math.pi*tau_rc13)/1e3:.1f} kHz |")
P(f"| D20 recovery after a clamp event | clamp not conducting below VBR (14.7 V); recovery = filter settling | to 0.01 % of 50 mV: 9.2 tau = {9.2*tau_rc13*1e6:.0f} us (INA228 conversion time >= 50 us; discard the first conversion after an event) |")
P("| connector-entry diodes D15/D16 on the Kelvin lines (1.5SMBJ48A, leakage <= 1 uA at VRWM 48 V / 25 C per the supplied datasheet, CM up to 44 V) | they sit BEFORE R42/R43, so their leakage flows through the cable / shunt Kelvin lead (assume <= 1 ohm), not through the 10 ohm resistors | mismatch error <= 1 uA x 1 ohm = 1 uV = 20 ppm of 50 mV; with the 1.5SMBJ48A footprint (also <= 1 uA) the same bound |")
P("| D5/D6 (existing) leakage x R42/R43 | <= 1 uA x 10 ohm | 10 uV line-to-line mismatch worst case (0.02 % of 50 mV) - unchanged from RC1.2 and now measurable by the zero-current offset test |")
P("| D17/D19 (PACK_INA_CON, RELAY_OUT) leakage | before R41 / R26 and fed by the stiff pack node | no divider/gain effect; VBUS gain error stays 57 ohm / ZVBUS = 0.005-0.007 % |")
P("| D18 (PACK_ADC) leakage | diode before the 150 kohm divider R17+R18; source = pack lead resistance (<= 1 ohm) | <= 1 uV; no effect on the 16:1 ADC divider ratio |")
P("| connector-entry diode capacitance (1.5SMBJ48A: datasheet value not extracted; assume <= 500 pF) | on 10 ohm / 47 ohm series: corner >> 10 MHz | no effect on the 40 kHz differential filter (10 ohm x 500 pF = 5 ns); slightly slows the fast hot-plug edge (damping, beneficial) |\n")
P("## 4. ERJP08 (Panasonic) - unchanged status\n")
P("Candidate Panasonic ERJ-P08F47R0V / F10R0V: 0.66 W @ 70 C, limiting-element voltage 125 V, overload voltage 500 V, no pulse-energy / pulse-limiting curve in the supplied datasheet. **No verified pulse-energy limit is claimed.** With the connector-entry stage the series resistor sees (V_node - V_D) instead of the full generator: the table above gives the new stress; whether it survives is a first-article (pulse-test) item.\n")
open(os.path.join(HERE, "protection_rc13_results.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out))

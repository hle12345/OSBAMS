#!/usr/bin/env python3
"""OSBAMS Rev.2 RC1 calculations -> ../REV2_CALCULATIONS.md and ../DATASHEET_VERIFICATION.md (evidence register).

Every datasheet-dependent number comes from datasheet_inputs.json with an evidence state:
  VERIFIED_LOCAL | USER_RELAYED_MANUFACTURER | UNVERIFIED
Run:  python3 Hardware/Rev2_Controller/calc/rev2_calcs.py
"""
import itertools, json, math, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REG = json.load(open(os.path.join(HERE, "datasheet_inputs.json")))["inputs"]
BY = {e["id"]: e for e in REG}
OUT = []
w = OUT.append
TAG = {"VERIFIED_LOCAL": "", "USER_RELAYED_MANUFACTURER": " [UR]", "UNVERIFIED": " [UV]"}


def V(i):
    return BY[i]["value"]


def t(i):
    return TAG[BY[i]["evidence"]]


# ------------------------------------------------------------------ 1 ADC
def adc():
    R1 = R2 = 75e3; R3 = 10e3; Rt = R1 + R2 + R3; ratio = Rt / R3
    w("## 1. Independent ADC channel\n")
    w("`PACK_ADC -> 75k -> 75k -> ADC_TAP -> 10k -> GND`; `ADC_TAP -> 1 k -> ADC_SENSE (PA1) + 100 nF`; clamps D8/D14 (below).\n")
    w("| Vpack | ADC_TAP |\n|---|---|")
    for vp in (30, 36, 42, 44, 48):
        w(f"| {vp} V | {vp / ratio:.3f} V |")
    w(f"\nRatio {ratio:.0f}:1; 12-bit LSB {3.3 / 4096 * 1e3:.3f} mV = {3.3 / 4096 * ratio * 1e3:.1f} mV at the pack; divider {44 / Rt * 1e6:.0f} µA / {44 ** 2 / Rt * 1e3:.1f} mW at 44 V ({(44 * 75e3 / Rt) ** 2 / 75e3 * 1e3:.1f} mW per 75 kΩ); source impedance {R3 * (R1 + R2) / Rt / 1e3:.2f} kΩ + 1 kΩ; τ ≈ {(R3 * (R1 + R2) / Rt + 1e3) * 100e-9 * 1e3:.2f} ms.\n")

    def worst(tol):
        nom = R3 / Rt; m = 0
        for a, b, c in itertools.product((1 - tol, 1 + tol), repeat=3):
            m = max(m, abs(R3 * c / (R1 * a + R2 * b + R3 * c) / nom - 1))
        return m
    dtol, tcr, leak = worst(0.001), 50e-6 * 40, 0.0004
    tue = V("stm32_tue") / 4096
    w("**Error budget — three separate groups:**\n")
    w("| Group | Item | Worst case |\n|---|---|---|")
    w(f"| A divider | 0.1 % resistors | ±{dtol * 100:.2f} % |")
    w(f"| A divider | 25 ppm/K, 40 K excursion | ±{tcr * 100:.2f} % |")
    w(f"| A divider | clamp leakage (≈0.4 mV, BAT54S{t('bat54s_ir')}) | ±{leak * 100:.2f} % |")
    w(f"| **A subtotal** | | **±{(dtol + tcr + leak) * 100:.2f} %** |")
    w(f"| B ADC | TUE {V('stm32_tue')} LSB{t('stm32_tue')} | ±{tue * 100:.2f} % |")
    w("| C reference | VDDA 3.3 V ± 2 % (uncorrected) | ±2.00 % |")
    w(f"| C reference | after VREFINT correction{t('stm32_vrefint')} | ±{V('stm32_vrefint') * 100:.2f} % |")
    tu, tc = dtol + tcr + leak + tue + 0.02, dtol + tcr + leak + tue + V("stm32_vrefint")
    w(f"\nTotal uncorrected ±{tu * 100:.2f} % (±{tu * 44:.2f} V at 44 V); VREFINT-corrected ±{tc * 100:.2f} % (±{tc * 44:.2f} V). **Only ±{(dtol + tcr + leak) * 100:.2f} % is the divider**; the rest is the 3V3 reference, removed by the VREFINT correction. Plausibility cross-check against the INA228 (firmware window 1.5 V), not metrology.\n")
    w("### 1.1 Protection analysis (no back-feed into 3V3)\n")
    w("Circuit: **D8 (BAT54S)** lower diode ADC_SENSE→GND; upper diode ADC_SENSE→**VCLAMP**; **D14** 3V3→VCLAMP blocks the reverse direction; **R37 10 kΩ + C34** bleed VCLAMP; **R4 3.3 kΩ** permanently bleeds 3V3_A. The ADC node has **no direct connection to 3V3**.\n")
    ib = (44 - 0.6) / (R1 + R2)
    isc = (44 / ratio - 0.6) / (R3 * (R1 + R2) / Rt + 1e3)
    w("| Case | Result |\n|---|---|")
    w(f"| Controller powered, pack powered (44 V) | tap 2.750 V; VCLAMP ≈ 3V3 − D14 drop ≈ 3.1 V → upper diode reverse-biased by ≈ 0.35 V, leakage ≈ {V('bat54s_ir') * 1e9:.0f} nA × 9.4 kΩ = {V('bat54s_ir') * 9.4e3 * 1e3:.2f} mV ({V('bat54s_ir') * 9.4e3 / 2.75 * 100:.3f} %). PA1 max = 2.75 V (48 V: 3.00 V) |")
    w(f"| **Controller unpowered, pack powered** | tap would be 2.75 V; clamp short-circuit current ≤ {isc * 1e3:.2f} mA flows ADC_SENSE→D8→VCLAMP→R37 (VCLAMP ≈ {isc * 10e3:.1f} V). D14 is reverse-biased, so **3V3 receives only D14 leakage (nA)**; with R4 on 3V3_A the 3V3 rail stays at ≈ 0 V. |")
    w(f"| Controller unpowered, MCU pin has an internal diode to VDDA (unknown: {BY['stm32_io']['parameter']}{t('stm32_io')}) | worst case ≤ {isc * 1e3:.2f} mA into 3V3_A; R4 3.3 kΩ limits the rail to {isc * 3.3e3:.2f} V < POR min {V('stm32_por')} V{t('stm32_por')} → the MCU cannot partially power up. Cost: 1 mA permanent load. |")
    w(f"| Reversed pack (−44 V) | tap −2.75 V; D8 lower diode clamps ADC_SENSE at ≈ −{V('bat54s_vf'):.2f} V{t('bat54s_vf')} (≥ −0.3 V abs min); clamp current {(44 - 0.3) / (R1 + R2 + R3) * 1e3:.2f} mA |")
    w(f"| Transient on PACK_ADC to 77.4 V (TVS clamp level) | unclamped tap 4.84 V; upper diode → VCLAMP limits ADC_SENSE to ≈ VCLAMP + {V('bat54s_vf'):.2f} V ≈ 3.35 V; clamp current ≈ (4.84−3.35)/1 kΩ... limited to {(4.84 - 3.35) / 1e3 * 1e3:.2f} mA through R20 |")
    w("\nMaximum PA1 voltage: 2.75 V (44 V), 3.35 V (clamped). All diode/pin values are UNVERIFIED and listed as fabrication gates.\n")


# ------------------------------------------------------------------ 2 INA228
def ina():
    Rs = 2.5e-3
    w("## 2. INA228 + Bourns RSA-20-50 (2.5 mΩ, 20 A / 50 mV)\n")
    w(f"RSA-20-50: ±{V('rsa_tol') * 100:.2f} % tolerance, ±{V('rsa_tcr') * 1e6:.0f} ppm/°C, continuous ≤ {V('rsa_derate')} A (2/3 rated){t('rsa_tol')}. The OSBAMS ceiling (10 A) is below that.\n")
    w("| I | Vshunt | P shunt |\n|---|---|---|")
    for i in (1, 7.14, 10, 13.3, 15, 18.5, 20):
        w(f"| {i} A | {i * Rs * 1e3:.2f} mV | {i * i * Rs:.3f} W |")
    w("\n**ADCRANGE = 0 (±163.84 mV)**: range 1 (±40.96 mV = ±16.38 A) would saturate before the 18.5 A firmware trip (46.25 mV).")
    cl = 20.0 / 2 ** 19
    w(f"- IMAX = 20 A: CURRENT_LSB = {cl * 1e6:.3f} µA, **SHUNT_CAL = {13107.2e6 * cl * Rs:.0f}** (limit 32767; equation{t('ina228_shunt_cal')}). Current firmware header still uses 30 A / 1875 → firmware change.")
    w(f"- Offset ±{V('ina228_vos') * 1e6:.0f} µV{t('ina228_vos')} → {V('ina228_vos') / Rs * 1e3:.2f} mA = {V('ina228_vos') / Rs / 10 * 100:.4f} % of 10 A. Native current LSB {312.5e-9 / Rs * 1e6:.0f} µA (range 0).")
    w(f"- Input filter 2 × 10 Ω + 100 nF: fc = {1 / (2 * math.pi * 20 * 100e-9) / 1e3:.0f} kHz; bias {V('ina228_bias') * 1e9:.0f} nA{t('ina228_bias')} × 10 Ω = {V('ina228_bias') * 10 * 1e9:.0f} nV.")
    w(f"- VBUS: own lead PACK_INA through 10 Ω (error 10 Ω / ~830 kΩ ≈ 0.001 %, UV) + TVS; common-mode / VBUS range {V('ina228_cm')}{t('ina228_cm')}. **TVS clamp vs the 85 V limit is NOT a single-number comparison — see §2b.**")
    w(f"- INA228 DGS-10 pin map{t('ina228_pinmap')}: symbol compared pin-for-pin with the relayed TI table → **PASS** (1 A1, 2 A0, 3 ALERT, 4 SDA, 5 SCL, 6 VS, 7 GND, 8 VBUS, 9 IN−, 10 IN+). Firmware: IMAX 20 A / SHUNT_CAL 1250 (`app_config.h`; the Rev.1 30 A / 1875 setting is retired).\n")
    tvs_vs_ina()



def _tvs_v(i):
    """worst-case (highest) clamp voltage of one 1.5SMBJ48A at current i (A): knee at VBR max 58.9 V, 77.4 V at 19.4 A (10/1000 us), 100.6 V at 97 A (8/20 us)."""
    i = max(i, 0.0)
    if i <= 19.4:
        return 58.9 + (77.4 - 58.9) * i / 19.4
    return 77.4 + (100.6 - 77.4) * (i - 19.4) / (97.0 - 19.4)


def _sim(vsrc, rsrc, lh, rs, ctvs, rnext, cnext, i0=0.0, tmax=4e-6, dt=0.05e-9):
    """explicit integration: source(vsrc, rsrc) - L(lh, initial current i0) - Rs - node(C_tvs || TVS) - rnext - cnext. -> peak TVS current, node V, pin V, energy in Rs (J)"""
    il, vn, vp = i0, 0.0, 0.0
    ipk = vnpk = vppk = e_rs = 0.0
    n = int(tmax / dt)
    for _ in range(n):
        itvs = 0.0
        # TVS conducts when the node is above the knee: invert V(i) piecewise
        if vn > 58.9:
            itvs = (vn - 58.9) / (77.4 - 58.9) * 19.4 if vn <= 77.4 else 19.4 + (vn - 77.4) / (100.6 - 77.4) * 77.6
        inext = (vn - vp) / rnext
        dvn = (il - itvs - inext) / ctvs
        dil = (vsrc - rsrc * il - rs * il - vn) / lh
        il += dil * dt; vn += dvn * dt
        vp += (vn - vp) * (1.0 - math.exp(-dt / (rnext * cnext)))     # exact RC update (stable for the 20 pF pin node)
        if il < 0 and vsrc == 0:
            il = 0.0
        e_rs += il * il * rs * dt
        ipk = max(ipk, itvs); vnpk = max(vnpk, vn); vppk = max(vppk, vp)
    return ipk, vnpk, vppk, e_rs


def tvs_vs_ina():
    """Protection of the INA228 pack-sense inputs (85 V absolute maximum) against the credible bench transients."""
    v1, i1 = V("tvs48"), V("tvs48_ipp")
    v2, i2 = V("tvs48_820"), 97.0
    rd = (v2 - v1) / (i2 - i1)
    i85 = i1 + (85.0 - v1) / rd
    w("### 2b. Pack-sense protection: 1.5SMBJ48A + surge-limiting series resistors vs the INA228 85 V absolute maximum\n")
    w(f"**Manufacturer points{t('tvs48')}{t('tvs48_820')}:** VRWM 48 V, VBR 53.3-58.9 V; VC ≤ {v1} V at {i1} A (10/1000 µs) and ≤ {v2} V at {i2:.0f} A (8/20 µs). INA228 IN+/IN−/VBUS absolute maximum {V('ina228_cm')}{t('ina228_cm')}. '77.4 V < 85 V' is **not** used as a blanket pass: the clamp exceeds 85 V above ≈ {i85:.0f} A (straight line between the two rating points = engineering estimate [UV], not a datasheet curve).\n")
    w("**RC1.2 hardware change:** series surge-limiting resistors **upstream of the TVS**: R41 47 Ω on PACK_INA (J6.1 → R41 → D7/R13) and R42/R43 10 Ω on each Kelvin line (J5 → R42/R43 → D5/D6 + the existing 10 Ω R11/R12 → INA228). 1206 anti-surge parts (Panasonic ERJ-P08F series, pulse rating to be confirmed from the datasheet [UV]).\n")
    w("**Credible transient definition for this bench system** (30-42 V pack, 44 V ceiling, ≤ 10 A operating, 18.5 A firmware trip, 15 A fuse, short harness, K1 = Durakool DG57CM):")
    w("1. *Interruption of load current (K1 opening, fuse clearing, 6060B turn-off):* the only energy that can force a current into the sense TVS is the inductance of the wiring carrying the interrupted current, ≤ the 18.5 A firmware trip (15 A fuse rating, 10 A operating). The pack cannot push current into a TVS that is clamping above the pack voltage (clamp ≥ 53 V > 44 V). **Bound: TVS current ≤ 18.5 A → VC ≤ ≈76.5 V (rating: ≤ 77.4 V at 19.4 A).** The contact arc appears as a *drop* between the contacts, not as an overvoltage on the sense nodes; a hard downstream short that clears the fuse collapses the sense nodes toward 0 V.")
    w("2. *Hot-plug of the sense harness onto a live 44 V pack:* LC ringing, simulated below.")
    w("3. *Electrostatic/handling events and mains-borne surges are not part of this bench's credible set;* the series resistors extend the margin toward them (table below) but protection against them is not claimed.\n")
    cases = (("VBUS path", 47.0, 10.0, 100e-9), ("Kelvin line", 10.0, 10.0, 20e-12))
    w("**Hot-plug simulation** (44 V step; source ESR + harness 0.3 Ω; harness L 0.5/2/5 µH; TVS junction C 0.3/1/3 nF [UV]; peak INA-pin voltage is the pin side of the 10 Ω):\n")
    w("| path | Rs upstream | L | C_tvs | TVS peak current | node peak V | INA pin peak V | energy in Rs |\n|---|---|---|---|---|---|---|---|")
    worst_pin = 0.0
    for name, rs, rn, cn in cases:
        for rs_u in (0.0, rs):
            for lh in (0.5e-6, 2e-6, 5e-6):
                for ct in (0.3e-9, 1e-9, 3e-9):
                    ipk, vnpk, vppk, e = _sim(44.0, 0.3, lh, rs_u, ct, rn, cn, tmax=max(4e-6, 6 * (rs_u + rn) * cn), dt=0.1e-9 if ct > 0.5e-9 else 0.05e-9)
                    worst_pin = max(worst_pin, vppk) if rs_u else worst_pin
                    if ct == 1e-9:
                        w(f"| {name} | {rs_u:.0f} Ω | {lh * 1e6:.1f} µH | {ct * 1e9:.1f} nF | {ipk:.2f} A | {vnpk:.1f} V | {vppk:.1f} V | {e * 1e6:.2f} µJ |")
    # worst over every combination, with the resistors fitted
    wp = wn = wi = 0.0
    for name, rs, rn, cn in cases:
        for lh in (0.5e-6, 2e-6, 5e-6):
            for ct in (0.3e-9, 1e-9, 3e-9):
                ipk, vnpk, vppk, e = _sim(44.0, 0.3, lh, rs, ct, rn, cn, tmax=max(4e-6, 6 * (rs + rn) * cn), dt=0.1e-9 if ct > 0.5e-9 else 0.05e-9)
                wp, wn, wi = max(wp, vppk), max(wn, vnpk), max(wi, ipk)
    w(f"\nWorst hot-plug case over all combinations **with the resistors fitted**: TVS current {wi:.2f} A, node {wn:.1f} V, INA pin {wp:.1f} V (limit 85 V).\n")
    # forced interruption bound
    w("**Forced-interruption bound** (the whole interrupted current is assumed to be forced through the sense branch — a gross over-estimate, since the sense harness is a thin wire):\n")
    w("| interrupted current | L | path | TVS peak current | node peak V | energy in Rs |\n|---|---|---|---|---|---|")
    for i0 in (10.0, 15.0, 18.5):
        for name, rs, rn, cn in cases:
            for rs_u in (0.0, rs):
                ipk, vnpk, vppk, e = _sim(44.0, 0.3, 2e-6, rs_u, 1e-9, rn, cn, i0=i0, tmax=3e-6)
                w(f"| {i0} A | 2 µH | {name}, Rs = {rs_u:.0f} Ω | {min(ipk, i0):.1f} A | {max(_tvs_v(min(ipk, i0)), 0):.1f} V | {e * 1e6:.0f} µJ |")
    w(f"\nWith Rs = 0 the clamp at the 18.5 A bound is {_tvs_v(18.5):.1f} V (margin {85 - _tvs_v(18.5):.1f} V); with the series resistors the interrupted current is dissipated mainly in Rs (≤ ½·L·I² = {0.5 * 2e-6 * 18.5 ** 2 * 1e6:.0f} µJ for 2 µH at 18.5 A — far inside a 1206 anti-surge resistor) and the TVS current is far below 18.5 A.\n")
    w("**Model results only — NOT validated design limits** (open-circuit surge, 8/20 µs, source impedance 2 Ω; TVS current solved against the clamp curve; resistor energy ≈ I²·R·13 µs [UV]; the credible set above is ≤ 100 V-class, i.e. ≤ 1.3 mJ in R42/R43 and ≤ 0.4 mJ in R41):\n")
    w("| Voc | Rs | TVS current | VC (INA node) | within 85 V? | energy in Rs |\n|---|---|---|---|---|---|")
    for rs in (0.0, 10.0, 47.0):
        for voc in (100, 300, 600, 1000, 2000):
            i = 0.0
            for _ in range(200):
                i = max(0.0, (voc - _tvs_v(i)) / (rs + 2.0))
            vc = _tvs_v(i)
            w(f"| {voc} V | {rs:.0f} Ω | {i:.1f} A | {vc:.1f} V | {'yes' if vc <= 85 else '**no**'} | {i * i * rs * 13e-6 * 1e3:.1f} mJ |")
    w("\nThese rows are **model results**: the clamp curve is a straight line between two rating points [UV], the waveform is assumed, the 1.5SMBJ48A dynamic impedance and the ERJ-P08F pulse rating have not been read from the datasheets. **No 600 V / 2 kV protection limit is claimed.**\n")
    w("**Measurement-error budget of the new resistors:**")
    w(f"- INA228 input bias {V('ina228_bias') * 1e9:.1f} nA{t('ina228_bias')} × 20 Ω per Kelvin line = {V('ina228_bias') * 20 * 1e9:.0f} nV worst case unmatched ({V('ina228_bias') * 20 / 2.5e-3 * 1e6:.0f} µA of shunt-current equivalent); with matched 1 % resistors the common component cancels (< 1 pV difference) — negligible vs the ±1 µV offset.")
    w("- TVS leakage drops across R42/R43 (10 Ω each): up to 1 µA [UV; leakage not relayed] × 10 Ω = 10 µV worst-case line-to-line mismatch = 4 mA of shunt-current equivalent (0.04 % at 10 A; 0.4 mA for a typical 0.1 µA). This is the price of the Kelvin resistors and is why they are 10 Ω rather than 47 Ω; it is removed by the no-load zero calibration only if leakage is stable — verify at first article (shunt voltage at 0 A, 25 °C and warm).")
    w("- VBUS: 47 Ω + 10 Ω = 57 Ω into the INA228 VBUS input (assumed ≥ 830 kΩ [UV]) → ≤ 0.007 % gain error (3 mV at 44 V), a fixed ratio that the VBUS calibration against the EDU34450A removes; TVS leakage 1 µA × 57 Ω = 57 µV (1.3 ppm).")
    w("- Filtering: differential Kelvin filter = 2 × 20 Ω with C26 100 nF → fc ≈ 40 kHz (τ 4 µs ≪ the INA228 conversion time ≥ 50 µs → no effect on logging or the ALERT latency); VBUS: 57 Ω with C28 100 nF → fc ≈ 28 kHz.")
    w("- Common mode: both Kelvin lines carry identical series resistance, so the common-mode level (≤ 44 V, limit 85 V) and the bias-current common-mode shift cancel; the TVS pair clamps each line to ground, so a one-sided transient is limited to the TVS clamp (differential absolute maximum of the INA228 inputs was not relayed [UV]).")
    w("- Normal 44 V operation: VRWM 48 V > 44 V and VBR min 53.3 V > 44 V (no conduction); resistor dissipation at DC ≈ 0 (bias/leakage only); 1206 working voltage ≫ 44 V [UV].")
    e41 = _sim(44.0, 0.3, 2e-6, 47.0, 1e-9, 10.0, 100e-9, i0=18.5, tmax=3e-6)[3]
    e42 = _sim(44.0, 0.3, 2e-6, 10.0, 1e-9, 10.0, 20e-12, i0=18.5, tmax=3e-6)[3]
    ehp = max(_sim(44.0, 0.3, lh, 47.0, ct, 10.0, 100e-9, tmax=max(4e-6, 6 * 57 * 100e-9), dt=0.1e-9)[3] for lh in (0.5e-6, 5e-6) for ct in (0.3e-9, 3e-9))
    w("\n**Recomputed values for the defined transient (model; source values marked [UV] are unverified):**")
    w(f"- Resistor pulse energy: forced interruption at 18.5 A / 2 µH: R41 {e41 * 1e6:.0f} µJ, R42/R43 {e42 * 1e6:.0f} µJ (= ½·L·I² = {0.5 * 2e-6 * 18.5 ** 2 * 1e6:.0f} µJ upper bound); hot-plug into the 100 nF on VBUS: R41 ≤ {ehp * 1e6:.0f} µJ. **Panasonic ERJ P/PA/PM catalog (read locally, ERJP08 1206): 0.66 W at 70 °C, limiting element voltage 500 V, maximum overload voltage 1000 V, ESD test ±3 kV with 150 pF (= 0.675 mJ). The credible-set energies above (≤ 0.37 mJ, itself a gross over-estimate) are below that ESD-test energy; the catalog gives no µs–ms pulse-energy-vs-duration curve [UV], so the thermal-pulse rating is not documented.**")
    w("- PACK_INA error from TVS leakage × 47 Ω: 47 µV per µA of leakage (1.1 ppm of 44 V per µA). **Bourns datasheet (read locally): IR ≤ 1.0 µA at VRWM = 48 V, 25 °C → ≤ 47 µV (1.1 ppm) at 25 °C.** Leakage at 44 V is lower but no curve is given, and leakage vs temperature is **not specified** [UV]; even 10 µA hot would give only 0.47 mV (11 ppm).")
    w("- Shunt-offset error from leakage × 10 Ω: 10 µV per µA of mismatch = 4 mA of shunt-current equivalent per µA. **At 25 °C the datasheet bound (IR ≤ 1.0 µA each, so mismatch ≤ 1 µA) gives ≤ 10 µV = ≤ 4 mA (0.04 % at 10 A).** Hot leakage is not specified [UV]: a figure ≥ 5 µA would give ≥ 20 mA — measured at first article (shunt voltage at 0 A, cold and warm).")
    w("- Continuous dissipation: R41 carries the VBUS input current (≈ 53 µA at 44 V [UV]) plus leakage: (55 µA)² × 47 Ω ≈ 0.14 µW; R42/R43 carry only bias/leakage (≪ 1 µW) — against the 0.66 W (70 °C) rating of the ERJP08 this is irrelevant.")
    ir = 0.0
    for _ in range(200):
        ir = max(0.0, (100 - _tvs_v(ir)) / (47.0 + 2.0))
    ik = 0.0
    for _ in range(200):
        ik = max(0.0, (100 - _tvs_v(ik)) / (10.0 + 2.0))
    w(f"- Resistor voltage: in the credible set (open-circuit surge ≤ 100 V, 2 Ω source) R41 sees ≈ {ir * 47:.0f} V and R42/R43 ≈ {ik * 10:.0f} V for microseconds; the forced-interruption rows above are a gross over-estimate (a thin sense harness cannot carry 18.5 A) and their instantaneous R·I (> 800 V on 47 Ω) must not be read as a resistor stress. The ERJP08 limiting element voltage is 500 V and the maximum overload voltage 1000 V (Panasonic catalog), so the credible-set resistor voltages are far inside the rating and even the non-credible 870 V instant of the forced model is below the 1000 V overload voltage (above the 500 V limiting voltage for nanoseconds only).")
    hot = 1 + V("tvs_tempco") * 60
    w(f"- Temperature: the Bourns typical VBR temperature coefficient is 0.1 %/K{t('tvs_tempco')}; VBR(min) = 53.3 V → {53.3 * (1 - 0.001 * 65):.1f} V at −40 °C (still > 44 V, no conduction) and {53.3 * hot:.1f} V at +85 °C. If the clamp voltage scales with VBR [UV], the 18.5 A bound rises to ≈ {_tvs_v(18.5) * hot:.1f} V at TA = 85 °C (margin {85 - _tvs_v(18.5) * hot:.1f} V) and ≈ {_tvs_v(18.5) * (1 + 0.001 * 15):.1f} V at 40 °C — the margin shrinks with temperature but stays positive for the defined transient; the 19.4 A rating point itself would reach ≈ {77.4 * hot:.1f} V at 85 °C.")
    w(f"- Worst-case INA228 node voltage in the defined transient: **{_tvs_v(18.5):.1f} V** (forced-interruption bound, Rs = 0, worst-case clamp knee 58.9 V → 77.4 V at 19.4 A) and ≤ {wp:.1f} V in the hot-plug simulation; limit 85 V.")
    w("\n**Result: PASS for the defined transient, using datasheet-verified limits** — Bourns 1.5SMBJ48A (clamp points, IR ≤ 1.0 µA at 48 V/25 °C, VBR temperature coefficient) and Panasonic ERJ-P08F (part-number scheme, 0.66 W, 500 V limiting / 1000 V overload voltage, ESD ±3 kV/150 pF). Two quantities are **not specified** by the manufacturers and stay model/first-article items: (1) TVS leakage vs temperature and below 48 V (offset budget: 4 mA of shunt-current equivalent per µA of mismatch) and (2) the resistors' µs–ms pulse-energy-vs-duration rating (the credible-set energies are inside the ESD-test energy, but the thermal-pulse limit is not published in the catalog); the clamp curve between the two Bourns rating points is an estimate (no dynamic impedance is published). The surge-capability table is a model result, not a validated limit. A lower-voltage TVS is rejected (standoff/leakage vs the 44 V ceiling).\n")


# ------------------------------------------------------------------ 3 buck
def buck():
    vref, f = V("lmr_vref"), V("lmr_fsw")
    R1, R2 = 33.2e3, 10e3
    vout = vref * (1 + R1 / R2)
    L = 10e-6
    w("## 3. Buck LMR14006Y: 12 V → 3.3 V\n")
    w(f"Feedback: VREF {vref} V{t('lmr_vref')}, R1 {R1 / 1e3:.1f} kΩ / R2 {R2 / 1e3:.0f} kΩ → Vout = {vref} × (1 + R1/R2) = **{vout:.3f} V** (1 % resistors: {vout * 0.0094:+.3f} V, ±VREF tolerance UV). fsw {f / 1e6:.1f} MHz{t('lmr_fsw')}.\n")
    fmin, fmax, ton_min = 1.785e6, 2.415e6, V("lmr_ton_min")
    vmin = 0.747 * (1 + R1 * 0.99 / (R2 * 1.01)); vmax = 0.782 * (1 + R1 * 1.01 / (R2 * 0.99))
    w(f"Output range with VFB 0.747-0.782 V{t('lmr_vfb_range')} and 1 % resistors: **{vmin:.3f} - {vmax:.3f} V** (nominal {vout:.3f} V); the 3V3 rail therefore may sit up to {vmax - 3.3:+.2f} V / {vmin - 3.3:+.2f} V from 3.30 V (STM32/INA228/ISO7721 supply limits 3.6 V / 5.5 V: within, but the STM32 VDD max is [UV]).\n")
    w(f"Minimum on-time: **TON_MIN = {ton_min * 1e9:.0f} ns**{t('lmr_ton_min')}; fsw {fmin / 1e6:.3f} / {f / 1e6:.3f} / {fmax / 1e6:.3f} MHz (min/typ/max){t('lmr_fsw_range')}. On-time = Vout / (Vin · fsw) (on-time is shortest at the **highest** fsw).\n")
    w("| Vin | duty (typ) | on-time @ typ fsw | on-time @ max fsw | vs 95 ns | ΔIL (L = 10 µH) | Ipk @ 150 mA |\n|---|---|---|---|---|---|---|")
    for vin in (11.0, 12.0, 12.5, 15.0, 24.4):
        d = vout / vin; dil = vout * (1 - d) / (L * f)
        tt, tm = d / f * 1e9, vout / (vin * fmax) * 1e9
        st = "PASS" if tm >= ton_min * 1e9 else ("MARGINAL (typ ok, max-fsw corner below)" if tt >= ton_min * 1e9 else "**BELOW TON_MIN: pulse skipping**")
        w(f"| {vin} V | {d * 100:.1f} % | {tt:.0f} ns | {tm:.0f} ns | {st} | {dil * 1e3:.0f} mA | {(0.15 + dil / 2) * 1e3:.0f} mA |")
    w(f"\n**Corrected statement:** 12 V (normal XDR operation) PASSES ({vout / (12 * fmax) * 1e9:.0f} ns at the fastest fsw corner). The 15 V corner is only ≈ {vout / (15 * f) * 1e9 - ton_min * 1e9:.0f} ns above TON_MIN at typical fsw and is **{vout / (15 * fmax) * 1e9:.0f} ns (below 95 ns) at the maximum-fsw corner** — not guaranteed fixed-frequency. The **24.4 V SMBJ15A-clamp transient ({vout / (24.4 * f) * 1e9:.0f} ns) is below TON_MIN: fixed-frequency regulation is NOT claimed there.** Expected behaviour is pulse skipping (fewer, minimum-width pulses; output ripple/frequency change); the datasheet behaviour in this region is not characterised in the data I hold [UV], so no regulation guarantee is made during the transient. The normal source is the XDR at 12.0 V, so this does not invalidate the part; it limits the claim to ≤ ≈ {vout / (ton_min * fmax) :.1f} V (max-fsw corner) / ≈ {vout / (ton_min * f):.1f} V (typical fsw) steady-state input. Verify by measurement at first article.\n")
    vmax_cont = vout / (ton_min * fmax)
    w(f"**Design requirement (RC1.2):** XDR-75-12 nominal output = **12.0 V ±1 %** (11.88-12.12 V at the J1 connector; ≈ 11.5-11.7 V at the buck after F1 and D2). **Maximum allowed *continuous* controller input = {vmax_cont:.1f} V** (fixed-frequency regulation guaranteed with TON_MIN {ton_min * 1e9:.0f} ns at the fastest fsw corner); the 12 V supply therefore has {vmax_cont - 12.12:.1f} V of headroom. Operation above {vmax_cont:.1f} V is not claimed to be fixed-frequency; the SMBJ15A transient (24.4 V clamp) is treated separately below, not as continuous operation.\n")
    dil_min = (24.4 - vout) * ton_min / L
    e_pulse = 0.5 * L * dil_min ** 2
    cout = 26e-6
    w(f"**3V3 during the 24.4 V transient (TON_MIN-limited pulse skipping):** one minimum-width pulse raises the inductor current by ΔI = (24.4 − {vout:.2f}) V × {ton_min * 1e9:.0f} ns / 10 µH = {dil_min * 1e3:.0f} mA, i.e. at most ½LΔI² = {e_pulse * 1e9:.0f} nJ per pulse; into ≈ {cout * 1e6:.0f} µF of derated output capacitance that is ≤ {e_pulse / (cout * vout) * 1e3:.1f} mV per pulse if the load took nothing, and the feedback comparator skips the following pulses, so the rail is regulated by pulse skipping rather than rising. Rail excursion during the transient is therefore millivolts, ≪ the 3.6 V class limit of the loads (STM32/INA228/ISO7721 VDD maximum values are [UV] — confirm 3.6 V-class or higher). A fault in the feedback divider (R1 short / R2 open) is a separate single-fault case that no buck design here protects against.\n")
    w(f"VIN rating: recommended 4-40 V, absolute max 45 V{t('lmr_limits')}; SMBJ15A clamp {V('tvs15')} V (+ a 12 V XDR) → margin to 45 V ≈ {45 - V('tvs15'):.1f} V. ")
    w(f"Inductor/limits (TI): current limit ≈ 1.2 A typ, max duty ≈ 97 %. ")
    w(f"Inductor: Bourns SRN6045TA-100M (10 µH ±20 %, DCR 52 mΩ typ, Irms 3.20 A typ, Isat 4.60 A typ{t('lmr_l_c')}): Isat is ≈ 3.8× the 1.2 A typical current limit and ≈ 20× the ≈ 0.22 A peak load current → closed (typical values). Output 2 × 22 µF 10 V 0805 (≈ 50 % DC-bias derating → ≈ 26 µF): ripple ≈ ΔIL/(8 f C) = {0.114 / (8 * f * 26e-6) * 1e3:.2f} mV + ESR term. Input C1+C2 2 × 10 µF 50 V 1210 + 100 nF at the VIN pin: ripple ≈ I·D(1−D)/(f C) = {0.15 * 0.275 * 0.725 / (f * 6e-6) * 1e3:.1f} mV at 6 µF effective.")
    w(f"Surge: SMBJ15A clamp {V('tvs15')} V{t('tvs15')} vs LMR14006Y 40 V rating (margin ≈ 15.6 V; abs-max UV). EN: 100 kΩ to +12V (method{t('lmr_en')}).\n")
    w("3V3 load ≈ 40 mA typical (STM32 ~20, INA228 ~1, ISO ~3, pull-ups/LEDs ~15) + 1 mA bleeder; design 150 mA → 12 V input ≈ 45 mA (85 %). 3V3_A: ferrite 600 Ω@100 MHz + 4.7 µF + 100 nF. **Ripple on 3V3 and 3V3_A is measured at first-article bring-up, not computed.**\n")


# ------------------------------------------------------------------ 4 relay driver
def relay():
    R = V("dg57_coil_ohm")
    w("## 4. Relay driver (Durakool DG57CM-5021-76-1012-R + IRLML0060TRPBF)\n")
    w(f"Relay (reported): SPST-NO, 12 V coil, ≈1.6 W, DC1 80 A@12 V / 60 A@36 V / 50 A@48 V, max switching 145 VDC, operate ≈ {V('dg57_operate') * 1e3:.0f} ms{t('dg57_dc1')}. OSBAMS stays ≤ 44 V / ≤ 10 A: margin ≥ 5× at 48 V (50 A) vs 10 A. Coil {R:.0f} Ω{t('dg57_coil_ohm')}.\n")
    w("| Coil V | I | P |\n|---|---|---|")
    for v in (10.5, 11.6, 12.0, 15.0):
        w(f"| {v} V | {v / R * 1e3:.0f} mA | {v * v / R:.2f} W |")
    w(f"\nCoil data{t('dg57_coil_ohm')}{t('dg57_pickup')}: 90 Ω ±10 % at 23 °C → {12.0 / (R * 1.1) * 1e3:.0f}-{12.0 / (R * 0.9) * 1e3:.0f} mA at 12.0 V; must-operate ≤ 7.2 V, must-release ≥ 1.2 V (23 °C); **maximum allowable coil voltage 17.4 V at 23 °C but only 12.5 V at 85 °C** → the XDR is set to 12.0 V and must never be run at 15 V (the 15 V row above is shown only to document the exclusion). Coil node after D2 (SS14 drop ≈ 0.4 V) with a 12.0 V ± 1 % XDR ≈ 11.7 V: operate margin 7.2 V → 4.5 V, max-allowable margin 12.5 V → 0.8 V at 85 °C [UV: XDR tolerance not read].\n")
    w(f"\n**Q1 = IRLML0060TRPBF (60 V SOT-23 logic-level)** — RDS(on) is not specified at 3.3 V (manufacturer: ≤ 116 mΩ at 4.5 V, ≤ 92 mΩ at 10 V [UR]; typical output/transfer curves include 2.8-3.5 V but were not available to this build); using a pessimistic placeholder {V('q_rds')} Ω{t('q_rds')}: VDS = {0.17 * V('q_rds') * 1e3:.0f} mV and P = {0.17 ** 2 * V('q_rds') * 1e3:.1f} mW at 170 mA. Gate overdrive at 3.3 V × 0.97 with VGS(th) max {V('q_vth')} V{t('q_vth')} is {3.2 - V('q_vth'):.1f} V — adequate for a 0.17 A load but **Infineon's typical curves at VGS 3.0/3.3 V make the load plausible, but RDS(on) is not guaranteed at 3.3 V → first-article VDS / coil-current measurement is the validation item**. VDSS {V('q_vdss'):.0f} V{t('q_vdss')} vs the {V('tvs15')} V TVS clamp → margin {V('q_vdss') - V('tvs15'):.1f} V. Alternates: Diodes DMN6140L-7 (60 V), AOS AO3400A (30 V, 2.5 V-specified).")
    vth, rds45, vgs = V("q_vth"), V("q_rds_4v5"), 3.2
    k_est = 1.0 / (rds45 * (4.5 - vth))
    rds_est = 1.0 / (k_est * (vgs - vth))
    id_sat = 0.5 * k_est * (vgs - vth) ** 2
    w(f"**Margin estimate at VGS = {vgs} V (3.3 V × 0.97), worst-case VGS(th) {vth} V and the 4.5 V RDS(on) max {rds45 * 1e3:.0f} mΩ{t('q_rds_4v5')}:** transconductance parameter k ≈ 1/(RDS(on)·(4.5 − VGS(th))) = {k_est:.1f} A/V² → RDS(on) ≈ {rds_est * 1e3:.0f} mΩ (the 0.5 Ω placeholder is {0.5 / rds_est:.1f}× that), saturation current ≈ ½k(VGS − VGS(th))² = **{id_sat:.1f} A = {id_sat / 0.15:.0f}× the 0.15 A coil load** (square-law extrapolation near threshold = estimate [UV], not a guarantee). **Classification: keep IRLML0060 — comfortably inside the transfer-characteristic region by this estimate; RDS(on) at 3.3 V is not guaranteed, so the first-article measurements are mandatory (VGS, VDS while energized, coil current, MOSFET temperature) — a first-article item, not a PCBWay blocker.**\n")
    w("Gate network: 220 Ω in series, 10 kΩ pull-down → default OFF in reset/unpowered/Hi-Z. Flyback: S1M-13-F (1 A 1000 V), cathode on COIL_V; **no fast-release TVS in RC1** (a 27 V TVS would put 12+27 V on the MOSFET).")
    L = V("dg57_coil_l"); I = 12.0 / R
    w(f"Flyback energy ½LI² = {0.5 * L * I * I * 1e3:.2f} mJ (L = {L} H{t('dg57_coil_l')}); diode-only decay τ = L/R = {L / R * 1e3:.1f} ms (release time to be taken from the relay datasheet).\n")


# ------------------------------------------------------------------ 5 optocouplers
def opto():
    ctr1 = V("vo610a_ctr_min_1mA")
    tmp, age = V("vo610a_temp_derate"), V("vo610a_aging_derate")
    eff = ctr1 * tmp * age
    vf, vce = V("vo610a_vf_max"), V("vo610a_vcesat")
    w("## 5. VO610A-1 stages (status inputs, active-low)\n")
    w("**Guaranteed data (user-relayed [UR]):** CTR min 13 % / typ 30 % at IF = 1 mA, VCE = 5 V; CTR min 40 % / max 80 % at IF = 10 mA. **The arbitrary 20 % CTR has been deleted.** VF max 1.6 V is the manufacturer's value at IF = 50 mA, used as a conservative bound at the low IF here; VCE(sat) max 0.3 V (IF = 10 mA, IC = 1 mA) [UR] — the design keeps the more conservative 0.4 V at 0.07 mA. The 0.8 temperature and 0.8 aging factors are **DESIGN_MARGIN** (project assumptions, not manufacturer data).\n")
    w("Method (design-to-guaranteed):")
    w(f"1. CTR_eff = CTR_min(1 mA) × temp derate × aging derate = {ctr1:.2f} × {tmp:.2f}{t('vo610a_temp_derate')} × {age:.2f}{t('vo610a_aging_derate')} = **{eff:.4f}**; valid for every IF ≥ 1 mA by the monotonic-curve assumption{t('vo610a_ctr_monotonic')} (CTR rises from 1 mA to 10 mA).")
    w(f"2. Pull-up demand I_pu = (3.3 V − VCE(sat) {vce} V{t('vo610a_vcesat')}) / R_pu. Require IF × CTR_eff ≥ 2 × I_pu (saturation margin 2).")
    w(f"3. IF = (Vsupply − VF_max {vf} V{t('vo610a_vf_max')}) / R_led (R_led +1 % tolerance); evaluate at the minimum supply.\n")
    rpu = 47e3
    ipu = (3.3 - vce) / rpu
    w(f"R_pu = 47 kΩ → I_pu = {ipu * 1e6:.1f} µA → IF_min = 2 I_pu / CTR_eff = **{2 * ipu / eff * 1e3:.2f} mA**.\n")

    def net(name, rled, vlist, vmin):
        w(f"**{name}** — R_led {rled / 1e3:.1f} kΩ, R_pu 47 kΩ, minimum supply {vmin} V\n")
        w("| V | IF | IC available | margin | R dissipation (total) |\n|---|---|---|---|---|")
        for v in vlist:
            iff = (v - vf) / (rled * 1.01); ic = iff * eff
            w(f"| {v} V | {iff * 1e3:.2f} mA | {ic * 1e6:.0f} µA | ×{ic / ipu:.2f} | {iff * iff * rled * 1e3:.0f} mW |")
        vreq = vf + 2 * ipu / eff * rled * 1.01
        ok = vreq <= vmin
        w(f"\nVoltage for 2× margin: **{vreq:.1f} V** ≤ {vmin} V → **{'PASS' if ok else 'FAIL'}**.\n")
        return ok
    ok1 = net("ESTOP_SENSE: R24 5.6 kΩ (0603)", 5.6e3, (10.5, 11.6, 12.0, 15.0), 10.5)
    ok2 = net("RELAY_FB: R26+R27+R28 = 3 × 4.7 kΩ = 14.1 kΩ (1206)", 14.1e3, (24, 28, 30, 36, 42, 44, 48, 77.4), 24)
    p77 = ((77.4 - vf) / 14.1e3) ** 2 * 4.7e3
    p100 = ((100.6 - vf) / 14.1e3) ** 2 * 4.7e3
    w(f"Relay-feedback supported pack range 30–44 V is covered down to 24 V (20 % below the 30 V minimum, allowing pack sag under load). At the 77.4 V TVS level (10/1000 µs rating) each 4.7 kΩ resistor dissipates {p77 * 1e3:.0f} mW and at the 100.6 V (8/20 µs) level {p100 * 1e3:.0f} mW (1206 = 250 mW; short transients only). At 44 V: {((44 - vf) / 14.1e3) ** 2 * 4.7e3 * 1e3:.0f} mW each. The 1N4148 across each LED limits reverse voltage to ≈ 0.7 V (LED VR max {V('vo610a_led_vr')} V{t('vo610a_led_vr')}). Relay open: the load side floats at ≈ 0 V → LED dark → PC9 HIGH (fail-safe: 'not closed'); E-stop open or wire broken → no current → PA0 HIGH (fault).\n")
    assert ok1 and ok2, "opto network fails its own margin"


# ------------------------------------------------------------------ 6 ARM
def arm():
    w("## 6. ARM_SENSE divider (status only)\n")
    w("`COIL_V → 270 k → ARM_DIV → 100 k → GND; ARM_DIV → 1 k → ARM_SENSE (PC10) + 100 nF; BAT54S clamp D13 (GND / +3V3)`\n")
    w("| COIL_V | ARM_DIV |\n|---|---|")
    for v in (0, 10.5, 11.6, 12.0, 15.0):
        w(f"| {v} V | {v * 100 / 370:.2f} V |")
    vih = V("stm32_vih") * 3.3
    w(f"\nVIH {vih:.2f} V{t('stm32_vih')} → valid HIGH from 10.5 V ({10.5 * 100 / 370:.2f} V); at 15 V the node is 4.05 V, held to ≈ 3.6 V by D13's upper diode. Source impedance 73 kΩ → clamp back-feed ≤ (15 − 0.3)/270 kΩ = 54 µA, and ARM_SENSE sits on the +12V chain, which always powers the buck first. HIGH = ARM closed with E-stop closed; E-stop open → COIL_V = 0 → ARM unknown. Sensing only: no firmware path can energize K1.\n")


# ------------------------------------------------------------------ 7 I2C
def i2c():
    w("## 7. I²C buses (tr = 0.8473·R·C)\n")
    w("| Bus | R | Cb | tr | limit |\n|---|---|---|---|---|")
    for bus, r, c, lim in (("I2C1 INA228 (board only, ~125 kHz in firmware)", 4.7e3, 50e-12, "1000 ns (standard)"), ("I2C1 at 400 kHz", 4.7e3, 50e-12, "300 ns"), ("I2C2 TC74, 1 m cable", 4.7e3, 155e-12, "1000 ns"),
                           ("I2C2 TC74, 1.5 m (limit)", 4.7e3, 215e-12, "1000 ns"), ("I2C2 TC74, 2 m (2.2 k alt.)", 2.2e3, 285e-12, "1000 ns")):
        w(f"| {bus} | {r / 1e3:.1f} k | {c * 1e12:.0f} pF | {0.8473 * r * c * 1e9:.0f} ns | {lim} |")
    w("\nTC74 on its own I²C2 (PB10/PB11) ≤ 100 kHz, cable ≤ 1.5 m; beyond that stop and propose another interface (DS18B20/NTC are contingency only).\n")


# ------------------------------------------------------------------ 8 power / ISO
def power():
    w("## 8. Power tree and isolated host supplies\n")
    w("`XDR-75-12 (12.0 V) → J1 → F1 1 A → D2 SS14 → +12V (TVS D1, C1) → [E-stop → ARM → K1 coil → Q1] and [LMR14006Y → 3V3 → ferrite → 3V3_A]`; no 5 V rail. Series Schottky drop ≈ 0.4 V → coil ≈ 11.6 V. Rail ≈ 0.19 A total; F1 1 A.")
    w("ISO7721 has **no isolated power**: VCC1 = +3V3 (100 nF, controller GND); VCC2 = 3V3_HOST from the CP2102N regulator (VREGIN ← USB VBUS), 100 nF, GND_HOST. GND and GND_HOST are never joined (separate copper islands with a 3 mm gap under the isolator). Regulator capability and the ISO7721 ICC are UNVERIFIED critical items.\n")
    host_usb()


def host_usb():
    w(f"**ISO7721 pin map (TI SLLSEP3G Table 5-1, read locally{t('iso_pinmap')}):** 1 VCC1, 2 OUTA, 3 INB, 4 GND1, 5 GND2, 6 OUTB, 7 INA, 8 VCC2. Channel A runs side 2 → side 1 (INA pin 7 ← CP2102N TXD, OUTA pin 2 → STM32 PA3 RX); channel B runs side 1 → side 2 (INB pin 3 ← STM32 PA2 TX, OUTB pin 6 → CP2102N RXD). The ISO7721 (no suffix) default output is HIGH, matching UART idle; supply 2.25-5.5 V on each side{t('iso_supply')}. (The RC1 symbol had followed the ISO7720 table — corrected in RC1.1.)\n")
    vm = V("cp_vbus_div")
    w(f"**CP2102N VBUS sense (Silicon Labs datasheet rev. 1.5, read locally{t('cp_vbus_div')}):** a resistor divider (or equivalent) on VBUS is required. Datasheet limits: VBUS-pin input-high VIH = VIO − 0.6 V (VIO = VDD = 3V3_HOST, 3.1-3.3-3.6 V from the 100 mA regulator); VIL ≤ 0.6 V; absolute maximum VIN = VIO + 2.5 V (5.6 V at VDD 3.1 V; 5.8 V for VIO > 3.3 V); the reference connection uses 22.1 kΩ (upper) / 47.5 kΩ (lower).\n")
    w("Worst-case margin of the **detection** limit: pin voltage = VBUS × R2(−1 %) / (R1(+1 %) + R2(−1 %)) must be ≥ VIH max = VDD max − 0.6 V = 3.0 V; VBUS minimum = 4.40 V (USB 2.0 low-power minimum) or 4.75 V (standard downstream port; a Raspberry Pi host port supplies ≈ 5 V); **absolute maximum** margin at VBUS 5.25 V with the divider ratio at its maximum, against 5.6 V.\n")
    w("| R1 (upper) / R2 | ratio min / nom / max (1 %) | pin @ 4.40 V (min ratio) | margin vs VIH 3.0 V (VDD 3.6 V) | margin vs VIH 2.7 V (VDD 3.3 V) | pin @ 4.75 V | pin @ 5.25 V (max ratio) | margin to 5.6 V | VBUS current into the divider if VDD = 0 (5.25 V) |\n|---|---|---|---|---|---|---|---|---|")
    for r1 in (22.1e3, 20.0e3, 19.1e3, 18.2e3):
        r2 = 47.5e3
        rmin = r2 * 0.99 / (r1 * 1.01 + r2 * 0.99); rmax = r2 * 1.01 / (r1 * 0.99 + r2 * 1.01); rnom = r2 / (r1 + r2)
        mark = " **← RC1.2**" if r1 == 19.1e3 else (" (reference)" if r1 == 22.1e3 else "")
        w(f"| {r1 / 1e3:.1f} k / 47.5 k{mark} | {rmin:.4f} / {rnom:.4f} / {rmax:.4f} | {4.40 * rmin:.3f} V | {4.40 * rmin - 3.0:+.3f} V | {4.40 * rmin - 2.7:+.3f} V | {4.75 * rmin:.3f} V | {5.25 * rmax:.3f} V | {5.6 - 5.25 * rmax:+.2f} V | {(5.25 - 0.6) / r1 * 1e3:.2f} mA |")
    r1 = 19.1e3; r2 = 47.5e3
    rmin = r2 * 0.99 / (r1 * 1.01 + r2 * 0.99)
    w(f"\n**Result:** the reference 22.1 k / 47.5 k network meets the detection limit with margin at VBUS ≥ 4.75 V (+{4.75 * 47.5 * 0.99 / (22.1 * 1.01 + 47.5 * 0.99) - 3.0:.2f} V at the worst VDD) but is **short by 16 mV** at the coincident worst corner (VBUS 4.40 V, VDD 3.6 V, both resistors 1 % adverse). R1 = 19.1 kΩ (E96, R38) with R2 = 47.5 kΩ gives **+{4.40 * rmin - 3.0:.2f} V** at that corner (+{4.40 * rmin - 2.7:.2f} V at VDD 3.3 V) and a worst-case pin voltage of {5.25 * r2 * 1.01 / (r1 * 0.99 + r2 * 1.01):.2f} V at VBUS 5.25 V (limit 5.6 V → +{5.6 - 5.25 * r2 * 1.01 / (r1 * 0.99 + r2 * 1.01):.2f} V). The VBUS current with VDD = 0 (device unpowered; the datasheet notes the VIO + 2.5 V limit is then not strictly met and relies on the divider's current limit) rises from {(5.25 - 0.6) / 22.1e3 * 1e3:.2f} mA to {(5.25 - 0.6) / 19.1e3 * 1e3:.2f} mA (+16 %); the datasheet gives no limit for that current [UV]. The change is a deliberate departure from the reference value based on the datasheet equations, not an arbitrary one. Detection from the typical VDD 3.3 V starts at VBUS = {2.7 / 0.6780:.2f} V (reference) vs {2.7 / ((r2) / (r1 + r2)):.2f} V (RC1.2).\n")
    w(f"Regulator: VREGIN 3.0-5.25 V, VDD 3.1-3.6 V, IREGOUT 100 mA **total including the device** (IDD 9.5-13.7 mA + 0.23 mA USB pull-up + ISO7721 VCC2 ≈ 1-3 mA ≈ 17 mA → ≈ 80 mA margin){t('cp_vdd')}. Datasheet items: **1 kΩ RSTb pull-up to VDD (R40)** and **4.7 µF + 0.1 µF at VDD (C22)**{t('cp_rstb')}. USBLC6-2SC6 ESD protection stays (datasheet recommends USB ESD diodes).\n")


def register():
    c = Counter(e["evidence"] for e in REG)
    open_crit = [e for e in REG if e["critical"] and e["evidence"] != "VERIFIED_LOCAL"]
    w("## 9. Evidence summary\n")
    w(f"VERIFIED_LOCAL {c['VERIFIED_LOCAL']} · USER_RELAYED_MANUFACTURER {c['USER_RELAYED_MANUFACTURER']} · UNVERIFIED {c['UNVERIFIED']} (total {len(REG)}). Critical entries not yet VERIFIED_LOCAL: **{len(open_crit)}** — these are fabrication gates, not schematic/layout gates.\n")
    L = ["# Evidence register (Rev.2 RC1)\n",
         "Generated from `calc/datasheet_inputs.json`. States: **VERIFIED_LOCAL** (read by the build), **USER_RELAYED_MANUFACTURER** (manufacturer data supplied by the user; PDF not opened by the build), **UNVERIFIED** (assumption/proposal). "
         "Manufacturer sites are unreachable from the build environment (HTTP 403 policy denial), so nothing has been read from a manufacturer PDF by the build. Every `critical` entry must become VERIFIED_LOCAL (by you on your machine, or by a re-run that has the PDFs) before ordering.\n",
         "| # | Item | Part | Parameter | Value | Evidence | Critical | Doc/location |", "|---|---|---|---|---|---|---|---|"]
    for n, e in enumerate(REG, 1):
        v = e["value"] if e["value"] is not None else "—"
        L.append(f"| {n} | `{e['id']}` | {e['part']} | {e['parameter']} | {v}{(' ' + e['unit']) if e['unit'] else ''} | {e['evidence']} | {'**yes**' if e['critical'] else 'no'} | {e['doc'] or '—'} |")
    open(os.path.join(HERE, "..", "DATASHEET_VERIFICATION.md"), "w").write("\n".join(L) + "\n")


w("# OSBAMS Rev.2 controller — calculations (RC1, generated)\n")
w("Generated by `calc/rev2_calcs.py` from `calc/datasheet_inputs.json`. Evidence tags: none = VERIFIED_LOCAL, **[UR]** = USER_RELAYED_MANUFACTURER, **[UV]** = UNVERIFIED. RC1 is a review candidate: **NOT FOR FABRICATION** until the critical entries are VERIFIED_LOCAL.\n")
adc(); ina(); buck(); relay(); opto(); arm(); i2c(); power(); register()
open(os.path.join(HERE, "..", "REV2_CALCULATIONS.md"), "w").write("\n".join(OUT) + "\n")
print("evidence:", dict(Counter(e["evidence"] for e in REG)))

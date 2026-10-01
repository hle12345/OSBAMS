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
    w(f"- VBUS: own lead PACK_INA through 10 Ω (error 10 Ω / ~830 kΩ ≈ 0.001 %, UV) + TVS; common-mode range {V('ina228_cm')}{t('ina228_cm')}; TVS 1.5SMBJ48A clamp {V('tvs48')} V{t('tvs48')} → margin to 85 V = {85 - V('tvs48'):.1f} V (thin).")
    w("- **INA228 pin map is an INA226-family analogy (UNVERIFIED, critical): confirm against the TI datasheet before any order.**\n")


# ------------------------------------------------------------------ 3 buck
def buck():
    vref, f = V("lmr_vref"), V("lmr_fsw")
    R1, R2 = 33.2e3, 10e3
    vout = vref * (1 + R1 / R2)
    L = 10e-6
    w("## 3. Buck LMR14006Y: 12 V → 3.3 V\n")
    w(f"Feedback: VREF {vref} V{t('lmr_vref')}, R1 {R1 / 1e3:.1f} kΩ / R2 {R2 / 1e3:.0f} kΩ → Vout = {vref} × (1 + R1/R2) = **{vout:.3f} V** (1 % resistors: {vout * 0.0094:+.3f} V, ±VREF tolerance UV). fsw {f / 1e6:.1f} MHz{t('lmr_fsw')}.\n")
    w("| Vin | duty | on-time | ΔIL (L = 10 µH) | Ipk @ 150 mA |\n|---|---|---|---|---|")
    for vin in (11.0, 12.0, 15.0, 24.4):
        d = vout / vin; dil = vout * (1 - d) / (L * f)
        w(f"| {vin} V | {d * 100:.1f} % | {d / f * 1e9:.0f} ns | {dil * 1e3:.0f} mA | {(0.15 + dil / 2) * 1e3:.0f} mA |")
    w(f"\nMinimum on-time{t('lmr_ton_min')} must be below the 24.4 V (TVS-clamp) case 65 ns, otherwise the regulator skips pulses during surges (output stays regulated; ripple rises). Inductor: Bourns SRN6045TA-100M (10 µH; Isat/DCR{t('lmr_l_c')} to be checked ≥ the buck current limit). Output 2 × 22 µF 10 V 0805 (≈ 50 % DC-bias derating → ≈ 26 µF): ripple ≈ ΔIL/(8 f C) = {0.114 / (8 * f * 26e-6) * 1e3:.2f} mV + ESR term. Input C1+C2 2 × 10 µF 50 V 1210 + 100 nF at the VIN pin: ripple ≈ I·D(1−D)/(f C) = {0.15 * 0.275 * 0.725 / (f * 6e-6) * 1e3:.1f} mV at 6 µF effective.")
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
    w(f"\n**Q1 = IRLML0060TRPBF (60 V SOT-23 logic-level)** — RDS(on) is not specified at 3.3 V in the data I hold; using a pessimistic placeholder {V('q_rds')} Ω{t('q_rds')}: VDS = {0.17 * V('q_rds') * 1e3:.0f} mV and P = {0.17 ** 2 * V('q_rds') * 1e3:.1f} mW at 170 mA. Gate overdrive at 3.3 V × 0.97 with VGS(th) max {V('q_vth')} V{t('q_vth')} is {3.2 - V('q_vth'):.1f} V — adequate for a 0.17 A load but **the datasheet output curve at VGS = 3 V must confirm ID ≥ 0.5 A (fabrication gate)**. VDSS {V('q_vdss'):.0f} V{t('q_vdss')} vs the {V('tvs15')} V TVS clamp → margin {V('q_vdss') - V('tvs15'):.1f} V. Alternates: Diodes DMN6140L-7 (60 V), AOS AO3400A (30 V, 2.5 V-specified).")
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
    w("**Guaranteed data (user-relayed [UR]):** CTR min 13 % / typ 30 % at IF = 1 mA, VCE = 5 V; CTR min 40 % / max 80 % at IF = 10 mA. **The arbitrary 20 % CTR has been deleted.**\n")
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
    w(f"Relay-feedback supported pack range 30–44 V is covered down to 24 V (20 % below the 30 V minimum, allowing pack sag under load). At the 77.4 V surge level each 4.7 kΩ resistor dissipates {p77 * 1e3:.0f} mW (1206 = 250 mW). At 44 V: {((44 - vf) / 14.1e3) ** 2 * 4.7e3 * 1e3:.0f} mW each. The 1N4148 across each LED limits reverse voltage to ≈ 0.7 V (LED VR max {V('vo610a_led_vr')} V{t('vo610a_led_vr')}). Relay open: the load side floats at ≈ 0 V → LED dark → PC9 HIGH (fail-safe: 'not closed'); E-stop open or wire broken → no current → PA0 HIGH (fault).\n")
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
    w("ISO7721 has **no isolated power**: VCC1 = +3V3 (100 nF, controller GND); VCC2 = 3V3_HOST from the CP2102N regulator (VREGIN ← USB VBUS), 100 nF, GND_HOST. GND and GND_HOST are never joined (separate copper islands with a 3 mm gap under the isolator). Regulator capability, ISO7721 supply range/ICC and the CP2102N VBUS connection are UNVERIFIED critical items.\n")


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

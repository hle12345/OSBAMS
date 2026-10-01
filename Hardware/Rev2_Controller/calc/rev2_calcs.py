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



def tvs_vs_ina():
    """1.5SMBJ48A clamp voltage depends on the surge current; INA228 IN+/IN-/VBUS abs max is 85 V."""
    v1, i1 = V("tvs48"), V("tvs48_ipp")                 # 10/1000 us rating point
    v2, i2 = V("tvs48_820"), 97.0                        # 8/20 us rating point
    rd = (v2 - v1) / (i2 - i1)
    i85 = i1 + (85.0 - v1) / rd
    w("### 2b. 1.5SMBJ48A (D5/D6/D7) vs INA228 85 V absolute maximum\n")
    w(f"Manufacturer points{t('tvs48')}{t('tvs48_820')}: VRWM 48 V, VBR 53.3-58.9 V; **VC ≤ {v1} V at {i1} A (10/1000 µs)** and **VC ≤ {v2} V at {i2:.0f} A (8/20 µs)**. INA228 IN+/IN−/VBUS absolute maximum {V('ina228_cm')}{t('ina228_cm')}. '77.4 V < 85 V' therefore holds only up to the 19.4 A rating point; at the 8/20 µs rating point the clamp ({v2} V) is **{v2 - 85:.1f} V above** the INA228 limit.\n")
    w(f"Estimate of the clamp curve (straight line through the two rating points — different waveforms, so an engineering estimate, NOT a datasheet curve [UV]): dynamic resistance ≈ {rd * 1e3:.0f} mΩ → VC = 85 V at **I ≈ {i85:.0f} A**. Below ≈ {i85:.0f} A the clamp stays under 85 V; above it the INA228 pin rating is exceeded.\n")
    w("| TVS current | VC (estimate; ≤ 77.4 V up to 19.4 A is a rating) | margin to 85 V |\n|---|---|---|")
    for i in (1, 5, 10, 15, 19.4, 30, 44.8, 60, 97):
        vc = min(v1, v1 - 0.0) if i <= i1 else v1 + rd * (i - i1)
        w(f"| {i} A | {'≤ ' if i <= i1 else '≈ '}{vc:.1f} V | {85 - vc:+.1f} V |")
    w("\n**Credible-transient bound (assumptions [UV], to be signed off by the project owner):**")
    w("1. *Steady state / pack ≤ 44 V:* VRWM 48 V > 44 V and VBR min 53.3 V > 44 V → no conduction, leakage only. PASS.")
    w("2. *Interrupting load current with the pack-side wiring inductance (K1 opening, 15 A fuse clearing at its rating):* the TVS can be asked to carry at most the interrupted current, ≤ 10 A operating ceiling (≤ 18.5 A firmware hard trip, ≤ 15 A fuse rating) < 19.4 A → VC ≤ 77.4 V → margin ≥ 7.6 V. PASS under this bound.")
    w("3. *Sense-harness hot-plug onto a live 44 V pack:* the VBUS path (10 Ω + 100 nF with 2 µH of harness inductance, ζ ≈ 1.1) is overdamped. The IN± Kelvin paths have only 10 Ω in front of the pins and a differential (not common-mode) 100 nF, so they are **underdamped** (TVS capacitance not read [UV]); ringing up to ≈ 2 × 44 V is possible and is clipped by D5/D6 (VC ≤ 77.4 V for the few-ampere ring currents). PASS as an estimate; not simulated — confirm on the bench with a scope on IN+/IN− during harness hot-plug.")
    w(f"4. *Fast high-current surges (ESD/lightning class, hard shorts interrupted by the fuse, ≥ {i85:.0f} A into the TVS):* the clamp can reach ≈ {v2} V and the INA228 pins exceed 85 V → **NOT protected.** This is outside the intended bench environment; if the owner wants it covered, add a series resistor (e.g. 47-100 Ω, pulse-rated 1206) *upstream of the TVS* on PACK_INA (DC error ≈ 100 Ω / 830 kΩ ≈ 0.012 %) and a higher-rated/two-stage clamp on the Kelvin lines — **not applied in RC1** (no electrical change made; decision recorded as an open sign-off item).")
    w("Do not substitute a lower-voltage TVS without re-checking standoff/leakage against the 44 V ceiling (a 40 V-class part would conduct near a charged 10S pack).\n")

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
    w(f"**CP2102N (Silicon Labs datasheet rev. 1.5, read locally{t('cp_vbus_div')}):** the bus-powered reference divides VBUS with 22.1 kΩ (upper) and 47.5 kΩ (lower) → R38/R39. VBUS-pin input-high threshold VIH = VIO − 0.6 V, absolute maximum VIO + 2.5 V (5.8 V when VIO > 3.3 V); VIO = VDD = 3V3_HOST (3.1-3.6 V):\n")
    w("| VBUS_USB | VBUS pin | divider current | vs VIH (VDD = 3.3 V → 2.7 V; VDD = 3.6 V → 3.0 V) |\n|---|---|---|---|")
    for v in (4.4, 4.75, 5.0, 5.25):
        pin = v * 47.5 / 69.6
        w(f"| {v} V | {pin:.2f} V | {v / 69.6e3 * 1e6:.0f} µA | {'OK' if pin >= 3.0 else 'FAIL'} (margin {pin - 3.0:+.2f} V at the worst VDD) |")
    w(f"\nVBUS is detected for VBUS_USB ≥ {2.7 / 0.6825:.2f} V (VDD 3.3 V) / {3.0 / 0.6825:.2f} V (VDD 3.6 V worst case — equal to the 4.40 V USB minimum, no margin there; the typical case has ≈ 0.4 V margin); the pin never exceeds {5.25 * 47.5 / 69.6:.2f} V (abs max ≥ 5.8 V). Regulator: VREGIN 3.0-5.25 V, VDD 3.1-3.6 V, IREGOUT 100 mA **total including the device** (IDD 9.5-13.7 mA + 0.23 mA USB pull-up + ISO7721 VCC2 ≈ 1-3 mA ≈ 17 mA → ≈ 80 mA margin){t('cp_vdd')}. Datasheet items added in RC1.1: **1 kΩ RSTb pull-up to VDD (R40)** and **4.7 µF + 0.1 µF at VDD (C22 raised from 1 µF)**{t('cp_rstb')}. USBLC6-2SC6 ESD protection stays (datasheet recommends USB ESD diodes).\n")


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

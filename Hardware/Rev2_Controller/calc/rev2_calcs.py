#!/usr/bin/env python3
"""OSBAMS Rev.2 controller calculations -> ../REV2_CALCULATIONS.md.

Every datasheet-dependent number comes from datasheet_inputs.json (verified=false until a manufacturer PDF is read).
The report ends with the schematic-freeze status: BLOCKED while any input is unverified.
Run:  python3 Hardware/Rev2_Controller/calc/rev2_calcs.py
"""
import itertools, json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
INP = json.load(open(os.path.join(HERE, "datasheet_inputs.json")))["inputs"]
V = lambda k: INP[k]["value"]
OUT = []
w = OUT.append


def tag(k):
    return "" if INP[k]["verified"] else " ⚠[unverified]"


def unverified():
    return [k for k, v in INP.items() if not v["verified"]]


# ---------------------------------------------------------------- 1. ADC divider
def adc():
    R1 = R2 = 75e3; R3 = 10e3; Rtot = R1 + R2 + R3; ratio = Rtot / R3
    w("## 1. Independent ADC channel  PACK_ADC → 75 k → 75 k → ADC_TAP → 10 k → GND ; 1 k series ; 100 nF at the pin\n")
    w("| Vpack | ADC_TAP (3.3 V full scale) |\n|---|---|")
    for vp in (30, 36, 42, 44, 48, 77.4):
        w(f"| {vp} V | {vp / ratio:.3f} V |")
    w(f"\nRatio {ratio:.0f}:1 · LSB(12 bit, 3.3 V) = {3.3 / 4096 * 1e3:.3f} mV → {3.3 / 4096 * ratio * 1e3:.1f} mV per LSB at the pack · full scale {3.3 * ratio:.1f} V.")
    w(f"Divider current at 44 V {44 / Rtot * 1e6:.0f} µA, {44 ** 2 / Rtot * 1e3:.1f} mW total, each 75 kΩ sees {44 * 75e3 / Rtot:.1f} V and {(44 * 75e3 / Rtot) ** 2 / 75e3 * 1e3:.1f} mW (0805 thin film: fine). "
      f"Source impedance (tap ∥ 1 k series) ≈ {R3 * (R1 + R2) / Rtot / 1e3 + 1:.2f} kΩ, τ with 100 nF ≈ {(R3 * (R1 + R2) / Rtot + 1e3) * 100e-9 * 1e3:.2f} ms.\n")
    # --- error decomposition (kept separate on purpose)
    def worst_ratio(tol):
        nom = R3 / Rtot; m = 0
        for a, b, c in itertools.product((1 - tol, 1 + tol), repeat=3):
            m = max(m, abs(R3 * c / (R1 * a + R2 * b + R3 * c) / nom - 1))
        return m
    div_tol = worst_ratio(0.001)
    tcr = 50e-6 * 40            # 25 ppm/K each, worst differential, 40 K excursion
    leak = 0.0004               # <1 mV clamp leakage (placeholder, datasheet needed)
    adc_tue = V("stm32_adc_tue_lsb") / 4096
    vref_uncorr = 0.02          # 3V3 rail tolerance assumed ±2 % (Chat draft) — reference error
    vref_corr = V("stm32_vrefint_tol")
    w("**Error budget — three separate groups (do not mix them):**\n")
    w("| Group | Item | Worst case |\n|---|---|---|")
    w(f"| A. Divider (resistors only) | 0.1 % tolerance, all three resistors | ±{div_tol * 100:.2f} % |")
    w(f"| A. Divider | tempco 25 ppm/K, 40 K excursion | ±{tcr * 100:.2f} % |")
    w(f"| A. Divider | clamp leakage (placeholder{tag('stm32_pa1_io_type')}) | ±{leak * 100:.2f} % |")
    divider = div_tol + tcr + leak
    w(f"| **A. subtotal (divider)** | | **±{divider * 100:.2f} %** |")
    w(f"| B. ADC | TUE {V('stm32_adc_tue_lsb')} LSB 12-bit{tag('stm32_adc_tue_lsb')} | ±{adc_tue * 100:.2f} % |")
    w(f"| C. Reference | VDDA = 3.3 V ± 2 % (assumption, uncorrected) | ±{vref_uncorr * 100:.2f} % |")
    w(f"| C. Reference | after VREFINT correction{tag('stm32_vrefint_tol')} | ±{vref_corr * 100:.2f} % |")
    tot_u = divider + adc_tue + vref_uncorr; tot_c = divider + adc_tue + vref_corr
    rss = lambda *x: math.sqrt(sum(i * i for i in x))
    w(f"\nTotal worst case uncorrected ±{tot_u * 100:.2f} % (≈ ±{tot_u * 44:.2f} V at 44 V); with VREFINT correction ±{tot_c * 100:.2f} % (≈ ±{tot_c * 44:.2f} V). RSS corrected ±{rss(div_tol, tcr, leak, adc_tue, vref_corr) * 100:.2f} %.")
    w(f"**Only ±{divider * 100:.2f} % of the uncorrected figure comes from the divider; the rest is the 3V3 reference, which the firmware removes by measuring VREFINT.** Adequate for a plausibility cross-check against the INA228 (firmware agreement window 1.5 V); not metrology.\n")
    # --- back-feed
    w("### 1.1 PACK+ present, controller unpowered (back-feed analysis)\n")
    w("Decision: **no upper clamp to 3V3 on PA1.** Protection is 1 kΩ series + a clamp **to GND only** (negative excursions) — so the external circuit offers no path into the 3V3 rail. "
      "Whether the pin's own structure has a diode to VDD/VDDA is a datasheet item (`stm32_pa1_io_type`, unverified). If it does, the divider (≤ 0.29 mA) could lift the rail; the guard is a bleeder across 3V3A:\n")
    w("| Bleeder | max rail rise = I·R | vs POR min |\n|---|---|---|")
    ib = (44 - 0.6) / 150e3
    for rb in (None, 6.8e3, 3.3e3, 2.2e3):
        if rb is None:
            w(f"| none | up to the diode-clamped node voltage (≈ 2.75 V) → **can reach POR** ⚠ | {V('stm32_por_min')} V{tag('stm32_por_min')} |")
        else:
            w(f"| {rb / 1e3:.1f} kΩ ({3.3 / rb * 1e3:.2f} mA from 3V3) | {ib * rb:.2f} V | {V('stm32_por_min')} V |")
    w(f"\nBack-feed current ≤ {ib * 1e3:.2f} mA at 44 V. Baseline: bleeder footprint (3.3 kΩ) **DNP**; fit it if the datasheet shows an upper protection diode on PA1. "
      "Overvoltage: 1.5SMBJ48A clamp 77.4 V → tap 4.84 V (needs the pin tolerance from the datasheet); reverse pack −44 V → GND clamp holds the pin ≥ −0.3 V with ≤ 0.3 mA.\n")


# ---------------------------------------------------------------- 2. INA228
def ina():
    Rs = 2.5e-3
    w("## 2. INA228 + Bourns RSA-20-50 (2.5 mΩ, 20 A / 50 mV)  — equations " + ("⚠[unverified]" if not INP["ina228_shunt_cal_eq"]["verified"] else "") + "\n")
    w("| I | Vshunt | P shunt |\n|---|---|---|")
    for i in (1, 7.14, 10, 15, 18.5, 20):
        w(f"| {i} A | {i * Rs * 1e3:.2f} mV | {i * i * Rs:.3f} W |")
    w("\nADCRANGE=0 (±163.84 mV, 312.5 nV/LSB → 125 µA/LSB native) is kept: ADCRANGE=1 (±40.96 mV) saturates at 16.38 A and would hide the 18.5 A firmware trip (46.25 mV).")
    for imax in (20.0, 30.0):
        cl = imax / 2 ** 19; cal = 13107.2e6 * cl * Rs
        w(f"- IMAX {imax:.0f} A: CURRENT_LSB = {cl * 1e6:.3f} µA, **SHUNT_CAL = {cal:.0f}** (limit 32767){'  ← chosen (20 A shunt scale)' if imax == 20 else '  (old firmware app_config.h scale — to be changed)'}")
    vos = V("ina228_vos_max")
    w(f"- Offset {vos * 1e6:.1f} µV{tag('ina228_vos_max')} → {vos / Rs * 1e3:.2f} mA = {vos / Rs / 10 * 100:.4f} % of 10 A.")
    w(f"- 2 × 10 Ω + 100 nF differential: fc = {1 / (2 * math.pi * 20 * 100e-9) / 1e3:.0f} kHz; bias {V('ina228_bias_current') * 1e9:.1f} nA{tag('ina228_bias_current')} × 10 Ω = {V('ina228_bias_current') * 10 * 1e9:.0f} nV.")
    w(f"- TVS 1.5SMBJ48A Vc ≈ {V('tvs_1p5smbj48a_vc')} V{tag('tvs_1p5smbj48a_vc')} vs abs max {V('ina228_abs_max_in')} V{tag('ina228_abs_max_in')} → margin {V('ina228_abs_max_in') - V('tvs_1p5smbj48a_vc'):.1f} V (thin; verify the clamp at the real surge current).")
    w("- RSA-20-50 (reported, ⚠ unverified): ±0.25 % tolerance, ±15 ppm/°C TCR, continuous ≤ 2/3 of rating = 13.3 A (> our 10 A ceiling). Shunt self-heating at 10 A is 0.25 W → ΔR/R ≈ 15 ppm/K × rise; calibration against the EDU34450A remains the accuracy basis.")
    w("- Sense wiring: IN+ = relay load side (RELAY_OUT), IN− = shunt load-side Kelvin; **VBUS from PACK_INA (upstream of K1)** so open-circuit voltage is read with the relay open; separate PACK_ADC lead for the independent channel; only GND_SENSE bonds logic ground to the pack.\n")


# ---------------------------------------------------------------- 3. Relay driver
def relay():
    R = V("relay_coil_ohm")
    w("## 3. Relay driver (Durakool DG57CM-5021-76-1012-R) — coil data " + ("⚠[unverified]" if not INP["relay_coil_ohm"]["verified"] else "") + "\n")
    w("Contact rating evidence (reported, ⚠ not read here): DC1 loads 80 A @12 V, 60 A @36 V, 50 A @48 V; our envelope is ≤ 44 V, ≤ 10 A (15 A fault) → ≥ 5× margin on the reported figures. To record against the datasheet page when the PDF is available.\n")
    w("| Coil V | I | P |\n|---|---|---|")
    for v in (10.5, 11.55, 12.0, 13.8, 15.0):
        w(f"| {v} V | {v / R * 1e3:.0f} mA | {v * v / R:.2f} W |")
    w("\nXDR-75-12 is adjustable (to ~15 V): **set and verify 12.0 V** (2.5 W in the coil at 15 V).")
    w("**Q1 = AOS AO3400A (SOT-23, 30 V N-FET) — chosen by you; RDS(on) 48 mΩ max at VGS = 2.5 V is reported, not read here" + tag("mosfet_candidate") + ".**")
    rds = 0.048
    for v in (11.55, 12.0, 15.0):
        i = v / R
        w(f"- coil {v} V: I = {i * 1e3:.0f} mA → VDS(on) = {i * rds * 1e3:.1f} mV, P = {i * i * rds * 1e3:.2f} mW (RDS(on) = 48 mΩ at 2.5 V; the 3.3 V drive is above the specified point)")
    w("- Gate network: 220 Ω series, 10 kΩ pull-down → relay OFF when the MCU is in reset/unpowered/Hi-Z (gate leakage × 10 kΩ ≪ VGS(th); VGS(th) still to be read).")
    w(f"- **VDS margin (30 V part):** diode flyback clamps COIL_SW at ≈ +12…15 V + 0.7 V; the +12V surge clamp is the SMBJ15A at {V('tvs_smbj15a_vc')} V{tag('tvs_smbj15a_vc')} → worst-case drain stress ≈ 24.4 V vs 30 V (margin ≈ 5.6 V, thin: re-check with the real clamp/leakage and any inductive kick that bypasses the diode).")
    w("- **Fast-release 27 V TVS is REJECTED for this MOSFET:** coil rail + TVS = 12 + 27 = 39 V (+ diode) > 30 V VDSS. Baseline is the plain diode; the DNP link/TVS footprint stays but a fast-release clamp is allowed only after a new VDS transient analysis proves margin (e.g. a lower-voltage clamp or a different MOSFET).")
    L = V("relay_coil_L"); I = 12.0 / R
    w(f"- Flyback energy ½LI² = {0.5 * L * I * I * 1e3:.2f} mJ (L {L} H{tag('relay_coil_L')}); diode-only decay τ = L/R = {L / R * 1e3:.1f} ms. Baseline: plain diode (no fast-release clamp, see above).\n")


# ---------------------------------------------------------------- 4. optocoupler stages
def opto():
    ctr = V("vo610a_ctr_min_IF_curve") * V("vo610a_ctr_temp_derate") * V("vo610a_ctr_aging_derate")
    vf, vce = V("vo610a_vf_at_IF"), V("vo610a_vcesat")
    w("## 4. VO610A-1 stages — design-to-guaranteed method (NOT frozen)\n")
    w("The datasheet guarantees CTR_min only at one LED current; the stage must still saturate at the real IF after temperature and aging. Method:\n")
    w("1. CTR_eff = CTR_min(IF curve) × temp derate × aging derate  →  "
      f"{V('vo610a_ctr_min_IF_curve'):.2f} × {V('vo610a_ctr_temp_derate'):.2f} × {V('vo610a_ctr_aging_derate'):.2f} = **{ctr:.3f}** (all three ⚠[unverified], placeholders; the 40 % @ 10 mA bin figure is {V('vo610a_ctr_min_10mA'):.2f}{tag('vo610a_ctr_min_10mA')}).")
    w("2. Required: IF · CTR_eff ≥ 2 × I_pullup_needed  (2× margin), I_pullup_needed = (3.3 − VCEsat)/Rpu.")
    w("3. Evaluate over the whole supply range; reject any network that does not meet step 2 at the minimum voltage.\n")

    def row(name, vmin, vmax, rled, rpu, vlist):
        ipu = (3.3 - vce) / rpu
        w(f"**{name}** — R_LED {rled / 1e3:.1f} kΩ, pull-up {rpu / 1e3:.0f} kΩ (needs {ipu * 1e3:.3f} mA)\n")
        w("| V | IF | IC available (CTR_eff) | margin | R dissipation |\n|---|---|---|---|---|")
        ok_min = None
        for v in vlist:
            iff = (v - vf) / rled; icav = iff * ctr; mg = icav / ipu
            w(f"| {v} V | {iff * 1e3:.2f} mA | {icav * 1e3:.3f} mA | ×{mg:.1f} | {iff * iff * rled * 1e3:.0f} mW |")
        vreq = vf + 2 * ipu / ctr * rled
        w(f"\nMinimum voltage for 2× margin: **{vreq:.1f} V** (required ≤ {vmin} V → {'PASS' if vreq <= vmin else 'FAIL (placeholder CTR)'}).\n")
    row("RELAY_FB, Chat draft 4×3.6 k + 22 k", 28, 44, 14.4e3, 22e3, (24, 28, 30, 36, 44, 77.4))
    row("RELAY_FB, Code draft 2×6.8 k + 33 k", 28, 44, 13.6e3, 33e3, (24, 28, 30, 36, 44, 77.4))
    row("ESTOP_SENSE, Chat draft 5.6 k + 22 k", 10.5, 15, 5.6e3, 22e3, (10.5, 11.55, 12, 15))
    row("ESTOP_SENSE, Code draft 5.1 k + 33 k", 10.5, 15, 5.1e3, 33e3, (10.5, 11.55, 12, 15))
    w(f"Both drafts' networks are *candidate sizing only*: they pass or fail purely on placeholder derates. **Frozen resistor values come from the official VO610A-1 datasheet CTR-vs-IF data**; no assumed 20 % CTR may remain in the frozen schematic.\n"
      f"Single-fault and surge notes: two or more series resistors on the LED so one short cannot overdrive it; 1N4148 antiparallel across the LED limits reverse voltage (LED VR max {V('vo610a_led_vr_max')} V{tag('vo610a_led_vr_max')}); at the 77.4 V TVS clamp IF ≈ {(77.4 - vf) / 14.4e3 * 1e3:.1f} mA and each of four 3.6 k resistors dissipates {((77.4 - vf) / 14.4e3) ** 2 * 3.6e3 * 1e3:.0f} mW (0805 = 125 mW — marginal, check pulse rating).\n")


# ---------------------------------------------------------------- 5. ARM
def arm():
    vih = V("stm32_vih_frac") * 3.3
    w("## 5. ARM_SENSE divider (status only)  COIL_V → 270 k → ARM_DIV → 100 k → GND ; 1 k ; 100 nF\n")
    w("| COIL_V | ARM_DIV |\n|---|---|")
    for v in (0, 10.5, 11.55, 12, 13.8, 15):
        w(f"| {v} V | {v * 100 / 370:.2f} V |")
    w(f"\nVIH = {vih:.2f} V{tag('stm32_vih_frac')} → thresholds satisfied from 10.5 V up ({10.5 * 100 / 370:.2f} V); at 15 V the node is 4.05 V. **No clamp to 3V3** (same back-feed argument as §1.1): protection is 1 kΩ + 100 nF and **PC10 must be a 5 V-tolerant pin** (`stm32_pa1_io_type`, unverified); if it is not, the ratio changes to ≤ 0.22 so that 15 V stays ≤ 3.3 V. HIGH = ARM closed with E-stop closed; E-stop tripped → COIL_V = 0 → ARM unknown. Sensing only, no authority.\n")


# ---------------------------------------------------------------- 6. I2C
def i2c():
    w("## 6. I²C buses (rise time tr = 0.8473·R·C; standard-mode limit 1000 ns)\n")
    w("| Bus | Rpu | Cb | tr | note |\n|---|---|---|---|---|")
    for bus, rpu, cb, nt in (("I2C1 INA228 (board only)", 4.7e3, 50e-12, "400 kHz budget tr ≤ 300 ns → use 2.2 kΩ if Cb > 50 pF"), ("I2C2 TC74, 1 m cable", 4.7e3, 155e-12, "≈ 30 pF board + 100 pF cable + TC74/ESD"), ("I2C2 TC74, 1.5 m", 4.7e3, 215e-12, "go/no-go limit"), ("I2C2 TC74, 2 m", 2.2e3, 285e-12, "2.2 kΩ option"), ("I2C2 TC74, 3 m", 2.2e3, 400e-12, "beyond limit")):
        w(f"| {bus} | {rpu / 1e3:.1f} k | {cb * 1e12:.0f} pF | {0.8473 * rpu * cb * 1e9:.0f} ns | {nt} |")
    w("\nTC74 stays on its own I²C2 (PB10/PB11) at ≤ 100 kHz; INA228 on I²C1 (PB8/PB9). Limit: ≤ 1.5 m of shielded twisted pair; beyond that or if V1 fails, stop and propose another interface (DS18B20/NTC are contingency only, not in the baseline schematic).\n")


# ---------------------------------------------------------------- 7. power tree
def power():
    w("## 6b. ISO7721 supplies (reported: no integrated isolated power)\n")
    w("VCC1 = 3V3 (controller side). VCC2 must be supplied from the host side: the CP2102N's 3.3 V regulator output (VREGIN from USB VBUS) feeds both the bridge VDD and ISO7721 VCC2; its output-current capability vs the isolator's ICC2 plus the bridge's own load, and both supply ranges, are to be verified from the CP2102N and ISO7721 datasheets (`cp2102n_package`, `isolator_iso7721`). Each side gets 100 nF at the pins; no common ground between sides.\n")
    w("## 7. Power tree (wide-input buck directly to 3.3 V; **no 5 V rail**)\n")
    w("XDR-75-12 (set to 12.0 V) → J1 → F1 1 A fast → reverse-protection Schottky → SMBJ15A → +12V. +12V feeds (a) the coil chain E-stop → ARM → coil → Q1, (b) the buck → 3V3 → ferrite → 3V3A.\n")
    loads = {"STM32L476 @ 80 MHz + peripherals": 20.0, "INA228": 1.0, "pull-ups/sense/ISO7721 MCU side": 11.0, "TC74 probe": 0.5, "2 status LEDs": 6.0}
    tot = sum(loads.values())
    w("| 3V3 load | mA (typical, ⚠ datasheet values not verified) |\n|---|---|")
    for k, v in loads.items():
        w(f"| {k} | {v} |")
    w(f"| **total** | **{tot:.1f} (design for 150 mA)** |")
    R = V("relay_coil_ohm")
    for eff in (0.85, 0.80):
        iin = 0.150 * 3.3 / eff / 12.0
        w(f"\nBuck at 150 mA, η {eff:.2f}: input {iin * 1e3:.0f} mA, loss {0.150 * 3.3 * (1 / eff - 1) * 1e3:.0f} mW")
    w(f"\n12 V rail: coil {12 / R * 1e3:.0f} mA + buck ≈ 45 mA + sense 4 mA ≈ {(12 / R + 0.045 + 0.004) * 1e3:.0f} mA of a 6.24 A supply; F1 1 A. Series Schottky drop ≈ 0.4 V → coil at ≈ 11.6 V.")
    w(f"Surge margin: SMBJ15A clamp {V('tvs_smbj15a_vc')} V{tag('tvs_smbj15a_vc')} vs buck VIN: LMR14006Y is a 4–40 V part (reported) → ≈ 15.6 V margin over the 24.4 V clamp. TPS54202 is dropped. "
      "Buck output → LC → 3V3; 3V3A = ferrite + 1 µF + 100 nF (VDDA, INA228); ripple at bring-up, not by calculation.\n")


# ---------------------------------------------------------------- status
def status():
    u = unverified()
    w("## 8. Schematic-freeze status\n")
    w(f"**{'BLOCKED' if u else 'READY'} — {len(u)} of {len(INP)} datasheet inputs unverified.**\n")
    if u:
        w("Unverified inputs (see `DATASHEET_VERIFICATION.md` for what to read and where it is used):\n")
        w(", ".join(f"`{k}`" for k in u))
    w("\n*Generated by `calc/rev2_calcs.py` from `calc/datasheet_inputs.json`; re-run after changing either.*")


w("# OSBAMS Rev.2 controller — calculations (design phase, merged)\n")
w("All results are generated. ⚠[unverified] marks a datasheet-dependent input that is still a placeholder. **Nothing in this file is frozen until its inputs are verified** (§8).\n")
adc(); ina(); relay(); opto(); arm(); i2c(); power(); status()
open(os.path.join(HERE, "..", "REV2_CALCULATIONS.md"), "w").write("\n".join(OUT) + "\n")
print("unverified:", len(unverified()), "of", len(INP))


# ---------------------------------------------------------------- datasheet worklist
def worklist():
    L = ["# Datasheet verification worklist (Rev.2 controller)\n",
         "Generated from `calc/datasheet_inputs.json`. **This sandbox cannot reach any manufacturer site** (st.com, ti.com, vishay.com … return HTTP 403 from the egress policy; distributor and datasheet-mirror sites are likewise unreachable), "
         "so no value below is verified and no citation can honestly be written. Values you relayed from the manufacturer documents are recorded in the “Reported” column but stay unverified until the PDF itself is read. To close an item: upload the manufacturer PDF (or its relevant pages), the value is read, `verified` is set to true with `doc` = document number + table/figure/page, and the calculations are re-run.\n",
         "The schematic is not created until the **critical** items are verified (`tests/test_pcb_release_gates.py` enforces: no `.kicad_sch` in `Hardware/Rev2_Controller/` while any `critical` input is unverified).\n",
         "| # | Input | Critical | Part | What to read | Reported by you (unverified) | Verified | Document / location |", "|---|---|---|---|---|---|---|---|"]
    for n, (k, v) in enumerate(INP.items(), 1):
        L.append(f"| {n} | `{k}` | {'**yes**' if v.get('critical') else 'no'} | {v['part']} | {v['need']} | {'; '.join(r['value'] for r in v.get('reported', [])) or '—'} | {'YES' if v['verified'] else 'no'} | {v['doc'] or '—'} |")
    L.append("\n## Checked from the installed KiCad 7 libraries (not datasheets)\n")
    L.append("- STM32L476RGTx: symbol + `LQFP-64_10x10mm_P0.5mm` footprint present; LQFP-64 pin numbers for every signal in the pin table read from the library (PA0=14, PA1=15, PA2=16, PA3=17, PA5=21, PA6=22, PA9=42, PA10=43, PA13=46, PA14=49, PB0=26, PB3=55, PB8=61, PB9=62, PB10=29, PB11=30, PC8=39, PC9=40, PC10=51, NRST=7, VBAT=1, VDDA=13, VSSA=12, VDDUSB=48).")
    L.append("- **Missing symbols (must be drawn from datasheet pin tables): INA228, ISO7721, VO610A, LMR14006, TC74.** Present: TPS54202DDC, BAT54S, D_TVS, USBLC6-2*, AP2112K (not used).")
    L.append("- CP2102N: the library symbol is QFN20 only; the BOM candidate is QFN24 → package decision needed.")
    L.append("- Footprints present: LQFP-64, VSSOP-10, SOIC-8, DIP-4_W7.62, QFN-24/QFN-20 variants, KK-254, JST PH, USB4105. **EB21A-02-C has no library footprint** (draw from the Adam Tech drawing).")
    open(os.path.join(HERE, "..", "DATASHEET_VERIFICATION.md"), "w").write("\n".join(L) + "\n")


worklist()

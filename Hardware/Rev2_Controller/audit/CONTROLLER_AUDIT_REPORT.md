# OSBAMS Rev.2 controller — footprint and protection audit (read-only)

Scope: `claude/gallant-ride-tdr3hw` (RC1.2, read via `git archive`; nothing was committed to either branch). Evidence = the uploaded manufacturer files plus facts relayed in the brief. The Pi/display branch is untouched.

## 1. What the uploaded datasheets now verify
| Item | Result | Replaces |
|---|---|---|
| INA228 absolute max (TI SLYS021A, p.3) | VBUS and VCM −0.3…85 V; **differential (IN+)−(IN−) ±40 V**; input current into any pin 5 mA; HBM ±2 kV; CDM ±1 kV | `ina228_diff_max` (UNVERIFIED) → **VERIFIED** |
| INA228 electrical (p.5) | **Z_VBUS 0.8 / 1 / 1.2 MΩ**; I_B 0.1 nA typ, 2.5 nA max; **R_DIFF 92 kΩ**; shunt ±163.84 / ±40.96 mV | the RC1.2 assumption "≥ 830 kΩ [UV]" is slightly optimistic: minimum is 800 kΩ (gain-error bound 0.0071 %, not 0.007 %; calibrated out) |
| INA228 pin map | 1 A1, 2 A0, 3 ALERT, 4 SDA, 5 SCL, 6 VS, 7 GND, 8 VBUS, 9 IN−, 10 IN+ | matches the controller symbol |
| Bourns 1.5SMBJ | 48A: V_RWM 48, V_BR 53.3–58.9 V, V_C 77.4 V @ 19.4 A (10/1000), 100.6 V @ 97 A (8/20); **I_R ≤ 1 µA at V_RWM, 25 °C**; ΔV_BR = 0.1 % × V_BR per °C | relayed clamp points confirmed; leakage at 44 V ≤ the 1 µA @ 48 V figure (25 °C) — temperature dependence still not in the file |
| Panasonic ERJP08 (AOA0000C331, 28-Mar-26) | 1206, 0.66 W @ 70 °C, limiting element voltage 125 V, max overload 500 V, TCR ±200 ppm/K (≥ 10 Ω), AEC-Q200; part-number pattern `ERJP08 F 47R0 V` (±1 %, four-digit, embossed 4 mm reel); ±1 % range 10 Ω–1 MΩ so 10R0 is at the lower limit | `rs_pulse_rating`: **still OPEN** — the file has no pulse-limiting/surge curve (only an ESD test, 3 kV/150 pF ≈ 0.68 mJ) |
| Samtec FTSH catalog (SMT page) | `FTSH-105-01-L-DV-K` is a valid code: **-01** = 3.05 mm post (mates FFSD), **-L** = 10 µin Au post/matte-tin tail, **-DV** = double vertical, **-K = keying shroud** for FFSD (not merely a notch; SMT: 5–25 pins/row), **-TR** tape & reel; 3.4 A per pin (2 pins powered), 280 VAC/396 VDC. Family spec: 4.2 A one pin/row, 500 cycles | pad pattern/shroud outline still not in the files |
| JST PH catalog | B4B-PH-K-S: 2.0 ±0.05 mm, hole Ø0.7 +0.1/0, outline 4.5 mm, height 8 mm, A = 6.0, B = 9.9 mm; 2 A, 100 V; contact resistance 10 mΩ initial / 20 mΩ after test | — |
| GCT USB4105 drawing | pad/hole/slot numbers present in the drawing | see §2 |

## 2. Connector footprint audit
| Part | Controller footprint (as placed in RC1.2) | Comparison | Status |
|---|---|---|---|
| **J7 JST B4B-PH-K-S** | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | pitch 2.0 ✓; drill 0.75 within Ø0.7 +0.1/0 ✓; Fab outline x −1.95…7.95 = **9.9 mm = B** ✓; y −1.7…2.8 = **4.5 mm width** ✓ with the catalog's 1.95/1.7 offsets ✓ (footprint cites this same ePH.pdf) | **MATCHES** on every dimension the catalog gives. Pin-1 end/orientation vs the housing mark not checkable from text |
| **J8 GCT USB4105-GF-A** | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` (cites gct.co usb4105.pdf; tags include USB4105-GF-A) | drawing numbers 0.25/0.75/1.25/1.75/2.40 pad offsets ✓, 4×0.60 + 8×0.30 pad widths ✓, 2×Ø0.65 positioning holes at 5.78 mm ✓, 3.68 pad-row offset ✓, shell slots 2.10/1.70 and 1.80/1.40 ✓ | **MATCHES** the dimensions present in the drawing. Not checked: board-edge/shell clearance (7.35/8.94 dimensions), rotation 90° placement, A1 orientation |
| **J5 Molex 22-27-2031 / J6 22-27-2041** | `Molex_KK-254_AE-6410-03A/04A_1x0N_P2.54mm_Vertical` (library note: "AE-6410-03A example for new part number 22-27-2031") | pitch 2.54 ✓, 3/4 circuits ✓, no locator/retention features ✓ (none in footprint); **hole 1.19 / pad 1.74×2.19 not compared** — the Molex pages/drawings were not uploaded and molex.com is blocked | **UNVERIFIED** (consistent, derived from the Molex series drawing, not checked against it) |
| **J9 Samtec FTSH-105-01-L-DV-K** | generic `PinHeader_2x05_P1.27mm_Vertical_SMD` (pads 2.40×0.74 at x = ±1.95) | the FTSH-DV has its own land pattern and a keying shroud (-K); the generic KiCad header is **not** that part; Samtec's SMT footprint/series print was not in the files | **NOT VERIFIED — likely wrong**: replace with the Samtec footprint before release |

## 3. Protection recomputation (script: `protection_audit.py`)
Inputs: 1.5SMBJ48A clamp points; INA228 limits; credible events from the brief (hot-plug, interruption ≤ 18.5 A, ESD ±8 kV contact / ±15 kV air at accessible connectors, wiring faults). Clamp curve = straight line between the datasheet rating points (an engineering estimate, not a datasheet curve).

**Result: the existing 1.5SMBJ48A + 47 Ω network passes the surge/interruption/hot-plug events and does NOT demonstrably pass the new ESD requirement or the differential limit for one-sided events.**
| Event | Node clamp (48A) | Margin to 85 V |
|---|---|---|
| Interruption, 18.5 A, Rs = 0 | 76.5 V | +8.5 V |
| Hot-plug, Kelvin path (10 Ω upstream), worst of 12 L/C combinations | 59.5 V | +25.5 V (matches the controller's own 59.5 V) |
| Hot-plug, VBUS path (47 Ω upstream, 100 nF) | 44.0 V (no overshoot) | +41 V; R41 energy ≈ 80 µJ (matches ≤ 83 µJ) |
| ESD 8 kV contact (330 Ω gun + 47 Ω upstream → 21 A in the TVS) | 77.9 V (DC level) | +7.1 V |
| ESD 15 kV air (≈ 40 A in the TVS) | 83.4 V (25 °C) / **87.0 V (+60 K, V_BR tempco)** | +1.6 V / **−2.0 V** |
The ESD rows exclude the first-nanosecond L·di/dt spike (5 nH × 30 A/ns ≈ 150 V), which no datasheet model resolves; only an IEC-gun/TLP test at the connector can show the INA pin stays < 85 V. The 47 Ω upstream resistor barely reduces ESD current (330 Ω gun impedance dominates), so it is not an ESD measure.

**INA228 differential stress (±40 V).** Both sense leads live: a one-sided clamp event gives 32–39 V differential (1–8 V margin). If the other lead is open or connects later (IN− held only by the 92 kΩ R_DIFF), the same event is 60–83 V differential → **exceeds ±40 V**. (The RC1.2 text already flagged this as "UNVERIFIED"; the limit is now verified.)

**Errors.** VBUS: 57 Ω into 0.8–1.2 MΩ = 0.0047–0.0071 % (fixed ratio, calibrated out; Z-spread 0.0024 % remains). TVS leakage × 47 Ω = 47 µV per µA (1.1 ppm of 44 V). Kelvin: 1 µA × (10 + 10) Ω = 20 µV mismatch = 8 mA-equivalent on a 2.5 mΩ shunt (0.04 % of 20 A) at the 1 µA maximum, cold; leakage rises with temperature and the Bourns file gives no curve → keep as a measured first-article item. INA228 bias 2.5 nA × 20 Ω = 50 nV (negligible).
**Resistors.** ERJP08 working voltage is not the issue (RCWV 5.6 V for 47 Ω; node peaks ≤ 77 V ≪ 125 V limiting element voltage and 500 V overload). The credible pulses (≈ 0.1–0.4 mJ) are small, but **no pulse rating exists in the supplied datasheet** → request the ERJP08 pulse-limiting curve or test the part.
**Recovery.** The TVS is not damaged below its 97 A (8/20) / 19.4 A (10/1000) ratings; recovery is immediate (no latch).

## 4. Recommendations for the controller session (changes belong on its branch)
1. **Differential clamp across IN+/IN−** on the INA side of R11/R12 (bidirectional TVS or back-to-back clamp, V_RWM well above the ±164 mV signal range and below 40 V, low leakage), so a one-sided or open-lead event cannot exceed ±40 V. Check its leakage on the 2.5 mΩ shunt budget (nA-level is negligible).
2. **ESD:** decide whether the ±8/±15 kV requirement applies to J5/J6; if yes, 1.5SMBJ48A + 47 Ω cannot be shown to meet ±15 kV air at the INA228 pin. Options (to be evaluated, not selected here): a lower-clamp part — **1.5SMBJ45A** is the lowest standoff above the 44 V ceiling (clamp ≈ 5–6 V lower, margin +7.3 V at 15 kV air, but only 1 V standoff headroom and higher leakage near 44 V) — plus a dedicated fast ESD stage at the connector, and an IEC 61000-4-2 gun test of the assembled input as a first-article pass/fail.
3. **ERJP08 suffixes:** `ERJP08F47R0V` (47 Ω ±1 %) and `ERJP08F10R0V` (10 Ω ±1 %) are consistent with the part-number scheme and ±1 % range (10 Ω at the limit); orderability/stock not checked; pulse rating open.
4. **Footprints:** replace J9 with the Samtec FTSH-DV footprint (needs the series print + footprint file); compare J5/J6 against the Molex drawing (needs the two Molex PDFs); J7 and J8 can be marked verified for the dimensions listed above.
5. **Evidence register:** upgrade `ina228_diff_max`, `ina228` VBUS impedance/bias, `tvs48`/`tvs48_820`/`tvs48_ipp` to verified; keep `rs_pulse_rating` open; narrow `tvs_leakage` to "≤ 1 µA at V_RWM, 25 °C verified; temperature open".

## 5. Still needed
Molex 22-27-2031 and 22-27-2041 PDFs/drawings; Samtec FTSH-DV series print and SMT footprint; Panasonic ERJP08 pulse-limiting curve (or a statement that it will be tested); decision on whether the ESD requirement applies to which connectors; permission/instruction on where to commit this audit.

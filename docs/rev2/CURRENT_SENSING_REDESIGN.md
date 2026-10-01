# Rev.2 current-sensing redesign

Context: Rev.1 uses a 20 A-class shunt (RSA-20-50, 2.5 mΩ) with an INA228. The
6060B can sink up to 60 A *at low voltage only* (`min(60 A, 300 W / V)`), so a
higher-range sensor matters only for packs at ≤ 30 V (> 10 A) — see
`LV_POWER_PATH_CAPABILITY.md`. **Nothing below is implemented in hardware or
bench-verified.** Candidates must be evaluated on the bench; a high current
rating alone is not a reason to choose a part.

## Requirements
Accuracy at low current (DCIR steps use small ΔI; capacity tests run at
1–3 A), range for high-current/low-voltage tests, Kelvin sensing, thermal
monitoring, appropriate isolation, STM32/I²C compatibility (INA228 driver
already exists).

## Options evaluated

| Option | Strengths | Weaknesses | Verdict |
|---|---|---|---|
| **A. 50–75 A precision shunt (e.g. ~1 mΩ, 4-terminal) + existing INA228** | Best low-current accuracy per cost; INA228 24-bit ADC; Kelvin; driver exists; INA228 common-mode rating (85 V) covers 60 V so no isolator is needed for sensing | Signal at 1 A is only ~1 mV (offset/thermal EMF matter); 60 A ⇒ 60 mV and 3.6 W in the shunt (needs heat-sinking/airflow); copper/connection resistance must be outside the Kelvin sense points | **Recommended baseline** |
| B. Hall-effect sensor (open-loop or closed-loop) | Galvanic isolation; no insertion loss | Typical offset/linearity/drift errors are a percent of *full scale* — poor at 1–3 A when full scale is ≥ 50 A; analog chain into the STM32 ADC | Not the primary meter. Optional **independent over-current trip** |
| C. Multiple measurement ranges (low-range shunt for < ~10 A, high-range for the rest) | Keeps low-current resolution and high-current reach | Needs range switching or series shunts with input protection; added relay/MOSFET failure modes; more calibration | Only if bench tests show Option A's low-current error is unacceptable |

## Recommendation
1. Prototype **Option A**: ~1 mΩ four-terminal shunt (≈ 60–75 A class) on an
   off-board bus bar, INA228 in ADCRANGE 0 (±163.84 mV), shunt calibration
   updated in `OSBAMS_SHUNT_MICRO_OHM` / `OSBAMS_INA228_IMAX_MA`.
2. Add a shunt temperature sensor (the TC74 is 1 °C resolution; a separate
   NTC on the shunt body is better) and stop on limit.
3. Validate low-current accuracy against the **EDU34450A** (0.1 A – 10 A) and the
   6060B readback before trusting any number; record in `calibration_records`.
4. Keep the Rev.1 shunt path until Option A passes; only then raise the
   validated current limit (and only up to the weakest component).
5. If low-current error is too large, escalate to Option C; Hall (B) can be added
   as an isolated over-current trip, never as the accuracy meter.

Success criteria are set in `PHYSICAL_VALIDATION_PLAN.md` (REV2-V3), not claimed here.

# 5 V distribution voltage-drop budget (RC1.1)

Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT contacts -> harness -> Pi-end contacts -> Pi 5V pins` and return. 2 contacts paralleled per rail, 16 AWG <=150 mm (x1.2 hot), 2 oz copper from the measured layout.
Target: **>= 4.85 V at the Pi header at 5 A, worst case** (Pi floor 4.75 V, ceiling 5.25 V).

## Inputs and their status (`datasheet_inputs.json`)

| Input | Value | Status | Source |
|---|---|---|---|
| j_out_contact_max_mohm | 10.0 | UNVERIFIED | Molex Micro-Fit 43045 test summary: 10 mOhm max initial low-level contact resistance (cited by project owner, not independently fetched) |
| j_out_contact_typ_mohm | 5.0 | UNVERIFIED | ASSUMED (Molex quotes a max only; owner notes measured values include wire resistance) |
| j_out_rating_a | 8.5 | UNVERIFIED | Molex 43045-0400, 8.5 A max per contact (cited by project owner) |
| pi_end_contact_max_mohm | 20.0 | UNVERIFIED | ASSUMED - Pi-end is a 2.54 mm crimp terminal, NOT Micro-Fit; needs the chosen terminal's datasheet |
| pi_end_contact_typ_mohm | 8.0 | UNVERIFIED | ASSUMED |
| f2_resistance_max_mohm | 15.0 | UNVERIFIED | ASSUMED - need Littelfuse 0451008.MRL cold resistance (and hot/voltage-drop at 5 A) |
| f2_resistance_typ_mohm | 8.0 | UNVERIFIED | ASSUMED |
| rsdw_tolerance_pct | 2.0 | UNVERIFIED | ASSUMED +-2 % setpoint+line+load; need RSDW40F-05 datasheet |
| rsdw_trim_allowed | False | UNVERIFIED | Need Mean Well trim range + formula + resistor topology (R2: TRIM-+VOUT, R3: TRIM--VOUT) |
| rsdw_trim_max_pct | 0.0 | UNVERIFIED | Need datasheet |
| rsdw_footprint_drawing | False | UNVERIFIED | Need Mean Well mechanical drawing (body, pin XY, pin dia, drill) |
| erc_clean_kicad10 | False | UNVERIFIED | Run ERC in KiCad 10 locally |

**Clarification on the 20 mOhm:** that figure is the *Pi-end* 2.54 mm crimp terminal + header pin, not Micro-Fit. The Molex 10 mOhm max applies to the J_OUT mating contacts, which RC1.1 already budgeted at 10 mOhm max. The Micro-Fit data therefore does not lower the Pi-end term; it only becomes 10 mOhm if the chosen Pi-end terminal is *specified* at <=10 mOhm (case B). Molex quotes a maximum only, and as you note the measured value includes wire resistance, so the max-stack below is conservative.

## Results at the Pi 5V pins

| Case | R typ / max (mOhm) | V@Pi 3 A typ / worst | V@Pi 5 A typ / worst | max src (no load) |
|---|---|---|---|---|
| A  RC1.1 baseline (16 AWG/150 mm, Pi-end 20 mOhm max, F2 15 max) | 25.6 / 49.6 | 4.92 / 4.75 | 4.87 / 4.65 | 5.10 |
| B  A + Pi-end terminal <= 10 mOhm (selection requirement) | 25.6 / 39.6 | 4.92 / 4.78 | 4.87 / 4.70 | 5.10 |
| C  B + F2 <= 8 mOhm (lower-resistance fuse) | 25.6 / 32.6 | 4.92 / 4.80 | 4.87 / 4.74 | 5.10 |
| D  C + 4 Pi GND pins | 25.6 / 30.1 | 4.92 / 4.81 | 4.87 / 4.75 | 5.10 |

## Is 4.85 V achievable in the stacked worst case? (setpoint window)

| Worst-case R (mOhm) | Setpoint needed for 4.85 V @5 A (worst) | No-load max at that setpoint | Fits <= 5.25 V? |
|---|---|---|---|
| A: 49.6 | 5.202 V (+4.0 %) | 5.306 V | NO |
| B: 39.6 | 5.151 V (+3.0 %) | 5.254 V | NO |
| C: 32.6 | 5.115 V (+2.3 %) | 5.218 V | yes |
| D: 30.1 | 5.103 V (+2.1 %) | 5.205 V | yes |

With +-2 % source tolerance, a setpoint that gives 4.85 V at 5 A *and* stays <= 5.25 V at no load exists only if worst-case R <= **38.8 mOhm** (non-fuse terms: 34.6 mOhm with a 20 mOhm Pi-end terminal -> F2 <= 4.2 mOhm; 24.6 mOhm with a 10 mOhm Pi-end terminal -> F2 <= 14.2 mOhm). So the Pi-end terminal must be a <=~10 mOhm part and F2 must be a low-resistance part for any trim setting to satisfy both limits.
Preferred 4.9-5.0 V at 5 A needs either a tighter RSDW tolerance than assumed or lower resistance than any configuration above - to be settled from the RSDW datasheet, not assumed.

## What must be verified before RC2 (blocking)

1. F2 exact cold resistance and 5 A voltage drop - Littelfuse 0451008.MRL datasheet; if it exceeds the F2 limit above, choose a lower-resistance suitable Nano2 (keep over-current protection; the 451/453 family goes to 20 A) and re-check I2t/ratings against U1's overload limit.
2. RSDW40F-05 setpoint tolerance, trim range, formula and resistor topology (which of R2/R3, value) - Mean Well datasheet. Use trim only if explicitly permitted; R2/R3 stay DNP.
3. RSDW40F-05 mechanical drawing -> U1 footprint.
4. Pi-end terminal contact resistance (<=10 mOhm class selection) and a measured harness.
5. Bench: voltage at the Pi header under real Pi 5 + Waveshare load.

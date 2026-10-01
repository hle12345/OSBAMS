# OSBAMS Rev.2 Controller RC1.3 — change report (review candidate, NOT released for fabrication)

Branch `claude/gallant-ride-tdr3hw` only. RC1.2 baseline (`../OSBAMS_Rev2_RELEASE_CANDIDATE_1`) is untouched; RC1.3 is a fork in `rc1_3/`. Tools: KiCad 10.0.6, Freerouting 1.9.0.

## CHANGES MADE
1. **INA228 differential clamp D20** (Bourns 1.5SMBJ12CA, bidirectional, SMB) across `SHUNT_INP_RAW`/`SHUNT_INN_RAW` (after R42/R43 and the 48 V TVSs, before R11/R12/C26). Datasheet NOT supplied: all its values are ASSUMED.
2. **Connector-entry ESD stage** D15/D16 (J5.1/J5.2), D17/D18/D19 (J6.1/J6.2/J6.3), unidirectional to GND, placed at the connector pads, ahead of R41/R42/R43. Architecture is now connector → fast clamp → pulse-rated series R (ERJ-P08 candidate, no verified pulse limit claimed) → 1.5SMBJ48A surge TVS (kept, not swapped to 45A) → R11/R12/R13 + C26/C28 → INA228.
   - A 200 W SOD-123FL 48 V part (SMF48A) was tried first and **rejected by the calculation** (Rdyn ≈ 7 Ω leaves 93–269 V across the series resistor). D15–D19 are therefore the verified 1.5SMBJ48A (SMB, Rdyn ≈ 1 Ω). No purpose-built ≥48 V ESD diode with a verified low Rdyn was found in the supplied files — owner decision if one is wanted.
3. **J9**: NOT changed. The supplied Samtec pages (catalog F-226, spec CLP/FTSH, screenshot) carry no land pattern or key position (only pitch 1.27, post 0.40 sq, tail span 5.84, tail 2.92). I did not invent geometry; the generic KiCad footprint remains and is explicitly NOT claimed exact. See blockers.
4. J5 = Molex 22-27-2031, J6 = 22-27-2041 kept; pad/hole/body dimensions flagged only (no dimensioned drawing supplied).
5. Revision strings RC1.3 (schematic variable, silkscreen, reports); docs updated. New scripts: `design/viafix.py`, `design/islandfix.py`, stitch clearance fix for un-netted pads (fiducials) and pad bounding boxes; `calc/protection_rc13.py` → `calc/protection_rc13_results.md`.
6. Audit files committed earlier under `Hardware/Rev2_Controller/audit/`.

## CALCULATION RESULTS  (full tables: `calc/protection_rc13_results.md`)
- Checks on the final RC1.3 board: **ERC 0/0/0; DRC 0 violations, 0 unconnected, 0 footprint errors; schematic↔PCB netlist 415 pads, 0 mismatches; diode polarity errors none; isolation host↔controller min 0.999 mm vs 1.0 mm rule (audit tolerance 0.01 mm), custom-rule fresh-folder DRC 0**.
- ESD (8 kV contact / 15 kV air, 330 Ω/150 pF, DC-level clamp model): RC1.2 had 0.2–1.9 kV across the series resistor and 83–87 V at the clamp (85 V limit exceeded at 15 kV air, +60 K). RC1.3: series R sees 19–41 V, R pulse energy 0.3–3.3 µJ (was 136–2440 µJ), surge clamp 59–66 V, ≥19 V margin to 85 V.
- Differential (one-sided hot-plug / open-lead): RC1.2 up to 77.9–83.4 V across the 40 V limit; RC1.3 ≈ 14.7–14.9 V (≈ +1 V hot), margin ≈ 25 V (D20 values ASSUMED).
- Normal error 0–50 mV: D20 leakage ≈ 0.4 µV (8 ppm) ohmic-scaled; 100 µV (0.2 %) only under an unrealistic flat 5 µA bound; D15/D16 mismatch ≤ 1 µV (before R42/R43). Differential τ 4.00 → 4.08 µs (fc 39.8 → 39.0 kHz, assumed 2 nF); recovery ≈ 38 µs to 0.01 %.

## FIRST-ARTICLE TESTS
1. IEC 61000-4-2 gun at J6.1/J6.2/J6.3/J5.1/J5.2 (±8 kV contact, ±15 kV air) with INA228 and ERJ-P08 monitored; TLP on the connector-entry diodes; resistor value drift afterwards. Design/first-article target, not a certification.
2. Scope the INA228 VBUS and IN± pins during ESD and hot-plug at 44 V (first-nanosecond spike is not in any datasheet model).
3. Zero-current offset and 20 A gain with/without D20 populated (leakage/capacitance error); filter step response (recovery).
4. One-sided hot-plug and open-lead tests of IN+/IN− (differential ≤ 40 V).
5. Measure D20 / D15–D19 leakage at 44 V CM, 25 °C and 85 °C.

## REMAINING FABRICATION BLOCKERS
- **J9 exact Samtec FTSH-105-01-L-DV-K footprint and key/pin-1 orientation**: need the Samtec land pattern / product print (samtec.com FTSH product page → footprint/download specs). Blocker until supplied.
- 1.5SMBJ12CA datasheet (Vbr, Vc, leakage, capacitance) — D20 numbers are assumed.
- ERJ-P08 pulse/surge curve (or test) — no verified pulse-energy limit.
- Owner's export of Gerbers and ERC/DRC re-confirmation in KiCad 10; BOM adds 5×1.5SMBJ48A + 1×1.5SMBJ12CA (consign has 2 of the 48 V).
- Not blockers (flag only): J5/J6 Molex drawing dimensions.
- Note: routing is non-deterministic; the committed board is attempt 4 of repeated runs after DRC-in-the-loop repair (viafix/islandfix).

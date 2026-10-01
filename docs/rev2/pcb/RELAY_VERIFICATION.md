# Relay K1 — keep unless the verified rating is inadequate

**Decision rule:** keep the installed Durakool. Replace only if its verified DC make/break rating, for the exact installed suffix, is below the OSBAMS envelope. No automatic swap to an Albright SW60 (or anything else).

## Envelope the relay must satisfy
| Case | Voltage | Current | Notes |
|---|---|---|---|
| Normal make/break (load test) | ≤ 44 V DC | ≤ 10 A | system ceiling, provisional |
| Fuse-fault interrupt window | ≤ 44 V DC | ≤ 15 A | fuse clears; relay must survive carry/possible break |
| Firmware hard trip | ≤ 44 V DC | 18.5 A | protection layer; relay opens on trip, ideally ≤ 15 A rating margin documented |
| Rated carry | — | ≥ 10 A continuous (≥ 15 A short) | |

## Evidence so far (listing level — NOT verified)
- Firmware records **DG57CM-5021-76-1012-R**; purchase record agrees.
- Listing figures: 12 V coil, ~90 Ω (≈ 133 mA), 80 A @ 12 V, 145 VDC max switching; family ratings 60 A @ 36 V and 50 A @ 48 V.
- No auxiliary contact (firmware comment) → K1 feedback is the VO610A stage.
- On those figures the margin vs 10 A @ 44 V is ≥ 5×. This is **likely adequate** but is not a verified datasheet value for this suffix.

## To close (bench V6 + paper)
1. Read the full marking and date code off the installed unit (V6); photograph.
2. Obtain the manufacturer datasheet for that exact suffix; record DC make/break at the envelope (voltage, current, resistive vs inductive, life cycles).
3. Measure coil resistance and current at 12 V (V6). If ≈ 133 mA, track width and netclass concern in G-09 is closed (0.3 mm is marginal; use ≥ 0.5 mm).
4. Record result in `HARDWARE_ACCEPTANCE_RECORD.md`; flip G-02 to closed or "replace".
If the datasheet shows inadequate DC breaking rating, the replacement is a separate decision with its own comparison (do not pre-select).

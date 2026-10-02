# RevB carrier vs RC2 (separate power board + interposer)

| Item | RC2 | RevB carrier |
|---|---|---|
| PCBs | power board (100 × 70 mm) + interposer (65 × 24 mm) | **one board** 85 × 67.5 mm |
| Power board → Pi connection | J_OUT → 4 × 18 AWG harness (≤ 150 mm) → interposer J1 → SSW socket | **direct copper** to the SSW socket |
| Mechanical support | power board standalone; interposer carried by the header + 2 M2.5 × 20 key standoffs | 4 × M3 × 20 enclosure standoffs (2 are key posts); header-end spacers only locate |
| Display feed | J_DISP | J_DISP (kept) |
| Trim | R2 (no part) + R3 | R3 only (R2 removed: trim-down is never used) |
| Worst-case Pi-pin voltage, 5 A + 1.0 A display | 4.829 V (−21 mV vs 4.85 V target) | **4.962 V** (+112 mV) |

## Parts removed vs RC2
| Removed | Qty | Why |
|---|---|---|
| Molex 430450400 J_OUT (power board) | 1 | no harness |
| Molex 430450400 J1 (interposer) | 1 | no harness |
| Molex 43025-0400 housings | 2 | no harness |
| Molex 43030-0038 terminals | 8 (of 12) | 4 remain: J_IN 2, J_DISP 2 |
| 18 AWG Pi-branch wires (4 × ≤ 150 mm) | 4 | no harness |
| Interposer PCB | 1 | merged |
| R2 footprint | 1 | trim-down never used |
| M2.5 × 20 key standoffs | 2 | replaced by M3 × 20 enclosure standoffs |
| (net effect on the 5 V path) | — | −26.5 mOhm worst case (55.0 → 28.5 mOhm to the Pi pins) |

Kept: RSDW40F-05, F1 0407008.WR, F2 0451008.MRL, TVS1 SMBJ15A, J_IN / J_DISP 430450200, SSW-120-01-L-D, C1 / C2 / C4 / C5 / C6, R1 / D1 (power-good), R3, TP1–TP5.

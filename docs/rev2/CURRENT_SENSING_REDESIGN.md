# Current sensing — future optimization (NOT being done now)

**Decision:** the Rev.1 current path (RSA-20-50, 2.5 mΩ, ~20 A class, INA228) is
**kept unchanged**, and the OSBAMS operating ceiling stays at **10 A,
provisionally** (`config.SAFETY_MAX_CURRENT_A`).

Why: every physical SFSU battery is 36–42 V. At 42 V the 6060B's 300 W limit
allows only 300 / 42 = **7.14 A** (8.33 A at 36 V), and the profiles are lower
still (1 A, 2.5 A, 3 A recommended). The existing ~20 A measurement path
already exceeds the current any of those packs can be loaded with.

Layered limits (distinct concepts, deliberately not equal):

| Layer | Value | Meaning |
|---|---|---|
| Firmware hard safety trip | 18.5 A | absolute protection boundary |
| OSBAMS operating ceiling | 10 A | operating/test boundary (provisional) |
| 6060B @ 42 V | 7.14 A | `min(60 A, 300 W / V)` |
| Battery profile | e.g. 1–5 A | per-pack |
| **Commanded maximum** | **min of the operating layers** | e.g. 5 A for a profile limit of 5 A |

## When this becomes relevant
Only for **lower-voltage packs** (≤ 30 V gives > 10 A; 12 V gives 25 A; the full
60 A needs ≤ 5 V) — none of which are on hand. If such packs are acquired, evaluate:
a ~1 mΩ four-terminal 50–75 A shunt on the existing INA228 (first choice: best
accuracy at low current, Kelvin, driver exists), multiple ranges (only if the
bench shows a low-current accuracy problem), or a Hall sensor (isolation, but
percent-of-full-scale errors make it unsuitable as the accuracy meter; at most
an independent over-current trip). Also needed then: DC-rated contactor, fuse,
wiring and connector review (`LV_POWER_PATH_CAPABILITY.md`). Do not design or buy
any of this now.

# Current sensing — no redesign planned

**Decision:** the Rev.1 current path (RSA-20-50, 2.5 mΩ, ~20 A class, INA228) is
**kept unchanged**, and the OSBAMS operating ceiling stays at **10 A,
provisionally** (`config.SAFETY_MAX_CURRENT_A`).

Why: every supported pack is 36–42 V (≤ 44 V ceiling). The 6060B's 300 W limit
allows 300 / 42 = **7.14 A** (8.33 A at 36 V), and the profiles are lower still.
The existing path already exceeds any current these packs can be loaded with.

Layered limits (distinct concepts, deliberately not equal):

| Layer | Value | Meaning |
|---|---|---|
| Firmware hard safety trip | 18.5 A | absolute protection boundary |
| OSBAMS operating ceiling | 10 A | operating/test boundary (provisional) |
| 6060B @ 42 V | 7.14 A | `min(60 A, 300 W / V)` |
| Battery profile | e.g. 1–5 A | per pack |
| **Commanded maximum** | **min of the operating layers** | e.g. 5 A for a profile limit of 5 A |

The only thing to measure is whether the existing shunt/INA228 is accurate enough at
the 1–3 A test currents — that is bench step E1, not a redesign.

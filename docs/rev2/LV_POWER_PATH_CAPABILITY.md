# Rev.2 LV power-path capability

**Purpose:** decide, component by component, how much of the 6060B's
3–60 V / 60 A / 300 W envelope the OSBAMS power path can *actually* use.
Nothing here is assumed. "Verified source" says where each number comes from;
anything not read from a datasheet/measurement is marked so.

Power path (from `Documentation/HARDWARE_DESIGN.md`):
`Battery + → connector J1 → fuse F1 → manual disconnect SW1 → contactor K1 → shunt RS1 / INA228 → 6060B → Battery −`

## 1. Component table

| Component | Voltage rating | Current rating | Power / thermal constraint | Verified source | System constraint |
|---|---|---|---|---|---|
| 6060B electronic load | 3–60 V input | 60 A | 300 W total; `I_max = min(60, 300/V)` | Project owner, from manufacturer envelope | 60 A only at ≤ 5 V; 7.14 A at 42 V |
| Shunt RS1 (Rev.1: RSA-20-50, 2.5 mΩ) | n/a (sense element) | **20 A / 50 mV** | 20 A² × 2.5 mΩ = 1.0 W at rating | Repo (`app_config.h`, `HARDWARE_DESIGN.md`) | **Hard cap 20 A** — firmware trip 18.5 A; operating limit 10 A |
| INA228 (U2) | Bus 0–85 V; covers 60 V | n/a (set by shunt) | Shunt input ±163.84 mV (ADCRANGE 0) | Repo + INA228 datasheet (range figures as used in `ina228.c`) | Not the limit: 85 V > 60 V. Current range is set by the shunt |
| Current-scale register | — | `OSBAMS_INA228_IMAX_MA` = 30 A | digital scale only | Repo (`app_config.h`) | Above shunt rating on purpose; not a capability |
| Fuse F1 | "58 V DC" noted | **NOT SPECIFIED** | needs DC interrupt rating ≥ 60 V and ≥ prospective pack short-circuit current | Repo notes only; part not chosen | Unspecified → cannot support any claim; sized to operating limit |
| Manual disconnect SW1 (Blue Sea 6006 noted) | not verified here | not verified here | contact heating | Repo names the part; rating **not checked in this build** | Read the datasheet before relying on it |
| Contactor K1 | needs published **DC breaking** rating ≥ 60 V | **NOT SPECIFIED / not frozen** | coil power, contact heating | Repo: "single most important remaining hardware selection" | Unspecified → blocks anything beyond the validated limit |
| Connector J1 (XT30 / XT60 / XT90 + adapters) | XT-series nominal ratings are well above 60 V | Nominal XT30 ≈ 30 A, XT60 ≈ 60 A, XT90 ≈ 90 A (manufacturer figures, **not re-verified; derate for continuous use**) | contact resistance heating | Manufacturer nominal values from memory/not rechecked | **Connector never sets test current.** Always derated by profile/instrument |
| Wiring | insulation ≥ 60 V | depends on gauge/length/temperature; e.g. 14 AWG is a ~15–25 A class conductor, a 60 A run needs ~6 AWG class | I²R heating, voltage drop to the sense point | General engineering practice — **check the wire-ampacity chart** for the actual cable | Wire actually installed is unspecified |
| PCB copper (KiCad board) | — | A standard 1 oz trace cannot carry tens of amps | trace heating | Board not inspected for this document | Keep the power path **off-PCB** (bus bar/cable + off-board shunt) |
| Terminals / lugs | not verified | not verified | torque, heating | Not specified | Specify with the cable |
| Battery profile | per pack | per profile (`maximum_osbams_test_current_a`) | cell/BMS limits | `services/battery_profiles.py` | Always part of the `min()` |

## 2. Derived Rev.2 validated operating envelope

`permitted I = min(profile, OSBAMS validated limit, connector, fuse, wiring, contactor, shunt/sensor, 60 A, 300 W / V)`

| Quantity | Rev.2 initial value | Why |
|---|---|---|
| Voltage | 3 – 60 V instrument window; **profile decides within it** | 6060B range; INA228 85 V |
| Current (OSBAMS validated hardware limit) | **10 A** (`config.SAFETY_MAX_CURRENT_A`) | Largest value the documented path can plausibly support; fuse, contactor, wiring, connector are unspecified, so nothing higher is claimed |
| Power | ≤ 300 W | 6060B |
| Shunt cap (known) | 20 A | RSA-20-50 rating |

Effective current for the actual SFSU batteries:

| Pack | V_max | 300 W / V | OSBAMS 10 A | **Permitted** |
|---|---|---|---|---|
| 36 V Ninebot / Shenzhen Elite / NEE1006-M | 42 V | 7.14 A | 10 A | **7.14 A** (then profile) |
| 48 V-class | 54.6 V | 5.49 A | 10 A | 5.49 A |
| 60 V boundary | 60 V | 5.00 A | 10 A | 5.00 A |
| 24 V | 25.2 V | 11.9 A | 10 A | 10 A |
| 12 V | 12.6 V | 23.8 A | 10 A | 10 A |

### Key finding
**Every pack the lab actually owns (36–42 V) is capped by the 6060B's own 300 W
at ≤ 8.33 A. The Rev.1-class path (20 A shunt, 10 A operating limit) already
covers 100 % of them.** More than 10 A only becomes reachable for packs at
**≤ 30 V** (300 W / 30 V = 10 A), and the full 60 A only at ≤ 5 V. A hardware
redesign therefore buys capability for 12 V/24 V packs and single-cell /
low-voltage work — not for the scooter batteries.

## 3. Hardware changes needed to exploit more of the 6060B

Needed only if testing > 10 A at low voltage is wanted. **Do not raise
`SAFETY_MAX_CURRENT_A` before all of these are built and verified.**

1. **Shunt/sensor** — replace the 20 A shunt (see `CURRENT_SENSING_REDESIGN.md`).
2. **Contactor** — DC-rated for ≥ 60 V at the target current, with published DC breaking rating (also needed for the 60 V claim at any current).
3. **Fuse** — DC-rated ≥ 60 V, interrupt rating above prospective short-circuit current of the largest allowed pack, sized below the wire limit.
4. **Wiring and lugs** — gauge for the target current with voltage-drop budget to the sense point; specify crimp/torque.
5. **Disconnect SW1** — confirm continuous and DC-break ratings.
6. **Connector** — keep XT30/XT60/XT90 adapters, but derate and label the permitted current from the profile, never from the plug.
7. **Power path off the PCB** — bus bar/cable with off-board Kelvin-sensed shunt; PCB carries sense and logic only.
8. **Thermal** — shunt and connector temperature sensing, stop on limit.
9. **Re-run the E-stop/contactor timing and fault-injection validation** (`PHYSICAL_VALIDATION_PLAN.md`) after any change.

Once changed and validated, record the new component limits in
`equipment.capability.PowerPathLimits` — the model then caps current
automatically.

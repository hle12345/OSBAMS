# Rev.2 power-path capability (battery / discharge side)

Frozen candidate and open part numbers: `HARDWARE_FREEZE_CANDIDATE.md`.
Equipment stack: `SFSU_EQUIPMENT_MATRIX.md`.

**Final permitted current**

```
min(profile_limit, osbams_limit, 60 A, 300 W / conservative_pack_voltage,
    fuse, disconnect, relay/contactor, shunt/sensor, wiring, connector)
```

`conservative_pack_voltage` = max(OCV, highest voltage seen), never lowered by
sag. The 60 A front-panel rating never overrides the 300 W limit
(`equipment/capability.py`; hard invariant in `services/test_orchestrator.py`).
Operating ceiling: **≤ 10 A and ≤ 44 V, provisional, until the power path is
physically validated.**

## 1. Component table

Power path: `pack → XT60 → fuse → Blue Sea 6006 → Durakool DG57CM → shunt/INA228 → 6060B → pack −`.
"Verified source" is honest: **no number below has been read off the physical unit yet**.

| Component | Voltage rating | Current rating | Power / thermal constraint | Verified source | System constraint |
|---|---|---|---|---|---|
| Agilent 6060B load | 3–60 V input | 60 A | **300 W**; `I = min(60 A, 300 W / V)` | project owner, manufacturer envelope | 7.14 A at 42 V, 8.33 A at 36 V, 10 A at 30 V |
| Shunt RS1 (RSA-20-50, 2.5 mΩ) | sense element | **20 A / 50 mV** | 1.0 W at 20 A | repo (`app_config.h`, `HARDWARE_DESIGN.md`); installed part not confirmed | cap 20 A; firmware trip 18.5 A (protection) |
| INA228 | bus 0–85 V | set by shunt | ±163.84 mV shunt range | repo / datasheet | not the limit |
| Fuse F1 | 58 V (Littelfuse 0997015.WXN per purchase record; holder 0FHM0001ZXJ-RED DC rating unverified, V5) | **15 A target** | sits above the 10 A operating ceiling and below the wire limit | purchase list: Littelfuse/Eaton DC fuse, "HOLD - verify part"; holder Blue Sea 5504 or exact match | protects against abnormal fault current, not normal regulation (see layered limits in `HARDWARE_FREEZE_CANDIDATE.md`) |
| Manual disconnect (Blue Sea 6006) | 48 V DC max | 300 A continuous; **25 A switching** | contact heating | manufacturer values as shown in distributor listings; not read from the unit | not for routine opening under load |
| Relay/contactor K1 (Durakool DG57CM, 12 V coil) | up to 145 V DC switching (listing) | variant-dependent: ~60 A@36 V, 50 A@48 V | coil power, contact heating | Durakool listing; **suffix not read** | UNSPECIFIED in the model until the suffix is known |
| Connector (XT60; adapter only if needed) | XT-series nominal rating far above 44 V | nominal rating is derated for continuous use | contact resistance | manufacturer nominal values, not re-verified | **connector type does not determine test capability — the validated power path does** |
| Wiring | insulation ≥ 48 V | depends on gauge/length — check the ampacity chart for the installed cable | I²R, voltage drop to the sense point | not specified | UNSPECIFIED |
| PCB copper | — | not a power conductor | trace heating | board not inspected | keep the power path off the PCB |
| Battery profile | per pack | per profile (`maximum_osbams_test_current_a`) | cell/BMS limits | `services/battery_profiles.py` | always part of the `min()` |

## 2. Derived validated operating envelope

| Quantity | Rev.2 value | Why |
|---|---|---|
| Pack voltage | **≤ 44 V** (provisional OSBAMS ceiling) | 48 V disconnect with margin; 42 V full-charge packs |
| Operating current ceiling | **10 A** (`config.SAFETY_MAX_CURRENT_A`) | nothing in the path is verified above it |
| Power | ≤ 300 W | 6060B |
| Firmware hard trip | 18.5 A / 60 °C | separate protection boundary, not an operating limit |

Permitted current for the supported lithium-ion class (profile limit not applied):

| Pack V (conservative) | 300 W / V | OSBAMS 10 A | **Permitted** |
|---|---|---|---|
| 30 V | 10.00 A | 10 A | 10.00 A |
| 33 V | 9.09 A | 10 A | 9.09 A |
| 36 V | 8.33 A | 10 A | **8.33 A** |
| 37 V | 8.11 A | 10 A | 8.11 A |
| 40 V | 7.50 A | 10 A | 7.50 A |
| 42 V | 7.14 A | 10 A | **7.14 A** |
| 44 V | 6.82 A | 10 A | 6.82 A |
| > 44 V | — | — | **blocked** (above the OSBAMS ceiling) |

Then the battery profile applies (recommended 1 A / 2.5 A / 3 A; ceilings 5.2 / 6.4 / 7 A for the three packs on hand).

### Key finding
Every supported pack is limited by the 6060B's 300 W long before the 20 A-class
shunt, the 15 A fuse or the 10 A ceiling matters. The existing measurement path is
sufficient; no power-path redesign is planned (`CURRENT_SENSING_REDESIGN.md`).
Do not raise `SAFETY_MAX_CURRENT_A` or the 44 V ceiling until the exact parts are
read off the hardware and the validation steps (`LV_HARDWARE_VALIDATION_PLAN.md`) pass.

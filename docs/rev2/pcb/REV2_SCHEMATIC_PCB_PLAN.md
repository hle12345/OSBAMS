# Rev.2 controller schematic / PCB plan — PROPOSAL, board NOT modified

Status: **APPROVED by the user 2026-10-01** (see `APPROVED_DECISIONS.md`); plan only until V1–V10 are filed. The KiCad files are untouched. No fabrication outputs exist (`MANUFACTURING_STATE.md`). The existing board is **revised, not redrawn**: same 80×80 mm 2-layer THT carrier, same J1–J6, Q1, U1, same Nucleo-header architecture.

## 0. Sequence
1. Bench: fill `BENCH_V1_V10_ONE_PAGE.pdf` (P1 rows first: V7, V6, V1, V9, V2, V4).
2. Update `REV1_HARDWARE_TRUTH_INVENTORY.md` and `HARDWARE_ACCEPTANCE_RECORD.md` from the sheets; set `rev1_physical_observations_recorded` only with sheets filed.
3. Resolve the decisions in §6 (user).
4. Revise the existing KiCad schematic, then PCB. ERC, DRC with KiCad 10.
5. BOM with manufacturer + exact MPN; only then generate PCBWay files (all six gates true).

## 1. Items deliberately NOT done yet
| Topic | Position | Document |
|---|---|---|
| Relay | Keep Durakool DG57CM-5021-76-1012-R unless verified DC rating is inadequate. Footprint stays; no SW60. | `RELAY_VERIFICATION.md` |
| Pi 5 / display 5 V | **Decided: dedicated external supply.** Spec in `PI_POWER_ARCHITECTURE.md`. | `PI_POWER_ARCHITECTURE.md` |
| TC74 | **HOLD until V1.** If V1 confirms viability the final sensor is a remote pack-surface probe (keyed 4-wire connector, 100 nF at sensor, SDA/SCL TPs, DNP pull-ups, ≤ 100 kHz I²C, short cable); if the needed cable length is unreliable, stop and propose a different interface. **Previously:** Root cause unproven. No interface redesign until the four V1 discriminators are recorded. No-regret only: 100 nF at VDD, SDA/SCL test points, DNP pull-up pads (see §2.9). Sensor choice, remote probe connector and pull-up values wait for V1. | audit F2, Inventory §5 |

## 2. Mandatory Rev.2 schematic additions (existing board)

### 2.1 Corrected diode polarity (G-01 BLOCKER)
Cause: `OSBAMS:D_H` / `D_TVS` symbols have pin 1 = anode, KiCad footprints `D_DO-201AD` / `D_SMB` have pad 1 = cathode, so D1–D3 cathodes land on the wrong nets.
Fix: rebuild the two symbols with **pin 1 = K, pin 2 = A**, matching footprints (preferred over editing footprints); re-annotate pin↔net.
Required cathode nets: D1 (SMBJ15A TVS) K→+12V_IN side of load, A→GND; D3 (series Schottky) A→J1 +12V, K→protected +12V rail; D2 (1N5408 flyback) K→+12 V coil rail, A→Q1 drain.
Verification (no ERC dependence; script `tools/mfg/polarity_check.py` to be written with the revision): it reads the netlist and asserts the three cathode nets; ERC cannot catch this. Cross-check with V7 on the real unit before committing the direction of D3.

### 2.2 E-stop sense → PA0 (G-05)
Firmware: LOW = healthy, HIGH = tripped or wire broken, external pull-up, no internal pull.
- Option A (preferred if V6 shows ≥ 2 NC contacts, e.g. Eaton M22-PV-K02 style): second NC contact of the E-stop block to GND at J3; 10 kΩ pull-up to 3V3 on-board; 100 Ω series + 100 nF filter at PA0; clamp D to 3V3.
- Option B (if only one NC): VO610A opto from post-E-stop coil supply; output pulls PA0 low when coil supply present. LED series resistor sized for ~2 mA from 12 V.
Both footprints may be placed with the unused one DNP. Test point TP_PA0.

### 2.3 K1 / relay feedback → PC9
Firmware: active-low, external pull-up, VO610A-1. Reconstruct from V2: LED chain from relay load side (pack side of K1 contacts) via two series resistors (~2 mA at 44 V), reverse protection diode (1N4148 role to be confirmed), output pull-up 10 kΩ to 3V3, 100 nF at PC9. **Creepage ≥ 2 mm** between pack-side and logic-side pads. TP_PC9.

### 2.4 Protected ADC divider → PA1
150 kΩ / 10 kΩ (16:1, firmware scale; 44 V → 2.75 V), 0.1 % 25 ppm (confirm V4), 1 kΩ series to PA1, 100 nF at the tap, BAT54S clamp to 3V3/GND, TP_ADC. Pack-sense input on a keyed connector with its own ground return (Kelvin to pack negative, G-13). Firmware 1.5 V agreement window remains valid.

### 2.5 INA228 / shunt Kelvin interface (G-12)
Module header J4 kept (3V3/GND/SCL/SDA); add ALERT and A0/A1 strap pads and document. Add a 4-pin keyed **shunt sense connector** (IN+, IN−, VBUS, GND) so the shunt sense leads are a twisted pair soldered at the shunt sense terminals — no power current on the PCB. Whether the module sits at the shunt (preferred, short Kelvin) or on the PCB follows V3/V4.

### 2.6 ARM switch wiring (G-14)
ARM goes in **series with the coil path after the E-stop** (E-stop → ARM → coil), on a defined 2-pin header J7. No firmware sense exists; ARM_SENSE on a free GPIO (candidate PC10, confirm in V9) is **approved**: status/diagnostics only, can never bypass ARM (`APPROVED_DECISIONS.md`). The Nucleo interface must also be widened — J5 carries no PA0/PA1/PC9 today.

### 2.7 Verified connector footprints and MPNs (G-07/G-08)
Every connector's footprint is checked against the purchased part's drawing (pitch, drill, keying) from V8 and purchase records; no footprint is accepted from a name match. MPN rules in §5.

### 2.8 Test points and manufacturing markings (G-20)
TPs: GND (×2), 3V3, +12V, COIL_V, LOAD_EN (PC8), PA0, PC9, PA1/ADC, SDA, SCL, Q1 gate. 1.5 mm pads, silk labels.
Markings: board name/Rev/date, polarity marks on D1–D3 and J1, pin-1 and signal names on every header, "NOT FOR USE ABOVE 44 V / 10 A" legend, fab ID spot.

### 2.9 Supporting corrections (from audit)
- Netclass patterns lacked the "/" prefix, so the 1.2 mm class was never applied → fix; coil path ≥ 0.5 mm (G-09), power ≥ 1.2 mm.
- I²C pull-ups 4.7 kΩ to 3V3 with DNP option (G-11); decided together with V1/V3 evidence.
- Single ground bond point defined (G-13/V10).
- Current-ceiling inconsistency (G-10): board legend and docs use 10 A / 44 V provisional, firmware trip separate.
- Nucleo remains an external module, not placed on PCBA (G-21).

## 3. PCB revision plan (after §2 schematic is approved)
- Keep outline, mounting holes, J1–J6, Q1, U1 positions where V-results permit; move parts only for creepage/clearance.
- Widen coil and 12 V tracks; add GND pour stitching; keep the divider/INA228 grounds away from the coil/Q1 return.
- 2 mm creepage slot or keep-out under VO610A pack-side pins; ≥ 1 mm to edge for legends.
- Re-run `tools/mfg/review_checks.py`, then KiCad ERC/DRC (the only accepted evidence).

## 4. Gate tracking
| Gate | Closed by |
|---|---|
| BLOCKERS (G-01, G-02, G-05, …) | §2.1 + V7; relay V6; §2.2–2.4 + V2/V4/V6/V9 |
| HIGH (G-04, G-12, G-13, G-14, G-21 …) | closed or written disposition in this folder; TC74 disposition waits on V1 |
| ERC / DRC | KiCad 10 reports filed here |
| BOM | §5 |
| Rev.1 observations | V1–V10 sheet filed + inventory updated |

## 5. BOM policy
Manufacturer + exact orderable MPN on every populated line; no generic "resistor/diode". Currently missing: C2, C3, R1, R2, J1–J6 (and new parts). Fuse, XT60, shunt, relay contacts, 6060B are off-board and excluded.

## 6. Decisions
1. Pi/display 5 V — decided: external.
2. ARM sense — decided: yes, GPIO status only.
3. TC74 remote probe — decided conditional on V1.
4. E-stop sense A vs B — open until V6.

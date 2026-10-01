"""RC1.2 documents: report, evidence-risk classification, connector footprint check, pre-PCBWay checklist."""
import json, os, re
from collections import Counter
from . import rc_docs, reports
from .rc_docs import write, ROOT, TODAY

REG = lambda: json.load(open(os.path.join(ROOT, "calc", "datasheet_inputs.json")))["inputs"]

# class of damage a wrong value could cause, for every register entry that is not VERIFIED_LOCAL
RISK = {
    "WRONG_PINOUT": ["vo610a_pinout", "ina228_pinmap", "lmr_pinmap", "q_pinout", "tc74_pinmap"],
    "EXCEEDED_ABS_MAX": ["ina228_cm", "ina228_diff_max", "lmr_en", "lmr_limits", "stm32_io", "stm32_vrefint_range", "q_vdss", "vo610a_led_vr", "vo610a_ratings", "dg57_pickup",
                         "dg57_vmax", "tvs15", "bat54s_ir", "bat54s_vf"],
    "WRONG_FOOTPRINT": ["conn_footprints", "conn_pitch", "lmr_pkg"],
    "UNSAFE_PROTECTION": ["tvs48", "tvs48_820", "tvs48_ipp", "rs_pulse_rating", "tvs_leakage", "dg57_dc1", "ina228_status"],
}
NOTES = {
    "vo610a_pinout": "DIP-4 opto: wrong pin order would make both status inputs dead; relayed pinout matches the netlist.",
    "ina228_pinmap": "relayed TI table matches the symbol pin-for-pin; a mismatch would make the INA228 unusable (no measurement).",
    "lmr_pinmap": "relayed table matches; a mismatch would stop the 3.3 V rail.",
    "q_pinout": "relayed 1 G / 2 S / 3 D matches; a mismatch would leave the relay always off/on.",
    "tc74_pinmap": "relayed table matches (probe board).",
    "ina228_cm": "85 V limit used in the protection analysis (closed by the RC1.2 network, relayed value).",
    "ina228_diff_max": "differential input maximum NOT relayed; the TVS pair clamps each line to ground, a one-sided transient can reach the clamp level across IN+/IN-.",
    "lmr_en": "SHDN threshold/abs max not relayed; SHDN is pulled to +12V through 100 k (limits current); confirm the pin allows +12 V through 100 k.",
    "lmr_limits": "VIN abs max 45 V vs SMBJ15A clamp 24.4 V (relayed).",
    "stm32_io": "PA1 not 5 V tolerant while the ADC switch is connected: the clamp network protects it (relayed structure).",
    "stm32_vrefint_range": "firmware must use the factory calibration constant.",
    "q_vdss": "60 V vs 12 V coil + flyback: large margin.",
    "vo610a_led_vr": "1N4148 limits the LED reverse voltage to ~0.7 V.",
    "vo610a_ratings": "VCEO 70 V vs the 3.3 V pull-up: large margin.",
    "dg57_pickup": "coil max allowable 12.5 V at 85 C vs the XDR set to 12.0 V: needs the XDR set/verified at 12.0 V (first article).",
    "dg57_vmax": "145 VDC switching vs 44 V ceiling.",
    "bat54s_ir": "diode leakage/forward voltage enter the PA1 back-feed analysis; the R4 bleeder guards the unknown.",
    "bat54s_vf": "same.",
    "conn_footprints": "stock KiCad footprints; geometry beyond pitch/pin count not checked against the manufacturer drawings (J5, J6, J7, J8, J9). OPEN until the drawings are compared.",
    "conn_pitch": "pitch and pin count match.",
    "lmr_pkg": "KiCad SOT-23-6 vs the TI DDC land pattern (pitch/pin numbering match; land pattern not compared).",
    "rs_pulse_rating": "OPEN: Panasonic ERJ-P08F pulse-energy/surge rating and exact orderable suffix not read; the pack-sense protection is not fully closed until it is.",
    "tvs_leakage": "OPEN: Bourns 1.5SMBJ48A leakage maximum vs voltage/temperature not read; sets the Kelvin-line offset error (4 mA per uA) and the PACK_INA error (47 uV per uA).",
    "tvs48": "protection analysis (model) in calculations 2b uses the relayed clamp points; NOT fully closed (see rs_pulse_rating, tvs_leakage).",
    "tvs48_820": "same (the 8/20 us point exceeds 85 V; the added series resistors keep the credible set within the limit).",
    "tvs48_ipp": "same.",
    "dg57_dc1": "relay DC rating >> the 10 A / 44 V ceiling.",
    "ina228_status": "informational.",
    "tvs15": "SMBJ15A clamp vs LMR14006 VIN abs max 45 V (relayed).",
}


def _cls(i):
    for k, v in RISK.items():
        if i in v:
            return k
    return "FIRST_ARTICLE / INFORMATIONAL"


def evidence_risk():
    reg = [e for e in REG() if e["evidence"] != "VERIFIED_LOCAL"]
    rows = {k: [] for k in list(RISK) + ["FIRST_ARTICLE / INFORMATIONAL"]}
    for e in reg:
        rows[_cls(e["id"])].append(e)
    out = [f"# Evidence risk classification — RC1.2 ({TODAY})\n",
           "Every register entry that is **not VERIFIED_LOCAL** is classified by what a wrong value could actually cause. `USER_RELAYED_MANUFACTURER` values are used as authoritative for electrical checks; the PDFs have not been read by the build. Entries read locally (ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing, KiCad library facts) are not listed.\n",
           f"{len(reg)} entries are not VERIFIED_LOCAL: " + ", ".join(f"{k}: {len(v)}" for k, v in rows.items()) + ".\n"]
    heads = {"WRONG_PINOUT": "Could cause a WRONG PINOUT (supply the datasheet to move these to VERIFIED_LOCAL — highest priority)",
             "EXCEEDED_ABS_MAX": "Could cause an EXCEEDED ABSOLUTE MAXIMUM",
             "WRONG_FOOTPRINT": "Could cause a WRONG FOOTPRINT",
             "UNSAFE_PROTECTION": "Protection-related (analysis closed in `REV2_CALCULATIONS.md` using the relayed numbers)",
             "FIRST_ARTICLE / INFORMATIONAL": "First-article measurements / design margins / informational (cannot cause a wrong pinout, absolute-maximum violation, wrong footprint or unsafe protection)"}
    for k, v in rows.items():
        out.append(f"\n## {heads[k]}\n")
        out.append("| id | part | parameter | evidence | note |\n|---|---|---|---|---|")
        for e in v:
            out.append(f"| `{e['id']}` | {e['part']} | {e['parameter'][:110]} | {e['evidence']} | {NOTES.get(e['id'], '')} |")
    out.append("""
## Mandatory first-article measurements (not PCBWay blockers)
1. **Relay driver (IRLML0060, K1 coil):** VGS at the gate, VDS while energized, coil current (expect ≈ 121–148 mA at 12.0 V), MOSFET case temperature; XDR output set and verified at 12.0 V (coil limit 12.5 V at 85 °C).
2. **3V3 / 3V3_A:** ripple and level with the real load, and during an input step to 12.5 V; confirm no pulse-skipping instability at 12.0 V.
3. **INA228 chain:** shunt voltage at 0 A (leakage of the TVS diodes through R42/R43, cold and warm), VBUS vs the EDU34450A, scope on IN+/IN− during sense-harness hot-plug.
4. **PA1 ADC protection:** pack powered / controller unpowered, reversed pack, injection test; read VREFINT calibration.
5. **Status networks:** ESTOP_SENSE and RELAY_FB thresholds at 10.5–15 V and 24–44 V; ARM_SENSE.
6. **CP2102N / ISO7721:** USB enumeration, VBUS detect (reference divider: threshold 3.96 V typical, 4.40 V worst case), UART echo through the isolator, 3V3_HOST rail current.
""")
    return write("EVIDENCE_RISK_CLASSIFICATION.md", "\n".join(out) + "\n")


def connector_check():
    fp = open(os.path.join(ROOT, "build", "connfp.txt")).read() if os.path.exists(os.path.join(ROOT, "build", "connfp.txt")) else "(run design connector extraction)"
    t = f"""# Connector footprint check — RC1.2 ({TODAY})

**Status: OPEN.** The manufacturer drawings for these five parts were not available to the build (manufacturer sites are blocked; none were supplied). Only the numbers relayed by the user (pitch, circuits, A/B dimensions, tail length) could be compared, and those match; pad/drill/shield/courtyard/pin-1/orientation geometry could **not** be compared with an official drawing, so `conn_footprints` stays UNVERIFIED and critical. The EB21A footprint is verified and not part of this item.

## What was compared (relayed numbers vs the KiCad stock footprints)
| Part | Footprint | Relayed manufacturer data | Result |
|---|---|---|---|
| Molex 22-27-2031 (J5) | `Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical` | 3 circuits, 2.54 mm, PCB 1.60 mm, tail 3.56 mm, shrouded/polarized | pitch / circuits match |
| Molex 22-27-2041 (J6) | `Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical` | 4 circuits, same family | pitch / circuits match |
| JST B4B-PH-K-S (J7) | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | 4 circuits, 2.0 mm, A = 6.0 mm (= 3 × 2.0), B = 9.9 mm | pitch and A match; B not checkable from the footprint |
| GCT USB4105-GF-A (J8) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | USB-C, horizontal, VBUS 5 A, GND 6.25 A | named for the family; geometry not compared |
| Samtec FTSH-105-01-L-DV-K (J9) | `PinHeader_2x05_P1.27mm_Vertical_SMD` | 10 pins, 1.27 mm, vertical SMT, keyed | generic SMD 2×5 footprint; keying/row spacing not compared |

## Extracted geometry of the footprints as placed (for the drawing comparison)
```
{fp}
```

## Checks to perform against each official drawing (drawings needed: Molex 22-27-2031 and 22-27-2041, JST B4B-PH-K-S, GCT USB4105-GF-A, Samtec FTSH-105-01-L-DV-K)
- pad size and recommended hole/drill diameter; hole-to-pad annular ring; pad pitch and row spacing;
- body outline and courtyard vs the manufacturer's keep-out; connector overhang past the board edge (J8 overhangs ~0.8 mm by design);
- pin 1 location and the numbering direction; polarization/key orientation vs the silkscreen;
- mating direction vs the board edge and neighbours (J5/J6/J7 mate vertically; J8 mates horizontally to the right edge; J9 needs the shroud notch toward the keyed side);
- shield/NPTH holes and tail length vs the 1.6 mm board.
"""
    return write("CONNECTOR_FOOTPRINT_CHECK.md", t)


def pre_pcbway_checklist():
    t = f"""# PRE-PCBWAY RELEASE CHECKLIST — actions only you can perform ({TODAY})

Baseline: OSBAMS Rev.2 Controller RC1.2 (project `OSBAMS_Rev2_RC1.kicad_pro`). This package contains **no Gerbers**: export them yourself from the final PCB. The design is **not** called final or released for fabrication.

1. **Open the exact project in KiCad 10** (`OSBAMS_Rev2_RC1.kicad_pro` with the `.kicad_sch` sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty/`, `sym-lib-table`, `fp-lib-table`, `OSBAMS_Rev2_RC1.kicad_dru`). Keep the `.kicad_dru` next to the `.kicad_pro` (it holds the 1.0 mm isolation rule and the INA228 fine-pitch exemption). Confirm it is active: Board Setup → Design Rules → Custom Rules must list `isolation_host_to_controller`, `isolation_controller_to_host` and `fine_pitch_ina228` without syntax errors; the DRC must then give 0 violations (`ISOLATION_RULE_CHECK.txt` shows the build container's proof).
2. **Local ERC** — expected 0 errors, 0 warnings.
3. **Local DRC** — run with "all violations", re-fill all zones first (Edit → Fill all zones). Expected 0 violations, 0 unconnected, 0 footprint errors. Any difference from `DRC_REPORT.rpt` must be explained before continuing.
4. **Connector drawings** — compare J5, J6, J7, J8, J9 against the official manufacturer drawings using `CONNECTOR_FOOTPRINT_CHECK.md` (or send me the five PDFs).
5. **Manufacturer PDFs:** (a) the five connector drawings; (b) Panasonic ERJ-P08F datasheet (pulse rating, suffix) and Bourns 1.5SMBJ datasheet (leakage vs voltage/temperature) — needed to close the pack-sense protection; (c) the entries classified as wrong-pinout risk in `EVIDENCE_RISK_CLASSIFICATION.md` (INA228, LMR14006Y, IRLML0060, VO610A, TC74) — send them to move those entries from USER_RELAYED to VERIFIED_LOCAL.
6. **Edit the silkscreen text** `NOT FOR FABRICATION` / revision line to your release wording (silkscreen only; no copper change), then save.
7. **Export Gerbers and drills from KiCad 10** (File → Fabrication Outputs): copper F.Cu/In1.Cu/In2.Cu/B.Cu, F/B mask, F/B silkscreen, F/B paste, Edge.Cuts; Excellon drill with PTH and NPTH in separate files and a drill map; use the board origin consistently.
8. **Gerber viewer inspection** (KiCad Gerber viewer or another viewer): check layer count/order, outline, drill vs pad alignment, mask openings on 0.5 mm-pitch parts, silkscreen not over pads, polarity marks, the GND_HOST island and its gap.
9. **PCBWay CAM inspection:** upload the Gerbers, review their DFM report (4-layer capability, minimum track/space/drill/annular ring, mask bridge on LQFP-64/QFN-20) and approve any engineering questions.
10. **PCBWay CPL orientation inspection:** load `OSBAMS_Rev2_RC1_CPL.csv` + BOM in their assembly preview and confirm rotation/polarity of every SOT-23/SOT-23-6, QFN-20, LQFP-64, SOIC-8, MSOP-10, diode and electrolytic-style marked part (library rotation offsets differ); the CPL uses KiCad footprint-origin data.
11. **Stock and substitution review:** fill `Supplier SKU` / `Stock Check Date` in the BOM, confirm every orderable suffix (the BOM column "MPN suffix status" lists which are not yet confirmed), approve or reject the listed alternates, decide consign vs PCBWay-sourced (owned: 5 × EB21A-02-C, 2 × VO610A-1, 2 × 1N4148, 2 × 1.5SMBJ48A + 1 more needed, VJ0805Y104JXXAT × 2 for the probe).
12. **Set and verify the XDR-75-12 output at 12.0 V** before first power-up (coil limit 12.5 V at 85 °C; continuous controller input must stay ≤ 14.4 V).
"""
    return write("PRE_PCBWAY_RELEASE_CHECKLIST.md", t)


def rc_report(s, net_errs, pol_errs):
    reg = REG()
    c = Counter(e["evidence"] for e in reg)
    crit = [e for e in reg if e["critical"] and e["evidence"] != "VERIFIED_LOCAL"]
    drc_types = ", ".join(f"{k} {v}" for k, v in sorted(s["drc_types"].items())) or "none"
    t = f"""# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1.2 ({TODAY})

**Status: RELEASE CANDIDATE 1.2 — FOR REVIEW. NOT final, NOT released for fabrication, NOT hardware validated.** Gerbers are intentionally not included: export them from the final PCB in your own KiCad 10 (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## READY FOR REVIEW
Checked with KiCad 10.0.6 in the build container (`BUILD_ENVIRONMENT.md`):

- **ERC: {s['erc']} violations.** **DRC: {s['drc_viol']} violations, {s['drc_unconn']} unconnected pads, {s['drc_fp']} footprint errors** (types: {drc_types}). **Netlist vs PCB: {len(net_errs)} mismatches.** Diode/LED polarity: {'PASS' if not pol_errs else 'FAIL'}.
- **Isolation:** every HOST-net item keeps ≥ 1.0 mm from every controller-net item on all layers (custom DRC rule; 3.0 mm in the ISO7721 area) — `ISOLATION_CHECK.txt`.
- **Pack-level clearance:** 0.2 mm class (IPC-2221B B4 0.13 mm × 1.5), INA228 courtyard exempt at 0.15 mm — see `FABRICATION_NOTES.md`; PCBWay capability to be confirmed in their tool.
- **Pack-sense protection — PASS under model assumptions, NOT fully closed:** series surge resistors R41 (47 Ω) and R42/R43 (10 Ω) upstream of the 1.5SMBJ48A diodes; defined-transient model: ≤ 76.5 V (interruption bound ≤ 18.5 A), hot-plug ≤ 60 V, limit 85 V. Open source values: ERJ-P08F pulse rating/suffix (Panasonic) and 1.5SMBJ48A leakage (Bourns). Surge-capability numbers are model results, not validated limits — `REV2_CALCULATIONS.md` §2b.
- **CP2102N VBUS divider:** R38 19.1 kΩ / R39 47.5 kΩ — +0.12 V margin to VIH at VBUS 4.40 V / VDD 3.6 V / 1 % resistors (the 22.1 k reference is −16 mV there); pin ≤ 3.77 V at 5.25 V (limit 5.6 V) — §8.
- **Custom rule check:** `ISOLATION_RULE_CHECK.txt` shows the `.kicad_dru` is applied when the project is opened from a fresh folder (clean 0 violations; tightened rule → 131).
- **Buck:** XDR 12.0 V ±1 %; maximum continuous controller input 14.4 V; 24.4 V transient treated separately (pulse skipping, millivolt-level rail excursion) — §3.
- **IRLML0060:** kept; margin ≈ 7× the coil load by estimate; RDS(on) at 3.3 V not claimed as guaranteed; first-article measurements mandatory — §4.
- **Evidence:** VERIFIED_LOCAL {c['VERIFIED_LOCAL']} · USER_RELAYED_MANUFACTURER {c['USER_RELAYED_MANUFACTURER']} · UNVERIFIED {c['UNVERIFIED']}; classified by consequence in `EVIDENCE_RISK_CLASSIFICATION.md`. Read locally: ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing.
- **Outputs:** schematic PDF, BOM xlsx/csv (Qty, MPN, suffix status, source, DNP), CPL, assembly drawing, copper-layer PDF, assembly/fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, supply-chain report, evidence register, reconciliation, connector check, pre-PCBWay checklist, TC74 probe project (`probe/`).

## BLOCKERS BEFORE PCBWAY ORDER
1. **Connector footprints (J5 Molex ×2, J7 JST, J8 GCT USB-C, J9 Samtec) not compared with the official drawings** — `CONNECTOR_FOOTPRINT_CHECK.md` (drawings needed; none supplied, manufacturer sites unreachable).
1a. **Pack-sense protection source values unread:** Panasonic ERJ-P08F pulse rating/suffix and Bourns 1.5SMBJ48A leakage vs voltage/temperature — protection is not fully closed until they are.
2. **Wrong-pinout-class datasheets still USER_RELAYED** (INA228, LMR14006Y, IRLML0060, VO610A, TC74): they match the netlist but the PDFs have not been read — `EVIDENCE_RISK_CLASSIFICATION.md`.
3. **Your local actions** in `PRE_PCBWAY_RELEASE_CHECKLIST.md`: KiCad 10 ERC/DRC, Gerber/drill export, Gerber viewer inspection, PCBWay CAM and CPL inspection, stock/substitution review ({len(crit)} critical register entries are not VERIFIED_LOCAL).
4. Open measured/first-article items are listed in `EVIDENCE_RISK_CLASSIFICATION.md` and are **not** order blockers.

## Package contents
KiCad project (`OSBAMS_Rev2_RC1.kicad_pro/.kicad_dru/.kicad_sch/.kicad_pcb`, 10 sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC1_Schematic.pdf`, BOM/CPL files, `OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf`, `OSBAMS_Rev2_RC1_Copper_Layers.pdf`, notes and reports listed above, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `ISOLATION_CHECK.txt`, `probe/`.
"""
    return write("PCBWAY_RELEASE_CANDIDATE_REPORT.md", t)

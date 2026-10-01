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
    "WRONG_FOOTPRINT": ["conn_footprints", "conn_pitch", "lmr_pkg", "conn_molex", "conn_samtec_key"],
    "UNSAFE_PROTECTION": ["tvs48", "tvs48_820", "tvs48_ipp", "rs_pulse_rating", "tvs_leakage", "dg57_dc1", "ina228_status", "tvs_diff", "esd_connector"],
}
NOTES = {
    "vo610a_pinout": "DIP-4 opto: wrong pin order would make both status inputs dead; relayed pinout matches the netlist.",
    "ina228_pinmap": "relayed TI table matches the symbol pin-for-pin; a mismatch would make the INA228 unusable (no measurement).",
    "lmr_pinmap": "relayed table matches; a mismatch would stop the 3.3 V rail.",
    "q_pinout": "relayed 1 G / 2 S / 3 D matches; a mismatch would leave the relay always off/on.",
    "tc74_pinmap": "relayed table matches (probe board).",
    "ina228_cm": "85 V limit used in the protection analysis (closed by the RC1.2 network, relayed value).",
    "ina228_diff_max": "VIN+ - VIN- = -40 to +40 V absolute maximum (TI table, relayed; not the 163.84/40.96 mV measurement ranges): closed as USER_RELAYED, PDF still to be committed; D15 is a backstop.",
    "tvs_diff": "D15 SMF12CA: VRWM 12 V, VBR 13.3-14.7 V, VC 19.9 V at 10.1 A relayed; leakage, capacitance, pulse curve and land pattern vs D_SMF open.",
    "esd_connector": "ESD at J5/J6 cannot be shown by simulation; R41-R43 sit upstream of the TVS -> first-article test F1, connector-level TVS = RC1.3 fallback.",
    "conn_molex": "022272041 drawing is a 3D isometric without dimensions, 022272031 not supplied -> J5/J6 pad/drill/outline/ramp side OPEN.",
    "conn_samtec_key": "J9 land pattern is verified; which shroud side carries the -K key slot is not resolved by the drawings -> check on the part (F6).",
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
    "conn_footprints": "J7, J8 and J9 verified against manufacturer drawings; J5/J6 (Molex) still OPEN.",
    "conn_pitch": "pitch and pin count match.",
    "lmr_pkg": "KiCad SOT-23-6 vs the TI DDC land pattern (pitch/pin numbering match; land pattern not compared).",
    "rs_pulse_rating": "OPEN: the catalog (read) gives DC ratings and the +/-3 kV 150 pF ESD test only; the pulse-data document AOA0000C331.pdf is not checked. ERJP08 ratings (relayed from the current datasheet): 125 V limiting / 500 V overload; modeled 8 kV ESD = about 1.3 kV across R41, above the overload rating -> ESD_PROTECTION_OPEN.",
    "tvs_leakage_temp": "Bourns gives IR <= 1.0 uA at 48 V/25 C only; leakage vs temperature/voltage is unspecified: sets the hot Kelvin-line offset (4 mA per uA) and the PACK_INA error (47 uV per uA) -> first-article measurement.",
    "tvs48": "protection analysis (model) in calculations 2b uses the datasheet clamp points; NOT closed (see rs_pulse_rating, tvs_leakage, tvs_diff, esd_connector and CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md).",
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
    out = [f"# Evidence risk classification — RC1.2e ({TODAY})\n",
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
    t = f"""# Connector footprint check — RC1.2e ({TODAY})

**Status: PARTLY CLOSED.** J7 (JST), J8 (GCT USB-C) and **J9 (Samtec FTSH, land pattern)** are verified against the manufacturer drawings supplied (committed in `docs/rev2/pcb/evidence/`). **J5/J6 (Molex 22-27-2031/-2041) remain OPEN:** the 022272041 drawing supplied is a 3D isometric with no dimensions, the 022272031 sheet was not supplied, and the product pages give only circuits, 2.54 mm pitch, 3.56 mm tail, 1.60 mm PCB and partially shrouded/polarized to the mating part. The EB21A footprint is verified separately. J9 key side (-K slot vs pin 1) is a first-article check on the physical part.

## Results
| Part | Footprint | Source | Result |
|---|---|---|---|
| JST B4B-PH-K-S (J7) | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | JST PH catalog ePH (p.1 through-hole layout, p.3 header table) | **PASS** — pitch 2.0 ±0.05 (pads at 0/2/4/6), recommended hole φ0.7 +0.1/0 (footprint drill 0.75 is inside that range; JST notes larger holes may be needed for hard PCB material), A = 6.0, B = 9.9 (outline x −1.95…7.95), body depth 4.5 with the pin row 1.7 mm from one edge (outline y −1.7…2.8), No. 1 circuit at the left viewed from the mounting surface (pin 1 at left, as placed), top-entry mating (cable/mating part comes from +Z; keep ≥ 8 mm above the board). Pad size 1.2 × 1.75 is a design choice (not on the drawing). |
| GCT USB4105-GF-A (J8) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | GCT drawing rev B | **PASS (footprint) + placement corrected.** Pad x positions ±0.25/0.75/1.25/1.75 (0.30 wide) and ±2.40/±3.20 (0.60 wide), pad length 1.15, A1…A12/B1…B12 order with A1 at the left viewed from the component side, shell slots 1.0 × 2.1 (hole 0.6 × 1.7) and 1.0 × 1.8 (hole 0.6 × 1.4) at ±4.32 (spacing 4.18), two NPTH φ0.65 at ±2.89 (5.78 apart), rear slot centre 2.60 from the PCB edge — all identical in the KiCad footprint. **Mismatch found and fixed:** the connector sat 0.275 mm too close to the board edge (the footprint's PCB-edge reference line was 0.275 mm outside the real edge); J8 moved from x = 96.600 to 96.325 mm so the shell slots are 2.60 mm from the edge and the front overhang is 0.6 mm as drawn. Signals: CC1/CC2 on A5/B5 with 5.1 kΩ, D± tied A6/B6 and A7/B7, SBU unused, all VBUS/GND pads and the four shell slots connected. |
| Samtec FTSH-105-01-L-DV-K (J9) | `OSBAMS_Rev2:FTSH-105-01-L-DV-K` (custom, RC1.2e) | Samtec recommended PCB layout rev H + product drawing rev FX | **PASS (land pattern) — changed in RC1.2e.** The generic KiCad footprint had pads 0.74 × 2.40 on a 6.30 mm span; the drawing gives 0.74 × 2.79 on 6.86 mm (rows 4.07 mm apart, 1.28 mm gap), -K has no locating hole. Pin 01/02/03 mapping reproduced by a +90° rotation (same handedness). Key side not resolved by the drawings → first-article F6. |
| Molex 22-27-2031 (J5), 22-27-2041 (J6) | `Molex_KK-254_AE-6410-03A/04A_1x0N_P2.54mm_Vertical` | Molex product pages (twice), 022272041 3D drawing without dimensions | **OPEN (partly consistent)** — circuits 3/4, vertical, through-hole, pitch 2.54, tail 3.56, PCB 1.60, partially shrouded, polarized to the mating part match; pad 1.74 × 2.19 / drill 1.19 / outline / ramp side vs pin 1 need a dimensioned sales drawing or the Molex ECAD model. |

## Extracted geometry of the footprints as placed
```
{fp}
```

## Still to compare once the dimensioned drawings arrive (J5, J6; J9 key side on the part)
- pad size, recommended hole/drill, annular ring, pad pitch and row spacing;
- body outline/courtyard against the manufacturer keep-out; pin 1 and numbering direction; polarization/key orientation vs the silkscreen;
- mating direction vs the board edge and neighbours (J5/J6 mate vertically; J9 needs the shroud notch toward the keyed side);
- tail length vs the 1.6 mm board.
"""
    return write("CONNECTOR_FOOTPRINT_CHECK.md", t)


def pre_pcbway_checklist():
    t = f"""# PRE-PCBWAY RELEASE CHECKLIST — actions only you can perform ({TODAY})

Baseline: OSBAMS Rev.2 Controller RC1.2e (project `OSBAMS_Rev2_RC1.kicad_pro`). This package contains **no Gerbers**: export them yourself from the final PCB. The design is **not** called final or released for fabrication.

1. **Open the exact project in KiCad 10** (`OSBAMS_Rev2_RC1.kicad_pro` with the `.kicad_sch` sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty/`, `sym-lib-table`, `fp-lib-table`, `OSBAMS_Rev2_RC1.kicad_dru`). Keep the `.kicad_dru` next to the `.kicad_pro` (it holds the 1.0 mm isolation rule and the INA228 fine-pitch exemption). Confirm it is active: Board Setup → Design Rules → Custom Rules must list `isolation_host_to_controller`, `isolation_controller_to_host` and `fine_pitch_ina228` without syntax errors; the DRC must then give 0 violations (`ISOLATION_RULE_CHECK.txt` shows the build container's proof).
2. **Local ERC** — expected 0 errors, 0 warnings.
3. **Local DRC** — run with "all violations", re-fill all zones first (Edit → Fill all zones). Expected 0 violations, 0 unconnected, 0 footprint errors. Any difference from `DRC_REPORT.rpt` must be explained before continuing.
4. **Connector drawings** — J7, J8 and J9 (land pattern) are verified; J5/J6 need the dimensioned Molex sheets `022272031_sd.pdf` / `022272041_sd.pdf` (the 3D-only drawing and product pages have no dimensions) or the Molex ECAD model; check the J9 key side on the physical part (`CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`, F6).
5. **Manufacturer PDFs:** (a) `022272031_sd.pdf`, `022272041_sd.pdf` (dimensioned); (b) the Panasonic pulse-data document AOA0000C331.pdf (resistor pulse capability is OPEN), the SMF12CA datasheet (D15); Bourns 1.5SMBJ and the Panasonic ERJ-P08 catalog are read; TVS leakage vs temperature is a first-article item; (c) the entries classified as wrong-pinout risk in `EVIDENCE_RISK_CLASSIFICATION.md` (LMR14006Y, IRLML0060, VO610A, TC74; the INA228 datasheet has been read) — send them to move those entries from USER_RELAYED to VERIFIED_LOCAL.
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
    t = f"""# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1.2e ({TODAY})

**Status: RELEASE CANDIDATE 1.2e — FOR REVIEW. NOT final, NOT released for fabrication, NOT hardware validated.** Gerbers are intentionally not included: export them from the final PCB in your own KiCad 10 (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## READY FOR REVIEW
Checked with KiCad 10.0.6 in the build container (`BUILD_ENVIRONMENT.md`):

- **ERC: {s['erc']} violations.** **DRC: {s['drc_viol']} violations, {s['drc_unconn']} unconnected pads, {s['drc_fp']} footprint errors** (types: {drc_types}). **Netlist vs PCB: {len(net_errs)} mismatches.** Diode/LED polarity: {'PASS' if not pol_errs else 'FAIL'}.
- **Isolation:** every HOST-net item keeps ≥ 1.0 mm from every controller-net item on all layers (custom DRC rule; 3.0 mm in the ISO7721 area) — `ISOLATION_CHECK.txt`.
- **Pack-level clearance:** 0.2 mm class (IPC-2221B B4 0.13 mm × 1.5), INA228 courtyard exempt at 0.15 mm — see `FABRICATION_NOTES.md`; PCBWay capability to be confirmed in their tool.
- **Pack-sense protection — hot-plug and interruption bounds PASS; protection NOT closed.** Series resistors R41 (47 Ω) and R42/R43 (10 Ω) upstream of the TVS diodes; ≤ 76.5 V at the 18.5 A bound, hot-plug ≤ 60 V, limit 85 V. RC1.2e adds **D15 (SMF12CA) across IN+/IN−** because the INA228 differential limit (±40 V, relayed) is violated by a one-Kelvin-lead-open fault. Classification `MODELED_PASS / DATASHEET_VERIFICATION_OPEN`; `ESD_PROTECTION_OPEN` (ERJP08 overload rating 500 V vs ≈ 1.3 kV modeled across R41 at 8 kV; a connector-level clamp is a likely RC1.3 change if bare pins are accessible). Open: resistor µs–ms pulse curve, SMF12CA leakage/capacitance/land pattern — `CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`.
- **CP2102N VBUS divider:** R38 19.1 kΩ / R39 47.5 kΩ — +0.12 V margin to VIH at VBUS 4.40 V / VDD 3.6 V / 1 % resistors (the 22.1 k reference is −16 mV there); pin ≤ 3.77 V at 5.25 V (limit 5.6 V) — §8.
- **Custom rule check:** `ISOLATION_RULE_CHECK.txt` shows the `.kicad_dru` is applied when the project is opened from a fresh folder (clean 0 violations; tightened rule → 131).
- **Buck:** XDR 12.0 V ±1 %; maximum continuous controller input 14.4 V; 24.4 V transient treated separately (pulse skipping, millivolt-level rail excursion) — §3.
- **IRLML0060:** kept; margin ≈ 7× the coil load by estimate; RDS(on) at 3.3 V not claimed as guaranteed; first-article measurements mandatory — §4.
- **Evidence:** VERIFIED_LOCAL {c['VERIFIED_LOCAL']} · USER_RELAYED_MANUFACTURER {c['USER_RELAYED_MANUFACTURER']} · UNVERIFIED {c['UNVERIFIED']}; classified by consequence in `EVIDENCE_RISK_CLASSIFICATION.md`. Read locally: ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing.
- **Outputs:** schematic PDF, BOM xlsx/csv (Qty, MPN, suffix status, source, DNP), CPL, assembly drawing, copper-layer PDF, assembly/fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, supply-chain report, evidence register, reconciliation, connector check, pre-PCBWay checklist, TC74 probe project (`probe/`).

## BLOCKERS BEFORE PCBWAY ORDER
1. **Connector footprints J5/J6 (Molex 22-27-2031/-2041) not compared with dimensioned drawings** (the 022272041 file is a 3D isometric without dimensions; the 022272031 sheet was not supplied). J7 (JST), J8 (GCT) and J9 (Samtec land pattern, replaced in RC1.2e) are verified — `CONNECTOR_FOOTPRINT_CHECK.md`.
1b. **Protection items open:** resistor pulse capability (Panasonic AOA0000C331.pdf), D15 SMF12CA datasheet, ESD first-article test — `CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`.
1a. **Residual (first-article):** TVS leakage vs temperature is not published by Bourns; covered by first-article measurement.
2. **Wrong-pinout-class datasheets still USER_RELAYED** (LMR14006Y, IRLML0060, VO610A, TC74; the INA228 datasheet has been read): they match the netlist but the PDFs have not been read — `EVIDENCE_RISK_CLASSIFICATION.md`.
3. **Your local actions** in `PRE_PCBWAY_RELEASE_CHECKLIST.md`: KiCad 10 ERC/DRC, Gerber/drill export, Gerber viewer inspection, PCBWay CAM and CPL inspection, stock/substitution review ({len(crit)} critical register entries are not VERIFIED_LOCAL).
4. Open measured/first-article items are listed in `EVIDENCE_RISK_CLASSIFICATION.md` and are **not** order blockers.

## Package contents
KiCad project (`OSBAMS_Rev2_RC1.kicad_pro/.kicad_dru/.kicad_sch/.kicad_pcb`, 10 sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC1_Schematic.pdf`, BOM/CPL files, `OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf`, `OSBAMS_Rev2_RC1_Copper_Layers.pdf`, notes and reports listed above, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `ISOLATION_CHECK.txt`, `CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`, `probe/`.
"""
    return write("PCBWAY_RELEASE_CANDIDATE_REPORT.md", t)

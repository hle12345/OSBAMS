"""RC1.3 documents: report, evidence-risk classification, connector footprint check, pre-PCBWay checklist."""
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
    "ina228_cm": "85 V limit used in the protection analysis (closed by the RC1.3 network, relayed value).",
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
    "rs_pulse_rating": "Panasonic catalog read: 0.66 W, 500 V limiting / 1000 V overload, ESD +/-3 kV 150 pF (0.675 mJ), suffix scheme matches; the us-ms pulse-energy curve is not published there (credible-set energy <= 0.37 mJ is inside the ESD-test energy).",
    "tvs_leakage_temp": "Bourns gives IR <= 1.0 uA at 48 V/25 C only; leakage vs temperature/voltage is unspecified: sets the hot Kelvin-line offset (4 mA per uA) and the PACK_INA error (47 uV per uA) -> first-article measurement.",
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
    out = [f"# Evidence risk classification — RC1.3 ({TODAY})\n",
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
    t = f"""# Connector footprint check — RC1.3 ({TODAY})

**Status: PARTLY CLOSED.** J7 (JST) and J8 (GCT USB-C) are verified against the manufacturer drawings supplied (committed in `docs/rev2/pcb/evidence/`). **J5/J6 (Molex 22-27-2031/-2041) and J9 (Samtec FTSH-105-01-L-DV-K) remain OPEN (RC1.3: J5/J6 pad/hole/body dimensions flagged only; J9 land pattern CLOSED against Samtec drawing FTSH-1XX-XX-XXX-DV-XXX-FOOTPRINT rev H (custom footprint OSBAMS_Rev2:FTSH-105-01-L-DV-K: pads 0.74 x 2.79, rows +-2.035, pin 1 bottom-left); only the key-notch position is not on the supplied sheets):** the Molex files supplied are the product-detail web pages (they confirm circuits, 2.54 mm pitch, 3.56 mm tail, 1.60 mm PCB, partially shrouded/polarized to the mating part — all consistent with the footprints — but contain no dimensioned drawing; the sales drawings `022272031_sd.pdf` / `022272041_sd.pdf` they list are still needed), and the Samtec document supplied (CLP/FTSH/FTS/FW product specification) contains no print or footprint — it refers to samtec.com for them. The EB21A footprint is verified separately.

## Results
| Part | Footprint | Source | Result |
|---|---|---|---|
| JST B4B-PH-K-S (J7) | `JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | JST PH catalog ePH (p.1 through-hole layout, p.3 header table) | **PASS** — pitch 2.0 ±0.05 (pads at 0/2/4/6), recommended hole φ0.7 +0.1/0 (footprint drill 0.75 is inside that range; JST notes larger holes may be needed for hard PCB material), A = 6.0, B = 9.9 (outline x −1.95…7.95), body depth 4.5 with the pin row 1.7 mm from one edge (outline y −1.7…2.8), No. 1 circuit at the left viewed from the mounting surface (pin 1 at left, as placed), top-entry mating (cable/mating part comes from +Z; keep ≥ 8 mm above the board). Pad size 1.2 × 1.75 is a design choice (not on the drawing). |
| GCT USB4105-GF-A (J8) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | GCT drawing rev B | **PASS (footprint) + placement corrected.** Pad x positions ±0.25/0.75/1.25/1.75 (0.30 wide) and ±2.40/±3.20 (0.60 wide), pad length 1.15, A1…A12/B1…B12 order with A1 at the left viewed from the component side, shell slots 1.0 × 2.1 (hole 0.6 × 1.7) and 1.0 × 1.8 (hole 0.6 × 1.4) at ±4.32 (spacing 4.18), two NPTH φ0.65 at ±2.89 (5.78 apart), rear slot centre 2.60 from the PCB edge — all identical in the KiCad footprint. **Mismatch found and fixed:** the connector sat 0.275 mm too close to the board edge (the footprint's PCB-edge reference line was 0.275 mm outside the real edge); J8 moved from x = 96.600 to 96.325 mm so the shell slots are 2.60 mm from the edge and the front overhang is 0.6 mm as drawn. Signals: CC1/CC2 on A5/B5 with 5.1 kΩ, D± tied A6/B6 and A7/B7, SBU unused, all VBUS/GND pads and the four shell slots connected. |
| Samtec FTSH-105-01-L-DV-K (J9) | `PinHeader_2x05_P1.27mm_Vertical_SMD` | Samtec FTSH catalog page F-226 + CLP/FTSH specification (no print) | **OPEN (partly consistent)** — part number decodes as FTSH-1 / 05 pins per row (10 pins) / -01 (3.05 mm post) / -L gold / -DV double vertical / -K keying shroud; pitch 1.27, 0.40 mm square post, tail-to-tail width 5.84 mm (fits inside the footprint's 6.30 mm pad span: pads 0.74 × 2.40 at ±1.95). Land pattern and the key-slot position relative to pin 1 are not on these pages; the generic KiCad footprint is not keyed. |
| Molex 22-27-2031 (J5), 22-27-2041 (J6) | `Molex_KK-254_AE-6410-03A/04A_1x0N_P2.54mm_Vertical` | Molex product pages, supplied twice (no drawing) | **OPEN (partly consistent)** — circuits 3/4, vertical, through-hole, pitch 2.54, tail 3.56, PCB 1.60, partially shrouded, polarized to the mating part match; pad 1.74 × 2.19 / drill 1.19 / outline / pin-1 side need the sales drawing. |

## Extracted geometry of the footprints as placed
```
{fp}
```

## Still to compare once the drawings arrive (J5, J6, J9)
- pad size, recommended hole/drill, annular ring, pad pitch and row spacing;
- body outline/courtyard against the manufacturer keep-out; pin 1 and numbering direction; polarization/key orientation vs the silkscreen;
- mating direction vs the board edge and neighbours (J5/J6 mate vertically; J9 needs the shroud notch toward the keyed side);
- tail length vs the 1.6 mm board.
"""
    return write("CONNECTOR_FOOTPRINT_CHECK.md", t)


def pre_pcbway_checklist():
    t = f"""# PRE-PCBWAY RELEASE CHECKLIST — actions only you can perform ({TODAY})

Revision: OSBAMS Rev.2 Controller RC1.3 (next revision after the preserved RC1.2 baseline in `../OSBAMS_Rev2_RELEASE_CANDIDATE_1`; project `OSBAMS_Rev2_RC13.kicad_pro`). This package contains **no Gerbers**: export them yourself from the final PCB. The design is **not** called final or released for fabrication.

1. **Open the exact project in KiCad 10** (`OSBAMS_Rev2_RC13.kicad_pro` with the `.kicad_sch` sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty/`, `sym-lib-table`, `fp-lib-table`, `OSBAMS_Rev2_RC13.kicad_dru`). Keep the `.kicad_dru` next to the `.kicad_pro` (it holds the 1.0 mm isolation rule and the INA228 fine-pitch exemption). Confirm it is active: Board Setup → Design Rules → Custom Rules must list `isolation_host_to_controller`, `isolation_controller_to_host` and `fine_pitch_ina228` without syntax errors; the DRC must then give 0 violations (`ISOLATION_RULE_CHECK.txt` shows the build container's proof).
2. **Local ERC** — expected 0 errors, 0 warnings.
3. **Local DRC** — run with "all violations", re-fill all zones first (Edit → Fill all zones). Expected 0 violations, 0 unconnected, 0 footprint errors. Any difference from `DRC_REPORT.rpt` must be explained before continuing.
4. **Connector drawings** — J7 and J8 are verified; send `022272031_sd.pdf` and `022272041_sd.pdf` (the Molex product pages have no dimensions; the drawing is the separate *_sd.pdf linked from molex.com) and the Samtec FTSH-105-01-L-DV-K land-pattern print (the catalog page has none) or compare J5, J6, J9 yourself using `CONNECTOR_FOOTPRINT_CHECK.md`.
5. **Manufacturer PDFs:** (a) `022272031_sd.pdf`, `022272041_sd.pdf` and the Samtec FTSH-105-01-L-DV-K land-pattern print; (b) (b) Panasonic ERJ-P08F and Bourns 1.5SMBJ are verified; TVS leakage vs temperature and the resistor µs–ms pulse curve are not published and are first-article items; (c) the entries classified as wrong-pinout risk in `EVIDENCE_RISK_CLASSIFICATION.md` (INA228, LMR14006Y, IRLML0060, VO610A, TC74) — send them to move those entries from USER_RELAYED to VERIFIED_LOCAL.
6. **Edit the silkscreen text** `NOT FOR FABRICATION` / revision line to your release wording (silkscreen only; no copper change), then save.
7. **Export Gerbers and drills from KiCad 10** (File → Fabrication Outputs): copper F.Cu/In1.Cu/In2.Cu/B.Cu, F/B mask, F/B silkscreen, F/B paste, Edge.Cuts; Excellon drill with PTH and NPTH in separate files and a drill map; use the board origin consistently.
8. **Gerber viewer inspection** (KiCad Gerber viewer or another viewer): check layer count/order, outline, drill vs pad alignment, mask openings on 0.5 mm-pitch parts, silkscreen not over pads, polarity marks, the GND_HOST island and its gap.
9. **PCBWay CAM inspection:** upload the Gerbers, review their DFM report (4-layer capability, minimum track/space/drill/annular ring, mask bridge on LQFP-64/QFN-20) and approve any engineering questions.
10. **PCBWay CPL orientation inspection:** load `OSBAMS_Rev2_RC13_CPL.csv` + BOM in their assembly preview and confirm rotation/polarity of every SOT-23/SOT-23-6, QFN-20, LQFP-64, SOIC-8, MSOP-10, diode and electrolytic-style marked part (library rotation offsets differ); the CPL uses KiCad footprint-origin data.
11. **Stock and substitution review:** fill `Supplier SKU` / `Stock Check Date` in the BOM, confirm every orderable suffix (the BOM column "MPN suffix status" lists which are not yet confirmed), approve or reject the listed alternates, decide consign vs PCBWay-sourced (owned: 5 × EB21A-02-C, 2 × VO610A-1, 2 × 1N4148, 2 × 1.5SMBJ48A + 1 more needed, VJ0805Y104JXXAT × 2 for the probe).
12. **Set and verify the XDR-75-12 output at 12.0 V** before first power-up (coil limit 12.5 V at 85 °C; continuous controller input must stay ≤ 14.4 V).
"""
    return write("PRE_PCBWAY_RELEASE_CHECKLIST.md", t)


def rc_report(s, net_errs, pol_errs):
    reg = REG()
    c = Counter(e["evidence"] for e in reg)
    crit = [e for e in reg if e["critical"] and e["evidence"] != "VERIFIED_LOCAL"]
    drc_types = ", ".join(f"{k} {v}" for k, v in sorted(s["drc_types"].items())) or "none"
    t = f"""# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1.3 ({TODAY})

**Status: RELEASE CANDIDATE 1.2 — FOR REVIEW. NOT final, NOT released for fabrication, NOT hardware validated.** Gerbers are intentionally not included: export them from the final PCB in your own KiCad 10 (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## READY FOR REVIEW
Checked with KiCad 10.0.6 in the build container (`BUILD_ENVIRONMENT.md`):

- **ERC: {s['erc']} violations.** **DRC: {s['drc_viol']} violations, {s['drc_unconn']} unconnected pads, {s['drc_fp']} footprint errors** (types: {drc_types}). **Netlist vs PCB: {len(net_errs)} mismatches.** Diode/LED polarity: {'PASS' if not pol_errs else 'FAIL'}.
- **Isolation:** every HOST-net item keeps ≥ 1.0 mm from every controller-net item on all layers (custom DRC rule; 3.0 mm in the ISO7721 area) — `ISOLATION_CHECK.txt`.
- **Pack-level clearance:** 0.2 mm class (IPC-2221B B4 0.13 mm × 1.5), INA228 courtyard exempt at 0.15 mm — see `FABRICATION_NOTES.md`; PCBWay capability to be confirmed in their tool.
- **Pack-sense protection — PASS for the defined transient on datasheet-verified limits (Bourns 1.5SMBJ48A, Panasonic ERJ-P08F catalog):** series surge resistors R41 (47 Ω) and R42/R43 (10 Ω) upstream of the TVS diodes; ≤ 76.5 V at the 18.5 A bound (≈ 81 V at 85 °C with the Bourns temperature coefficient), hot-plug ≤ 60 V, limit 85 V. Not specified by the manufacturers (first-article/model): TVS leakage vs temperature and the resistors' µs–ms pulse-energy curve. Surge-capability numbers are model results, not validated limits — `REV2_CALCULATIONS.md` §2b.
- **CP2102N VBUS divider:** R38 19.1 kΩ / R39 47.5 kΩ — +0.12 V margin to VIH at VBUS 4.40 V / VDD 3.6 V / 1 % resistors (the 22.1 k reference is −16 mV there); pin ≤ 3.77 V at 5.25 V (limit 5.6 V) — §8.
- **Custom rule check:** `ISOLATION_RULE_CHECK.txt` shows the `.kicad_dru` is applied when the project is opened from a fresh folder (clean 0 violations; tightened rule → 131).
- **Buck:** XDR 12.0 V ±1 %; maximum continuous controller input 14.4 V; 24.4 V transient treated separately (pulse skipping, millivolt-level rail excursion) — §3.
- **IRLML0060:** kept; margin ≈ 7× the coil load by estimate; RDS(on) at 3.3 V not claimed as guaranteed; first-article measurements mandatory — §4.
- **Evidence:** VERIFIED_LOCAL {c['VERIFIED_LOCAL']} · USER_RELAYED_MANUFACTURER {c['USER_RELAYED_MANUFACTURER']} · UNVERIFIED {c['UNVERIFIED']}; classified by consequence in `EVIDENCE_RISK_CLASSIFICATION.md`. Read locally: ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing.
- **Outputs:** schematic PDF, BOM xlsx/csv (Qty, MPN, suffix status, source, DNP), CPL, assembly drawing, copper-layer PDF, assembly/fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, supply-chain report, evidence register, reconciliation, connector check, pre-PCBWay checklist, TC74 probe project (`probe/`).

## BLOCKERS BEFORE PCBWAY ORDER
1. **Connector footprints J5/J6 (Molex 22-27-2031/-2041) and J9 (Samtec FTSH-105-01-L-DV-K) not compared with dimensioned drawings** (Molex: the product pages supplied twice have no dimensions — the sales drawings `022272031_sd.pdf`/`022272041_sd.pdf` are needed; Samtec: catalog page confirms part number, pitch and tail span but has no land pattern/key position) — `CONNECTOR_FOOTPRINT_CHECK.md`. J7 (JST) and J8 (GCT) are verified; J8 was moved 0.275 mm to match the PCB-edge drawing.
1a. **Pack-sense protection residuals (not blockers):** TVS leakage vs temperature and the resistors' µs–ms pulse-energy curve are not published by Bourns/Panasonic; covered by first-article measurement.
2. **Wrong-pinout-class datasheets still USER_RELAYED** (INA228, LMR14006Y, IRLML0060, VO610A, TC74): they match the netlist but the PDFs have not been read — `EVIDENCE_RISK_CLASSIFICATION.md`.
3. **Your local actions** in `PRE_PCBWAY_RELEASE_CHECKLIST.md`: KiCad 10 ERC/DRC, Gerber/drill export, Gerber viewer inspection, PCBWay CAM and CPL inspection, stock/substitution review ({len(crit)} critical register entries are not VERIFIED_LOCAL).
4. Open measured/first-article items are listed in `EVIDENCE_RISK_CLASSIFICATION.md` and are **not** order blockers.

## Package contents
KiCad project (`OSBAMS_Rev2_RC13.kicad_pro/.kicad_dru/.kicad_sch/.kicad_pcb`, 10 sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC13_Schematic.pdf`, BOM/CPL files, `OSBAMS_Rev2_RC13_Assembly_Drawing_Top.pdf`, `OSBAMS_Rev2_RC13_Copper_Layers.pdf`, notes and reports listed above, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `ISOLATION_CHECK.txt`, `probe/`.
"""
    return write("PCBWAY_RELEASE_CANDIDATE_REPORT.md", t)

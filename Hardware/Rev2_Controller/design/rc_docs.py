"""Generate the written RC1 documents (host side) from live build data."""
import json, os, re, sys, datetime
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from design import rev2_design as D, reports, checks

ROOT = reports.ROOT
RC = reports.RC
BD = reports.BOARD
TODAY = "2026-10-01"


def rpt_count(path, pat):
    try:
        t = open(path).read()
    except OSError:
        return None
    m = re.search(pat, t)
    return int(m.group(1)) if m else None


def stats():
    s = {}
    s["erc"] = rpt_count(os.path.join(RC, "ERC_REPORT.rpt"), r"\*\* ERC messages: (\d+)")
    if s["erc"] is None:
        t = open(os.path.join(RC, "ERC_REPORT.rpt")).read()
        s["erc"] = len(re.findall(r"^\[", t, re.M))
    t = open(os.path.join(RC, "DRC_REPORT.rpt")).read()
    s["drc_viol"] = int(re.search(r"Found (\d+) DRC violations", t).group(1))
    s["drc_unconn"] = int(re.search(r"Found (\d+) unconnected pads", t).group(1))
    s["drc_fp"] = int(re.search(r"Found (\d+) Footprint errors", t).group(1))
    s["drc_types"] = Counter(re.findall(r"^\[(\w+)\]", t, re.M))
    s["tracks"], s["vias"] = len(BD["tracks"]), len(BD["vias"])
    s["min_track"] = min([x["w"] for x in BD["tracks"]] or [0])
    s["min_via_drill"] = min([x["drill"] for x in BD["vias"]] or [0])
    s["min_via"] = min([x["w"] for x in BD["vias"]] or [0])
    s["tht"] = sum(1 for f in BD["footprints"].values() if f["tht"])
    s["smd"] = sum(1 for f in BD["footprints"].values() if f["smd"] and not f["tht"])
    return s


def write(name, text):
    p = os.path.join(RC, name)
    open(p, "w").write(text)
    return p


def fabrication_notes(s):
    t = f"""# OSBAMS Rev.2 Controller — Fabrication notes ({TODAY})

**{reports.NOTFAB}.** These are working notes for the RC1 review package, not an order specification.

## Board
- Name `OSBAMS Rev.2 Controller`, revision RC1.2, size 100 x 90 mm, single piece (no panelization specified yet), 4 copper layers, 1.6 mm FR-4 (TG >= 150 C suggested), outer copper 1 oz, inner copper 0.5 oz or 1 oz.
- Layer use: L1 components + signals, L2 solid GND plane, L3 routing + GND fill, L4 components/signals + GND fill. A separate **GND_HOST island** (isolated USB side) occupies x 74.5-97.5 mm, y 2.5-47.5 mm on all layers; **every host-net copper item keeps >= 1.0 mm from every controller-net copper item on every layer** (custom DRC rule in `OSBAMS_Rev2_RC1.kicad_dru`; 3.0 mm gap in the ISO7721 area). See `ISOLATION_CHECK.txt`.
- Finish: ENIG recommended (0.5 mm pitch LQFP-64, QFN-20). Soldermask green or black, white silkscreen. Lead-free.
- Edge: plain rectangle, no V-cut, 4 x M3 NPTH (3.2 mm) at (4,4), (96,4), (4,86), (96,86). 3 fiducials 1 mm / 2 mm mask opening.
- Design rules (netclasses in the .kicad_pro + custom rules in the .kicad_dru): default track 0.2 mm / clearance 0.15 mm; POWER 0.3 mm / 0.2 mm; RAIL 0.3 mm / 0.15 mm; **pack-level and Kelvin nets 0.2 mm clearance — a deliberate LOW-VOLTAGE SENSE-NET rule (sense circuitry up to the 44 V ceiling, ~77 V TVS clamp), NOT a general high-voltage clearance rule (an intentional choice: IPC-2221B Table 6-1, 31-100 V, B4 = external conductors under permanent polymer coating/solder mask = 0.13 mm, internal B1 = 0.1 mm; 0.2 mm is 1.5x B4 — exposed pads/terminations (A6 0.6 mm) cannot be met on 0.5 mm-pitch parts, so the INA228 courtyard is exempt at 0.15 mm)**; host-to-controller 1.0 mm; via 0.6/0.3 mm (0.5/0.3 mm in a few congested spots), min track {s['min_track']:.2f} mm, copper-to-edge 0.3 mm. **PCBWay's current 4-layer minimum track/space/drill/annular-ring capability must be confirmed in their quote/DFM tool** (this build could not reach their site); the values above are well above the usual 0.1 mm / 0.2 mm drill minimums.
- Controlled impedance: none required (no high-speed nets; USB 2.0 full-speed D+/D- are short, 90 ohm not controlled in RC1 - review).
- Silkscreen: connector names, pin numbers, polarity, `OSBAMS Rev.2 Controller`, `RC1.2 2026-10-01`, `44 V / 10 A MAX`, `NOT FOR FABRICATION` (remove at release by editing the text in KiCad before the final export).

## Files
This package contains **no Gerber or drill files**: the earlier script-generated candidate Gerbers were removed so they cannot be used by mistake. Export Gerbers/drills from the final `.kicad_pcb` in your own KiCad 10 after your local ERC/DRC (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## Open fabrication gates
See `PCBWAY_RELEASE_CANDIDATE_REPORT.md` (BLOCKERS BEFORE PCBWAY ORDER).
"""
    return write("FABRICATION_NOTES.md", t)


def assembly_notes(s):
    smt = s["smd"]
    t = f"""# OSBAMS Rev.2 Controller — Assembly notes ({TODAY})

**{reports.NOTFAB}.**

## Assembly summary
- {smt} SMT/SMD-only footprints (top side) and {s['tht']} through-hole footprints (including connectors, 2 x VO610A-1 DIP-4, 2 x 1N4148 DO-35, JP1, mounting hole/test-point features are not parts).
- Parts are on the **top side only**; no bottom-side assembly. Test points are bare 1.5 mm pads (no component).
- **THT parts needing hand/selective soldering:** J1-J4 (Adam Tech EB21A-02-C), J5 (Molex 22-27-2031), J6 (22-27-2041), J7 (JST B4B-PH-K-S), JP1, U4/U5 (VO610A-1 DIP-4), D11/D12 (1N4148 DO-35), J9/J8 mixed SMT+THT shield.
- **Consigned vs sourced:** default is PCBWay-sourced. Owned parts that can be consigned (BOM column `PCBWay Source / Consign`): 2 x VO610A-1 (exactly the two needed), 2 x 1N4148, EB21A-02-C (5 owned, 4 needed), 1.5SMBJ48A (2 owned, 3 needed), SMBJ15A. VJ0805Y104JXXAT (2 owned) are used on the probe board.
- **Do not populate:** R1/R2 on the probe board (DNP). Everything on the controller BOM is fitted in the baseline (I2C2 pull-ups fitted).

## Polarity / orientation
- Diodes: pad 1 = cathode on every diode footprint (checked against the library geometry and the netlist; see `DFM_DFA_REPORT.md`). D1, D2, D5-D7, D9 SMA/SMB bars face pad 1; D11/D12 DO-35 band at pad 1 side; LEDs D3/D4/D10 pad 1 = cathode.
- U1 pin 1 dot top-left; U2 (MSOP-10) pin 1 dot; U3, U9, U10 SOT-23-6 pin 1; U6 QFN-20 pin 1 + exposed pad to GND_HOST; U7 SOIC-8 pin 1.
- J1-J4: pin 1 square pad, wire entry toward the board edge. Footprint `EB21A-02-C` follows the Adam Tech drawing (VERIFIED_LOCAL); the drawing does not number the pins, so pin 1 = the 2.50 mm end is a design convention.
- J5/J6/J7 are keyed (KK 254 / PH). J9 SWD is a shrouded keyed header. J8 USB-C front face overhangs the right edge by ~0.8 mm.

## CPL
`OSBAMS_Rev2_RC1_CPL.csv` (SMT) and `..._CPL_ALL.csv` use KiCad footprint-origin positions/rotations (mm, bottom-left origin, y up). **PCBWay's pick-and-place library rotation conventions differ for some packages (SOT-23-6, QFN-20, LQFP-64, SOIC-8, MSOP-10, diodes): verify every rotation in PCBWay's CAM preview before accepting.**

## First-article note
Build 2-3 boards. Bring-up order: power (+12V, 3V3, 3V3_A ripple), reset/SWD attach, 80 MHz clock, GPIO, I2C scan (INA228 0x40), UART echo through the isolator, feedback/E-stop/ARM readbacks, relay driver with the real K1 coil at 12.0 V.
"""
    return write("ASSEMBLY_NOTES.md", t)


def dfm_report(s, pol_notes, pol_errs):
    types = ", ".join(f"{k}: {v}" for k, v in sorted(s["drc_types"].items())) or "none"
    t = f"""# OSBAMS Rev.2 Controller — DFM / DFA report ({TODAY})

**{reports.NOTFAB}.** Automated checks are in the repository (`design/checks.py`, KiCad ERC/DRC). Human review of PCBWay's CAM feedback is still required.

## Electrical rule checks (KiCad 10.0.6)
- ERC (schematic, 11 sheets): **{s['erc']} violations**.
- DRC (PCB): **{s['drc_viol']} violations, {s['drc_unconn']} unconnected pads, {s['drc_fp']} footprint errors**. Violation types: {types}.
- Netlist: the KiCad schematic netlist was compared with the design intent (66+ nets, every pin): see `NETLIST_CHECK.txt`.

## Polarity
| Ref | Footprint | Check | Pad 1 net | Result |
|---|---|---|---|---|
""" + "\n".join(f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in pol_notes) + f"""

Result: {'**PASS**' if not pol_errs else '**FAIL: ' + '; '.join(pol_errs) + '**'}. (Rev.1's symbol-vs-footprint polarity defect is not repeated: every diode uses a KiCad symbol with K = pin 1 and a footprint with the cathode bar at pad 1.)

## Layout statistics
{s['tracks']} track segments, {s['vias']} vias, min track {s['min_track']:.2f} mm, min via {s['min_via']:.2f}/{s['min_via_drill']:.2f} mm, {s['smd']} SMD footprints, {s['tht']} through-hole footprints, 3 fiducials, 4 mounting holes, {sum(1 for c in D.COMPS.values() if c['key'] == 'TP')} test points.

## DFM items for review
- 0.5 mm pitch LQFP-64 and QFN-20: confirm PCBWay minimum solder-mask bridge and paste stencil; ENIG recommended.
- Via-in-pad is NOT used. Tracks to LQFP pads leave on the pad axis.
- THT connectors (EB21A-02-C) use a footprint drawn from the Adam Tech drawing EB21A-XX-C rev B (hole 1.30 mm, pad 2.6 mm [design choice], body 10.6 x 8.5 mm).
- Mounting holes are NPTH 3.2 mm; fiducials 1 mm / 2 mm opening at three corners.
- USB-C GCT USB4105-GF-A: confirm the shield tab/NPTH holes against the connector drawing; overhang 0.8 mm beyond the board edge is intentional.
- Isolation: the whole perimeter of the GND_HOST island is the controller/host boundary. A custom DRC rule enforces >= 1.0 mm between any host-net item and any controller-net item on every layer (3.0 mm in the ISO7721 area); `ISOLATION_CHECK.txt` lists the minimum per layer with coordinates. No track, via or pad of either domain lies in the other; the ISO7721 is the only crossing. The working voltage across the barrier is at most the 44 V ceiling (functional isolation; IPC-2221B coated 0.13 mm); the ISO7721 D-8 package ratings must be confirmed against the datasheet insulation tables.
- Kelvin pair (INA_INP/INA_INN) and the other pack-level nets use the 0.2 mm clearance class (see FABRICATION_NOTES for the IPC-2221B basis); routed as a pair, with 10 Ω surge resistors R42/R43 at the connector and 10 Ω R11/R12 at the INA228.

## DFA items for review
- Mixed SMT + THT; THT is hand/selective-solder.
- Reflow/wave: one-pass reflow plus manual THT is assumed.
- Fiducials present; no components under connectors; clearance between SMT parts >= 0.35 mm courtyard margin.
"""
    return write("DFM_DFA_REPORT.md", t)


def supply_chain():
    rows = reports.bom_rows()
    t = f"""# OSBAMS Rev.2 Controller — Supply-chain report ({TODAY})

**{reports.NOTFAB}.**

**Stock and lifecycle were NOT checked.** The build environment cannot reach distributor or manufacturer sites (HTTP 403). Every row below therefore shows `Stock Check Date: NOT CHECKED`. Lifecycle is `ACTIVE (user-confirmed)` only for INA228 and LMR14006; all other parts are `UNKNOWN (not checked)`. Approved alternates are proposals and are themselves UNVERIFIED.

| Item | MPN | Manufacturer | Evidence | Lifecycle | Source | Alternate |
|---|---|---|---|---|---|---|
""" + "\n".join(f"| {r['Reference(s)'] if len(r['Reference(s)']) < 28 else r['Reference(s)'][:25] + '...'} | {r['MPN']} | {r['Manufacturer']} | {r['Evidence Status']} | {r['Lifecycle']} | {r['PCBWay Source / Consign']} | {r['Approved Alternate']} |" for r in rows) + """

## Owned hardware (validation / fallback)
NUCLEO-L476RG (keep intact; ST-LINK probe), spare Adafruit INA228 modules (reference/comparison), RSA-20-50, 2 x VO610A-1, VJ0805Y104JXXAT x 2, 1N4148 x 2, 5 x EB21A-02-C, 2 x 1.5SMBJ48A, Durakool DG57CM relay, 2 x TC74A5-3.3VAT, existing Rev.1 components.

## Actions before an order
1. Query authorized-distributor stock/lifecycle for every MPN and fill `Supplier SKU` / `Stock Check Date` (BOM xlsx).
2. Decide consign vs PCBWay-sourced for the owned parts; the 3rd 1.5SMBJ48A and the ~25 x 0603 100 nF are not in stock and must be sourced.
3. Confirm the INA228AIDGSR / LMR14006YDDCR / ISO7721DR / CP2102N-A02-GQFN20 orderable suffixes.
"""
    return write("SUPPLY_CHAIN_REPORT.md", t)


def rc_report(s, net_errs, pol_errs):
    reg = json.load(open(os.path.join(ROOT, "calc", "datasheet_inputs.json")))["inputs"]
    c = Counter(e["evidence"] for e in reg)
    crit = [e for e in reg if e["critical"] and e["evidence"] != "VERIFIED_LOCAL"]
    drc_types = ", ".join(f"{k} {v}" for k, v in sorted(s["drc_types"].items())) or "none"
    t = f"""# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1 ({TODAY})

**Status: RELEASE CANDIDATE 1 — FOR REVIEW. NOT authorization to fabricate.** This report does not call the design final, production ready, hardware validated or released for fabrication; the evidence does not support those statements.

## READY FOR REVIEW
Everything below is complete and internally checked (KiCad 10.0.6 tooling in the build container, see `BUILD_ENVIRONMENT.md`):

- **Architecture** reconciled (rev D) and decisions closed: direct STM32L476RGT6, bare INA228, no 5 V rail (LMR14006Y → 3V3 → 3V3_A), TC74 on its own I²C2, isolated host path, SMD IRLML0060 relay driver with plain flyback.
- **Calculations** regenerated (`POWER_TREE_AND_CALCULATIONS.md`): ADC divider error split (divider ±0.43 % / reference), ADC protection analysis with no back-feed (powered / unpowered / reversed / transient, clamp currents, PA1 max voltage, leakage error), INA228 scaling (ADCRANGE 0, SHUNT_CAL 1250), buck design equations, relay driver, **VO610A stages recomputed from the guaranteed CTR (13 % @ 1 mA, 40 % @ 10 mA) with temperature/aging derates and 2× saturation margin — the arbitrary 20 % CTR is deleted**; ESTOP_SENSE 5.6 kΩ and RELAY_FB 3 × 4.7 kΩ both pass their own margin tests down to the supported range (RELAY_FB ≥ 24 V, supported pack range ≈ 30–44 V).
- **KiCad project** (`OSBAMS_Rev2_RC1.kicad_pro/.kicad_sch/.kicad_pcb`, 11 schematic pages, custom symbol/footprint libraries): standard KiCad 10 symbols; custom symbols only for INA228, LMR14006Y, ISO7721.
- **ERC (KiCad 10.0.6): {s['erc']} violations** (`ERC_REPORT.rpt`). A negative control (deleting a no-connect) was confirmed to make ERC fail, so the check is live.
- **Netlist check:** KiCad schematic netlist vs PCB pad nets — {len(net_errs)} mismatches (`NETLIST_CHECK.txt`); diode/LED polarity check — {'PASS' if not pol_errs else 'FAIL'} (cathode pad 1 on every diode footprint verified against the footprint library geometry and the nets).
- **4-layer PCB** 100 × 90 mm: L2 solid GND, L3 signal routing + GND fill, isolated GND_HOST island (3.0 mm gap in the ISO7721 area, 0.25 mm zone clearance elsewhere), analog zone away from the buck, Kelvin pair nets, 4 × M3, 3 fiducials, connector/polarity/revision/`44 V / 10 A MAX` silkscreen, 27 test points. Autorouted with Freerouting 1.9.0 and checked with KiCad DRC.
- **DRC (KiCad 10.0.6): {s['drc_viol']} violations, {s['drc_unconn']} unconnected pads, {s['drc_fp']} footprint errors** — types: {drc_types} (`DRC_REPORT.rpt`).
- **Outputs:** schematic PDF, Gerber + drill files and ZIP (named NOT_FOR_FABRICATION), BOM xlsx/csv, CPL (SMT and all parts), assembly drawing (top) and copper-layer PDFs, assembly notes, fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, evidence register ({c['VERIFIED_LOCAL']} VERIFIED_LOCAL / {c['USER_RELAYED_MANUFACTURER']} USER_RELAYED_MANUFACTURER / {c['UNVERIFIED']} UNVERIFIED), supply-chain report.
- **Remote TC74 probe PCB** (`probe/`): schematic, ERC and layout for the small pack-surface probe with the owned VJ0805Y104JXXAT at the sensor VDD.

## BLOCKERS BEFORE PCBWAY ORDER
Only items that genuinely must be resolved before ordering:

1. **Manufacturer-document verification** — {len(crit)} critical register entries are not VERIFIED_LOCAL (see `EVIDENCE_REGISTER.md`, `MANUFACTURER_DATA_RECONCILIATION.md`). Read locally from the supplied PDFs (VERIFIED_LOCAL): ISO7721, CP2102N, SRN6045TA-100M and the EB21A drawing. All other pin maps (INA228, LMR14006Y, IRLML0060, VO610A, TC74, STM32 LQFP64 pins) match the data relayed by the user but remain USER_RELAYED_MANUFACTURER until their datasheets are supplied. Still open: **IRLML0060 at a 3.3 V gate** (first-article VDS/coil-current measurement), STM32 POR/VDD max, DG57CM release time, connector footprint geometry beyond pitch/pin count, LMR14006Y SHDN threshold, INA228 differential input maximum.
1a. **LMR14006Y minimum on-time:** TON_MIN = 95 ns (relayed). 12 V passes; the 15 V corner is marginal at the highest fsw; the 24.4 V transient (64 ns) is below TON_MIN — no regulation claim there (pulse skipping expected), limited to ≈ 14–16 V steady-state input.
1b. **1.5SMBJ48A vs INA228 85 V:** clamp is 77.4 V only at 19.4 A; 100.6 V at the 8/20 µs rating point (97 A). Bounded credible transients (≤ 19.4 A) are within 85 V; fast ≥ 45 A surges are not protected. Owner sign-off (or the optional series-resistor/two-stage-clamp redesign) required — see calculations §2b.
2. **ERC/DRC and Gerber regeneration on your own KiCad 10 installation.** The ERC/DRC results above come from the build container; the Gerber/drill files in this package are exports of a script-generated design and must not be used for fabrication. Remaining DRC items ({s['drc_viol']}) must be reviewed and dispositioned (see `DFM_DFA_REPORT.md`).
3. **Protection calculation sign-off:** the ADC clamp/back-feed analysis depends on UNVERIFIED diode leakage/forward-voltage and on the MCU pin structure; the 3V3_A bleeder (R4) is fitted to guard the unknown, at 1 mA permanent load.
4. **Distributor stock / lifecycle / supplier SKUs** were not checked (sites unreachable); orderable suffixes (INA228AIDGSR, LMR14006YDDCR, ISO7721DR, CP2102N-A02-GQFN20, SS14-E3/61T) must be confirmed; only 2 of ~25 VJ0805-style 100 nF are owned, and a 3rd 1.5SMBJ48A is needed.
5. **PCBWay CPL rotations** must be checked in PCBWay's CAM preview (library rotation offsets differ).
6. Relay-feedback and E-stop resistor networks are sized from user-relayed CTR data with design-margin derates (0.8 × 0.8, UNVERIFIED); confirm with the official CTR-vs-IF curve.

*First-article measurements (3V3/3V3_A ripple, coil current, release time) are bring-up items, not order blockers.*

## Package contents
`OSBAMS_Rev2_RC1.kicad_pro/.kicad_sch/.kicad_pcb` (+ sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC1_Schematic.pdf`, `OSBAMS_Rev2_RC1_Gerbers_NOT_FOR_FABRICATION.zip`, `gerber/`, `drill/`, `OSBAMS_Rev2_RC1_BOM.xlsx/.csv`, `OSBAMS_Rev2_RC1_CPL.csv`, `OSBAMS_Rev2_RC1_CPL_ALL.csv`, `OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf`, `ASSEMBLY_NOTES.md/.pdf`, `FABRICATION_NOTES.md/.pdf`, `OSBAMS_Rev2_RC1_Test_Point_Map.pdf`, `POWER_TREE_AND_CALCULATIONS.md`, `DFM_DFA_REPORT.md`, `EVIDENCE_REGISTER.md/.json`, `MANUFACTURER_DATA_RECONCILIATION.md`, `SUPPLY_CHAIN_REPORT.md`, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `probe/`.
"""
    return write("PCBWAY_RELEASE_CANDIDATE_REPORT.md", t)

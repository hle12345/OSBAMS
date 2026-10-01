# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1.2e (2026-10-01)

**Status: RELEASE CANDIDATE 1.2e — FOR REVIEW. NOT final, NOT released for fabrication, NOT hardware validated.** Gerbers are intentionally not included: export them from the final PCB in your own KiCad 10 (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## READY FOR REVIEW
Checked with KiCad 10.0.6 in the build container (`BUILD_ENVIRONMENT.md`):

- **ERC: 0 violations.** **DRC: 0 violations, 0 unconnected pads, 0 footprint errors** (types: none). **Netlist vs PCB: 0 mismatches.** Diode/LED polarity: PASS.
- **Isolation:** every HOST-net item keeps ≥ 1.0 mm from every controller-net item on all layers (custom DRC rule; 3.0 mm in the ISO7721 area) — `ISOLATION_CHECK.txt`.
- **Pack-level clearance:** 0.2 mm class (IPC-2221B B4 0.13 mm × 1.5), INA228 courtyard exempt at 0.15 mm — see `FABRICATION_NOTES.md`; PCBWay capability to be confirmed in their tool.
- **Pack-sense protection — hot-plug and interruption bounds PASS; protection NOT closed.** Series resistors R41 (47 Ω) and R42/R43 (10 Ω) upstream of the TVS diodes; ≤ 76.5 V at the 18.5 A bound, hot-plug ≤ 60 V, limit 85 V. RC1.2e adds **D15 (SMF12CA) across IN+/IN−** because the INA228 differential limit (±40 V, relayed) is violated by a one-Kelvin-lead-open fault. Classification `MODELED_PASS / DATASHEET_VERIFICATION_OPEN`; `ESD_PROTECTION_OPEN` (ERJP08 overload rating 1000 V vs ≈ 1.3 kV modeled across R41 at 8 kV; a connector-level clamp is a likely RC1.3 change if bare pins are accessible). Open: resistor µs–ms pulse curve — `CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`.
- **CP2102N VBUS divider:** R38 19.1 kΩ / R39 47.5 kΩ — +0.12 V margin to VIH at VBUS 4.40 V / VDD 3.6 V / 1 % resistors (the 22.1 k reference is −16 mV there); pin ≤ 3.77 V at 5.25 V (limit 5.6 V) — §8.
- **Custom rule check:** `ISOLATION_RULE_CHECK.txt` shows the `.kicad_dru` is applied when the project is opened from a fresh folder (clean 0 violations; tightened rule → 131).
- **Buck:** XDR 12.0 V ±1 %; maximum continuous controller input 14.4 V; 24.4 V transient treated separately (pulse skipping, millivolt-level rail excursion) — §3.
- **IRLML0060:** kept; margin ≈ 7× the coil load by estimate; RDS(on) at 3.3 V not claimed as guaranteed; first-article measurements mandatory — §4.
- **Evidence:** VERIFIED_LOCAL 33 · USER_RELAYED_MANUFACTURER 40 · UNVERIFIED 19; classified by consequence in `EVIDENCE_RISK_CLASSIFICATION.md`. Read locally: ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing.
- **Outputs:** schematic PDF, BOM xlsx/csv (Qty, MPN, suffix status, source, DNP), CPL, assembly drawing, copper-layer PDF, assembly/fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, supply-chain report, evidence register, reconciliation, connector check, pre-PCBWay checklist, TC74 probe project (`probe/`).

## BLOCKERS BEFORE PCBWAY ORDER
1. **Connector footprints J5/J6 (Molex 22-27-2031/-2041) not compared with dimensioned drawings** (the 022272041 file is a 3D isometric without dimensions; the 022272031 sheet was not supplied). J7 (JST), J8 (GCT) and J9 (Samtec land pattern, replaced in RC1.2e) are verified — `CONNECTOR_FOOTPRINT_CHECK.md`.
1b. **Protection items open:** resistor pulse capability (Panasonic AOA0000C331.pdf), D15 SMF12CA datasheet, ESD first-article test — `CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`.
1a. **Residual (first-article):** TVS leakage vs temperature is not published by Bourns; covered by first-article measurement.
2. **Wrong-pinout-class datasheets still USER_RELAYED** (LMR14006Y, IRLML0060, VO610A, TC74; the INA228 datasheet has been read): they match the netlist but the PDFs have not been read — `EVIDENCE_RISK_CLASSIFICATION.md`.
3. **Your local actions** in `PRE_PCBWAY_RELEASE_CHECKLIST.md`: KiCad 10 ERC/DRC, Gerber/drill export, Gerber viewer inspection, PCBWay CAM and CPL inspection, stock/substitution review (27 critical register entries are not VERIFIED_LOCAL).
4. Open measured/first-article items are listed in `EVIDENCE_RISK_CLASSIFICATION.md` and are **not** order blockers.

## Package contents
KiCad project (`OSBAMS_Rev2_RC1.kicad_pro/.kicad_dru/.kicad_sch/.kicad_pcb`, 10 sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC1_Schematic.pdf`, BOM/CPL files, `OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf`, `OSBAMS_Rev2_RC1_Copper_Layers.pdf`, notes and reports listed above, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `ISOLATION_CHECK.txt`, `CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md`, `probe/`.

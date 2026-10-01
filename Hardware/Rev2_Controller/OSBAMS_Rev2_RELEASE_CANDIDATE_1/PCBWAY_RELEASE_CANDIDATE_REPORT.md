# PCBWAY RELEASE CANDIDATE REPORT — OSBAMS Rev.2 Controller RC1.2 (2026-10-01)

**Status: RELEASE CANDIDATE 1.2 — FOR REVIEW. NOT final, NOT released for fabrication, NOT hardware validated.** Gerbers are intentionally not included: export them from the final PCB in your own KiCad 10 (see `PRE_PCBWAY_RELEASE_CHECKLIST.md`).

## READY FOR REVIEW
Checked with KiCad 10.0.6 in the build container (`BUILD_ENVIRONMENT.md`):

- **ERC: 0 violations.** **DRC: 0 violations, 0 unconnected pads, 0 footprint errors** (types: none). **Netlist vs PCB: 0 mismatches.** Diode/LED polarity: PASS.
- **Isolation:** every HOST-net item keeps ≥ 1.0 mm from every controller-net item on all layers (custom DRC rule; 3.0 mm in the ISO7721 area) — `ISOLATION_CHECK.txt`.
- **Pack-level clearance:** 0.2 mm class (IPC-2221B B4 0.13 mm × 1.5), INA228 courtyard exempt at 0.15 mm — see `FABRICATION_NOTES.md`; PCBWay capability to be confirmed in their tool.
- **Pack-sense protection — PASS under model assumptions, NOT fully closed:** series surge resistors R41 (47 Ω) and R42/R43 (10 Ω) upstream of the 1.5SMBJ48A diodes; defined-transient model: ≤ 76.5 V (interruption bound ≤ 18.5 A), hot-plug ≤ 60 V, limit 85 V. Open source values: ERJ-P08F pulse rating/suffix (Panasonic) and 1.5SMBJ48A leakage (Bourns). Surge-capability numbers are model results, not validated limits — `REV2_CALCULATIONS.md` §2b.
- **CP2102N VBUS divider:** R38 19.1 kΩ / R39 47.5 kΩ — +0.12 V margin to VIH at VBUS 4.40 V / VDD 3.6 V / 1 % resistors (the 22.1 k reference is −16 mV there); pin ≤ 3.77 V at 5.25 V (limit 5.6 V) — §8.
- **Custom rule check:** `ISOLATION_RULE_CHECK.txt` shows the `.kicad_dru` is applied when the project is opened from a fresh folder (clean 0 violations; tightened rule → 131).
- **Buck:** XDR 12.0 V ±1 %; maximum continuous controller input 14.4 V; 24.4 V transient treated separately (pulse skipping, millivolt-level rail excursion) — §3.
- **IRLML0060:** kept; margin ≈ 7× the coil load by estimate; RDS(on) at 3.3 V not claimed as guaranteed; first-article measurements mandatory — §4.
- **Evidence:** VERIFIED_LOCAL 11 · USER_RELAYED_MANUFACTURER 50 · UNVERIFIED 17; classified by consequence in `EVIDENCE_RISK_CLASSIFICATION.md`. Read locally: ISO7721, CP2102N, SRN6045TA-100M, EB21A drawing.
- **Outputs:** schematic PDF, BOM xlsx/csv (Qty, MPN, suffix status, source, DNP), CPL, assembly drawing, copper-layer PDF, assembly/fabrication notes, test-point map, power-tree/calculation report, DFM/DFA report, supply-chain report, evidence register, reconciliation, connector check, pre-PCBWay checklist, TC74 probe project (`probe/`).

## BLOCKERS BEFORE PCBWAY ORDER
1. **Connector footprints (J5 Molex ×2, J7 JST, J8 GCT USB-C, J9 Samtec) not compared with the official drawings** — `CONNECTOR_FOOTPRINT_CHECK.md` (drawings needed; none supplied, manufacturer sites unreachable).
1a. **Pack-sense protection source values unread:** Panasonic ERJ-P08F pulse rating/suffix and Bourns 1.5SMBJ48A leakage vs voltage/temperature — protection is not fully closed until they are.
2. **Wrong-pinout-class datasheets still USER_RELAYED** (INA228, LMR14006Y, IRLML0060, VO610A, TC74): they match the netlist but the PDFs have not been read — `EVIDENCE_RISK_CLASSIFICATION.md`.
3. **Your local actions** in `PRE_PCBWAY_RELEASE_CHECKLIST.md`: KiCad 10 ERC/DRC, Gerber/drill export, Gerber viewer inspection, PCBWay CAM and CPL inspection, stock/substitution review (31 critical register entries are not VERIFIED_LOCAL).
4. Open measured/first-article items are listed in `EVIDENCE_RISK_CLASSIFICATION.md` and are **not** order blockers.

## Package contents
KiCad project (`OSBAMS_Rev2_RC1.kicad_pro/.kicad_dru/.kicad_sch/.kicad_pcb`, 10 sheets, `OSBAMS_Rev2.kicad_sym`, `OSBAMS_Rev2.pretty`, lib tables), `OSBAMS_Rev2_RC1_Schematic.pdf`, BOM/CPL files, `OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf`, `OSBAMS_Rev2_RC1_Copper_Layers.pdf`, notes and reports listed above, `ERC_REPORT.rpt`, `DRC_REPORT.rpt`, `NETLIST_CHECK.txt`, `ISOLATION_CHECK.txt`, `probe/`.

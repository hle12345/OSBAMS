#!/usr/bin/env python3
"""Assemble the RC1 package after the layout is routed: silkscreen cleanup, DRC, exports, BOM/CPL/PDF/reports, netlist check."""
import json, os, shutil, subprocess, sys, zipfile

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
import build_rc1 as B
from design import checks, reports, rc_docs, rc_docs2, rev2_design as D

RC = B.RC
W = B.W


def chroot_steps():
    B.kc(f"cd {W} && python3 -m design.silkfix")
    B.kc(f"cd {W} && python3 -m design.route fill")
    B.drc()
    open(os.path.join(RC, 'ISOLATION_CHECK.txt'), 'w').write(B.kc(f"cd {W} && python3 -m design.isocheck"))
    open(os.path.join(RC, 'ISOLATION_RULE_CHECK.txt'), 'w').write('Custom-rule activity check (design/isorule_test.py, KiCad 10.0.6): the project is copied to a fresh folder and DRC is run.\n' + B.kc(f"cd {W} && python3 -m design.isorule_test"))
    open(os.path.join(ROOT, 'build', 'connfp.txt'), 'w').write(B.kc(f"cd {W} && python3 -m design.connfp"))
    B.outputs()
    B.kc(f"cd {W}/OSBAMS_Rev2_RC13 && {B.CLI} sch export netlist --format kicadsexpr -o {W}/build/rc1.net {B.SCH}")


def main():
    chroot_steps()
    shutil.copy(os.path.join(ROOT, "build", "boarddata.json"), "/tmp/boarddata_copy.json")
    # reload board data in the reports module (it was read at import time before the export)
    import importlib
    importlib.reload(reports)
    importlib.reload(rc_docs)
    importlib.reload(rc_docs2)
    # netlist check
    net = checks.read_netlist(os.path.join(ROOT, "build", "rc1.net"))
    n, errs = checks.pcb_vs_schematic(net, reports.BOARD)
    pol_errs, pol_notes = checks.diode_polarity(reports.BOARD, D.COMPS)
    with open(os.path.join(RC, "NETLIST_CHECK.txt"), "w") as f:
        f.write("OSBAMS Rev.2 RC1 - KiCad schematic netlist vs PCB pad nets (KiCad 10.0.6)\n")
        f.write(f"nets in schematic netlist: {len(net)}; pads compared: {n}; mismatches: {len(errs)}\n")
        f.write("\n".join(errs) + ("\n" if errs else ""))
        f.write("\nDiode polarity (cathode pad = pad 1 on every diode/LED footprint):\n")
        for r in pol_notes:
            f.write("  " + " | ".join(r) + "\n")
        f.write("polarity errors: " + (", ".join(pol_errs) if pol_errs else "none") + "\n")
    # BOM / CPL / test points
    reports.write_bom(os.path.join(RC, "OSBAMS_Rev2_RC13_BOM.xlsx"))
    smt, allp = reports.write_cpl(os.path.join(RC, "OSBAMS_Rev2_RC13_CPL.csv"), os.path.join(RC, "OSBAMS_Rev2_RC13_CPL_ALL.csv"))
    ntp = reports.write_tp_map(os.path.join(RC, "OSBAMS_Rev2_RC13_Test_Point_Map.pdf"))
    shutil.copy(os.path.join(ROOT, "DATASHEET_VERIFICATION.md"), os.path.join(RC, "EVIDENCE_REGISTER.md"))
    shutil.copy(os.path.join(ROOT, "MANUFACTURER_DATA_RECONCILIATION.md"), os.path.join(RC, "MANUFACTURER_DATA_RECONCILIATION.md"))
    shutil.copy(os.path.join(ROOT, "calc", "datasheet_inputs.json"), os.path.join(RC, "EVIDENCE_REGISTER.json"))
    shutil.copy(os.path.join(ROOT, "REV2_CALCULATIONS.md"), os.path.join(RC, "POWER_TREE_AND_CALCULATIONS.md"))
    shutil.copy(os.path.join(ROOT, "REV2_BLOCK_DIAGRAM.png"), os.path.join(RC, "OSBAMS_Rev2_RC13_Block_Diagram.png"))
    # documents
    s = rc_docs.stats()
    rc_docs.fabrication_notes(s); rc_docs.assembly_notes(s); rc_docs.dfm_report(s, pol_notes, pol_errs); rc_docs.supply_chain()
    rc_docs2.evidence_risk(); rc_docs2.connector_check(); rc_docs2.pre_pcbway_checklist(); rc_docs2.rc_report(s, errs, pol_errs)
    for md, title in (("FABRICATION_NOTES.md", "Fabrication notes"), ("ASSEMBLY_NOTES.md", "Assembly notes")):
        reports.md_to_pdf(os.path.join(RC, md), os.path.join(RC, md.replace(".md", ".pdf")), "OSBAMS Rev.2 Controller RC1 - " + title)
    print("smt", smt, "all", allp, "tp", ntp, "stats", {k: v for k, v in s.items() if k != "drc_types"}, dict(s["drc_types"]))
    return s, errs, pol_errs


if __name__ == "__main__":
    main()

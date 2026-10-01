#!/usr/bin/env python3
"""OSBAMS Rev.2 RC1 build orchestrator (host).

Steps run inside the KiCad 10 container via tools/kc10 (see BUILD_ENVIRONMENT.md):
  schematic -> ERC -> PCB -> autoroute -> DRC -> outputs;  host: BOM/CPL/PDF/reports.
Usage: python3 Hardware/Rev2_Controller/build_rc1.py [sch|pcb|route|outputs|reports|all]
"""
import os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.dirname(__file__))
RC = os.path.join(ROOT, "OSBAMS_Rev2_RELEASE_CANDIDATE_1")
KC = os.path.join(ROOT, "tools", "kc10")
W = "/work/Hardware/Rev2_Controller"
CLI = "/usr/bin/kicad-cli"
PCB = "OSBAMS_Rev2_RC1.kicad_pcb"
SCH = "OSBAMS_Rev2_RC1.kicad_sch"


def kc(cmd):
    r = subprocess.run([KC, "bash", "-c", cmd], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit(f"step failed: {cmd[:120]}")
    return r.stdout


def sch():
    kc(f"cd {W} && python3 -m design.build_sch && python3 -m design.custom_fp && python3 -m design.probegen")
    kc(f"cd {W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1 && for f in *.kicad_sch; do {CLI} sch upgrade $f >/dev/null 2>&1; done; "
       f"{CLI} sch erc --severity-all --format report -o {W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1/ERC_REPORT.rpt {SCH}")
    kc(f"cd {W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1/probe && for f in *.kicad_sch; do {CLI} sch upgrade $f >/dev/null 2>&1; done; "
       f"{CLI} sch erc --severity-all --format report -o {W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1/probe/ERC_REPORT_PROBE.rpt OSBAMS_Rev2_TC74_Probe_RC1.kicad_sch")
    print(open(os.path.join(RC, "ERC_REPORT.rpt")).read()[:300])


def pcb():
    kc(f"cd {W} && python3 -m design.pcbgen")


def route():
    kc(f"cd {W} && python3 -m design.route export /tmp/rc1_edit.dsn")
    shutil.copy("/opt/kicad10/tmp/rc1_edit.dsn", "/tmp/rc1_edit.dsn")
    if os.path.exists("/tmp/rc1.ses"):
        os.remove("/tmp/rc1.ses")
    subprocess.run(["/tmp/runfr19.sh"], check=False)       # Freerouting 1.9.0 under xvfb (see BUILD_ENVIRONMENT.md)
    shutil.copy("/tmp/rc1.ses", "/opt/kicad10/tmp/rc1.ses")
    kc(f"cd {W} && python3 -m design.route import /tmp/rc1.ses")


def drc():
    kc(f"cd {W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1 && {CLI} pcb drc --severity-all --format report --units mm -o {W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1/DRC_REPORT.rpt {PCB}")


def outputs():
    o = f"{W}/OSBAMS_Rev2_RELEASE_CANDIDATE_1"
    kc(f"cd {o} && rm -rf gerber drill && mkdir -p gerber drill && "
       f"{CLI} pcb export gerbers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts -o gerber/ {PCB} && "
       f"{CLI} pcb export drill --format excellon --excellon-units mm --excellon-separate-th --generate-map --map-format pdf -o drill/ {PCB} && "
       f"{CLI} sch export pdf -o OSBAMS_Rev2_RC1_Schematic.pdf {SCH} && "
       f"{CLI} pcb export pdf --layers F.Fab,F.Silkscreen,Edge.Cuts,F.Courtyard -o OSBAMS_Rev2_RC1_Assembly_Drawing_Top.pdf {PCB} && "
       f"{CLI} pcb export pdf --layers F.Cu,In1.Cu,In2.Cu,B.Cu,Edge.Cuts -o OSBAMS_Rev2_RC1_Copper_Layers.pdf {PCB} && "
       f"{CLI} pcb export pos --format csv --units mm --side both -o build_pos.csv {PCB}")
    kc(f"cd {W} && python3 -m design.export_data")


def main(step="all"):
    steps = {"sch": sch, "pcb": pcb, "route": route, "drc": drc, "outputs": outputs}
    for s in (steps if step == "all" else [step]):
        print("==", s)
        steps[s]()


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["all"]))

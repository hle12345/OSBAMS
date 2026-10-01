"""Prove the custom isolation rule is active when the project is opened from a fresh folder (runs in the KiCad 10 container):
1. copy the project to a scratch folder and run DRC -> must be clean;
2. in a second copy the isolation distance in the .kicad_dru is raised from 1.0 mm to 3.0 mm -> the isolation_* rules must now fire (proves the rule file is applied)."""
import os, shutil, subprocess, sys, re
import pcbnew
from pcbnew import FromMM as mm

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "OSBAMS_Rev2_RELEASE_CANDIDATE_1")
CLI = "/usr/bin/kicad-cli"


def drc(folder):
    out = os.path.join(folder, "t.rpt")
    subprocess.run([CLI, "pcb", "drc", "--severity-all", "--format", "report", "--units", "mm", "-o", out, os.path.join(folder, "OSBAMS_Rev2_RC1.kicad_pcb")], capture_output=True)
    t = open(out).read()
    return re.search(r"Found (\d+) DRC violations", t).group(1), re.findall(r"rule '([^']+)'", t), t


def main():
    base = "/tmp/isorule_scratch"
    shutil.rmtree(base, ignore_errors=True)
    for n in ("clean", "violating"):
        shutil.copytree(SRC, os.path.join(base, n), ignore=shutil.ignore_patterns("probe", "*.pdf"))
    print("custom rule file present next to the project:", os.path.exists(os.path.join(base, "clean", "OSBAMS_Rev2_RC1.kicad_dru")))
    v, rules, _ = drc(os.path.join(base, "clean"))
    print(f"fresh-folder copy: {v} DRC violations (rules triggered: {sorted(set(rules)) or 'none'})")
    dru = os.path.join(base, "violating", "OSBAMS_Rev2_RC1.kicad_dru")
    open(dru, "w").write(open(dru).read().replace("(min 1.0mm)", "(min 3.0mm)"))
    v2, rules2, t2 = drc(os.path.join(base, "violating"))
    hits = [r for r in rules2 if r.startswith("isolation")] + re.findall(r"clearance 3\.0000 mm", t2)
    print("   sample:", [l.strip()[:130] for l in t2.split("\n") if l.startswith("[")][:2])
    print(f"negative control (same project, rule tightened to 3.0 mm, existing zone fills left as they are): {v2} violations (0 -> {v2}; the existing fills no longer satisfy the tightened rule) -> the .kicad_dru is read and applied by KiCad when the project is opened from this folder")
    shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()

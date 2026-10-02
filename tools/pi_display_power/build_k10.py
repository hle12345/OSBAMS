#!/usr/bin/env python3
"""Build both Pi-power projects with KiCad 10 (container wrapper kc10_pi) and run ERC / DRC / schematic-parity / custom checks.
usage: REL=RC2 python3 build_k10.py [out_root]   (out_root default = repo root; creates OSBAMS_Pi_Display_Power_RevA_$REL and OSBAMS_Pi_Power_Interposer_RevA_$REL)
No Gerbers are generated (the owner exports them from the final boards in KiCad 10)."""
import os, sys, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
REL = os.environ.get("REL", "RC2"); ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else REPO
N, NI = "OSBAMS_Pi_Display_Power_RevA", "OSBAMS_Pi_Power_Interposer_RevA"
PWR, IP = f"{ROOT}/{N}_{REL}", f"{ROOT}/{NI}_{REL}"
W = lambda p: "/work" + p[len(REPO):]
KC = os.path.join(HERE, "kc10_pi")
env = dict(os.environ, REL=REL)
def run(cmd, cwd=HERE, check=True):
    print("$", cmd[:150]); r = subprocess.run(cmd, shell=True, cwd=cwd, env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip(); print("\n".join(l for l in out.splitlines() if "Debug:" not in l)[-1500:])
    if check and r.returncode: sys.exit("FAILED: " + cmd)
    return r
def kc(cmd, check=True): return run(f'{KC} bash -c "export REL={REL}; cd {W(HERE)} && {cmd}"', check=check)
for d in (PWR, IP):
    for sub in ("kicad", "bom", "docs", "reports"): os.makedirs(f"{d}/{sub}", exist_ok=True)
os.makedirs(f"{PWR}/cpl", exist_ok=True)
# ---- power board
kc(f"python3 build_pcb.py {W(PWR)}/kicad/{N}.kicad_pcb")
run(f"python3 build_sch.py {PWR}/kicad/{N}.kicad_sch && python3 k10_symlib.py {PWR}/kicad/{N}.kicad_sch")
kc(f"python3 k10_sync.py {W(PWR)}/kicad {N} && python3 k10_finalize.py {W(PWR)}/kicad/{N}.kicad_pcb")
# ---- interposer
kc(f"python3 build_interposer.py {W(IP)}")
run(f"python3 k10_symlib.py {IP}/kicad/{NI}.kicad_sch")
kc(f"python3 k10_sync.py {W(IP)}/kicad {NI} && python3 k10_finalize.py {W(IP)}/kicad/{NI}.kicad_pcb")
# ---- KiCad 10 ERC / DRC / parity
kc(f"python3 k10_isolation.py {W(PWR)}/kicad {N} 8")
for d, n in ((PWR, N), (IP, NI)):
    k = f"{W(d)}/kicad"; rp = f"{W(d)}/reports"
    kc(f"cd {k} && kicad-cli sch erc --severity-all --format report -o {rp}/ERC_report_kicad10.rpt {n}.kicad_sch", check=False)
    kc(f"cd {k} && kicad-cli pcb drc --severity-all --schematic-parity --format report --units mm -o {rp}/DRC_report_kicad10.rpt {n}.kicad_pcb", check=False)
    for f in ("ERC_report_kicad10.rpt", "DRC_report_kicad10.rpt"):
        t = open(f"{d}/reports/{f}").read(); import re
        print(f"== {os.path.basename(d)} {f}:", re.findall(r"(?:ERC messages:.*|\*\* Found .*)", t))
# ---- custom checks (netlist/pin map/isolation) inside the container (python3 + pcbnew 10 + kicad-cli 10)
kc(f"python3 check_design.py {W(PWR)}", check=False)
kc(f"python3 check_interposer.py {W(IP)}", check=False)
run(f"python3 check_stack_height.py {IP}", check=False); run(f"python3 check_pi5_keying.py {IP}", check=False)
# ---- outputs (BOM/CPL/drawings/budget) - no Gerbers
run(f"python3 make_outputs.py {PWR}"); run(f"python3 make_figs.py {PWR}"); run(f"python3 voltage_budget.py {PWR}"); run(f"python3 power_budget_rc2.py {PWR}")
run(f"python3 make_interposer_outputs.py {IP}")
# ---- static docs (rc2_docs/), READMEs with the revision substituted
for src, dst in (("power", PWR), ("interposer", IP)):
    for f in os.listdir(f"{HERE}/rc2_docs/{src}"): shutil.copy(f"{HERE}/rc2_docs/{src}/{f}", f"{dst}/docs/{f}")
for f, dst in (("power_README.md", PWR), ("interposer_README.md", IP)):
    open(f"{dst}/README.md", "w").write(open(f"{HERE}/rc2_docs/{f}").read().replace("{REL}", REL))
for f in ("Keying_analysis.md",): pass
print("build_k10 done:", PWR, IP)

#!/usr/bin/env python3
"""Build OSBAMS_Pi_Power_Carrier_RevB_<REL> (combined power board + Pi interposer) with KiCad 10 and run ERC / DRC / schematic parity / isolation / pin-map checks.
usage: REL=RC1 python3 build_carrier_k10.py [out_root]   (no Gerbers)"""
import os, sys, shutil, subprocess, re
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
REL = os.environ.get("REL", "RC1"); ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else REPO
sys.path.insert(0, HERE)
from parts_carrier import NAME
PRJ = f"{ROOT}/{NAME}_{REL}"
W = lambda p: "/work" + p[len(REPO):]
KC = os.path.join(HERE, "kc10_pi"); env = dict(os.environ, REL=REL)
def run(cmd, check=True):
    print("$", cmd[:140]); r = subprocess.run(cmd, shell=True, cwd=HERE, env=env, capture_output=True, text=True)
    o = (r.stdout + r.stderr).strip(); print("\n".join(l for l in o.splitlines() if "Debug:" not in l)[-1200:])
    if check and r.returncode: sys.exit("FAILED: " + cmd)
    return r
def kc(cmd, check=True): return run(f'{KC} bash -c "export REL={REL}; cd {W(HERE)} && {cmd}"', check=check)
for sub in ("kicad", "bom", "cpl", "docs", "reports"): os.makedirs(f"{PRJ}/{sub}", exist_ok=True)
K = f"{PRJ}/kicad"; KW = W(K)
kc(f"python3 build_carrier_pcb.py {KW}/{NAME}.kicad_pcb")
run(f"python3 build_carrier_sch.py {K}/{NAME}.kicad_sch && python3 k10_symlib.py {K}/{NAME}.kicad_sch")
kc(f"python3 k10_sync.py {KW} {NAME} && python3 k10_finalize.py {KW}/{NAME}.kicad_pcb")
kc(f"python3 k10_isolation.py {KW} {NAME} 10")
kc(f"cd {KW} && kicad-cli sch erc --severity-all --format report -o {W(PRJ)}/reports/ERC_report_kicad10.rpt {NAME}.kicad_sch", check=False)
kc(f"cd {KW} && kicad-cli pcb drc --severity-all --schematic-parity --format report --units mm -o {W(PRJ)}/reports/DRC_report_kicad10.rpt {NAME}.kicad_pcb", check=False)
for f in ("ERC_report_kicad10.rpt", "DRC_report_kicad10.rpt"):
    print(f"== {f}:", re.findall(r"(?:ERC messages:.*|\*\* Found .*)", open(f"{PRJ}/reports/{f}").read()))
kc(f"python3 check_carrier.py {W(PRJ)}", check=False)
run(f"python3 check_carrier_mech.py {PRJ}", check=False)
run(f"python3 make_carrier_outputs.py {PRJ}"); run(f"python3 power_budget_carrier.py {PRJ}")
for f in os.listdir(f"{HERE}/carrier_docs"): shutil.copy(f"{HERE}/carrier_docs/{f}", f"{PRJ}/docs/{f}")
t = open(f"{PRJ}/docs/README.md").read().replace("{REL}", REL); os.replace(f"{PRJ}/docs/README.md", f"{PRJ}/README.md"); open(f"{PRJ}/README.md", "w").write(t)
print("build_carrier_k10 done:", PRJ)

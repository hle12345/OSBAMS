#!/usr/bin/python3
"""Interposer schematic <-> PCB connectivity + pin-map checks (custom, NOT KiCad ERC). /usr/bin/python3."""
import re, sys, subprocess, pcbnew
D = sys.argv[1]; N = "OSBAMS_Pi_Power_Interposer_RevA"
net = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", "/dev/stdout", f"{D}/kicad/{N}.kicad_sch"], capture_output=True, text=True).stdout
sch = {}; unc = 0
for ch in net.split("(net (code")[1:]:
    n = re.search(r'\(name "([^"]+)"\)', ch).group(1).lstrip("/")
    if n.startswith("unconnected"): unc += 1; continue
    sch[n] = {(r, p) for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', ch)}
b = pcbnew.LoadBoard(f"{D}/kicad/{N}.kicad_pcb"); pc = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname(): pc.setdefault(p.GetNetname(), set()).add((fp.GetReference(), p.GetNumber()))
res = []; fail = 0
for n in sorted(set(sch) | set(pc)):
    ok = sch.get(n) == pc.get(n); fail += not ok; res.append(("PASS " if ok else "FAIL ") + f"Net {n}: schematic {len(sch.get(n, []))} pins vs PCB {len(pc.get(n, []))} pads")
want5 = {("J1", "1"), ("J1", "2"), ("J2", "2"), ("J2", "4")}; wantg = {("J1", "3"), ("J1", "4"), ("J2", "6"), ("J2", "9"), ("J2", "14"), ("J2", "20")}
for nm, w in (("5V_PI", want5), ("PI_GND", wantg)):
    ok = pc.get(nm) == w; fail += not ok; res.append(("PASS " if ok else "FAIL ") + f"{nm} = J1 pins + Pi header pins as designed (+5 V: 2,4; GND: 6,9,14,20)")
res.append(f"INFO  {unc} unconnected (no-connect) nets = {unc} header pins (expect 34)"); fail += unc != 34
res.append("PASS 5V_PI and PI_GND share no pad" if not (sch["5V_PI"] & sch["PI_GND"]) else "FAIL shorted")
mh = [f.GetReference() for f in b.GetFootprints() if f.GetReference().startswith(("M", "K"))]
res.append(f"INFO  mounting/key holes: {', '.join(sorted(mh))}")
open(f"{D}/reports/ERC_equivalent_connectivity_report.txt", "w").write("Interposer custom connectivity check (NOT KiCad ERC; run ERC in KiCad 10)\n\n" + "\n".join(res) + f"\n\nRESULT: {'FAIL' if fail else 'PASS'}\n")
print("\n".join(res)); print("fail:", fail)

#!/usr/bin/python3
"""Custom consistency checks (NOT a substitute for KiCad ERC/DRC). Run with /usr/bin/python3."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import FLAG_NETS
import re, sys, subprocess, math, pcbnew
D = sys.argv[1]; K = f"{D}/kicad/OSBAMS_Pi_Display_Power_RevA"
net = subprocess.run(["kicad-cli","sch","export","netlist","--format","kicadsexpr","-o","/dev/stdout",K+".kicad_sch"],capture_output=True,text=True).stdout
nets = {}
for chunk in net.split("(net (code")[1:]:
    name = re.search(r'\(name "([^"]+)"\)', chunk).group(1).lstrip("/")
    nets[name] = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\).*?\(pintype "([^"]+)"\)', chunk)
out = []; fail = 0
def chk(ok, msg):
    global fail; out.append(("PASS  " if ok else "FAIL  ") + msg); fail += (not ok)
# 1. schematic vs PCB net parity
b = pcbnew.LoadBoard(K + ".kicad_pcb")
pcbn = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname(): pcbn.setdefault(p.GetNetname(), set()).add((fp.GetReference(), p.GetNumber()))
sch = {n: {(r, p) for r, p, t in v} for n, v in nets.items() if not n.startswith("unconnected")}
for n in sorted(set(sch) | set(pcbn)):
    chk(sch.get(n) == pcbn.get(n), f"Net {n}: schematic pins == PCB pads  ({len(sch.get(n, []))} vs {len(pcbn.get(n, []))})")
# 2. ERC-like rules
for n, v in nets.items():
    if n.startswith("unconnected"): continue
    types = [t for _, _, t in v]
    if "power_in" in types: chk(("power_out" in types or n in FLAG_NETS), f"Net {n}: power_in pin has a driver / PWR_FLAG")
    chk(len(v) >= 2, f"Net {n}: at least 2 connections")
chk(not (set(sch["PI_GND"]) & set(sch["12V_GND"])) , "PI_GND and 12V_GND share no pin")
u1 = {n for n, v in nets.items() for r, p, t in v if r == "U1" and p == "3"}
chk(all(n.startswith("unconnected") for n in u1), "U1 pin 3 (ON/OFF) unconnected (open) - confirm vs datasheet")
# 3. isolation: primary vs secondary copper gap
PRI = {"+12V_IN", "+12V_F", "12V_GND"}; SEC = {"5V_ISO_RAW", "5V_PI", "PI_GND", "PG_LED_A"}
def boxes(nset):
    r = []
    for t in b.GetTracks(): 
        if t.GetNetname() in nset: r.append(t.GetBoundingBox())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in nset: r.append(p.GetBoundingBox())
    for z in b.Zones():
        if z.GetNetname() in nset:
            for l in z.GetLayerSet().Seq():
                if z.HasFilledPolysForLayer(l):
                    r.append(z.GetFilledPolysList(l).BBox())
    return r
bp, bs = boxes(PRI), boxes(SEC)
pmax = max(x.GetRight() for x in bp) / 1e6; smin = min(x.GetLeft() for x in bs) / 1e6
chk(smin - pmax >= 8.0, f"Min primary-to-secondary copper gap = {smin - pmax:.2f} mm (primary max x {pmax:.2f}, secondary min x {smin:.2f}); target >= 8 mm (U1 internal barrier governs; module datasheet spacing NOT verified)")
bad = [(x, y) for x in bp for y in bs if x.Intersects(y)]
chk(not bad, "No primary/secondary copper bounding-box overlap")
for fp in b.GetFootprints():
    if fp.GetReference().startswith(("FID",)): continue
chk(sum(1 for fp in b.GetFootprints() if fp.GetReference().startswith("H")) == 4, "4 mounting holes")
chk(sum(1 for fp in b.GetFootprints() if fp.GetReference().startswith("FID")) >= 2, ">=2 fiducials")
open(f"{D}/reports/ERC_equivalent_connectivity_report.txt", "w").write(
 "OSBAMS_Pi_Display_Power_RevA RC1 - custom connectivity / isolation checks\n"
 "!! This is NOT KiCad ERC. kicad-cli 7.0.11 in the build container has no 'sch erc' command.\n"
 "!! Official KiCad ERC must still be run in KiCad 8+ and recorded before any FINAL status.\n\n" + "\n".join(out) + f"\n\nRESULT: {'FAIL' if fail else 'PASS'} ({fail} failures)\n")
print("\n".join(out)); print("fail:", fail)

#!/usr/bin/python3
"""Custom consistency checks (NOT a substitute for KiCad ERC/DRC). Run with /usr/bin/python3."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import FLAG_NETS
import re, sys, subprocess, math, pcbnew
D = sys.argv[1]; K = f"{D}/kicad/OSBAMS_Pi_Display_Power_RevA"
subprocess.run(["kicad-cli","sch","export","netlist","--format","kicadsexpr","-o","/tmp/_chk.net",K+".kicad_sch"],capture_output=True,text=True); net = open("/tmp/_chk.net").read()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexp
nets = {k.lstrip("/"): v for k, v in sexp.read_netlist(net).items()}
out = []; fail = 0
def chk(ok, msg):
    global fail; out.append(("PASS  " if ok else "FAIL  ") + msg); fail += (not ok)
# 1. schematic vs PCB net parity
b = pcbnew.LoadBoard(K + ".kicad_pcb")
pcbn = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() and not p.GetNetname().lstrip('/').startswith('unconnected'): pcbn.setdefault(p.GetNetname().lstrip('/'), set()).add((fp.GetReference(), p.GetNumber()))
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
# 2b. polarity and connector pin numbering (from the PCB pads, which the parity check ties to the schematic)
pn = {(fp.GetReference(), p.GetNumber()): p.GetNetname().lstrip("/") for fp in b.GetFootprints() for p in fp.Pads()}
for (r, n), want in {("TVS1", "1"): "+12V_F", ("TVS1", "2"): "12V_GND", ("D1", "1"): "PI_GND", ("D1", "2"): "PG_LED_A", ("C2", "1"): "+12V_F", ("C2", "2"): "12V_GND",
                     ("C4", "1"): "5V_PI", ("C4", "2"): "PI_GND", ("J_IN", "1"): "+12V_IN", ("J_IN", "2"): "12V_GND", ("J_OUT", "1"): "5V_PI", ("J_OUT", "2"): "5V_PI",
                     ("J_OUT", "3"): "PI_GND", ("J_OUT", "4"): "PI_GND", ("J_DISP", "1"): "5V_PI", ("J_DISP", "2"): "PI_GND", ("U1", "1"): "+12V_F", ("U1", "2"): "12V_GND",
                     ("U1", "4"): "5V_ISO_RAW", ("U1", "5"): "PI_GND", ("U1", "6"): "TRIM", ("F1", "1"): "+12V_IN", ("F1", "2"): "+12V_F", ("F2", "1"): "5V_ISO_RAW", ("F2", "2"): "5V_PI"}.items():
    chk(pn.get((r, n)) == want, f"Polarity/pinout {r} pin {n} = {want}  (PCB: {pn.get((r, n))})")
# 2c. U1 footprint vs the Mean Well drawing (bottom view u across 25.4 mm, v along 50.8 mm): the PCB top view is the mirror image -> dx = 25.4 - v, dy = 12.7 - u (a reflection)
u1 = [f for f in b.GetFootprints() if f.GetReference() == "U1"][0]; c = u1.GetPosition()
draw = {"1": (5.08, 48.26), "2": (10.16, 48.26), "3": (20.32, 48.26), "4": (2.54, 2.54), "5": (12.7, 2.54), "6": (22.86, 2.54)}
for n_, (uu, vv) in draw.items():
    pp = [p for p in u1.Pads() if p.GetNumber() == n_][0].GetPosition(); gx, gy = (pp.x - c.x) / 1e6, (pp.y - c.y) / 1e6
    chk(abs(gx - (25.4 - vv)) < 0.02 and abs(gy - (12.7 - uu)) < 0.02, f"U1 pin {n_} at ({gx:.2f}, {gy:.2f}) mm = mirrored Mean Well drawing position ({25.4 - vv:.2f}, {12.7 - uu:.2f})")
# 3. isolation: primary vs secondary copper gap
PRI = {"+12V_IN", "+12V_F", "12V_GND"}; SEC = {"5V_ISO_RAW", "5V_PI", "PI_GND", "PG_LED_A"}
def boxes(nset):
    r = []
    for t in b.GetTracks(): 
        if t.GetNetname().lstrip('/') in nset: r.append(t.GetBoundingBox())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname().lstrip('/') in nset: r.append(p.GetBoundingBox())
    for z in b.Zones():
        if z.GetNetname().lstrip('/') in nset:
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
 f"OSBAMS_Pi_Display_Power_RevA {os.environ.get('REL', 'RC1')} - custom connectivity / isolation checks (netlist from kicad-cli 10)\n"
 "Complementary to, not a replacement for, the KiCad 10 ERC/DRC reports (ERC_report_kicad10.rpt, DRC_report_kicad10.rpt).\n\n" + "\n".join(out) + f"\n\nRESULT: {'FAIL' if fail else 'PASS'} ({fail} failures)\n")
print("\n".join(out)); print("fail:", fail)

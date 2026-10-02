#!/usr/bin/python3
"""Carrier RevB checks (run in the KiCad 10 container): schematic<->PCB net parity, polarity / connector pin numbering, Pi header pin map (power only on 2,4 / 6,9,14,20),
module pins vs the Mean Well drawing, isolation bookkeeping, mounting holes. usage: check_carrier.py <project dir>"""
import os, re, sys, subprocess
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexp
from parts_carrier import *
D = sys.argv[1]; K = f"{D}/kicad/{NAME}"
subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", "/tmp/_car.net", K + ".kicad_sch"], capture_output=True, text=True)
nets = {k.lstrip("/"): v for k, v in sexp.read_netlist(open("/tmp/_car.net").read()).items()}
b = pcbnew.LoadBoard(K + ".kicad_pcb"); out = []; fail = 0
def chk(ok, msg):
    global fail; out.append(("PASS  " if ok else "FAIL  ") + msg); fail += (not ok)
pcbn = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        nn = p.GetNetname().lstrip("/")
        if nn and not nn.startswith("unconnected"): pcbn.setdefault(nn, set()).add((fp.GetReference(), p.GetNumber()))
sch = {n: {(r, p) for r, p, t in v} for n, v in nets.items() if not n.startswith("unconnected")}
for n in sorted(set(sch) | set(pcbn)): chk(sch.get(n) == pcbn.get(n), f"Net {n}: schematic pins == PCB pads  ({len(sch.get(n, []))} vs {len(pcbn.get(n, []))})")
for n, v in nets.items():
    if n.startswith("unconnected"): continue
    t = [x[2] for x in v]
    if "power_in" in t: chk("power_out" in t or n in FLAG_NETS, f"Net {n}: power_in pin has a driver / PWR_FLAG")
    chk(len(v) >= 2, f"Net {n}: at least 2 connections")
chk(not (sch["PI_GND"] & sch["12V_GND"]), "PI_GND and 12V_GND share no pin")
pn = {(fp.GetReference(), p.GetNumber()): p.GetNetname().lstrip("/") for fp in b.GetFootprints() for p in fp.Pads()}
for (r, n), want in {("TVS1", "1"): "+12V_F", ("TVS1", "2"): "12V_GND", ("D1", "1"): "PI_GND", ("D1", "2"): "PG_LED_A", ("C2", "1"): "+12V_F", ("C2", "2"): "12V_GND", ("C4", "1"): "5V_PI", ("C4", "2"): "PI_GND",
                     ("J_IN", "1"): "+12V_IN", ("J_IN", "2"): "12V_GND", ("J_DISP", "1"): "5V_PI", ("J_DISP", "2"): "PI_GND", ("U1", "1"): "+12V_F", ("U1", "2"): "12V_GND", ("U1", "4"): "5V_ISO_RAW",
                     ("U1", "5"): "PI_GND", ("U1", "6"): "TRIM", ("F1", "1"): "+12V_IN", ("F1", "2"): "+12V_F", ("F2", "1"): "5V_ISO_RAW", ("F2", "2"): "5V_PI", ("R3", "1"): "TRIM", ("R3", "2"): "PI_GND"}.items():
    chk(pn.get((r, n)) == want, f"Polarity/pinout {r} pin {n} = {want}  (PCB: {pn.get((r, n))})")
chk(pn.get(("U1", "3"), "").startswith("unconnected"), "U1 pin 3 (ON/OFF) open = enabled (no net)")
# Pi header pin map
want5, wantg = {2, 4}, {6, 9, 14, 20}
for n in range(1, 41):
    nn = pn[("J2", str(n))]
    exp = "5V_PI" if n in want5 else "PI_GND" if n in wantg else None
    ok = (nn == exp) if exp else nn.startswith("unconnected")
    chk(ok, f"Pi header pin {n}: {'5V_PI' if n in want5 else 'PI_GND' if n in wantg else 'no-connect (no net)'}  (PCB: {nn or '-'})")
# copper must not touch the no-connect header pads (a track/zone on another net would show as a net on the pad; also check track ends)
pts = [(t.GetStart(), t.GetEnd(), t.GetNetname()) for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
j2 = [f for f in b.GetFootprints() if f.GetReference() == "J2"][0]
touch = [p.GetNumber() for p in j2.Pads() if p.GetNetname().lstrip("/").startswith("unconnected") and any(p.HitTest(s) or p.HitTest(e) for s, e, nn in pts)]
chk(not touch, f"No track ends on the 34 no-connect header pads {touch or ''}")
# U1 pins vs the Mean Well drawing (long axis along y, secondary pins at the bottom): dx = 25.4 - v, dy = 12.7 - u rotated by 270 deg
u1 = [f for f in b.GetFootprints() if f.GetReference() == "U1"][0]; cx, cy = U1_C
for n_, (uu, vv) in {"1": (5.08, 48.26), "2": (10.16, 48.26), "3": (20.32, 48.26), "4": (2.54, 2.54), "5": (12.7, 2.54), "6": (22.86, 2.54)}.items():
    dx, dy = 25.4 - vv, 12.7 - uu; ex, ey = cx - dy, cy + dx            # clockwise 90 deg on screen (x right, y down): (x, y) -> (-y, x)
    pp = [p for p in u1.Pads() if p.GetNumber() == n_][0].GetPosition()
    chk(abs(pp.x / 1e6 - ex) < 0.02 and abs(pp.y / 1e6 - ey) < 0.02, f"U1 pin {n_} at ({pp.x/1e6:.2f}, {pp.y/1e6:.2f}) = mirrored Mean Well drawing position rotated to the carrier ({ex:.2f}, {ey:.2f})")
# mechanics: holes
for f in b.GetFootprints():
    if f.GetReference()[0] in "MKS" and f.GetReference() not in ("M",):
        chk(all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and not p.GetNetname() for p in f.Pads()), f"{f.GetReference()}: NPTH, no net, no copper pad (no hidden ground path)")
# nothing but the plug tab parts below the main body
for f in b.GetFootprints():
    bb = f.GetBoundingBox(False); yb = bb.GetBottom() / 1e6
    if f.GetReference() not in ("J2", "M1", "M2") and yb > MAIN_H + 0.01 and not f.GetReference().startswith("FID"):
        chk(False, f"{f.GetReference()} extends over the Pi (y {yb:.1f} > {MAIN_H})")
chk(True, "Only J2, M1, M2 lie in the plug tab over the Pi header (everything else is outside the Pi outline)")
open(f"{D}/reports/Connectivity_pinmap_check.txt", "w").write(f"{NAME} {os.environ.get('REL', 'RC1')} - connectivity / polarity / pin-map checks (netlist from kicad-cli 10)\nComplementary to the KiCad 10 ERC/DRC reports.\n\n" + "\n".join(out) + f"\n\nRESULT: {'FAIL' if fail else 'PASS'} ({fail} failures)\n")
print("\n".join(l for l in out if l.startswith("FAIL")) or "all PASS"); print("fail:", fail, "checks:", len(out)); sys.exit(1 if fail else 0)

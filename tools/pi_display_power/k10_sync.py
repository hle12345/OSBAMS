#!/usr/bin/env python3
"""Make the generated PCB identical to its schematic in the ways KiCad 10's schematic-parity DRC checks (run in the KiCad 10 container):
footprint <-> symbol link (path), value, DNP, Manufacturer/MPN fields, footprint library id, pad nets (names exactly as KiCad derives them from the
schematic, incl. 'unconnected-(...)' nets for no-connect pins); footprints that have no symbol (holes, fiducials, key posts) are marked board-only.
usage: k10_sync.py <kicad dir> <project name>"""
import os, re, sys, subprocess
import pcbnew
KD, NAME = sys.argv[1], sys.argv[2]
SCH = f"{KD}/{NAME}.kicad_sch"; PCB = f"{KD}/{NAME}.kicad_pcb"
t = open(SCH).read()
root = re.search(r'^\s*\(uuid "([^"]+)"', t, re.M).group(1)
def blocks(txt, head):
    i = 0
    while True:
        i = txt.find(head, i)
        if i < 0: return
        d = 0
        for j in range(i, len(txt)):
            d += (txt[j] == "(") - (txt[j] == ")")
            if d == 0: break
        yield txt[i:j + 1]; i = j + 1
syms = {}
body = t[t.index("(sheet_instances") - 0:] if False else t
for b in blocks(t, "(symbol (lib_id"):
    pr = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', b))
    ref = pr.get("Reference", "")
    if ref.startswith("#"): continue
    syms[ref] = dict(uuid=re.search(r'\(uuid "([^"]+)"', b).group(1), props=pr, dnp="(dnp yes)" in b, raw=b.split("(property", 1)[0])
# netlist -> pad nets
subprocess.run(["/usr/bin/kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", "/tmp/_sync.net", SCH], capture_output=True, text=True)
nl = open("/tmp/_sync.net").read()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexp
pad_net = {(r, p): nm for nm, nodes in sexp.read_netlist(nl).items() for r, p, _ in nodes}
b = pcbnew.LoadBoard(PCB)
nets = {n.GetNetname(): n for n in b.GetNetInfo().NetsByNetcode().values()}
def net(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); nets[name] = ni
    return nets[name]
# rename existing nets that only differ by the sheet prefix '/', then set every pad from the netlist
want = set(pad_net.values())
for n in list(nets):
    if n and "/" + n in want and n not in want:
        nets[n].SetNetname("/" + n); nets["/" + n] = nets.pop(n)
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref in syms:
        s = syms[ref]; fp.SetPath(pcbnew.KIID_PATH(f"/{root}/{s['uuid']}"))
        fp.SetValue(s["props"].get("Value", fp.GetValue())); fp.SetDNP(s["dnp"]); fp.SetExcludedFromBOM("(in_bom no)" in s["raw"])
        for k, v in s["props"].items():
            if k not in ("Reference", "Value", "Footprint", "Datasheet", "Description"):
                fp.SetField(k, v); fp.GetField(k).SetVisible(False)
        if s["props"].get("Footprint") and ":" in s["props"]["Footprint"]:
            lib, nm = s["props"]["Footprint"].split(":", 1); fp.SetFPID(pcbnew.LIB_ID(lib, nm))
        for p in fp.Pads():
            nn = pad_net.get((ref, p.GetNumber()))
            if nn is not None: p.SetNet(net(nn))
    else:
        fp.SetBoardOnly(True)
# tracks/zones keep their net objects (renamed above); drop now-unused nets
b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)
print("sync:", len(syms), "symbols,", sum(1 for f in b.GetFootprints() if f.IsBoardOnly()), "board-only footprints,", len(pad_net), "pad nets")

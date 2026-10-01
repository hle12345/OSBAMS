"""Netlist-level checks: KiCad netlist vs design intent, diode polarity, creepage-class sanity."""
import re, os, sys
from collections import defaultdict
from . import kisx, kilib


def read_netlist(path):
    t = kisx.parse(open(path).read())
    nets = {}
    for n in kisx.find(kisx.find1(t, 'nets'), 'net'):
        name = str(kisx.find1(n, 'name')[1])
        nodes = [(str(kisx.find1(x, 'ref')[1]), str(kisx.find1(x, 'pin')[1])) for x in kisx.find(n, 'node')]
        nets[name] = nodes
    return nets


def design_nets(D, resolve):
    """expected {net: set((ref,pin))} using the schematic generator's pin resolution (includes stacked/hidden pins)."""
    exp = defaultdict(set)
    for ref, c in D.COMPS.items():
        for p, net in resolve(c):
            if net:
                exp[net].add((ref, p['number']))
    return exp


def compare(exp, got):
    errs = []
    gotn = {}
    for name, nodes in got.items():
        key = name.lstrip('/')
        gotn[key] = set(nodes)
    # KiCad names global nets without sheet prefix; local nets get '/<sheet>/NAME'
    byname = defaultdict(set)
    for name, nodes in got.items():
        byname[name.split('/')[-1]] |= set(nodes)
    for net, nodes in exp.items():
        g = byname.get(net, set())
        if g != nodes:
            errs.append(f"net {net}: missing {sorted(nodes - g)} extra {sorted(g - nodes)}")
    return errs


# ---------------------------------------------------------------- polarity
EXPECTED_CATHODE = {"D1": "+12V", "D2": "+12V", "D5": "SHUNT_INP_RAW", "D6": "SHUNT_INN_RAW", "D7": "PACK_INA", "D9": "COIL_V",
                    "D11": "ES_LED_A", "D12": "FB_LED_A", "D3": "GND", "D4": "GND", "D10": "COIL_SW"}
FPDIR = "/usr/share/kicad/footprints"


def cathode_pad_from_library(fpid):
    """Return '1' or '2' = the pad nearest to the cathode bar drawn in the footprint library file (None if not derivable)."""
    lib, name = fpid.split(":")
    t = kisx.parse(open(os.path.join(FPDIR, lib + ".pretty", name + ".kicad_mod")).read())
    pads = {str(p[1]): float(kisx.find1(p, "at")[1]) for p in kisx.find(t, "pad")}
    if set(pads) != {"1", "2"}:
        return None
    x1, x2 = pads["1"], pads["2"]
    bars = []
    for n in kisx.find(t, "fp_line"):
        layer = kisx.find1(n, "layer")[1]
        s, e = kisx.find1(n, "start"), kisx.find1(n, "end")
        if layer in ("F.Fab", "F.SilkS") and abs(float(s[1]) - float(e[1])) < 1e-6 and abs(float(s[2]) - float(e[2])) > 0.8:
            bars.append((layer, float(s[1])))
    inner = [b for l, b in bars if min(x1, x2) + 0.3 < b < max(x1, x2) - 0.3 and abs(b) < 1.0 or (l == "F.SilkS" and min(x1, x2) < b < max(x1, x2))]
    if not inner:
        return None
    b = sum(inner) / len(inner)
    return "1" if abs(b - x1) < abs(b - x2) else "2"


def diode_polarity(boarddata, comps):
    errs, notes = [], []
    for ref, net in EXPECTED_CATHODE.items():
        f = boarddata["footprints"][ref]
        padnet = {p["num"]: p["net"].split("/")[-1] for p in f["pads"]}
        if padnet.get("1") != net:
            errs.append(f"{ref}: pad 1 (cathode by KiCad convention) is on {padnet.get('1')}, expected {net}")
        cp = cathode_pad_from_library(f["fpid"]) if not f["fpid"].startswith("LED") else None
        if cp is not None and cp != "1":
            errs.append(f"{ref}: library footprint {f['fpid']} has the cathode bar at pad {cp}, not pad 1")
        notes.append((ref, f["fpid"], "cathode pad from library bar: " + (cp or "silk C-shape convention"), "pad1 net " + padnet.get("1", "?"), "OK" if padnet.get("1") == net else "FAIL"))
    return errs, notes


def pcb_vs_schematic(netlist, boarddata):
    """Compare every (ref, pad) net in the PCB with the KiCad schematic netlist."""
    sch = {}
    for name, nodes in netlist.items():
        for ref, pin in nodes:                 # exact net names: the board must carry the schematic's names ('/<sheet>/NAME', 'unconnected-(...)')
            sch[(ref, pin)] = name
    errs, n = [], 0
    for ref, f in boarddata["footprints"].items():
        for p in f["pads"]:
            if p["num"] == "":
                continue
            key = (ref, p["num"])
            want = sch.get(key)
            if want is None:
                if p["net"]:
                    errs.append(f"{ref}.{p['num']}: PCB net {p['net']} but pad not in schematic netlist")
                continue
            n += 1
            have = p["net"]
            if (have or "") != want:
                errs.append(f"{ref}.{p['num']}: PCB net '{have}' != schematic net '{want}'")
    for key, net in sch.items():
        ref = key[0]
        if ref not in boarddata["footprints"] and not ref.startswith("#"):
            errs.append(f"{ref} in schematic but not on the PCB")
    return n, errs

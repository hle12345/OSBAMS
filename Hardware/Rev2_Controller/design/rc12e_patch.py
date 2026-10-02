"""RC1.2e local PCB patch (runs in the KiCad 10 container, in two stages because pcbnew's SWIG layer crashes when footprints
are added after other items were removed in the same process):

  stage 1:  python3 -m design.rc12e_patch 1   remove J9 (generic footprint) and the J9 breakout copper that the longer pads invalidate
  stage 2:  python3 -m design.rc12e_patch 2   add J9 with the Samtec land pattern, re-route its breakout, add D15 (differential clamp)

The patch is applied to the routed RC1.2d board so that the rest of the routing is unchanged (Freerouting is not deterministic).
Geometry follows the Samtec recommended PCB layout: pads 0.74 x 2.79 mm, pad rows 4.07 mm apart (1.28 mm gap between the rows)."""
import json, sys
import pcbnew
from pcbnew import ToMM, FromMM as mm
from . import stitch as S
from . import rev2_design as D

NETS = "/tmp/j9nets.json"
D15_POS = (119.25, 120.75, 0)
b = pcbnew.LoadBoard(S.PCB)
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
close = lambda a, x, y: abs(ToMM(a.x) - x) < .01 and abs(ToMM(a.y) - y) < .01


def seg(a, c, net, ly=pcbnew.F_Cu, w=0.2):
    s = pcbnew.PCB_TRACK(b); s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(w)); s.SetLayer(ly); s.SetNet(b.FindNet(net)); b.Add(s)


def new_fp(ref, nets):
    c = D.COMPS[ref]
    lib, name = c["fp"].split(":", 1)
    path = S.PCB.rsplit("/", 1)[0] + "/OSBAMS_Rev2.pretty" if lib == "OSBAMS_Rev2" else "/usr/share/kicad/footprints/" + lib + ".pretty"
    fp = pcbnew.FootprintLoad(path, name)
    fp.SetFPIDAsString(c["fp"])
    fp.SetReference(ref); fp.SetValue(str(c["value"]))
    for pad in fp.Pads():
        n = nets.get(pad.GetNumber())
        if n:
            pad.SetNet(b.FindNet(n))
    for k, v in (("MPN", c.get("mpn", "")), ("Manufacturer", c.get("mfr", "")), ("Evidence", c.get("evid", "")), ("Description", c.get("desc", ""))):
        fp.SetField(k, v); f = fp.GetField(k); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
    fp.Value().SetVisible(False)
    r = fp.Reference(); r.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); r.SetTextThickness(mm(0.12))
    return fp


stage = sys.argv[1]
if stage == "1":
    old = b.FindFootprintByReference("J9")
    json.dump({"pos": [ToMM(old.GetPosition().x), ToMM(old.GetPosition().y)], "rot": old.GetOrientationDegrees(),
               "nets": {p.GetNumber(): p.GetNetname() for p in old.Pads()}}, open(NETS, "w"))
    b.Remove(old)
    for t in list(b.GetTracks()):
        n = t.GetNetname()
        if t.GetClass() == "PCB_VIA":
            if n == "NRST" and close(t.GetPosition(), 156.3725, 140.6483):
                b.Remove(t)
            continue
        s, e = t.GetStart(), t.GetEnd()
        if n == "SWCLK" and ((close(s, 160.4983, 138.73) and close(e, 160.4983, 121.7483)) or (close(e, 160.4983, 138.73) and close(s, 160.4983, 121.7483))):
            b.Remove(t)
        elif n == "SWCLK" and close(s, 161.95, 138.73) and close(e, 160.4983, 138.73):
            b.Remove(t)
        elif n == "NRST" and t.GetLayerName() == "F.Cu" and min(ToMM(s.x), ToMM(e.x)) > 155.5 and min(ToMM(s.y), ToMM(e.y)) > 139:
            b.Remove(t)
        elif n == "NRST" and t.GetLayerName() == "In2.Cu" and close(e, 156.3725, 140.6483):
            b.Remove(t)
    b.Save(S.PCB)
else:
    j = json.load(open(NETS))
    fp = new_fp("J9", j["nets"]); fp.SetPosition(V(*j["pos"])); fp.SetOrientationDegrees(j["rot"]); b.Add(fp)
    X = 160.35        # inside the 1.28 mm gap between the pad rows (pad inner edges at 159.36 / 160.64)
    seg((162.035, 138.73), (X, 138.73), "SWCLK"); seg((X, 138.73), (X, 121.7483), "SWCLK"); seg((X, 121.7483), (160.4983, 121.7483), "SWCLK")
    seg((162.035, 142.54), (X, 142.54), "NRST"); seg((X, 142.54), (X, 140.635), "NRST"); seg((X, 140.635), (156.3, 140.635), "NRST"); seg((156.3, 140.635), (155.8, 140.0758), "NRST")
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(155.8, 140.0758)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(b.FindNet("NRST"))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
    seg((152.8009, 137.0767), (155.8, 140.0758), "NRST", pcbnew.In2_Cu)
    d = new_fp("D15", {"1": "INA_INP", "2": "INA_INN"}); d.SetPosition(V(D15_POS[0], D15_POS[1])); d.SetOrientationDegrees(D15_POS[2]); b.Add(d)
    for z in b.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(S.PCB)

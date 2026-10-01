#!/usr/bin/python3
"""Build the KiCad PCB with pcbnew (run with /usr/bin/python3, KiCad 7)."""
import sys, os, json, re
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I as V
sys.path.insert(0, os.path.dirname(__file__))
from parts import *

out = sys.argv[1]
b = pcbnew.BOARD()
nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    return nets[n]
for n in ["+12V_IN", "+12V_F", "12V_GND", "5V_ISO_RAW", "5V_PI", "PI_GND", "PG_LED_A"]:
    net(n)
P = lambda x, y: V(mm(x), mm(y))

def seg(fp, layer, x1, y1, x2, y2, w=0.15):
    s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    o = fp.GetPosition()
    s.SetStart0(P(x1, y1)); s.SetEnd0(P(x2, y2)); s.SetStart(V(o.x + mm(x1), o.y + mm(y1))); s.SetEnd(V(o.x + mm(x2), o.y + mm(y2)))
    s.SetLayer(layer); s.SetWidth(mm(w)); fp.Add(s)
def rect(fp, layer, x1, y1, x2, y2, w=0.15):
    for a in ((x1,y1,x2,y1),(x2,y1,x2,y2),(x2,y2,x1,y2),(x1,y2,x1,y1)): seg(fp, layer, *a, w=w)
def circ(fp, layer, cx, cy, r, w=0.15):
    s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    o = fp.GetPosition()
    s.SetStart0(P(cx, cy)); s.SetEnd0(P(cx + r, cy)); s.SetStart(V(o.x + mm(cx), o.y + mm(cy))); s.SetEnd(V(o.x + mm(cx + r), o.y + mm(cy)))
    s.SetLayer(layer); s.SetWidth(mm(w)); fp.Add(s)

def pad(fp, num, dx, dy, w, h, kind="smd", drill=0.0, shape=None, netname=None):
    p = pcbnew.PAD(fp); p.SetNumber(str(num))
    cx, cy = fp.GetPosition().x, fp.GetPosition().y
    p.SetPosition(V(cx + mm(dx), cy + mm(dy))); p.SetPos0(P(dx, dy)); p.SetSize(P(w, h))
    if kind == "smd":
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetLayerSet(p.SMDMask())
        p.SetShape(shape or pcbnew.PAD_SHAPE_ROUNDRECT); p.SetRoundRectRadiusRatio(0.2)
    elif kind == "tht":
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetLayerSet(p.PTHMask())
        p.SetShape(shape or pcbnew.PAD_SHAPE_CIRCLE); p.SetDrillSize(P(drill, drill))
    elif kind == "npth":
        p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetLayerSet(p.UnplatedHoleMask())
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetDrillSize(P(drill, drill))
    if netname: p.SetNet(net(netname))
    fp.Add(p); return p

def newfp(ref, x, y, value=""):
    fp = pcbnew.FOOTPRINT(b); fp.SetReference(ref); fp.SetValue(value or ref)
    fp.SetPosition(P(x, y)); b.Add(fp)
    fp.Reference().SetLayer(pcbnew.F_Fab); fp.Reference().SetTextSize(P(1, 1)); fp.Reference().SetTextThickness(mm(0.12))
    fp.Value().SetLayer(pcbnew.F_Fab); fp.Value().SetVisible(False)
    return fp

SIL, FAB = pcbnew.F_SilkS, pcbnew.F_Fab
meta = {p[0]: p for p in PARTS}
fps = {}
def mk(ref):
    x, y = POS[ref]; fp = newfp(ref, x, y, meta[ref][1]); fps[ref] = fp
    fp.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", meta[ref][5])); return fp
def refpos(fp, dx, dy):
    fp.Reference().SetPosition(V(fp.GetPosition().x + mm(dx), fp.GetPosition().y + mm(dy))); fp.Reference().SetPos0(P(dx, dy))

# U1 - RSDW40F-05  *** PLACEHOLDER GEOMETRY: body 50.8x25.4, 6 pins at 5.08 mm, ends of the module ***
fp = mk("U1"); R = pcbnew.PAD_SHAPE_CIRCLE
for n, dx, dy, nn in [(1,-22.86,-5.08,"+12V_F"),(2,-22.86,0,"12V_GND"),(3,-22.86,5.08,None),
                      (4,22.86,-5.08,"5V_ISO_RAW"),(5,22.86,0,"PI_GND"),(6,22.86,5.08,None)]:
    pad(fp, n, dx, dy, 2.2, 2.2, "tht", 1.2, netname=nn)
rect(fp, SIL, -25.4, -12.7, 25.4, 12.7, 0.2)
circ(fp, SIL, -22.86, -9.5, 0.6, 0.2); refpos(fp, 0, 0)
# Fuses (Nano2): placeholder land pattern
def fuse(ref, vertical, n1, n2):
    fp = mk(ref); pw, ph = (3.2, 5.0) if not vertical else (5.0, 3.2)
    off = 5.0
    if not vertical:
        pad(fp, 1, -off, 0, pw, ph, netname=n1); pad(fp, 2, off, 0, pw, ph, netname=n2)
        rect(fp, SIL, -6.0, -2.25, 6.0, 2.25)
    else:
        pad(fp, 1, 0, -off + 0.0, 4.6, 3.2, netname=n1); pad(fp, 2, 0, off, 4.6, 3.2, netname=n2)
        rect(fp, SIL, -2.25, -6.0, 2.25, 6.0)
    refpos(fp, 0, 0)
fuse("F1", False, "+12V_IN", "+12V_F")
fuse("F2", True, "5V_ISO_RAW", "5V_PI")
# TVS DO-214AA
fp = mk("TVS1"); pad(fp, 1, -2.2, 0, 2.2, 2.4, netname="+12V_F"); pad(fp, 2, 2.2, 0, 2.2, 2.4, netname="12V_GND")
rect(fp, SIL, -2.0, -1.9, 2.0, 1.9); seg(fp, SIL, -3.8, -1.9, -3.8, 1.9, 0.3); refpos(fp, 0, -3)
# Micro-Fit headers (pin pitch 3.0; PLACEHOLDER: pegs not modelled)
fp = mk("J_IN"); pad(fp, 1, 0, 0, 2.0, 2.0, "tht", 1.02, netname="+12V_IN"); pad(fp, 2, 3.0, 0, 2.0, 2.0, "tht", 1.02, netname="12V_GND")
rect(fp, SIL, -5.5, -2.5, 5.0, 2.5); refpos(fp, 4, -3.5)
fp = mk("J_OUT")
for n, dx, dy, nn in [(1,0,0,"5V_PI"),(2,0,3.0,"5V_PI"),(3,3.0,0,"PI_GND"),(4,3.0,3.0,"PI_GND")]:
    pad(fp, n, dx, dy, 2.0, 2.0, "tht", 1.02, netname=nn)
rect(fp, SIL, -3.0, -2.5, 6.0, 6.0); refpos(fp, 9, 0)
# Passives
def two(ref, p, w, h, n1, n2, outline, col=(0.0, 0.0)):
    fp = mk(ref); pad(fp, 1, -p, 0, w, h, netname=n1); pad(fp, 2, p, 0, w, h, netname=n2)
    rect(fp, SIL, *outline); refpos(fp, 0, -1.8); return fp
two("C1", 0.825, 0.8, 0.95, "+12V_F", "12V_GND", (-1.5, -0.8, 1.5, 0.8))
two("C5", 0.95, 1.0, 1.45, "PI_GND", "5V_PI", (-1.7, -1.0, 1.7, 1.0))
two("C6", 0.825, 0.8, 0.95, "PI_GND", "5V_PI", (-1.5, -0.8, 1.5, 0.8))
two("R1", 0.825, 0.8, 0.95, "PG_LED_A", "5V_PI", (-1.5, -0.8, 1.5, 0.8))
fps["R1"].FindPadByNumber("1").SetNet(net("5V_PI")); fps["R1"].FindPadByNumber("2").SetNet(net("PG_LED_A"))
fp = two("D1", 0.825, 0.8, 0.95, "PI_GND", "PG_LED_A", (-1.5, -0.8, 1.5, 0.8)); seg(fp, SIL, -2.0, -0.8, -2.0, 0.8, 0.3)
def radial(ref, d, pitch, drill, padd, npos, nneg):
    fp = mk(ref); pad(fp, 1, -pitch/2, 0, padd, padd, "tht", drill, netname=npos)   # + at -x
    pad(fp, 2, pitch/2, 0, padd, padd, "tht", drill, netname=nneg)
    circ(fp, SIL, 0, 0, d/2, 0.15); seg(fp, SIL, -pitch/2 - 2.2, -1.2, -pitch/2 - 2.2, 1.2, 0.2)
    refpos(fp, 0, d/2 + 1.2)
radial("C2", 8.0, 3.5, 0.8, 1.8, "+12V_F", "12V_GND")
radial("C4", 10.0, 5.0, 1.0, 2.2, "5V_PI", "PI_GND")
# polarity: for C4, '+' pad (1) at -x -> placed so + at x=68.5?  See below: swap so + is toward the 5V bar (+x)
for ref in ("C4",):
    fps[ref].FindPadByNumber("1").SetNet(net("PI_GND")); fps[ref].FindPadByNumber("2").SetNet(net("5V_PI"))
    # pad numbering kept (1=+ in library convention) -> keep nets correct, but number-swap for polarity
    fps[ref].FindPadByNumber("1").SetNumber("tmp"); fps[ref].FindPadByNumber("2").SetNumber("1"); fps[ref].FindPadByNumber("tmp").SetNumber("2")
fps["C2"]  # + at -x, bar is to the left (x<28.75 side is polygon) -> C2 + (28.75) fine
# Test points
for ref, nn in [("TP1","+12V_IN"),("TP2","12V_GND"),("TP3","5V_ISO_RAW"),("TP4","5V_PI"),("TP5","PI_GND")]:
    fp = mk(ref); pad(fp, 1, 0, 0, 1.5, 1.5, shape=pcbnew.PAD_SHAPE_CIRCLE, netname=nn); refpos(fp, 0, -1.6)
    t = pcbnew.FP_TEXT(fp); t.SetText(meta[ref][1]); t.SetLayer(SIL); t.SetTextSize(P(0.9, 0.9)); t.SetTextThickness(mm(0.15))
    t.SetPosition(V(fp.GetPosition().x, fp.GetPosition().y + mm(1.8))); t.SetPos0(P(0, 1.8)); fp.Add(t)
# Fiducials (1 mm copper, 2 mm mask opening) and M3 holes
for i, (x, y) in enumerate([(12, 66), (88, 5), (95, 40)], 1):
    fp = newfp(f"FID{i}", x, y, "FID"); fp.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", "FIDUCIAL_1MM"))
    p = pad(fp, 1, 0, 0, 1.0, 1.0, shape=pcbnew.PAD_SHAPE_CIRCLE); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.F_Mask); p.SetLayerSet(ls)
    p.SetLocalSolderMaskMargin(mm(0.5)); fp.Reference().SetVisible(False)
    fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
for i, (x, y) in enumerate([(4, 4), (96, 4), (4, 66), (96, 66)], 1):
    fp = newfp(f"H{i}", x, y, "M3"); fp.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", "MountingHole_3.2mm_M3"))
    pad(fp, "", 0, 0, 3.2, 3.2, "npth", 3.2); circ(fp, pcbnew.Dwgs_User, 0, 0, 3.0, 0.15)
    fp.Reference().SetVisible(False); fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)

# Tracks / vias
def trk(nn, pts, w, layer=pcbnew.F_Cu):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net(nn)); b.Add(t)
def via(nn, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetNet(net(nn))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
trk("+12V_IN", [(6, 14), (6, 8), (13, 8)], 2.0)
trk("+12V_IN", [(10, 4.5), (10, 8)], 0.8)
trk("12V_GND", [(14, 17), (15.5, 17)], 0.8); via("12V_GND", 15.5, 17)
trk("12V_GND", [(33.2, 8.5), (35.8, 8.5)], 1.5); via("12V_GND", 35.8, 8.5)
trk("12V_GND", [(31.825, 24), (31.825, 26.3)], 0.5); via("12V_GND", 31.825, 26.3)
trk("5V_PI", [(75.45, 50), (79, 50)], 0.8); trk("PI_GND", [(73.55, 50), (72.3, 50)], 0.5); via("PI_GND", 72.3, 50)
trk("5V_PI", [(75.325, 54), (79, 54)], 0.5); trk("PI_GND", [(73.675, 54), (72.3, 54)], 0.5); via("PI_GND", 72.3, 54)
trk("5V_PI", [(82.5, 57), (87.175, 57)], 0.5); trk("PG_LED_A", [(88.825, 57), (88.825, 53)], 0.5)
trk("PI_GND", [(87.175, 53), (85.5, 53)], 0.5); via("PI_GND", 85.5, 53)
trk("PI_GND", [(87, 59.5), (88.4, 59.5)], 0.8); via("PI_GND", 88.4, 59.5)
# extra stitching vias at module GND pins and output pads

# Zones
def zone(nn, layer, pts, prio=0, clr=0.5):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net(nn)); z.SetAssignedPriority(prio)
    z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(clr)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(z)
zone("+12V_F", pcbnew.F_Cu, [(22.5, 5), (38, 5), (38, 28.5), (22.5, 28.5)], 1)
zone("5V_ISO_RAW", pcbnew.F_Cu, [(70, 22.5), (83, 22.5), (83, 44), (78.2, 44), (78.2, 29.5), (70, 29.5)], 1)
zone("5V_PI", pcbnew.F_Cu, [(78.2, 48), (83, 48), (83, 68), (78.2, 68), (78.2, 62.5), (72, 62.5), (72, 57.5), (78.2, 57.5)], 1)
zone("12V_GND", pcbnew.B_Cu, [(1.5, 1.5), (45, 1.5), (45, 68.5), (1.5, 68.5)], 0, 0.4)
zone("PI_GND", pcbnew.B_Cu, [(55, 1.5), (98.5, 1.5), (98.5, 68.5), (55, 68.5)], 0, 0.4)

# Edge cuts, silkscreen
for a in ((0,0,100,0),(100,0,100,70),(100,70,0,70),(0,70,0,0)):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(a[0], a[1])); s.SetEnd(P(a[2], a[3]))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
def text(s, x, y, h=1.2, layer=pcbnew.F_SilkS, just=pcbnew.GR_TEXT_H_ALIGN_LEFT, bold=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
    t.SetTextSize(P(h, h)); t.SetTextThickness(mm(0.2 if h < 1.5 else 0.25)); t.SetHorizJustify(just); b.Add(t)
C = pcbnew.GR_TEXT_H_ALIGN_CENTER
text("OSBAMS Pi/Display Power Rev.A", 50, 2.6, 1.6, just=C)
text("12V IN", 7.5, 20.5, 1.4); text("PRIMARY 12V SIDE", 12, 63, 1.2); text("+12V   GND", 4.5, 11.0, 0.9)
text("ISOLATED 5V OUT", 56.0, 63.0, 0.9); text("5V / 8A MAX", 56.0, 60.6, 0.9)
text("1,2=+5V 3,4=GND", 88.3, 68.4, 0.7)
text("PI SIDE — ISOLATED", 56.0, 66.2, 1.1); text("ISOLATION BARRIER", 50, 38.5, 1.0, just=C)
text("NO COPPER CROSSING / 10mm GAP", 50, 40.2, 0.8, just=C)
text("RC1 - NOT FOR FAB", 50, 68.9, 0.8, pcbnew.F_SilkS, C)
text("OSBAMS Pi/Display Power Rev.A  2oz Cu", 50, 68.0, 0.9, pcbnew.B_SilkS, C)
for y in range(5, 66, 4):  # dashed isolation line
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(50, y)); s.SetEnd(P(50, y + 2.0))
    s.SetLayer(pcbnew.F_SilkS); s.SetWidth(mm(0.2)); b.Add(s)

ds = b.GetDesignSettings(); ds.SetBoardThickness(mm(1.6))
b.Save(out)
b = pcbnew.LoadBoard(out)
b.BuildConnectivity()
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(out)
# patch 2 oz stackup into setup
txt = open(out).read()
stack = ('(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) '
 '(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) (layer "F.Cu" (type "copper") (thickness 0.07)) '
 '(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02)) '
 '(layer "B.Cu" (type "copper") (thickness 0.07)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) '
 '(layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "ENIG") (dielectric_constraints no))')
txt, n = re.subn(r'\(setup\b', '(setup\n    ' + stack, txt, count=1)
open(out, "w").write(txt)
print("saved", out, "stackup patched" if n else "no setup block")

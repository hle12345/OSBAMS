#!/usr/bin/python3
"""Build the KiCad PCB with pcbnew (run with /usr/bin/python3, KiCad 7).
All parts except U1 use footprints from the official KiCad libraries (kicad-footprints)."""
import sys, os, re
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I as V
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import *

LIB = os.environ.get("KICAD_FP_DIR", "/usr/share/kicad/footprints")
out = sys.argv[1]
b = pcbnew.BOARD(); nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    return nets[n]
for n in ["+12V_IN", "+12V_F", "12V_GND", "5V_ISO_RAW", "5V_PI", "PI_GND", "PG_LED_A", "TRIM"]: net(n)
P = lambda x, y: V(mm(x), mm(y))
SIL, FAB = pcbnew.F_SilkS, pcbnew.F_Fab
meta = {p[0]: p for p in PARTS}
fps = {}

def libfp(ref, key, x, y, angle, padnets, hide_val=True):
    lib, name = key.split(":")
    fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name)
    assert fp is not None, key
    fp.SetReference(ref); fp.SetValue(meta[ref][1] if ref in meta else name)
    fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(angle)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    for p in fp.Pads():
        n = p.GetNumber()
        if n in padnets: p.SetNet(net(padnets[n]))
    for t in (fp.Reference(), fp.Value()):
        if t.GetLayer() == pcbnew.F_SilkS: t.SetLayer(pcbnew.F_Fab)
    fp.Value().SetVisible(False)
    b.Add(fp); fps[ref] = fp; return fp

N = lambda **k: {str(i): v for i, v in k.items()}
def two(ref, a, c): return {"1": a, "2": c}
# --- parts from official libraries
libfp("F1", meta["F1"][5], *POS["F1"], 0, two("F1", "+12V_IN", "+12V_F"))
libfp("F2", meta["F2"][5], *POS["F2"], 270, two("F2", "5V_ISO_RAW", "5V_PI"))
libfp("TVS1", meta["TVS1"][5], *POS["TVS1"], 0, two("T", "+12V_F", "12V_GND"))          # pad1 = cathode
libfp("J_IN", meta["J_IN"][5], *POS["J_IN"], 90, two("J", "+12V_IN", "12V_GND"))
libfp("J_OUT", meta["J_OUT"][5], *POS["J_OUT"], 180, {"1": "5V_PI", "2": "5V_PI", "3": "PI_GND", "4": "PI_GND"})
libfp("C1", meta["C1"][5], *POS["C1"], 0, two("C", "+12V_F", "12V_GND"))
libfp("C2", meta["C2"][5], *POS["C2"], 0, two("C", "+12V_F", "12V_GND"))                 # pad1 = +
libfp("C4", meta["C4"][5], *POS["C4"], 270, two("C", "5V_PI", "PI_GND"))                  # pad1 = +
libfp("C5", meta["C5"][5], *POS["C5"], 0, two("C", "5V_PI", "PI_GND"))
libfp("C6", meta["C6"][5], *POS["C6"], 0, two("C", "5V_PI", "PI_GND"))
libfp("R1", meta["R1"][5], *POS["R1"], 0, two("R", "5V_PI", "PG_LED_A"))
libfp("D1", meta["D1"][5], *POS["D1"], 0, two("D", "PI_GND", "PG_LED_A"))               # pad1 = cathode
libfp("R2", meta["R2"][5], *POS["R2"], 0, two("R", "TRIM", "5V_ISO_RAW"))
libfp("R3", meta["R3"][5], *POS["R3"], 0, two("R", "TRIM", "PI_GND"))
for ref, nn in [("TP1", "+12V_IN"), ("TP2", "12V_GND"), ("TP3", "5V_ISO_RAW"), ("TP4", "5V_PI"), ("TP5", "PI_GND")]:
    libfp(ref, meta[ref][5], *POS[ref], 0, {"1": nn})
for i, (x, y) in enumerate([(12, 66), (88, 5), (95, 40)], 1):
    f = libfp(f"FID{i}", "Fiducial:Fiducial_1mm_Mask2mm", x, y, 0, {}); f.Reference().SetVisible(False)
for i, (x, y) in enumerate([(4, 4), (96, 4), (4, 66), (96, 66)], 1):
    f = libfp(f"H{i}", "MountingHole:MountingHole_3.2mm_M3", x, y, 0, {}); f.Reference().SetVisible(False)

# --- U1 RSDW40F-05: geometry from the Mean Well drawing (RSDW40,RDDW40-SPEC 2022-05-24), "Bottom View".
# Bottom view (u across 25.4 mm width, v along 50.8 mm length): pins 4,5,6 at v=2.54, u=2.54/12.7/22.86;
# pins 1,2,3 at v=48.26, u=5.08/10.16/20.32. Pin dia 1+-0.1 mm. PCB top view = mirror of bottom view; module rotated so the
# long axis is along X with pins 1-3 (primary) at the left:  dx = 25.4 - v,  dy = 12.7 - u  (proper rotation of the mirrored view).
def seg(fp, layer, x1, y1, x2, y2, w=0.2):
    s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_SEGMENT); o = fp.GetPosition()
    s.SetStart0(P(x1, y1)); s.SetEnd0(P(x2, y2)); s.SetStart(V(o.x + mm(x1), o.y + mm(y1))); s.SetEnd(V(o.x + mm(x2), o.y + mm(y2)))
    s.SetLayer(layer); s.SetWidth(mm(w)); fp.Add(s)
fp = pcbnew.FOOTPRINT(b); fp.SetReference("U1"); fp.SetValue("RSDW40F-05"); fp.SetPosition(P(*POS["U1"]))
fp.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", "RSDW40F-05_MeanWell_2x1in")); b.Add(fp); fps["U1"] = fp
fp.Reference().SetLayer(FAB); fp.Value().SetVisible(False)
RSDW_PINS = {1: (5.08, 48.26), 2: (10.16, 48.26), 3: (20.32, 48.26), 4: (2.54, 2.54), 5: (12.7, 2.54), 6: (22.86, 2.54)}  # (u, v)
RSDW_NETS = {1: "+12V_F", 2: "12V_GND", 3: None, 4: "5V_ISO_RAW", 5: "PI_GND", 6: "TRIM"}
for n, (u_, v_) in RSDW_PINS.items():
    dx, dy = 25.4 - v_, 12.7 - u_
    p = pcbnew.PAD(fp); p.SetNumber(str(n)); o = fp.GetPosition()
    p.SetPosition(V(o.x + mm(dx), o.y + mm(dy))); p.SetPos0(P(dx, dy)); p.SetSize(P(2.4, 2.4))
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetLayerSet(p.PTHMask()); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetDrillSize(P(1.3, 1.3))
    if RSDW_NETS[n]: p.SetNet(net(RSDW_NETS[n]))
    fp.Add(p)
for a in ((-25.4,-12.7,25.4,-12.7),(25.4,-12.7,25.4,12.7),(25.4,12.7,-25.4,12.7),(-25.4,12.7,-25.4,-12.7)): seg(fp, SIL, *a)
seg(fp, SIL, -24.0, -8.5, -24.0, -6.5)   # pin-1 side marker (primary end)

# --- tracks / vias
def trk(nn, pts, w, layer=pcbnew.F_Cu):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net(nn)); b.Add(t)
def via(nn, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetNet(net(nn))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
def padpos(ref, n):
    p = fps[ref].FindPadByNumber(str(n)).GetPosition(); return (p.x / 1e6, p.y / 1e6)
# primary
YT = POS["F1"][1]
j1 = padpos("J_IN", 1); trk("+12V_IN", [j1, (j1[0], YT), (padpos("F1", 1)[0], YT)], 2.0)
tp1 = padpos("TP1", 1); trk("+12V_IN", [tp1, (tp1[0], YT)], 0.8)
tp2 = padpos("TP2", 1); trk("12V_GND", [tp2, (tp2[0] + 1.5, tp2[1])], 0.8); via("12V_GND", tp2[0] + 1.5, tp2[1])
t2 = padpos("TVS1", 2); trk("12V_GND", [t2, (t2[0] + 2.6, t2[1])], 1.5); via("12V_GND", t2[0] + 2.6, t2[1])
c1 = padpos("C1", 2); trk("12V_GND", [c1, (c1[0], c1[1] + 2.3)], 0.5); via("12V_GND", c1[0], c1[1] + 2.3)
# secondary
c5, c6 = padpos("C5", 1), padpos("C6", 1)
trk("5V_PI", [c5, (83.0, c5[1])], 0.8); trk("5V_PI", [c6, (83.0, c6[1])], 0.8)
for ref in ("C5", "C6"):
    g = padpos(ref, 2); trk("PI_GND", [g, (g[0] + 1.6, g[1])], 0.5); via("PI_GND", g[0] + 1.6, g[1])
c4 = padpos("C4", 1); trk("5V_PI", [c4, (79.0, c4[1])], 2.0)
r1p, r1n, d1k, d1a = padpos("R1", 1), padpos("R1", 2), padpos("D1", 1), padpos("D1", 2)
trk("5V_PI", [(83.0, 47.8), (85.0, 47.8), (85.0, r1p[1]), r1p], 0.5); trk("5V_PI", [(85.0, 47.8), padpos("TP4", 1)], 0.5)
trk("PG_LED_A", [r1n, d1a], 0.5); trk("PI_GND", [d1k, (d1k[0] - 1.7, d1k[1])], 0.5); via("PI_GND", d1k[0] - 1.7, d1k[1])
tp5 = padpos("TP5", 1); trk("PI_GND", [tp5, (tp5[0] + 1.5, tp5[1])], 0.8); via("PI_GND", tp5[0] + 1.5, tp5[1])
# trim option network (DNP): TRIM(pin6) -> R3 pad1 (R3 = trim-UP, TRIM->-Vout) and R2 pad1 (R2 = trim-down, TRIM->+Vout)
u6 = padpos("U1", 6); r2a, r2b, r3a, r3b = padpos("R2", 1), padpos("R2", 2), padpos("R3", 1), padpos("R3", 2)
trk("TRIM", [u6, r3a, (r3a[0], r2a[1]), r2a], 0.5)
trk("5V_ISO_RAW", [r2b, (r2b[0], 37.0)], 0.5)
trk("PI_GND", [r3b, (r3b[0] + 1.4, r3b[1])], 0.5); via("PI_GND", r3b[0] + 1.4, r3b[1])

def zone(nn, layer, pts, prio=0, clr=0.5):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net(nn)); z.SetAssignedPriority(prio)
    z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(clr)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(z)
zone("+12V_F", pcbnew.F_Cu, [(21.5, 35.3), (38.5, 35.3), (38.5, 62.5), (21.5, 62.5)], 1)
zone("5V_ISO_RAW", pcbnew.F_Cu, [(70, 36), (83, 36), (83, 44.6), (70, 44.6)], 1)
zone("5V_PI", pcbnew.F_Cu, [(78.2, 47.4), (83, 47.4), (83, 59.4), (89.7, 59.4), (89.7, 62.9), (78.2, 62.9)], 1)
zone("12V_GND", pcbnew.B_Cu, [(1.5, 1.5), (45, 1.5), (45, 68.5), (1.5, 68.5)], 0, 0.4)
zone("PI_GND", pcbnew.B_Cu, [(55, 1.5), (98.5, 1.5), (98.5, 68.5), (55, 68.5)], 0, 0.4)

for a in ((0,0,100,0),(100,0,100,70),(100,70,0,70),(0,70,0,0)):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(a[0], a[1])); s.SetEnd(P(a[2], a[3]))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
def text(s, x, y, h=1.2, layer=pcbnew.F_SilkS, just=pcbnew.GR_TEXT_H_ALIGN_LEFT):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
    t.SetTextSize(P(h, h)); t.SetTextThickness(mm(0.2 if h < 1.5 else 0.25)); t.SetHorizJustify(just); b.Add(t)
C = pcbnew.GR_TEXT_H_ALIGN_CENTER
text("OSBAMS Pi/Display Power Rev.A", 50, 2.6, 1.6, just=C)
text("12V IN", 6.5, 56.5, 1.4); text("PRIMARY 12V SIDE", 9, 64, 1.2); text("+12V   GND", 6.5, 51.5, 0.9)
text("ISOLATED 5V OUT", 56.0, 63.0, 0.9); text("5V / 8A MAX", 56.0, 60.6, 0.9)
text("1,2=+5V 3,4=GND", 56.0, 68.4, 0.8)
text("PI SIDE — ISOLATED", 56.0, 66.2, 1.1); text("ISOLATION BARRIER", 50, 38.5, 1.0, just=C)
text("NO COPPER CROSSING / 10mm GAP", 50, 40.2, 0.8, just=C)
text("R2/R3 DNP - TRIM OPTION", 56.0, 52.0, 0.8); text("U1 PIN1 SIDE", 28.0, 14.5, 0.8)
text("RC1.1 - NOT FOR FAB", 50, 69.0, 0.8, pcbnew.F_SilkS, C)
text("OSBAMS Pi/Display Power Rev.A  2oz Cu", 50, 68.0, 0.9, pcbnew.B_SilkS, C)
for y in range(5, 66, 4):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(50, y)); s.SetEnd(P(50, y + 2.0))
    s.SetLayer(pcbnew.F_SilkS); s.SetWidth(mm(0.2)); b.Add(s)

b.GetDesignSettings().SetBoardThickness(mm(1.6))
b.Save(out); b = pcbnew.LoadBoard(out); b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(out)
txt = open(out).read()
stack = ('(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) '
 '(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) (layer "F.Cu" (type "copper") (thickness 0.07)) '
 '(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02)) '
 '(layer "B.Cu" (type "copper") (thickness 0.07)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) '
 '(layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "ENIG") (dielectric_constraints no))')
txt, n = re.subn(r'\(setup\b', '(setup\n    ' + stack, txt, count=1); open(out, "w").write(txt)
print("saved", out)

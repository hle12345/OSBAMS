#!/usr/bin/python3
"""Build OSBAMS_Pi_Power_Carrier_RevB.kicad_pcb with pcbnew (KiCad 10 container, kcompat shim). usage: build_carrier_pcb.py <out.kicad_pcb>"""
import sys, os, re, math
import pcbnew, kcompat
from pcbnew import FromMM as mm, VECTOR2I as V
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_carrier import *

LIB = os.environ.get("KICAD_FP_DIR", "/usr/share/kicad/footprints"); REL = os.environ.get("REL", "RC1")
out = sys.argv[1]
b = pcbnew.BOARD(); nets = {}
P = lambda x, y: V(mm(x), mm(y))
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    return nets[n]
for n in ["+12V_IN", "+12V_F", "12V_GND", "5V_ISO_RAW", "5V_PI", "PI_GND", "PG_LED_A", "TRIM"]: net(n)
SIL, FAB = pcbnew.F_SilkS, pcbnew.F_Fab
meta = {p[0]: p for p in PARTS}; fps = {}
def seg(fp, layer, x1, y1, x2, y2, w=0.2):
    s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_SEGMENT); o = fp.GetPosition()
    s.SetStart(V(o.x + mm(x1), o.y + mm(y1))); s.SetEnd(V(o.x + mm(x2), o.y + mm(y2))); s.SetLayer(layer); s.SetWidth(mm(w)); fp.Add(s)
def libfp(ref, key, x, y, angle, padnets):
    lib, name = key.split(":")
    fp = pcbnew.FootprintLoad(f"{LIB}/{lib}.pretty", name); assert fp is not None, key
    fp.SetReference(ref); fp.SetValue(meta[ref][1] if ref in meta else name)
    fp.SetPosition(P(x, y)); fp.SetOrientationDegrees(angle); fp.SetFPID(pcbnew.LIB_ID(lib, name))
    for p in fp.Pads():
        n = p.GetNumber()
        if n in padnets: p.SetNet(net(padnets[n]))
    for t in (fp.Reference(), fp.Value()):
        if t.GetLayer() == SIL: t.SetLayer(FAB)
    fp.Value().SetVisible(False); b.Add(fp); fps[ref] = fp; return fp
def custom(ref, lib_name, x, y, value=None):
    fp = pcbnew.FOOTPRINT(b); fp.SetReference(ref); fp.SetValue(value or (meta[ref][1] if ref in meta else lib_name)); fp.SetPosition(P(x, y))
    fp.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", lib_name)); b.Add(fp); fps[ref] = fp
    fp.Reference().SetLayer(FAB); fp.Value().SetVisible(False); return fp
def pad(fp, num, dx, dy, w, h, attr, shape, netname=None, drill=None):
    p = pcbnew.PAD(fp); p.SetNumber(str(num)); o = fp.GetPosition(); p.SetPosition(V(o.x + mm(dx), o.y + mm(dy))); p.SetSize(P(w, h))
    if attr == "pth":
        p.SetAttribute(pcbnew.PAD_ATTRIB_PTH); p.SetLayerSet(p.PTHMask()); p.SetDrillSize(P(drill, drill))
    elif attr == "npth":
        p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetLayerSet(p.UnplatedHoleMask()); p.SetDrillSize(P(drill, drill))
    else:
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetLayerSet(p.SMDMask())
    p.SetShape({"rect": pcbnew.PAD_SHAPE_RECT, "circle": pcbnew.PAD_SHAPE_CIRCLE}[shape])
    if netname: p.SetNet(net(netname))
    fp.Add(p); return p
two = lambda r, a, c: {"1": a, "2": c}

# ---- primary side
libfp("J_IN", meta["J_IN"][5], *POS["J_IN"], two("J", "+12V_IN", "12V_GND"))
f1 = custom("F1", "Fuse_1206_Littelfuse407", POS["F1"][0], POS["F1"][1], "0407008.WR")      # Littelfuse 407 recommended land pattern: pad 1.0 x 1.8, gap 1.5
pad(f1, 1, -1.25, 0, 1.0, 1.8, "smd", "rect", "+12V_IN"); pad(f1, 2, 1.25, 0, 1.0, 1.8, "smd", "rect", "+12V_F")
for a_ in ((-1.6, -0.8, 1.6, -0.8), (1.6, -0.8, 1.6, 0.8), (1.6, 0.8, -1.6, 0.8), (-1.6, 0.8, -1.6, -0.8)): seg(f1, FAB, *a_, 0.1)
f1.SetOrientationDegrees(POS["F1"][2])
libfp("TVS1", meta["TVS1"][5], *POS["TVS1"], two("T", "+12V_F", "12V_GND"))
libfp("C1", meta["C1"][5], *POS["C1"], two("C", "+12V_F", "12V_GND"))
libfp("C2", meta["C2"][5], *POS["C2"], two("C", "+12V_F", "12V_GND"))
for ref, nn in (("TP1", "+12V_IN"), ("TP2", "12V_GND"), ("TP3", "5V_ISO_RAW"), ("TP4", "5V_PI"), ("TP5", "PI_GND")): libfp(ref, meta[ref][5], *POS[ref], {"1": nn})
# ---- U1 RSDW40F-05 (Mean Well drawing, bottom view; PCB top view = mirror image). Built for the primary-left orientation, then rotated.
u1 = custom("U1", "RSDW40F-05_MeanWell_2x1in", POS["U1"][0], POS["U1"][1], "RSDW40F-05")
RSDW_PINS = {1: (5.08, 48.26), 2: (10.16, 48.26), 3: (20.32, 48.26), 4: (2.54, 2.54), 5: (12.7, 2.54), 6: (22.86, 2.54)}
RSDW_NETS = {1: "+12V_F", 2: "12V_GND", 3: None, 4: "5V_ISO_RAW", 5: "PI_GND", 6: "TRIM"}
for n, (u_, v_) in RSDW_PINS.items(): pad(u1, n, 25.4 - v_, 12.7 - u_, 2.4, 2.4, "pth", "circle", RSDW_NETS[n], 1.3)
for a in ((-25.4, -12.7, 25.4, -12.7), (25.4, -12.7, 25.4, 12.7), (25.4, 12.7, -25.4, 12.7), (-25.4, 12.7, -25.4, -12.7)): seg(u1, SIL, *a)
seg(u1, SIL, -24.0, -8.5, -24.0, -6.5)
u1.SetOrientationDegrees(POS["U1"][2])
# ---- secondary side
libfp("F2", meta["F2"][5], *POS["F2"], two("F2", "5V_ISO_RAW", "5V_PI"))
libfp("R3", meta["R3"][5], *POS["R3"], two("R", "TRIM", "PI_GND"))
libfp("C4", meta["C4"][5], *POS["C4"], two("C", "5V_PI", "PI_GND"))
libfp("C5", meta["C5"][5], *POS["C5"], two("C", "5V_PI", "PI_GND"))
libfp("C6", meta["C6"][5], *POS["C6"], two("C", "5V_PI", "PI_GND"))
libfp("R1", meta["R1"][5], *POS["R1"], two("R", "5V_PI", "PG_LED_A"))
libfp("D1", meta["D1"][5], *POS["D1"], two("D", "PI_GND", "PG_LED_A"))
libfp("J_DISP", meta["J_DISP"][5], *POS["J_DISP"], {"1": "5V_PI", "2": "PI_GND"})
# ---- J2: Samtec SSW-120-01-L-D pattern by Pi pin number (THT 1.7 mm pad, 1.0 mm drill), mounted from the underside
j2 = custom("J2", "SSW-120-01-L-D_RPi_TopView", HDR[0], HDR[1], "SSW-120-01-L-D")
for n in range(1, 41):
    x, y = pin_xy(n); pad(j2, n, x - HDR[0], y - HDR[1], 1.7, 1.7, "pth", "rect" if n == 1 else "circle", PIN_NETS.get(n), 1.0)
for a in ((-1.5, -2.8, 50.5, -2.8), (50.5, -2.8, 50.5, 2.8), (50.5, 2.8, -1.5, 2.8), (-1.5, 2.8, -1.5, -2.8)): seg(j2, SIL, *a, 0.15)
# ---- mechanical: Pi header-end spacers (M2.5) and enclosure standoffs / key posts (M3), fiducials
for ref, (x, y) in PI_HOLES.items():
    k = custom(ref, "MountingHole_2.7mm_M2.5", x, y, "M2.5 to Pi"); pad(k, "", 0, 0, 2.7, 2.7, "npth", "circle", None, 2.7); k.SetBoardOnly(True)
for ref, (x, y) in MECH_HOLES.items():
    k = custom(ref, "MountingHole_3.2mm_M3_Standoff", x, y, "M3 standoff"); pad(k, "", 0, 0, 3.2, 3.2, "npth", "circle", None, 3.2); k.SetBoardOnly(True)
for i, (x, y) in enumerate([(4.0, 56.0), (80.0, 24.5), (45.0, 3.0)], 1):
    f = libfp(f"FID{i}", "Fiducial:Fiducial_1mm_Mask2mm", x, y, 0, {}); f.Reference().SetVisible(False)

# ---- copper
def trk(nn, pts, w, layer=pcbnew.F_Cu):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(P(*a)); t.SetEnd(P(*c)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(net(nn)); b.Add(t)
def via(nn, x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4)); v.SetNet(net(nn)); v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)
def padpos(ref, n):
    p = fps[ref].FindPadByNumber(str(n)).GetPosition(); return (p.x / 1e6, p.y / 1e6)
def zone(nn, layer, pts, prio=0, clr=0.5):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net(nn)); z.SetAssignedPriority(prio); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(clr)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(z)
if os.environ.get("CARRIER_DUMP"):
    for r, f in fps.items(): print(r, [(p.GetNumber(), round(p.GetPosition().x / 1e6, 2), round(p.GetPosition().y / 1e6, 2)) for p in f.Pads()][:6], [round(v / 1e6, 1) for v in (f.GetBoundingBox(False).GetLeft(), f.GetBoundingBox(False).GetTop(), f.GetBoundingBox(False).GetRight(), f.GetBoundingBox(False).GetBottom())])
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "carrier_routes.py")).read())

# ---- outline, text, stackup
poly = [(0, 0), (BOARD_W, 0), (BOARD_W, MAIN_H), (TAB[2], MAIN_H), (TAB[2], BOARD_H), (TAB[0], BOARD_H), (TAB[0], MAIN_H), (0, MAIN_H)]
for a, c in zip(poly, poly[1:] + poly[:1]):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(*a)); s.SetEnd(P(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
def text(s, x, y, h=1.0, layer=SIL, just=pcbnew.GR_TEXT_H_ALIGN_LEFT):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer); t.SetTextSize(P(h, h)); t.SetTextThickness(mm(0.18)); t.SetHorizJustify(just); b.Add(t)
C = pcbnew.GR_TEXT_H_ALIGN_CENTER
for ln in TEXTS: text(*ln[:4], just=C if len(ln) > 4 else pcbnew.GR_TEXT_H_ALIGN_LEFT)
for x in range(4, 82, 6):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(x, 26.25)); s.SetEnd(P(x + 3.0, 26.25)); s.SetLayer(SIL); s.SetWidth(mm(0.2)); b.Add(s)
b.GetDesignSettings().SetBoardThickness(mm(1.6))
b.Save(out); b = pcbnew.LoadBoard(out); b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(out)
txt = open(out).read()
stack = ('(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) '
 '(layer "F.Cu" (type "copper") (thickness 0.07)) (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02)) '
 '(layer "B.Cu" (type "copper") (thickness 0.07)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) (layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "ENIG") (dielectric_constraints no))')
txt, n = re.subn(r'\(setup\b', '(setup\n    ' + stack, txt, count=1); open(out, "w").write(txt)
print("saved", out)

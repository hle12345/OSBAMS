#!/usr/bin/python3
"""OSBAMS_Pi_Power_Interposer_RevA: keyed 5 V power interposer that plugs onto the Raspberry Pi 5 40-pin header.
Run with /usr/bin/python3 (KiCad 7 pcbnew).  Output dir: argv[1]."""
import sys, os, re, subprocess, uuid, glob, zipfile, csv
import pcbnew
from pcbnew import FromMM as mm, VECTOR2I as V
D = sys.argv[1]; NAME = "OSBAMS_Pi_Power_Interposer_RevA"; LIB = "/usr/share/kicad/footprints"
for sub in ("kicad", "gerbers", "drill", "bom", "docs", "reports"): os.makedirs(f"{D}/{sub}", exist_ok=True)
P = lambda x, y: V(mm(x), mm(y))
# ---------- geometry (mm, board top-left origin, +y down; header axis along x; outward (beyond Pi edge) = -y)
# HAT+ spec Fig.2: 65 mm wide, Pi mounting holes 3.5 mm from the edge on a 58 mm pitch, header centred between them on the hole-row axis.
BW = 65.0; XC = 32.5; X0 = XC - 19 * 2.54 / 2   # pin-1 column x (8.37)
YH, Y_TOP, Y_BOT = 20.0, 2.0, 24.0
DX = X0 - 4.0
PIN_NETS = {2: "5V_PI", 4: "5V_PI", 6: "PI_GND", 9: "PI_GND", 14: "PI_GND", 20: "PI_GND"}
def pin_xy(n):                 # Pi header, top view: odd pins inner row (y+1.27), even pins outer row (y-1.27)
    col = (n + 1) // 2
    return X0 + (col - 1) * 2.54, YH + (1.27 if n % 2 else -1.27)
J1 = (20.0 + DX, 11.1)              # Micro-Fit pin 1, rotation 0 -> body toward -y (off the board edge side)
b = pcbnew.BOARD(); nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    return nets[n]
net("5V_PI"); net("PI_GND")
def seg(fp, layer, x1, y1, x2, y2, w=0.15):
    s = pcbnew.FP_SHAPE(fp); s.SetShape(pcbnew.SHAPE_T_SEGMENT); o = fp.GetPosition()
    s.SetStart0(P(x1, y1)); s.SetEnd0(P(x2, y2)); s.SetStart(V(o.x + mm(x1), o.y + mm(y1))); s.SetEnd(V(o.x + mm(x2), o.y + mm(y2)))
    s.SetLayer(layer); s.SetWidth(mm(w)); fp.Add(s)
# J1: Molex 43045-0400 right-angle (official KiCad footprint), pins 1,2 = +5 V, 3,4 = GND
fp = pcbnew.FootprintLoad(f"{LIB}/Connector_Molex.pretty", "Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal")
fp.SetReference("J1"); fp.SetValue("43045-0400"); fp.SetPosition(P(*J1)); fp.SetFPID(pcbnew.LIB_ID("Connector_Molex", "Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal"))
for p in fp.Pads():
    if p.GetNumber() in ("1", "2"): p.SetNet(net("5V_PI"))
    if p.GetNumber() in ("3", "4"): p.SetNet(net("PI_GND"))
fp.Reference().SetLayer(pcbnew.F_Fab); fp.Value().SetVisible(False); b.Add(fp)
# J2: 2x20 socket pattern by Raspberry Pi pin number (THT 1.7 mm pad, 1.0 mm drill), mounted from the underside
fp2 = pcbnew.FOOTPRINT(b); fp2.SetReference("J2"); fp2.SetValue("2x20 stacking socket"); fp2.SetPosition(P(X0, YH))
fp2.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", "PinSocket_2x20_P2.54mm_RPi_TopView")); fp2.Reference().SetLayer(pcbnew.F_Fab); fp2.Value().SetVisible(False)
for n in range(1, 41):
    x, y = pin_xy(n); pd = pcbnew.PAD(fp2); pd.SetNumber(str(n)); pd.SetPosition(P(x, y)); pd.SetPos0(P(x - X0, y - YH))
    pd.SetSize(P(1.7, 1.7)); pd.SetAttribute(pcbnew.PAD_ATTRIB_PTH); pd.SetLayerSet(pd.PTHMask()); pd.SetDrillSize(P(1.0, 1.0))
    pd.SetShape(pcbnew.PAD_SHAPE_RECT if n == 1 else pcbnew.PAD_SHAPE_CIRCLE)
    if n in PIN_NETS: pd.SetNet(net(PIN_NETS[n]))
    fp2.Add(pd)
seg(fp2, pcbnew.F_SilkS, -1.5, -2.8, 50.5, -2.8); seg(fp2, pcbnew.F_SilkS, 50.5, -2.8, 50.5, 2.8); seg(fp2, pcbnew.F_SilkS, 50.5, 2.8, -1.5, 2.8); seg(fp2, pcbnew.F_SilkS, -1.5, 2.8, -1.5, -2.8)
b.Add(fp2)
# Pi mounting-hole positions (M2.5 spacers to the Pi, per HAT+ guidance: attach to at least one Pi hole; also strain relief)
for i, x in enumerate((3.5, 61.5), 1):
    k = pcbnew.FOOTPRINT(b); k.SetReference(f"M{i}"); k.SetValue("M2.5 to Pi"); k.SetPosition(P(x, YH)); k.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", "MountingHole_2.7mm_M2.5"))
    pd = pcbnew.PAD(k); pd.SetNumber(""); pd.SetPosition(P(x, YH)); pd.SetPos0(P(0, 0)); pd.SetSize(P(2.7, 2.7)); pd.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pd.SetLayerSet(pd.UnplatedHoleMask()); pd.SetShape(pcbnew.PAD_SHAPE_CIRCLE); pd.SetDrillSize(P(2.7, 2.7)); k.Add(pd)
    k.Reference().SetLayer(pcbnew.F_Fab); k.Value().SetVisible(False); b.Add(k)
# Key standoff holes (M2.5 NPTH 2.7 mm) on the OUTWARD side: reversed (180 deg) fitting would put them over the Pi PCB
for i, (x, y) in enumerate([(18.5, 5.5), (43.25, 5.5)], 1):
    k = pcbnew.FOOTPRINT(b); k.SetReference(f"K{i}"); k.SetValue("KEY M2.5"); k.SetPosition(P(x, y)); k.SetFPID(pcbnew.LIB_ID("OSBAMS_PiPwr", "KeyStandoff_M2.5"))
    pd = pcbnew.PAD(k); pd.SetNumber(""); pd.SetPosition(P(x, y)); pd.SetPos0(P(0, 0)); pd.SetSize(P(2.7, 2.7)); pd.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pd.SetLayerSet(pd.UnplatedHoleMask()); pd.SetShape(pcbnew.PAD_SHAPE_CIRCLE); pd.SetDrillSize(P(2.7, 2.7)); k.Add(pd)
    k.Reference().SetLayer(pcbnew.F_Fab); k.Value().SetVisible(False); b.Add(k)
def zone(nn, layer, pts, clr=0.5):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(net(nn)); z.SetMinThickness(mm(0.25)); z.SetLocalClearance(mm(clr)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(z)
zone("5V_PI", pcbnew.F_Cu, [(2.7 + DX, 9.0), (24.5 + DX, 9.0), (24.5 + DX, 12.7), (7.5 + DX, 12.7), (7.5 + DX, 19.8), (2.7 + DX, 19.8)])
zone("PI_GND", pcbnew.B_Cu, [(0.8, 2.8), (BW - 0.8, 2.8), (BW - 0.8, Y_BOT - 0.8), (0.8, Y_BOT - 0.8)], 0.4)
for a in ((0, Y_TOP, BW, Y_TOP), (BW, Y_TOP, BW, Y_BOT), (BW, Y_BOT, 0, Y_BOT), (0, Y_BOT, 0, Y_TOP)):
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(P(a[0], a[1])); s.SetEnd(P(a[2], a[3])); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); b.Add(s)
def text(s, x, y, h=1.0, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer); t.SetTextSize(P(h, h)); t.SetTextThickness(mm(0.18)); t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT); b.Add(t)
text("OSBAMS Pi Power Interposer Rev.A", 29.0 + DX, 3.4, 0.9); text("KEY", 17.5, 7.6, 0.8); text("KEY", 42.25, 7.6, 0.8)
text("FIT KEY STANDOFFS", 29.0 + DX, 9.6, 0.8); text("5V / 8A MAX  1,2=+5V 3,4=GND", 29.0 + DX, 12.6, 0.8); text("ISOLATED 5V IN", 29.0 + DX, 14.6, 0.8)
text("PI SIDE - ISOLATED", 29.0 + DX, 16.4, 0.8); text("PI PIN 1", 6.0, 22.9, 0.7); text("RC1 - NOT FOR FAB", 29.0 + DX, 22.7, 0.8)
text("Rev.A  2oz Cu  1.6mm", 30.0 + DX, 21.2, 0.8, pcbnew.B_SilkS)
b.GetDesignSettings().SetBoardThickness(mm(1.6))
out = f"{D}/kicad/{NAME}.kicad_pcb"; b.Save(out); b = pcbnew.LoadBoard(out); b.BuildConnectivity(); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(out)
stack = ('(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) '
 '(layer "F.Cu" (type "copper") (thickness 0.07)) (layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02)) '
 '(layer "B.Cu" (type "copper") (thickness 0.07)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) (layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) (copper_finish "ENIG") (dielectric_constraints no))')
t = open(out).read(); t = re.sub(r'\(setup\b', '(setup\n    ' + stack, t, count=1); open(out, "w").write(t)
open(f"{D}/kicad/{NAME}.kicad_pro", "w").write('{"meta":{"filename":"%s.kicad_pro","version":1},"board":{"design_settings":{"rules":{"min_copper_edge_clearance":0.5,"min_clearance":0.25}}},"sheets":[["root",""]]}\n' % NAME)
pcbnew.WriteDRCReport(pcbnew.LoadBoard(out), f"{D}/reports/DRC_report.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)

# ---------- schematic (embedded symbols, labels on pin ends)
ROOT = "3b1d6c7e-2a44-4f0e-8d5a-91c0a7e4b002"; G = 2.54; u = lambda: str(uuid.uuid4())
def sym_lib(name, left, right, hw=7.62):
    n = max(len(left), len(right)); hh = G * (n + 1) / 2
    o = [f'(symbol "OSBAMS_PiPwr:{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
         f'  (property "Reference" "J" (at 0 {hh+1.5:.2f} 0) (effects (font (size 1.27 1.27))))', f'  (property "Value" "{name}" (at 0 {-hh-1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
         '  (property "Footprint" "" (at 0 0 0) (effects hide))', '  (property "Datasheet" "" (at 0 0 0) (effects hide))',
         f'  (symbol "{name}_0_1" (rectangle (start {-hw} {hh:.2f}) (end {hw} {-hh:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))', f'  (symbol "{name}_1_1"']
    for side, x, ang in ((left, -hw - G, 0), (right, hw + G, 180)):
        for i, (num, nm) in enumerate(side):
            y = (len(side) - 1) * G / 2 - i * G
            o.append(f'    (pin passive line (at {x:.2f} {y:.2f} {ang}) (length {G}) (name "{nm}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))')
    o.append("  ))"); return "\n".join(o)
J1pins = ([("1", "+5V"), ("2", "+5V")], [("3", "GND"), ("4", "GND")])
RPI = {1: "3V3", 2: "5V", 3: "GPIO2", 4: "5V", 5: "GPIO3", 6: "GND", 7: "GPIO4", 8: "GPIO14", 9: "GND", 10: "GPIO15", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23", 17: "3V3", 18: "GPIO24", 19: "GPIO10", 20: "GND", 21: "GPIO9", 22: "GPIO25", 23: "GPIO11", 24: "GPIO8", 25: "GND", 26: "GPIO7", 27: "ID_SD", 28: "ID_SC", 29: "GPIO5", 30: "GND", 31: "GPIO6", 32: "GPIO12", 33: "GPIO13", 34: "GND", 35: "GPIO19", 36: "GPIO16", 37: "GPIO26", 38: "GPIO20", 39: "GND", 40: "GPIO21"}
J2pins = ([(str(n), f"{n} {RPI[n]}") for n in range(1, 41, 2)], [(str(n), f"{n} {RPI[n]}") for n in range(2, 41, 2)])
body = []
def place(ref, libname, pins, x0, y0, fpn, val, mpn):
    left, right = pins
    body.append(f'(symbol (lib_id "OSBAMS_PiPwr:{libname}") (at {x0:.2f} {y0:.2f} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n  (property "Reference" "{ref}" (at {x0:.2f} {y0-3:.2f} 0) (effects (font (size 1.27 1.27))))\n  (property "Value" "{val}" (at {x0:.2f} {y0+3:.2f} 0) (effects (font (size 1.27 1.27))))\n  (property "Footprint" "{fpn}" (at {x0:.2f} {y0:.2f} 0) (effects hide))\n  (property "Datasheet" "" (at {x0:.2f} {y0:.2f} 0) (effects hide))\n  (property "MPN" "{mpn}" (at {x0:.2f} {y0:.2f} 0) (effects hide))\n  '
        + "".join(f'(pin "{p[0]}" (uuid "{u()}"))' for p in left + right) + f'\n  (instances (project "{NAME}" (path "/{ROOT}" (reference "{ref}") (unit 1)))))')
    for side, sx, ang in ((left, -7.62 - G, 180), (right, 7.62 + G, 0)):
        for i, (num, nm) in enumerate(side):
            y = y0 - ((len(side) - 1) * G / 2 - i * G); x = x0 + sx
            net_ = {"J1": {"1": "5V_PI", "2": "5V_PI", "3": "PI_GND", "4": "PI_GND"}}.get(ref, PIN_NETS_STR).get(num)
            ex = x + (-G if ang == 180 else G)
            if net_ is None: body.append(f'(no_connect (at {x:.2f} {y:.2f}) (uuid "{u()}"))')
            else:
                body.append(f'(wire (pts (xy {x:.2f} {y:.2f}) (xy {ex:.2f} {y:.2f})) (stroke (width 0) (type default)) (uuid "{u()}"))')
                body.append(f'(label "{net_}" (at {ex:.2f} {y:.2f} {ang}) (effects (font (size 1.27 1.27)) (justify {"right" if ang == 180 else "left"} bottom)) (uuid "{u()}"))')
PIN_NETS_STR = {str(k): v for k, v in PIN_NETS.items()}
place("J1", "MicroFit4", J1pins, 40.0, 60.0, "Connector_Molex:Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal", "43045-0400", "430450400")
place("J2", "RPi40", J2pins, 130.0, 150.0, "OSBAMS_PiPwr:PinSocket_2x20_P2.54mm_RPi_TopView", "2x20 stacking socket", "TBD")
for i, net_ in enumerate(["5V_PI", "PI_GND"]):
    xx = 40.0 + i * 15
    body.append(f'(symbol (lib_id "OSBAMS_PiPwr:PWR_FLAG") (at {xx} 100 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid "{u()}")\n  (property "Reference" "#FLG0{i+1}" (at {xx} 97 0) (effects hide)) (property "Value" "PWR_FLAG" (at {xx} 103 0) (effects hide))\n  (pin "1" (uuid "{u()}")) (instances (project "{NAME}" (path "/{ROOT}" (reference "#FLG0{i+1}") (unit 1)))))')
    body.append(f'(wire (pts (xy {xx} 100) (xy {xx} 105.08)) (stroke (width 0) (type default)) (uuid "{u()}"))'); body.append(f'(label "{net_}" (at {xx} 105.08 270) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{u()}"))')
body.append(f'(text "OSBAMS Pi Power Interposer Rev.A RC1 - keyed Micro-Fit to Pi GPIO. +5 V on pins 2,4; GND on 6,9,14,20. All other pins unconnected." (at 12 12 0) (effects (font (size 2 2)) (justify left)) (uuid "{u()}"))')
pwr = '''(symbol "OSBAMS_PiPwr:PWR_FLAG" (power) (pin_names (offset 0) hide) (in_bom no) (on_board no)
  (property "Reference" "#FLG" (at 0 1.9 0) (effects (font (size 1.27 1.27)) hide)) (property "Value" "PWR_FLAG" (at 0 3.8 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects hide)) (property "Datasheet" "" (at 0 0 0) (effects hide))
  (symbol "PWR_FLAG_0_0" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))
  (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))))'''
open(f"{D}/kicad/{NAME}.kicad_sch", "w").write(f'(kicad_sch (version 20230121) (generator eeschema)\n  (uuid "{ROOT}") (paper "A2")\n  (title_block (title "OSBAMS Pi Power Interposer Rev.A") (rev "RC1"))\n  (lib_symbols\n{sym_lib("MicroFit4", *J1pins)}\n{sym_lib("RPi40", *J2pins)}\n{pwr}\n  )\n' + "\n".join(body) + '\n  (sheet_instances (path "/" (page "1")))\n)\n')
print("interposer built")

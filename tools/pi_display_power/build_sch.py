#!/usr/bin/env python3
"""Generate the KiCad 7 schematic (embedded symbols, net labels on pin ends)."""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(__file__))
from parts import *

ROOT = "7f3c1a52-0d4e-4c8e-9b61-5a0e3f2d1c11"
def u(): return str(uuid.uuid4())
FP = {"RSDW40_PLACEHOLDER": "OSBAMS_PiPwr:RSDW40F-05_PLACEHOLDER"}
meta = {p[0]: p for p in PARTS}

# part -> list of (pin number, pin name, type, net)  ; side L/R is assigned by order list below
SYM = {
 "U1": dict(L=[("1","+VIN","power_in","+12V_F"),("2","-VIN","power_in","12V_GND"),("3","ON/OFF","input","NC")],
            R=[("4","+VOUT","power_out","5V_ISO_RAW"),("5","-VOUT","power_out","PI_GND"),("6","TRIM","passive","NC")]),
 "F1": dict(L=[("1","1","passive","+12V_IN")], R=[("2","2","passive","+12V_F")]),
 "F2": dict(L=[("1","1","passive","5V_ISO_RAW")], R=[("2","2","passive","5V_PI")]),
 "TVS1": dict(L=[("1","K","passive","+12V_F")], R=[("2","A","passive","12V_GND")]),
 "J_IN": dict(L=[("1","+12V","passive","+12V_IN"),("2","GND","passive","12V_GND")], R=[]),
 "J_OUT": dict(L=[("1","+5V","passive","5V_PI"),("2","+5V","passive","5V_PI"),("3","GND","passive","PI_GND"),("4","GND","passive","PI_GND")], R=[]),
 "C1": dict(L=[("1","1","passive","+12V_F")], R=[("2","2","passive","12V_GND")]),
 "C2": dict(L=[("1","+","passive","+12V_F")], R=[("2","-","passive","12V_GND")]),
 "C4": dict(L=[("1","+","passive","5V_PI")], R=[("2","-","passive","PI_GND")]),
 "C5": dict(L=[("1","1","passive","PI_GND")], R=[("2","2","passive","5V_PI")]),
 "C6": dict(L=[("1","1","passive","PI_GND")], R=[("2","2","passive","5V_PI")]),
 "R1": dict(L=[("1","1","passive","5V_PI")], R=[("2","2","passive","PG_LED_A")]),
 "D1": dict(L=[("1","K","passive","PI_GND")], R=[("2","A","passive","PG_LED_A")]),
}
for t in ("TP1","TP2","TP3","TP4","TP5"):
    net = {"TP1":"+12V_IN","TP2":"12V_GND","TP3":"5V_ISO_RAW","TP4":"5V_PI","TP5":"PI_GND"}[t]
    SYM[t] = dict(L=[("1","TP","passive",net)], R=[])
FPNAME = {"RSDW40_PLACEHOLDER":"RSDW40F-05_PLACEHOLDER"}
G = 2.54
def libsym(ref):
    d = SYM[ref]; n = max(len(d["L"]), len(d["R"]), 1); hw = 7.62; hh = G * (n + 1) / 2 if n > 1 else G
    out = [f'(symbol "OSBAMS_PiPwr:{ref}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
           f'  (property "Reference" "{"U" if ref=="U1" else ref}" (at 0 {hh+1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
           f'  (property "Value" "{ref}" (at 0 {-hh-1.5:.2f} 0) (effects (font (size 1.27 1.27))))',
           '  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (symbol "{ref}_0_1" (rectangle (start {-hw} {hh:.2f}) (end {hw} {-hh:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'  (symbol "{ref}_1_1"']
    for side, x, ang in (("L", -hw - G, 0), ("R", hw + G, 180)):
        for i, (num, name, typ, _) in enumerate(d[side]):
            y = (len(d[side]) - 1) * G / 2 - i * G
            out.append(f'    (pin {typ} line (at {x:.2f} {y:.2f} {ang}) (length {G}) (name "{name}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))')
    out.append("  ))")
    return "\n".join(out)
pwrflag = '''(symbol "OSBAMS_PiPwr:PWR_FLAG" (power) (pin_names (offset 0) hide) (in_bom no) (on_board no)
  (property "Reference" "#FLG" (at 0 1.9 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" "PWR_FLAG" (at 0 3.8 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects hide)) (property "Datasheet" "" (at 0 0 0) (effects hide))
  (symbol "PWR_FLAG_0_0" (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))
  (symbol "PWR_FLAG_0_1" (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))))'''
body = []; pc = 0
def label(net, x, y, ang):
    just = "right" if ang == 180 else "left"
    body.append(f'(label "{net}" (at {x:.2f} {y:.2f} {ang}) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid "{u()}"))')
def wire(x1,y1,x2,y2): body.append(f'(wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type default)) (uuid "{u()}"))')
def noconn(x,y): body.append(f'(no_connect (at {x:.2f} {y:.2f}) (uuid "{u()}"))')
# placement grid: (col, row) per ref
LAY = {"J_IN":(1,1),"F1":(2,1),"TVS1":(3,1),"C1":(4,1),"C2":(5,1),"TP1":(1,2),"TP2":(2,2),"U1":(3,3),
       "F2":(1,5),"C4":(2,5),"C5":(3,5),"C6":(4,5),"R1":(5,5),"D1":(6,5),"J_OUT":(1,7),"TP3":(2,7),"TP4":(3,7),"TP5":(4,7)}
for ref, (cx, cy) in LAY.items():
    x0 = 25.4 + (cx - 1) * 45.72; y0 = 38.1 + (cy - 1) * 38.1
    d = SYM[ref]; hw = 7.62; m = meta[ref]
    fpn = f"OSBAMS_PiPwr:{m[5]}"
    pins = "".join(f'(pin "{p[0]}" (uuid "{u()}"))' for p in d["L"] + d["R"])
    refdes = ref
    body.append(f'(symbol (lib_id "OSBAMS_PiPwr:{ref}") (at {x0:.2f} {y0:.2f} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{u()}")\n'
      f'  (property "Reference" "{refdes}" (at {x0:.2f} {y0 - 6:.2f} 0) (effects (font (size 1.27 1.27))))\n'
      f'  (property "Value" "{m[1]}" (at {x0:.2f} {y0 + 6:.2f} 0) (effects (font (size 1.27 1.27))))\n'
      f'  (property "Footprint" "{fpn}" (at {x0:.2f} {y0:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
      f'  (property "Datasheet" "" (at {x0:.2f} {y0:.2f} 0) (effects hide))\n'
      f'  (property "Manufacturer" "{m[3]}" (at {x0:.2f} {y0:.2f} 0) (effects hide))\n'
      f'  (property "MPN" "{m[4]}" (at {x0:.2f} {y0:.2f} 0) (effects hide))\n  {pins}\n'
      f'  (instances (project "{NAME}" (path "/{ROOT}" (reference "{refdes}") (unit 1)))))')
    for side, sx, ang in (("L", -hw - G, 180), ("R", hw + G, 0)):
        for i, (num, name, typ, nn) in enumerate(d[side]):
            y = y0 - ((len(d[side]) - 1) * G / 2 - i * G); x = x0 + sx
            if nn == "NC": noconn(x, y)
            else:
                # short wire stub with label at the end for clean connectivity
                ex = x + (-2.54 if side == "L" else 2.54); wire(x, y, ex, y); label(nn, ex, y, ang)
# PWR_FLAGs
fy = 38.1 + 38.1 * 0
for i, (net) in enumerate(FLAG_NETS):
    x = 25.4 + 45.72 * (6 + i * 0) ; x = 230 - 0; xx = 235 + i * 12; yy = 50
    body.append(f'(symbol (lib_id "OSBAMS_PiPwr:PWR_FLAG") (at {xx:.2f} {yy:.2f} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid "{u()}")\n'
      f'  (property "Reference" "#FLG0{i+1}" (at {xx:.2f} {yy-3:.2f} 0) (effects hide)) (property "Value" "PWR_FLAG" (at {xx:.2f} {yy+3:.2f} 0) (effects hide))\n'
      f'  (pin "1" (uuid "{u()}")) (instances (project "{NAME}" (path "/{ROOT}" (reference "#FLG0{i+1}") (unit 1)))))')
    wire(xx, yy, xx, yy + 5.08); label(net, xx, yy + 5.08, 270)
txt = lambda s, x, y, sz=1.8: body.append(f'(text "{s}" (at {x} {y} 0) (effects (font (size {sz} {sz})) (justify left)) (uuid "{u()}"))')
txt("OSBAMS Pi/Display Power Rev.A - RC1 (NOT FOR FAB). XDR-75-12 12V -> RSDW40F-05 -> isolated 5V for Pi 5 + Waveshare DSI.", 12, 12, 2.2)
txt("PI_GND is isolated from 12V_GND. Do NOT tie them. 12V_GND is the XDR-75-12 return shared with OSBAMS Rev.2 controller PCB.", 12, 18)
txt("U1 pin 3 (ON/OFF) and pin 6 (TRIM) intentionally unconnected - confirm remote ON/OFF default state vs Mean Well datasheet.", 12, 22)
txt("Isolation barrier is inside U1 (1.6 kVDC). No Y-capacitor / bonding between PI_GND and 12V_GND is fitted.", 12, 26)
doc = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid "{ROOT}") (paper "A2")
  (title_block (title "OSBAMS Pi/Display Power Rev.A") (rev "RC1") (comment 1 "Release candidate - not final fabrication authorization"))
  (lib_symbols
{chr(10).join(libsym(r) for r in SYM)}
{pwrflag}
  )
{chr(10).join(body)}
  (sheet_instances (path "/" (page "1")))
)
'''
open(sys.argv[1], "w").write(doc)
print("wrote", sys.argv[1])

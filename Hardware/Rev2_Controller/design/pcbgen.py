"""KiCad 10 PCB generator (runs inside the KiCad 10 container with the pcbnew Python API).

Builds OSBAMS_Rev2_RC1.kicad_pcb from rev2_design.py: footprints, nets, placement, outline, 4-layer stack, zones,
netclasses/rules, silkscreen. Routing is done afterwards by an autorouter (route.py) and checked with kicad-cli DRC.
"""
import os, sys, math, json
import pcbnew
from pcbnew import FromMM as mm, ToMM

from . import rev2_design as D, schgen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRJ = os.path.join(ROOT, "OSBAMS_Rev2_RELEASE_CANDIDATE_1")
FPDIR = "/usr/share/kicad/footprints"
OX, OY = 100.0, 60.0            # board origin on the page
BW, BH = 100.0, 90.0            # board size


def V(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


# ------------------------------------------------------------------ manual placement (board mm, rotation deg CCW)
PLACE = {
    # left edge terminals (pads at x, pin 1 at y, pin 2 at y+5, entry toward the left edge)
    "J1": (12.5, 12.0, 0), "J2": (12.5, 27.0, 0), "J3": (12.5, 39.0, 0), "J4": (12.5, 51.0, 0),
    # power entry
    "F1": (25.0, 7.0, 0), "D2": (32.5, 7.0, 0), "D1": (40.0, 7.5, 0),
    # buck
    "U3": (31.0, 18.0, 0), "L1": (37.5, 18.5, 0),
    # MCU
    "U1": (58.0, 41.0, 0),
    # coil driver
    "Q1": (26.0, 54.0, 0),
    # status opto U4 (DIP-4)
    "U4": (22.0, 28.0, 0),
    # INA / pack sense (bottom-left)
    "J5": (14.0, 83.0, 0), "J6": (31.0, 83.0, 0), "U2": (24.0, 68.0, 0), "U5": (42.0, 76.0, 0),
    # SWD and boot
    "J9": (60.0, 80.0, 0), "SW1": (49.0, 63.0, 0), "JP1": (50.0, 70.0, 0),
    # host (isolated)
    "J8": (96.6, 22.0, 90), "U7": (73.0, 34.0, 0), "U6": (85.0, 32.0, 0), "U9": (88.0, 10.0, 0),
    # temperature probe interface
    "J7": (82.0, 86.0, 0), "U10": (76.0, 76.0, 0),
}

# passives are placed near an anchor pad: ref -> (anchor_ref, anchor_pad)
ANCHOR = {
    "C1": ("D1", "1"), "C2": ("U3", "5"), "C3": ("U3", "5"), "C4": ("U3", "1"), "R1": ("U3", "3"), "R2": ("U3", "3"), "R3": ("U3", "4"),
    "C5": ("L1", "2"), "C6": ("L1", "2"), "FB1": ("U1", "13"), "C7": ("FB1", "2"), "C8": ("FB1", "2"), "R4": ("FB1", "2"), "R5": ("L1", "2"), "D3": ("R5", "2"),
    "C10": ("U1", "19"), "C11": ("U1", "32"), "C12": ("U1", "64"), "C13": ("U1", "48"), "C14": ("U1", "1"), "C15": ("U1", "64"),
    "C16": ("U1", "13"), "C17": ("U1", "13"), "C18": ("U1", "7"), "R6": ("U1", "60"), "R7": ("U1", "21"), "D4": ("R7", "2"),
    "R38": ("U6", "8"), "R40": ("U6", "9"), "R39": ("R38", "2"), "R8": ("J8", "A5"), "R9": ("J8", "B5"), "R10": ("J8", "SH"), "C19": ("J8", "SH"), "C20": ("U6", "8"), "C21": ("U6", "8"), "C22": ("U6", "6"), "C23": ("U6", "6"),
    "C24": ("U7", "1"), "C25": ("U7", "8"),
    "R41": ("J6", "1"), "R42": ("J5", "1"), "R43": ("J5", "2"), "D5": ("R42", "2"), "D6": ("R43", "2"), "R11": ("U2", "10"), "R12": ("U2", "9"), "C26": ("U2", "10"), "C27": ("U2", "6"), "D7": ("R41", "2"), "R13": ("U2", "8"), "C28": ("U2", "8"),
    "R14": ("U2", "4"), "R15": ("U2", "5"), "R16": ("U2", "3"),
    "R17": ("J6", "2"), "R18": ("R17", "2"), "R19": ("R18", "2"), "R20": ("U1", "15"), "C29": ("U1", "15"), "D8": ("U1", "15"), "D14": ("D8", "2"), "R37": ("D8", "2"), "C34": ("D8", "2"),
    "R21": ("Q1", "1"), "R22": ("Q1", "1"), "D9": ("J4", "1"), "R23": ("J4", "1"), "D10": ("R23", "2"),
    "R24": ("U4", "1"), "D11": ("U4", "1"), "R25": ("U1", "14"), "C30": ("U1", "14"), "R26": ("J6", "3"), "R27": ("R26", "2"), "R28": ("R27", "2"),
    "D12": ("U5", "1"), "R29": ("U1", "40"), "C31": ("U1", "40"), "R30": ("J3", "2"), "R31": ("R30", "2"), "R32": ("U1", "51"), "C32": ("U1", "51"), "D13": ("U1", "51"),
    "C33": ("J7", "1"), "R33": ("U10", "6"), "R34": ("U10", "4"), "R35": ("U1", "29"), "R36": ("U1", "30"),
}

HOST_REFS = {"R40", "R38", "R39", "R8", "R9", "R10", "C19", "C20", "C21", "C22", "C23", "C25", "U6", "U9", "J8", "U7_side2"}
HOST_NETS = {"GND_HOST", "3V3_HOST", "VBUS_USB"}
HOST_BOX = (73.5, 0.0, 100.0, 48.0)      # x0, y0, x1, y1 of the isolated-side island (plus the isolation gap)

MINRAD = {"C10": 3.0, "C11": 3.0, "C12": 3.0, "C13": 3.0, "C14": 3.0, "C15": 3.5, "C16": 3.0, "C17": 3.0, "C18": 3.0, "R6": 3.0, "R7": 3.0, "C20": 3.5, "C21": 3.5, "C22": 3.5, "C23": 3.5, "C7": 3.0, "C8": 3.0, "R4": 3.0, "C25": 2.5, "C24": 2.5}

MH_POS = {"MH1": (4, 4), "MH2": (96, 4), "MH3": (4, 86), "MH4": (96, 86)}
FID_POS = {"FID1": (10, 2.5), "FID2": (90, 2.5), "FID3": (60, 88.0)}

from .netclasses import PK_NETS, PWR_NETS, RAIL_NETS, KELVIN_NETS, CLASSES


class PCB:
    def __init__(self, design=None, layers=4, size=None):
        self.D = design or D
        self.layers = layers
        self.size = size or (BW, BH)
        self.b = pcbnew.BOARD()
        self.fps = {}
        self.nets = {}
        self.g = schgen.SchGen(self.D, "/tmp/unused", self.D.PROJECT)

    # -------------------------------------------------- setup
    def setup(self):
        b = self.b
        b.SetCopperLayerCount(self.layers)
        ds = b.GetDesignSettings()
        ds.SetBoardThickness(mm(1.6))
        ds.m_MinClearance = mm(0.1)
        ds.m_TrackMinWidth = mm(0.15)
        ds.m_ViasMinSize = mm(0.5)
        ds.m_MinThroughDrill = mm(0.3)
        ds.m_CopperEdgeClearance = mm(0.3)
        ds.m_HoleClearance = mm(0.19)
        ds.m_SolderMaskMinWidth = mm(0.1)
        ns = ds.m_NetSettings
        dflt = ns.GetDefaultNetclass()
        dflt.SetClearance(mm(0.15)); dflt.SetTrackWidth(mm(0.2)); dflt.SetViaDiameter(mm(0.6)); dflt.SetViaDrill(mm(0.3))
        classes = {n: dict(w=w, c=c, nets=nets) for n, (c, w, nets) in CLASSES.items() if n != "Default"}
        for name, c in classes.items():
            nc = pcbnew.NETCLASS(name)
            nc.SetClearance(mm(c["c"])); nc.SetTrackWidth(mm(c["w"])); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
            ns.SetNetclass(name, nc)
            for n in c["nets"]:
                ns.SetNetclassPatternAssignment(n, name)

    def net(self, name):
        if name not in self.nets:
            ni = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(ni)
            self.nets[name] = ni
        return self.nets[name]

    # -------------------------------------------------- footprints
    def load_fp(self, fpid):
        lib, name = fpid.split(':', 1)
        path = os.path.join(PRJ, "OSBAMS_Rev2.pretty") if lib == "OSBAMS_Rev2" else os.path.join(FPDIR, lib + ".pretty")
        fp = pcbnew.FootprintLoad(path, name)
        if fp is None:
            raise RuntimeError(f"footprint {fpid} not found")
        return fp

    def add_footprints(self):
        for ref, c in self.D.COMPS.items():
            fp = self.load_fp(c['fp'])
            fp.SetReference(ref)
            fp.SetValue(str(c['value']))
            fp.SetFPIDAsString(c['fp']) if hasattr(fp, 'SetFPIDAsString') else None
            pinnet = {}
            for p, net in self.g.resolve(c):
                if net:
                    pinnet[p['number']] = net
            for pad in fp.Pads():
                n = pad.GetNumber()
                if n in pinnet:
                    pad.SetNet(self.net(pinnet[n]))
            for k, v in (("MPN", c.get('mpn', '')), ("Manufacturer", c.get('mfr', '')), ("Evidence", c.get('evid', '')), ("Description", c.get('desc', ''))):
                try:
                    fp.SetField(k, v)
                    f = fp.GetField(k)
                    f.SetVisible(False)
                    f.SetLayer(pcbnew.F_Fab)
                except Exception as e:
                    print("field", ref, k, e)
            fp.Value().SetVisible(False)
            r = fp.Reference()
            r.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
            r.SetTextThickness(mm(0.12))
            if c['key'] in ('MH', 'FID', 'TP'):
                r.SetVisible(False)
            elif ref[0] in 'RC' and c['key'] not in ('J_EB21',):
                r.SetLayer(pcbnew.F_Fab)       # small passives: designator on the fab layer only (assembly drawing)
            self.b.Add(fp)
            self.fps[ref] = fp
        # nets for every name (even unused pads)
        return self

    # -------------------------------------------------- geometry helpers
    def bbox(self, fp):
        bb = fp.GetBoundingBox(False)
        return ToMM(bb.GetLeft()) - OX, ToMM(bb.GetTop()) - OY, ToMM(bb.GetRight()) - OX, ToMM(bb.GetBottom()) - OY

    def pad_pos(self, ref, num):
        for p in self.fps[ref].Pads():
            if p.GetNumber() == num:
                return ToMM(p.GetPosition().x) - OX, ToMM(p.GetPosition().y) - OY
        raise KeyError(f"{ref}.{num}")

    def place(self, ref, x, y, rot=0, flip=False):
        fp = self.fps[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)

    def place_manual(self):
        for ref, (x, y, r) in PLACE.items():
            self.place(ref, x, y, r)
        for ref, (x, y) in MH_POS.items():
            self.place(ref, x, y)
        for ref, (x, y) in FID_POS.items():
            self.place(ref, x, y)

    def region_ok(self, ref, bb):
        """isolated-side parts stay inside the host island; everything else stays out of it (U7 straddles by design)."""
        if ref == "U7":
            return True
        x0, y0, x1, y1 = HOST_BOX
        inside = bb[0] >= x0 + 2.0 and bb[2] <= x1 - 1.0 and bb[1] >= y0 + 1.0 and bb[3] <= y1 - 1.0
        touches = bb[2] > x0 - 0.5 and bb[0] < x1 and bb[3] > y0 and bb[1] < y1
        if ref in HOST_REFS:
            return inside
        return not touches

    def overlaps(self, box, others, margin=0.35):
        l, t, r, bt = box
        for (a, b, c, d) in others:
            if l < c + margin and r > a - margin and t < d + margin and bt > b - margin:
                return True
        return False

    def place_passives(self):
        placed = [self.bbox(self.fps[r]) for r in list(PLACE) + list(MH_POS) + list(FID_POS)]
        order = [r for r in ANCHOR if r in self.fps]
        for ref in order:
            aref, apad = ANCHOR[ref]
            ax, ay = self.pad_pos(aref, apad)
            fp = self.fps[ref]
            anet = None
            for p in self.fps[aref].Pads():
                if p.GetNumber() == apad:
                    anet = p.GetNetname()
            best = None
            for rad in [x * 0.5 for x in range(int(2 * MINRAD.get(ref, 2.0)), 40)]:
                cands = []
                for ang in range(0, 360, 20):
                    cx, cy = ax + rad * math.cos(math.radians(ang)), ay + rad * math.sin(math.radians(ang))
                    cx, cy = round(cx * 2) / 2, round(cy * 2) / 2
                    for rot in (0, 90, 180, 270):
                        self.place(ref, cx, cy, rot)
                        bb = self.bbox(fp)
                        if bb[0] < 1.5 or bb[1] < 1.5 or bb[2] > BW - 1.5 or bb[3] > BH - 1.5:
                            continue
                        if self.overlaps(bb, placed) or not self.region_ok(ref, bb):
                            continue
                        cost = 0.0
                        for p in fp.Pads():
                            px, py = ToMM(p.GetPosition().x) - OX, ToMM(p.GetPosition().y) - OY
                            if anet and p.GetNetname() == anet:
                                cost += math.hypot(px - ax, py - ay)
                            else:
                                cost += 0.2 * math.hypot(px - ax, py - ay)
                        cands.append((cost, cx, cy, rot))
                if cands:
                    best = min(cands)
                    break
            if best is None:
                raise RuntimeError(f"no spot for {ref}")
            _, cx, cy, rot = best
            self.place(ref, cx, cy, rot)
            placed.append(self.bbox(fp))
        self.placed_boxes = placed

    def place_testpoints(self):
        tps = [r for r, c in self.D.COMPS.items() if c['key'] == 'TP']
        placed = list(self.placed_boxes)
        for ref in tps:
            fp = self.fps[ref]
            net = self.D.COMPS[ref]['nets'][1]
            pts = []
            for r2, f2 in self.fps.items():
                if r2 == ref:
                    continue
                for p in f2.Pads():
                    if p.GetNetname() == net:
                        pts.append((ToMM(p.GetPosition().x) - OX, ToMM(p.GetPosition().y) - OY))
            cxm = sum(p[0] for p in pts) / len(pts); cym = sum(p[1] for p in pts) / len(pts)
            # candidate points on a 1.25 mm grid, sorted by distance to the net centroid
            cand = sorted(((x * 1.25, y * 1.25) for x in range(2, 79) for y in range(2, 69)), key=lambda p: math.hypot(p[0] - cxm, p[1] - cym))
            for (x, y) in cand:
                self.place(ref, x, y)
                bb = self.bbox(fp)
                if bb[0] < 2 or bb[1] < 2 or bb[2] > BW - 2 or bb[3] > BH - 2:
                    continue
                mcu = self.bbox(self.fps['U1'])
                if mcu[0] - 7 < bb[2] and bb[0] < mcu[2] + 7 and mcu[1] - 7 < bb[3] and bb[1] < mcu[3] + 7:
                    continue
                hostnet = net in HOST_NETS
                x0, y0, x1, y1 = HOST_BOX
                inside = bb[0] >= x0 + 2.0 and bb[2] <= x1 - 1.0 and bb[1] >= y0 + 1.0 and bb[3] <= y1 - 1.0
                touches = bb[2] > x0 - 0.5 and bb[0] < x1 and bb[3] > y0 and bb[1] < y1
                if (hostnet and not inside) or (not hostnet and touches):
                    continue
                if not self.overlaps(bb, placed, 0.5):
                    placed.append(bb)
                    break
        self.placed_boxes = placed

    # -------------------------------------------------- board items
    def preroute(self):
        """escape stubs the autorouter handles poorly on the QFN-20 (U6)."""
        for pn in ():                 # U6 bottom-edge pins (VREGIN, VBUS-sense, RSTb): short escape stubs straight out of the package
            px, py = self.pad_pos("U6", pn)
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(V(px, py)); t.SetEnd(V(px, py + 0.8)); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu)
            t.SetNet(self.net([pd.GetNetname() for pd in self.fps["U6"].Pads() if pd.GetNumber() == pn][0]))
            self.b.Add(t)
        # corner pad 6 (VDD -> 3V3_HOST) of the QFN-20: short orthogonal escape stub the autorouter can attach to
        px, py = self.pad_pos("U6", "6")
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(V(px, py)); t.SetEnd(V(px - 1.0, py)); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu)
        t.SetNet(self.net("3V3_HOST"))
        self.b.Add(t)

    def gnd_fanout(self):
        """escape vias for the MCU VSS pads (the autorouter does not fan out plane pins on a 0.5 mm pitch package)"""
        u = self.fps["U1"]
        cx, cy = self.pad_pos("U1", "1")[0] * 0, 0
        ux, uy = ToMM(u.GetPosition().x) - OX, ToMM(u.GetPosition().y) - OY
        gnd = self.net("GND")
        for pad in u.Pads():
            if pad.GetNumber() in ("12", "18", "31", "47", "63"):
                px, py = ToMM(pad.GetPosition().x) - OX, ToMM(pad.GetPosition().y) - OY
                dx, dy = px - ux, py - uy
                if abs(dx) > abs(dy):
                    vx, vy = px + (1.7 if dx > 0 else -1.7), py
                else:
                    vx, vy = px, py + (1.7 if dy > 0 else -1.7)
                via = pcbnew.PCB_VIA(self.b)
                via.SetPosition(V(vx, vy)); via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3)); via.SetNet(gnd)
                via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                self.b.Add(via)
                t = pcbnew.PCB_TRACK(self.b)
                t.SetStart(V(px, py)); t.SetEnd(V(vx, vy)); t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd)
                self.b.Add(t)

    def outline(self):
        b = self.b
        pts = [(0, 0), (BW, 0), (BW, BH), (0, BH)]
        for i in range(4):
            s = pcbnew.PCB_SHAPE(b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i + 1) % 4]))
            s.SetWidth(mm(0.1))
            b.Add(s)

    def text(self, s, x, y, size=1.2, layer=None, rot=0, bold=False, just=None):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(V(x, y))
        t.SetLayer(layer if layer is not None else pcbnew.F_SilkS)
        size = max(size, 0.8)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(max(size * 0.15, 0.12)))
        t.SetTextAngleDegrees(rot)
        if bold:
            t.SetBold(True)
        if just == 'left':
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        elif just == 'right':
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        self.b.Add(t)

    def silk(self):
        self.text("OSBAMS Rev.2 Controller", 50, 2.2, 1.6, bold=True)
        self.text("RC1.2 2026-10-01  44 V / 10 A MAX  NOT FOR FABRICATION", 50, 4.6, 1.0)
        labels = {"J1": "12V IN  +/-", "J2": "E-STOP", "J3": "ARM", "J4": "K1 COIL", "J5": "SHUNT KELVIN", "J6": "PACK SENSE", "J7": "TEMP PROBE", "J8": "USB HOST", "J9": "SWD", "JP1": "BOOT0"}
        for ref, s in labels.items():
            x, y = self.pad_pos(ref, "1" if ref != "J8" else "A5")
            if ref in ("J1", "J2", "J3", "J4"):
                self.text(s, x - 5.2, y + 2.5, 1.0, just='right')
            elif ref in ("J5", "J6", "J7"):
                self.text(s, x + 3.5, y - 4.0, 1.0)
            elif ref == "J8":
                self.text(s, x - 9, y, 1.0, rot=90)
            else:
                self.text(s, x, y - 4.5, 1.0)
        # pin 1 / polarity legends for terminals
        for ref, names in {"J1": ("+12V", "GND"), "J2": ("+12V", "ESTOP_OUT"), "J3": ("ESTOP_OUT", "COIL_V"), "J4": ("COIL_V", "COIL_SW")}.items():
            x, y = self.pad_pos(ref, "1")
            self.text(f"1 {names[0]}", x - 5.2, y, 0.8, just='right')
            self.text(f"2 {names[1]}", x - 5.2, y + 5.0, 0.8, just='right')
        for ref, c in self.D.COMPS.items():
            if c['key'] == 'TP':
                x, y = ToMM(self.fps[ref].GetPosition().x) - OX, ToMM(self.fps[ref].GetPosition().y) - OY
                self.text(c['value'], x, y + 1.7, 0.7)
        self.text("ISOLATION BOUNDARY: GND | GND_HOST", 73.0, 14.0, 0.8, rot=90)

    def zones(self):
        b = self.b
        host = [(74.5, 2.5), (97.5, 2.5), (97.5, 47.5), (74.5, 47.5)]    # GND_HOST island (isolated side)
        main_poly = [(0.5, 0.5), (71.5, 0.5), (71.5, 47.5), (97.5, 47.5), (97.5, 89.5), (0.5, 89.5)]
        # host island: right of the isolation gap; main GND covers everything else with a 3 mm gap
        v33 = [(37.0, 12.0), (71.0, 12.0), (71.0, 70.0), (37.0, 70.0)]
        specs = [
            ("GND", main_poly, [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu], 2),
            ("GND_HOST", host, [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu], 3),
        ]
        for net, poly, layers, prio in specs:
            for ly in layers:
                z = pcbnew.ZONE(b)
                z.SetLayer(ly)
                z.SetNet(self.net(net))
                z.SetAssignedPriority(prio)
                z.SetMinThickness(mm(0.2))
                z.SetLocalClearance(mm(0.25))
                z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if ly in (pcbnew.F_Cu, pcbnew.B_Cu) else pcbnew.ZONE_CONNECTION_THT_THERMAL)
                z.SetThermalReliefGap(mm(0.3))
                z.SetThermalReliefSpokeWidth(mm(0.4))
                o = z.Outline()
                o.NewOutline()
                for (x, y) in poly:
                    o.Append(mm(OX + x), mm(OY + y))
                b.Add(z)

    def save(self, path):
        self.b.Save(path)


def build(path):
    p = PCB()
    p.setup()
    p.add_footprints()
    p.place_manual()
    p.place_passives()
    p.place_testpoints()
    p.preroute()
    p.gnd_fanout()
    p.outline()
    p.silk()
    p.zones()
    p.save(path)
    return p


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, "OSBAMS_Rev2_RC1.kicad_pcb")
    build(out)
    print("saved", out)

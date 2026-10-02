"""GND / GND_HOST stitching vias on a regular grid wherever they clear other copper (runs in the KiCad 10 container)."""
import os, sys
import pcbnew
from pcbnew import FromMM as mm, ToMM

PRJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RELEASE_CANDIDATE_1")
PCB = os.path.join(PRJ, "OSBAMS_Rev2_RC1.kicad_pcb")
OX, OY = 100.0, 60.0
HOST = (74.5, 2.5, 97.5, 47.5)           # GND_HOST island (x0, y0, x1, y1)
GAP = 3.0


def region(x, y):
    x0, y0, x1, y1 = HOST
    if x0 + 0.8 <= x <= x1 - 0.8 and y0 + 0.8 <= y <= y1 - 0.8:
        return "GND_HOST"
    if x0 - GAP - 0.8 <= x <= x1 + 0.8 and y <= y1 + 0.8:
        return None                       # isolation gap / host edge band
    if 1.2 <= x <= 98.8 and 1.2 <= y <= 88.8:
        return "GND"
    return None


def free(b, pos, net, clr):
    """no other-net copper (pads, tracks, vias, text-free) within the via radius + clearance of pos"""
    r = mm(0.3) + clr
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != net and pad.HitTest(pos, r):
                return False
            if pad.GetNetname() == net and pad.HitTest(pos, mm(0.05)):
                pass
            if pad.GetDrillSize().x > 0 and pad.HitTest(pos, r):      # keep off every hole
                return False
    for t in b.GetTracks():
        if t.GetNetname() != net and t.HitTest(pos, r):
            return False
        if t.GetNetname() == net and t.GetClass() == "PCB_VIA" and t.HitTest(pos, mm(1.0)):
            return False
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.HitTest(pos, mm(0.6)):
            return False
    return True


def seg_free(b, a, c, net, clr, half=mm(0.125)):
    n = max(2, int(((c.x - a.x) ** 2 + (c.y - a.y) ** 2) ** 0.5 / mm(0.15)))
    for k in range(n + 1):
        pos = pcbnew.VECTOR2I(int(a.x + (c.x - a.x) * k / n), int(a.y + (c.y - a.y) * k / n))
        r = half + clr
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() != net and pad.HitTest(pos, r):
                    return False
        for t in b.GetTracks():
            if t.GetNetname() != net and t.HitTest(pos, r):
                return False
    return True


def island_pass(b, nets, clr=mm(0.16)):
    """every GND/GND_HOST pad whose outer-layer fill island holds no via gets a short stub + via to the plane"""
    added = 0
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for z in b.Zones():
        if z.GetNetname() not in nets:
            continue
        ly = z.GetFirstLayer()
        polys = z.GetFilledPolysList(ly)
        net = z.GetNetname()
        for i in range(polys.OutlineCount()):
            ol = polys.COutline(i)
            if any(t.GetClass() == "PCB_VIA" and t.GetNetname() == net and ol.PointInside(t.GetPosition()) for t in b.GetTracks()):
                continue
            pads = [pd for f in b.GetFootprints() for pd in f.Pads() if pd.GetNetname() == net and pd.IsOnLayer(ly) and ol.PointInside(pd.GetPosition())]
            if not pads and ly in (pcbnew.F_Cu, pcbnew.B_Cu):
                continue
            if not pads:                              # inner-layer island without a via: drop one inside it
                bb = ol.BBox(); placed = False
                y = bb.GetTop()
                while y <= bb.GetBottom() and not placed:
                    x = bb.GetLeft()
                    while x <= bb.GetRight() and not placed:
                        pos = pcbnew.VECTOR2I(int(x), int(y))
                        inside = all(ol.PointInside(pcbnew.VECTOR2I(pos.x + dx, pos.y + dy)) for dx, dy in ((0, 0), (mm(0.5), 0), (-mm(0.5), 0), (0, mm(0.5)), (0, -mm(0.5))))
                        if inside and free(b, pos, net, clr):
                            v = pcbnew.PCB_VIA(b)
                            v.SetPosition(pos); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(nets[net])
                            v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                            b.Add(v); added += 1; placed = True
                        x += mm(0.5)
                    y += mm(0.5)
                if not placed:
                    print("no via spot inside inner-layer island", b.GetLayerName(ly), i)
                continue
            pad = pads[0]
            pc = pad.GetPosition()
            done = False
            for dist in (0.9, 1.2, 1.6, 2.0, 2.6, 3.2, 4.0, 5.0):
                for ang in range(0, 360, 15):
                    import math
                    pos = pcbnew.VECTOR2I(int(pc.x + mm(dist) * math.cos(math.radians(ang))), int(pc.y + mm(dist) * math.sin(math.radians(ang))))
                    if free(b, pos, net, clr) and seg_free(b, pc, pos, net, clr):
                        v = pcbnew.PCB_VIA(b)
                        v.SetPosition(pos); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(nets[net])
                        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                        b.Add(v)
                        tr = pcbnew.PCB_TRACK(b)
                        tr.SetStart(pc); tr.SetEnd(pos); tr.SetWidth(mm(0.25)); tr.SetLayer(ly); tr.SetNet(nets[net])
                        b.Add(tr)
                        added += 1; done = True
                        break
                if done:
                    break
            if not done:
                print("no stub+via spot for", pad.GetParentFootprint().GetReference(), pad.GetNumber())
    return added


def run(pitch=4.0, clr=mm(0.25)):
    b = pcbnew.LoadBoard(PCB)
    nets = {n: b.FindNet(n) for n in ("GND", "GND_HOST")}
    added = {"GND": 0, "GND_HOST": 0}
    y = 3.0
    while y < 89:
        x = 3.0 + (pitch / 2 if int((y - 3.0) / pitch) % 2 else 0)
        while x < 99:
            net = region(x, y)
            if net:
                pos = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
                if free(b, pos, net, clr):
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pos); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(nets[net])
                    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    b.Add(v); added[net] += 1
            x += pitch
        y += pitch
    for z in b.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    for _ in range(3):
        n = island_pass(b, nets)
        added["GND"] += n
        if not n:
            break
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(PCB)
    print("stitching vias", added)


if __name__ == "__main__":
    run(*(float(a) for a in sys.argv[1:2]))

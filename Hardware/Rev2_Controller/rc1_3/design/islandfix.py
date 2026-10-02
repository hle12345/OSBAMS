"""Give every GND / GND_HOST outer-layer fill island that holds pads but no via a via: first inside the island polygon (no stub), else stub + via (runs in the KiCad 10 container)."""
import math, pcbnew
from pcbnew import FromMM as mm, ToMM
from . import stitch as S
b = pcbnew.LoadBoard(S.PCB)
nets = {n: b.FindNet(n) for n in ("GND", "GND_HOST")}
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
fixed = 0
def newvia(pos, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(nets[net])
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v)
todo = []
for z in b.Zones():
    net = z.GetNetname()
    if net not in nets: continue
    for ly in z.GetLayerSet().Seq():
        if ly not in (pcbnew.F_Cu, pcbnew.B_Cu): continue
        polys = z.GetFilledPolysList(ly)
        for i in range(polys.OutlineCount()):
            ol = polys.COutline(i)
            if any(t.GetClass() == "PCB_VIA" and t.GetNetname() == net and ol.PointInside(t.GetPosition()) for t in b.GetTracks()): continue
            pads = [pd for f in b.GetFootprints() for pd in f.Pads() if pd.GetNetname() == net and pd.IsOnLayer(ly) and ol.PointInside(pd.GetPosition())]
            if pads: todo.append((net, ly, ol, pads))
for net, ly, ol, pads in todo:
    done = False
    bb = ol.BBox(); y = bb.GetTop()
    while y <= bb.GetBottom() and not done:
        x = bb.GetLeft()
        while x <= bb.GetRight() and not done:
            pos = pcbnew.VECTOR2I(int(x), int(y))
            if all(ol.PointInside(pcbnew.VECTOR2I(pos.x + dx, pos.y + dy)) for dx, dy in ((0, 0), (mm(0.35), 0), (-mm(0.35), 0), (0, mm(0.35)), (0, -mm(0.35)))) and S.free(b, pos, net, mm(0.2)):
                newvia(pos, net); fixed += 1; done = True
                print("island via inside", net, round(ToMM(pos.x) - 100, 2), round(ToMM(pos.y) - 60, 2))
            x += mm(0.1)
        y += mm(0.1)
    if done: continue
    pad = pads[0]; pc = pad.GetPosition()
    for dist in [0.9, 1.1, 1.4, 1.8, 2.2, 2.7, 3.3, 4.0, 5.0, 6.0]:
        for ang in range(0, 360, 10):
            pos = pcbnew.VECTOR2I(int(pc.x + mm(dist) * math.cos(math.radians(ang))), int(pc.y + mm(dist) * math.sin(math.radians(ang))))
            if S.free(b, pos, net, mm(0.2)) and S.seg_free(b, pc, pos, net, mm(0.2), half=mm(0.1)):
                newvia(pos, net)
                tr = pcbnew.PCB_TRACK(b); tr.SetStart(pc); tr.SetEnd(pos); tr.SetWidth(mm(0.2)); tr.SetLayer(ly); tr.SetNet(nets[net]); b.Add(tr)
                fixed += 1; done = True
                print("stub+via", pad.GetParentFootprint().GetReference(), pad.GetNumber(), round(ToMM(pos.x) - 100, 2), round(ToMM(pos.y) - 60, 2)); break
        if done: break
    if not done: print("NO SPOT for island with pad", pads[0].GetParentFootprint().GetReference(), pads[0].GetNumber())
print("islandfix added", fixed, "of", len(todo), "islands")
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(S.PCB)

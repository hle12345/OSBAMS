"""Measure GND / GND_HOST copper separation from the filled zones (runs in the KiCad 10 container)."""
import sys; sys.path.insert(0,"/work/Hardware/Rev2_Controller")
import pcbnew, math
from pcbnew import ToMM
from design import stitch as S
b=pcbnew.LoadBoard(S.PCB)
def pts(netname,layer):
    out=[]
    for z in b.Zones():
        if z.GetNetname()==netname and z.IsOnLayer(layer):
            P=z.GetFilledPolysList(layer)
            for i in range(P.OutlineCount()):
                ol=P.COutline(i)
                out+= [ol.CPoint(k) for k in range(ol.PointCount())]
    return out
def polys(netname,layer):
    ps=pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if z.GetNetname()==netname and z.IsOnLayer(layer):
            ps.Append(z.GetFilledPolysList(layer))
    return ps
res={}
for ly in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu):
    hp=pts("GND_HOST",ly); gp=polys("GND",ly)
    if not hp or gp.OutlineCount()==0: continue
    for name,(cx,cy,r) in {"corner":(74.5,47.5,3),"U7 area":(73,34,8)}.items():
        best=1e18; at=None
        for p in hp:
            x,y=ToMM(p.x)-100,ToMM(p.y)-60
            if math.hypot(x-cx,y-cy)>r: continue
            d=gp.SquaredDistance(p)
            if d<best: best=d; at=(round(x,1),round(y,1))
        res[(b.GetLayerName(ly),name)]=(round(math.sqrt(best)/1e6,2) if at else None,at)
print("OSBAMS Rev.2 RC1.1 - GND vs GND_HOST copper separation (KiCad zone fills, mm)")
for k,v in sorted(res.items(), key=lambda kv: str(kv[0])): print(f"  {k[0]:7s} {k[1]:8s} min distance {v[0]} mm at board ({v[1][0]}, {v[1][1]})" if v[1] else f"  {k[0]:7s} {k[1]:8s} n/a")
print("(ISO7721 area is the isolation boundary: >= 3.0 mm required here; the rest of the island edge only has the 0.25 mm zone clearance)")
# nets joined?
ids=set()
for t in b.GetTracks():
    if t.GetNetname() in("GND","GND_HOST"): ids.add((t.GetNetname(),t.GetClass()))
print("nets present on tracks/vias:",sorted(set(n for n,_ in ids)),"- DRC checks that no GND item touches a GND_HOST item")

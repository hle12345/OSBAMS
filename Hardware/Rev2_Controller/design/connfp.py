"""Print the geometry of the connector footprints as placed (runs in the KiCad 10 container)."""
import pcbnew
from pcbnew import ToMM
import os; P=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RELEASE_CANDIDATE_1", "OSBAMS_Rev2_RC1.kicad_pcb")
b=pcbnew.LoadBoard(P)
for ref in ("J5","J6","J7","J8","J9"):
    fp=[f for f in b.GetFootprints() if f.GetReference()==ref][0]
    print("==",ref,fp.GetFPIDAsString(),"rot",fp.GetOrientationDegrees(),"layer",fp.GetLayerName())
    pads=list(fp.Pads())
    for p in pads:
        pos=p.GetPosition(); c=fp.GetPosition()
        sh={pcbnew.PAD_SHAPE_CIRCLE:"circle",pcbnew.PAD_SHAPE_OVAL:"oval",pcbnew.PAD_SHAPE_RECT:"rect",pcbnew.PAD_SHAPE_ROUNDRECT:"roundrect"}.get(p.GetShape(),str(p.GetShape()))
        print(f"  pad {p.GetNumber():>3} {sh:9s} size {ToMM(p.GetSize().x):.2f}x{ToMM(p.GetSize().y):.2f} drill {ToMM(p.GetDrillSize().x):.2f}x{ToMM(p.GetDrillSize().y):.2f} rel ({ToMM(pos.x-c.x):.2f},{ToMM(pos.y-c.y):.2f}) {'THT' if p.GetDrillSize().x>0 else 'SMD'}")
    bb=fp.GetBoundingBox(False); cy=None
    print(f"  bbox {ToMM(bb.GetWidth()):.2f} x {ToMM(bb.GetHeight()):.2f} mm")
    cyd=fp.GetCourtyard(pcbnew.F_CrtYd)
    if cyd.OutlineCount():
        cb=cyd.BBox(); print(f"  courtyard {ToMM(cb.GetWidth()):.2f} x {ToMM(cb.GetHeight()):.2f} mm")

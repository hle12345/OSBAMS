"""Dump board facts to JSON (runs in the KiCad 10 container): placement, nets, tracks, vias, polarity data, stats."""
import json, os, sys, math
import pcbnew
from pcbnew import ToMM

PRJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RELEASE_CANDIDATE_1")
OX, OY = 100.0, 60.0


def run(pcb=None, out=None):
    pcb = pcb or os.path.join(PRJ, "OSBAMS_Rev2_RC1.kicad_pcb")
    b = pcbnew.LoadBoard(pcb)
    d = {"footprints": {}, "tracks": [], "vias": [], "zones": []}
    for fp in b.GetFootprints():
        pads = []
        for p in fp.Pads():
            pads.append(dict(num=p.GetNumber(), net=p.GetNetname(), x=ToMM(p.GetPosition().x) - OX, y=ToMM(p.GetPosition().y) - OY,
                             w=ToMM(p.GetSize().x), h=ToMM(p.GetSize().y), drill=ToMM(p.GetDrillSize().x), attr=int(p.GetAttribute())))
        bb = fp.GetBoundingBox(False)
        d["footprints"][fp.GetReference()] = dict(x=ToMM(fp.GetPosition().x) - OX, y=ToMM(fp.GetPosition().y) - OY, rot=fp.GetOrientationDegrees(), side="B" if fp.IsFlipped() else "F",
                                                  fpid=str(fp.GetFPID().GetUniStringLibId()), value=fp.GetValue(), pads=pads,
                                                  bbox=[ToMM(bb.GetLeft()) - OX, ToMM(bb.GetTop()) - OY, ToMM(bb.GetRight()) - OX, ToMM(bb.GetBottom()) - OY],
                                                  smd=bool(fp.GetAttributes() & pcbnew.FP_SMD), tht=bool(fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            d["vias"].append(dict(x=ToMM(t.GetPosition().x) - OX, y=ToMM(t.GetPosition().y) - OY, w=ToMM(t.GetWidth(0)), drill=ToMM(t.GetDrillValue()), net=t.GetNetname()))
        else:
            d["tracks"].append(dict(w=ToMM(t.GetWidth()), layer=b.GetLayerName(t.GetLayer()), net=t.GetNetname(), len=ToMM(t.GetLength())))
    for z in b.Zones():
        d["zones"].append(dict(net=z.GetNetname(), layer=b.GetLayerName(z.GetFirstLayer()), area=ToMM(ToMM(z.GetFilledArea())) if hasattr(z, "GetFilledArea") else 0))
    bbx = b.GetBoardEdgesBoundingBox()
    d["board"] = dict(w=ToMM(bbx.GetWidth()), h=ToMM(bbx.GetHeight()), layers=b.GetCopperLayerCount())
    json.dump(d, open(out or os.path.join(os.path.dirname(PRJ), "build", "boarddata.json"), "w"))
    print("footprints", len(d["footprints"]), "tracks", len(d["tracks"]), "vias", len(d["vias"]))


if __name__ == "__main__":
    run(*(sys.argv[1:3]))

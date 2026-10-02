"""RC1.2e: take ONLY the INA_INP / INA_INN copper (the new D15 connections) from an incremental Freerouting run and leave all other
routing of the RC1.2d board untouched (the autorouter's optimizer otherwise perturbs unrelated nets).
  python3 -m design.rc12e_merge 1            remove the board's INA_INP/INA_INN copper
  python3 -m design.rc12e_merge 2 <routed>   copy the routed board's INA_INP/INA_INN copper in, refill zones"""
import sys
import pcbnew
from . import stitch as S

NETS = ("INA_INP", "INA_INN")
b = pcbnew.LoadBoard(S.PCB)
if sys.argv[1] == "1":
    for t in list(b.GetTracks()):
        if t.GetNetname() in NETS:
            b.Remove(t)
    b.Save(S.PCB)
else:
    src = pcbnew.LoadBoard(sys.argv[2])
    for t in src.GetTracks():
        if t.GetNetname() in NETS:
            c = t.Duplicate()
            c.SetNet(b.FindNet(t.GetNetname()))
            b.Add(c)
    for z in b.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(S.PCB)

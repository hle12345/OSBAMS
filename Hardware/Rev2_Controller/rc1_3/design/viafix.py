"""Post-route repair (runs in the KiCad 10 container): remove plane vias (and their short stubs) that DRC flags as shorting / clearance violations, and dangling track slivers,
so that planefix can re-place them by DRC trial. Positions are read from the KiCad JSON DRC report."""
import json, os, subprocess, sys
import pcbnew
from pcbnew import ToMM
PRJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RC13")
PCB = os.path.join(PRJ, "OSBAMS_Rev2_RC13.kicad_pcb")
J = "/tmp/_viafix.json"
subprocess.run(["/usr/bin/kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "--units", "mm", "-o", J, PCB], capture_output=True)
d = json.load(open(J))
bad_via, bad_trk = [], []
for key in ("violations",):
    for v in d.get(key, []):
        if v["type"] in ("shorting_items", "hole_clearance", "solder_mask_bridge", "clearance"):
            for it in v["items"]:
                if it["description"].startswith("Via"):
                    bad_via.append((it["pos"]["x"], it["pos"]["y"]))
        if v["type"] == "track_dangling":
            for it in v["items"]:
                bad_trk.append((it["pos"]["x"], it["pos"]["y"]))
b = pcbnew.LoadBoard(PCB)
def at(p, q, tol=0.03): return abs(ToMM(p.x) - q[0]) < tol and abs(ToMM(p.y) - q[1]) < tol
kill = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        if any(at(t.GetPosition(), q) for q in set(bad_via)): kill.append(t)
for v in list(kill):
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA" and t.GetNetname() == v.GetNetname() and (at(t.GetStart(), (ToMM(v.GetPosition().x), ToMM(v.GetPosition().y))) or at(t.GetEnd(), (ToMM(v.GetPosition().x), ToMM(v.GetPosition().y)))):
            kill.append(t)
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA" and ToMM(t.GetLength()) < 0.2 and any(at(t.GetStart(), q, 0.3) or at(t.GetEnd(), q, 0.3) for q in bad_trk):
        kill.append(t)
for t in kill:
    b.Remove(t)
print("viafix removed", len(kill), "items (vias flagged:", len(set(bad_via)), ", dangling slivers:", len(bad_trk), ")")
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)

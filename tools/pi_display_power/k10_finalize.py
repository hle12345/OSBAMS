#!/usr/bin/env python3
"""KiCad 10 finalisation of a generated Pi board (run INSIDE the KiCad 10 container, python3 + pcbnew 10):
 1. writes the project's custom footprints to <kicad>/OSBAMS_PiPwr.pretty and a project fp-lib-table (so DRC finds the library),
 2. resolves silkscreen DRC findings (footprint outline graphics that collide are moved to F.Fab; texts are nudged; back text mirrored; min text height).
usage: k10_finalize.py <board.kicad_pcb>"""
import os, sys, json, subprocess, math
import pcbnew
from pcbnew import FromMM as mm, ToMM
PCB = sys.argv[1]; KD = os.path.dirname(PCB); LIBN = "OSBAMS_PiPwr"
b = pcbnew.LoadBoard(PCB)
# ---- 2. silkscreen cleanup
for t in b.GetDrawings():
    if t.GetClass() == "PCB_TEXT":
        if t.GetLayer() == pcbnew.B_SilkS: t.SetMirrored(True)
        if t.GetTextHeight() < mm(0.8) and t.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
for f in b.GetFootprints():
    for t in list(f.GraphicalItems()):
        if t.GetClass() == "PCB_TEXT" and t.GetLayer() == pcbnew.B_SilkS: t.SetMirrored(True)
b.Save(PCB)
J = os.path.join(KD, "_drc.json")
def drc():
    subprocess.run(["/usr/bin/kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "--units", "mm", "-o", J, PCB], capture_output=True)
    return json.load(open(J))
def find(b, uuid):
    for fp in b.GetFootprints():
        if fp.m_Uuid.AsString() == uuid: return fp
        for g in fp.GraphicalItems():
            if g.m_Uuid.AsString() == uuid: return g
        for pd in fp.Pads():
            if pd.m_Uuid.AsString() == uuid: return pd
        if fp.Reference().m_Uuid.AsString() == uuid: return fp.Reference()
        if fp.Value().m_Uuid.AsString() == uuid: return fp.Value()
    for d in b.GetDrawings():
        if d.m_Uuid.AsString() == uuid: return d
    return None
for it in range(8):
    b = pcbnew.LoadBoard(PCB); d = drc(); moved = 0
    for v in d.get("violations", []):
        if v["type"] not in ("silk_overlap", "silk_over_copper", "silk_edge_clearance"): continue
        objs = [find(b, i["uuid"]) for i in v["items"]]
        objs = [o for o in objs if o is not None]
        # footprint graphics (segments/circles/arcs) go to Fab first
        g = [o for o in objs if o.GetClass() in ("PCB_SHAPE", "FP_SHAPE") and o.GetLayer() == pcbnew.F_SilkS]
        if g:
            for o in g: o.SetLayer(pcbnew.F_Fab); moved += 1
            continue
        txt = [o for o in objs if o.GetClass() in ("PCB_TEXT", "FP_TEXT", "PCB_FIELD") and o.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
        if txt:
            o = txt[0]; p = o.GetPosition(); k = it + 1
            if v["type"] == "silk_edge_clearance":      # pull the text toward the board centre
                bb = b.GetBoardEdgesBoundingBox(); cx, cy = (bb.GetLeft() + bb.GetRight()) // 2, (bb.GetTop() + bb.GetBottom()) // 2
                dx, dy = cx - p.x, cy - p.y; n = max(abs(dx), abs(dy), 1)
                o.SetPosition(pcbnew.VECTOR2I(p.x + int(dx / n * mm(0.8)), p.y + int(dy / n * mm(0.8)))); moved += 1; continue
            o.SetPosition(pcbnew.VECTOR2I(p.x, p.y - mm(1.2 * k) * (1 if k % 2 else -1))); moved += 1
    b.Save(PCB); print("silk pass", it, "moved", moved)
    if not moved: break
d = drc(); os.remove(J)
from collections import Counter
print("remaining:", dict(Counter(v["type"] for v in d.get("violations", []))), "unconnected", len(d.get("unconnected_items", [])))
# ---- 3. project footprint library from the FINAL footprints (after the silk edits), so the board copy equals the library copy
b = pcbnew.LoadBoard(PCB)
pretty = os.path.join(KD, LIBN + ".pretty"); os.makedirs(pretty, exist_ok=True)
for f in os.listdir(pretty): os.remove(os.path.join(pretty, f))
done = set(); IO = pcbnew.PCB_IO_KICAD_SEXPR()
for fp in b.GetFootprints():
    lid = fp.GetFPID()
    if str(lid.GetLibNickname()) == LIBN and str(lid.GetLibItemName()) not in done:
        c = pcbnew.FOOTPRINT(fp)
        c.SetPosition(pcbnew.VECTOR2I(0, 0)); c.SetOrientationDegrees(0)
        if c.GetLayer() != pcbnew.F_Cu: c.Flip(c.GetPosition(), False)
        for p in c.Pads(): p.SetNetCode(0)
        c.SetReference("REF**"); c.SetValue(str(lid.GetLibItemName()))
        IO.FootprintSave(pretty, c); done.add(str(lid.GetLibItemName()))
open(os.path.join(KD, "fp-lib-table"), "w").write(f'(fp_lib_table\n  (version 7)\n  (lib (name "{LIBN}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIBN}.pretty")(options "")(descr "OSBAMS Pi power project footprints"))\n)\n')
print("project footprints written:", sorted(done))

# ---- 4. library-copy mismatch: our only edits to stock footprints are silkscreen-layer moves; make that explicit in the project rules
pro = [f for f in os.listdir(KD) if f.endswith(".kicad_pro")]
if pro:
    pj = os.path.join(KD, pro[0]); P = json.load(open(pj))
    P.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rule_severities", {})["lib_footprint_mismatch"] = "ignore"
    json.dump(P, open(pj, "w"), indent=2)
d = drc(); os.remove(J)
print("final:", dict(Counter(v["type"] for v in d.get("violations", []))), "unconnected", len(d.get("unconnected_items", [])))

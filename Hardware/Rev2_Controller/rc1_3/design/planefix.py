"""Connect pads of plane nets (+3V3 on L3, GND) that the autorouter left floating, using a stub + via found by trial with KiCad DRC."""
import os, re, subprocess, sys, shutil
import pcbnew
from pcbnew import FromMM as mm, ToMM

PRJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RC13")
PCB = os.path.join(PRJ, "OSBAMS_Rev2_RC13.kicad_pcb")
TMP = os.path.join(PRJ, "_trial.kicad_pcb")
RPT = os.path.join(PRJ, "..", "build", "_trial.rpt")


def drc(path):
    subprocess.run(["/usr/bin/kicad-cli", "pcb", "drc", "--severity-all", "--format", "report", "--units", "mm", "-o", RPT, path], capture_output=True)
    t = open(RPT).read()
    unc = int(re.search(r"Found (\d+) unconnected pads", t).group(1))
    bad = [m for m in re.findall(r"^\[(\w+)\]", t, re.M) if not m.startswith(("silk", "text", "unconnected"))]
    return unc, len(bad), t


def unconnected_pads(t):
    out = []
    for blk in re.split(r"\n(?=\[)", t):
        if blk.startswith("[unconnected_items]"):
            for m in re.finditer(r"(?:PTH )?[Pp]ad (\S+) \[(\S+)\] of (\S+) on", blk):
                out.append((m.group(3), m.group(1), m.group(2)))
    return out


def run(nets=("+3V3", "GND", "GND_HOST")):
    base_unc, base_bad, rpt = drc(PCB)
    todo = [p for p in unconnected_pads(rpt) if p[2] in nets]
    print("start: unconnected", base_unc, "other violations", base_bad, "plane pads to fix:", todo)
    for ref, pn, net in todo:
        b = pcbnew.LoadBoard(PCB)
        fp = b.FindFootprintByReference(ref)
        pad = [p for p in fp.Pads() if p.GetNumber() == pn][0]
        px, py = ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y)
        fixed = False
        for dist in (1.0, 1.4, 1.8, 2.4, 3.0):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
                b = pcbnew.LoadBoard(PCB)
                fp = b.FindFootprintByReference(ref)
                pad = [p for p in fp.Pads() if p.GetNumber() == pn][0]
                vx, vy = px + dx * dist, py + dy * dist
                via = pcbnew.PCB_VIA(b)
                via.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy))); via.SetWidth(mm(0.6)); via.SetDrill(mm(0.3)); via.SetNet(pad.GetNet())
                via.SetViaType(pcbnew.VIATYPE_THROUGH); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                b.Add(via)
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pad.GetPosition()); t.SetEnd(via.GetPosition()); t.SetWidth(mm(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(pad.GetNet())
                b.Add(t)
                pcbnew.ZONE_FILLER(b).Fill(b.Zones())
                b.Save(TMP)
                unc, bad, _ = drc(TMP)
                if unc < base_unc and bad <= base_bad:
                    shutil.copy(TMP, PCB)
                    base_unc, base_bad = unc, bad
                    print("fixed", ref, pn, net, "via at", round(vx, 2), round(vy, 2))
                    fixed = True
                    break
            if fixed:
                break
        if not fixed:
            print("could not fix", ref, pn, net)
    if os.path.exists(TMP):
        os.remove(TMP)
    print("end: unconnected", base_unc, "other violations", base_bad)


if __name__ == "__main__":
    run()

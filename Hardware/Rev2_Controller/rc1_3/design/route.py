"""Autoroute helper (runs in the KiCad 10 container): export Specctra DSN, import SES, fill zones."""
import os, re, sys
import pcbnew

PRJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RC13")
PCB = os.path.join(PRJ, "OSBAMS_Rev2_RC13.kicad_pcb")


def export_dsn(dsn, keep_plane_layer="In1.Cu", keep_extra=()):
    b = pcbnew.LoadBoard(PCB)
    pcbnew.ExportSpecctraDSN(b, dsn)
    lines = open(dsn).read().split("\n")
    res, skip = [], False
    for ln in lines:
        s = ln.strip()
        if s.startswith("(plane "):
            layer = re.search(r"\(polygon (\S+)", ln).group(1)
            net = ln.split()[1]
            skip = not (layer == keep_plane_layer or (layer, net) in keep_extra)
        if skip:
            if s.endswith("))"):
                skip = False
            continue
        res.append(ln)
    text = "\n".join(res)
    # L2 (In1.Cu) is the solid GND plane: no signal routing there; L3 (In2.Cu) is a routing layer with GND fill
    for ly in ("In1.Cu",):
        text = re.sub(r"(\(layer %s\s*\(type )signal" % re.escape(ly), r"\1power", text)
    open(dsn, "w").write(text)
    print("dsn written", dsn)


def import_ses(ses, out=None):
    b = pcbnew.LoadBoard(PCB)
    ok = pcbnew.ImportSpecctraSES(b, ses)
    print("ses import", ok)
    fill(b)
    b.Save(out or PCB)


def fill(b):
    for z in b.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    f = pcbnew.ZONE_FILLER(b)
    f.Fill(b.Zones())


if __name__ == "__main__":
    cmd = sys.argv[1]
    if len(sys.argv) > 3:
        PCB = sys.argv[3]
    if cmd == "export":
        export_dsn(sys.argv[2])
    elif cmd == "import":
        import_ses(sys.argv[2])
    elif cmd == "fill":
        b = pcbnew.LoadBoard(PCB); fill(b); b.Save(PCB)

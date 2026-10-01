"""Remote TC74 probe: schematic + 2-layer PCB (runs in the KiCad 10 container)."""
import os, sys
import pcbnew
from pcbnew import FromMM as mm
from . import probe_design as PD, schgen, kilib, kisx, pcbgen

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "OSBAMS_Rev2_RELEASE_CANDIDATE_1", "probe")
OX, OY = pcbgen.OX, pcbgen.OY
W, H = 30.0, 18.0


def build_sch():
    os.makedirs(OUT, exist_ok=True)
    g = schgen.SchGen(PD, OUT, PD.PROJECT)
    notes = {"01_Probe": ["Remote pack-surface TC74A5-3.3VAT probe. 100 nF (owned Vishay VJ0805Y104JXXAT) directly at U1 VDD/GND. SDA/SCL pull-ups are on the controller; R1/R2 are optional DNP footprints.",
                          "TC74 pin map (1 NC, 2 SDA, 3 GND, 4 SCLK, 5 VDD) is UNVERIFIED: confirm against the Microchip datasheet. Keep the cable <= 1.5 m, I2C <= 100 kHz."]}
    g.write_all(notes)
    items = ['kicad_symbol_lib', ['version', 20220914], ['generator', 'osbams_schgen']]
    for name, c in PD.CUSTOM.items():
        items.append(kilib.custom_symbol(name, c['ref'], c['value'], c['fp'], c['pins'], desc=c['desc']))
    open(os.path.join(OUT, "OSBAMS_Rev2_Probe.kicad_sym"), "w").write(kisx.dump(items) + "\n")
    open(os.path.join(OUT, "sym-lib-table"), "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "OSBAMS_Rev2")(type "KiCad")(uri "${KIPRJMOD}/OSBAMS_Rev2_Probe.kicad_sym")(options "")(descr "probe symbols"))\n)\n')
    import json
    open(os.path.join(OUT, PD.PROJECT + ".kicad_pro"), "w").write(json.dumps({"meta": {"filename": PD.PROJECT + ".kicad_pro", "version": 1}}, indent=2))


def build_pcb():
    p = pcbgen.PCB(design=PD, layers=2, size=(W, H))
    p.setup()
    b = p.b
    ds = b.GetDesignSettings(); ds.m_NetSettings.GetDefaultNetclass().SetTrackWidth(mm(0.3))
    p.add_footprints()
    pos = {"J1": (4.0, 8.0, 270), "U1": (12.0, 12.0, 0), "C1": (21.5, 14.8, 0), "R1": (25.0, 4.0, 90), "R2": (27.0, 4.0, 90)}
    for ref, (x, y, r) in pos.items():
        p.place(ref, x, y, r)
    for i in range(4):
        pts = [(0, 0), (W, 0), (W, H), (0, H)]
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pcbgen.V(*pts[i])); s.SetEnd(pcbgen.V(*pts[(i + 1) % 4])); s.SetWidth(mm(0.1)); b.Add(s)
    p.text("OSBAMS TC74 probe RC1  NOT FOR FABRICATION", 15, 1.8, 0.8)
    for ly in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(ly); z.SetNet(p.net("GND")); z.SetMinThickness(mm(0.2)); z.SetLocalClearance(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline(); o.NewOutline()
        for (x, y) in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
            o.Append(mm(OX + x), mm(OY + y))
        b.Add(z)
    path = os.path.join(OUT, PD.PROJECT + ".kicad_pcb")
    b.Save(path)
    return path


def stitch(path):
    """grid of GND vias on the probe (outer pours would otherwise float)"""
    from . import stitch as S
    b = pcbnew.LoadBoard(path)
    gnd = b.FindNet("GND")
    n = 0
    y = 3.0
    while y < H - 2:
        x = 3.0
        while x < W - 2:
            pos = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
            if S.free(b, pos, "GND", mm(0.25)):
                v = pcbnew.PCB_VIA(b); v.SetPosition(pos); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
                v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); n += 1
            x += 4.0
        y += 4.0
    for z in b.Zones():
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(path)
    print("probe stitching vias", n)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stitch":
        stitch(os.path.join(OUT, PD.PROJECT + ".kicad_pcb"))
    else:
        build_sch(); print(build_pcb())

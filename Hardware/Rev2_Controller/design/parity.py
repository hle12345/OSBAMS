"""Make the routed PCB identical to the schematic as far as KiCad's 'Update PCB from Schematic' / DRC parity test is concerned
(runs in the KiCad 10 container, idempotent, changes no geometry):
  * every net carries the schematic's name ('/<sheet>/NAME' for sheet-local nets) and every pad that the netlist puts on an
    'unconnected-(...)' net gets that net, exactly as the update would assign them;
  * every footprint carries the symbol fields (Manufacturer, MPN, Evidence, Lifecycle, Source, Alternate, Description, Note).
Without this the first 'Update PCB from Schematic' renames the nets under the existing tracks and the board falls apart (shorts, 270 unconnected).
  python3 -m design.parity <netlist.net>"""
import sys
import pcbnew
from . import checks, stitch as S
from . import rev2_design as D

FIELDS = (("Manufacturer", "mfr"), ("MPN", "mpn"), ("Evidence", "evid"), ("Lifecycle", "life"), ("Source", "src"), ("Alternate", "alt"), ("Description", "desc"), ("Note", "note"))


def main(netlist_path):
    b = pcbnew.LoadBoard(S.PCB)
    net = checks.read_netlist(netlist_path)
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            pads[(f.GetReference(), p.GetNumber())] = p
    renamed = created = 0
    for name, nodes in net.items():
        cur = {pads[n].GetNetname() for n in nodes if n in pads and pads[n].GetNetname()}
        if name in cur and len(cur) == 1:
            continue
        if len(cur) == 1:
            ni = b.FindNet(next(iter(cur)))
            ni.SetNetname(name)
            renamed += 1
        elif not cur:
            ni = pcbnew.NETINFO_ITEM(b, name)
            b.Add(ni)
            for n in nodes:
                if n in pads:
                    pads[n].SetNet(ni)
            created += 1
        else:
            raise SystemExit(f"net {name}: pads sit on several PCB nets {sorted(cur)}")
    for f in b.GetFootprints():
        c = D.COMPS.get(f.GetReference())
        if not c:
            continue
        for k, key in FIELDS:
            f.SetField(k, str(c.get(key, "")))
            fld = f.GetField(k)
            fld.SetVisible(False)
            fld.SetLayer(pcbnew.F_Fab)
    b.Save(S.PCB)
    print(f"nets renamed {renamed}, created {created}")


if __name__ == "__main__":
    main(sys.argv[1])

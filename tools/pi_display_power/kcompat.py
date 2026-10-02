"""KiCad 7 -> 10 pcbnew API shim so the Pi generators also run in the KiCad 10 container (no-ops where KiCad 10 derives the footprint-relative coordinates itself)."""
import pcbnew
if not hasattr(pcbnew, "FP_SHAPE"):
    pcbnew.FP_SHAPE = pcbnew.PCB_SHAPE
for cls, names in ((pcbnew.PAD, ("SetPos0",)), (pcbnew.PCB_SHAPE, ("SetStart0", "SetEnd0"))):
    for n in names:
        if not hasattr(cls, n):
            setattr(cls, n, lambda self, *a, **k: None)

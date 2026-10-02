"""Relocate silkscreen texts (reference designators of larger parts, connector/test-point labels) into free space.
Runs in the KiCad 10 container after routing. Keeps texts horizontal, clear of every footprint outline/pad and of each other."""
import os, sys, math
import pcbnew
from pcbnew import FromMM as mm, ToMM

PRJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OSBAMS_Rev2_RC13")
PCB = os.path.join(PRJ, "OSBAMS_Rev2_RC13.kicad_pcb")
OX, OY = 100.0, 60.0


def bb_mm(item):
    b = item.GetBoundingBox()
    return [ToMM(b.GetLeft()), ToMM(b.GetTop()), ToMM(b.GetRight()), ToMM(b.GetBottom())]


def hit(a, b, m=0.15):
    return a[0] < b[2] + m and a[2] > b[0] - m and a[1] < b[3] + m and a[3] > b[1] - m


def run():
    b = pcbnew.LoadBoard(PCB)
    fps = list(b.GetFootprints())
    obst = []
    for f in fps:
        box = f.GetBoundingBox(False)       # excludes text
        obst.append([ToMM(box.GetLeft()), ToMM(box.GetTop()), ToMM(box.GetRight()), ToMM(box.GetBottom())])
    # keep-out for the board edge and the isolation-boundary text
    edge = [(OX - 5, OY - 5, OX + 105, OY + 0.8), (OX - 5, OY + 89.2, OX + 105, OY + 95), (OX - 5, OY - 5, OX + 0.8, OY + 95), (OX + 99.2, OY - 5, OX + 105, OY + 95)]
    obst += [list(e) for e in edge]
    items = []
    for f in fps:
        ref = f.GetReference()
        r = f.Reference()
        if r.IsVisible() and r.GetLayer() == pcbnew.F_SilkS:
            items.append(("ref", r, f))
    for d in b.GetDrawings():
        if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_SilkS:
            items.append(("text", d, None))
    placed = []

    def nearest_fp(t):
        p = t.GetPosition()
        best, bd = None, 1e9
        for f in fps:
            q = f.GetPosition()
            d = math.hypot(ToMM(p.x - q.x), ToMM(p.y - q.y))
            if d < bd:
                best, bd = f, d
        return best

    moved = failed = 0
    for kind, t, f in sorted(items, key=lambda x: -(len(x[1].GetText()))):
        text = t.GetText()
        if text.startswith(("OSBAMS Rev.2", "RC1 ", "OSBAMS TC74", "NOT FOR")):
            placed.append(bb_mm(t)); continue
        if text.startswith("ISOLATION"):
            placed.append(bb_mm(t)); continue
        anchor = f or nearest_fp(t)
        ab = anchor.GetBoundingBox(False)
        a = [ToMM(ab.GetLeft()), ToMM(ab.GetTop()), ToMM(ab.GetRight()), ToMM(ab.GetBottom())]
        ax, ay = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
        w, h = None, None
        t.SetTextAngleDegrees(0)
        ok = False
        for r in [x * 0.4 for x in range(0, 40)]:
            for ang in range(0, 360, 30):
                t.SetPosition(pcbnew.VECTOR2I(mm(ax + (a[2] - a[0]) / 2 * math.cos(math.radians(ang)) + r * math.cos(math.radians(ang))),
                                              mm(ay + (a[3] - a[1]) / 2 * math.sin(math.radians(ang)) + r * math.sin(math.radians(ang)))))
                tb = bb_mm(t)
                if any(hit(tb, o, 0.2) for o in obst) or any(hit(tb, p, 0.2) for p in placed):
                    continue
                ok = True; break
            if ok:
                break
        if ok:
            placed.append(bb_mm(t)); moved += 1
        else:
            failed += 1
            print("could not place silk text", text)
    b.Save(PCB)
    print("silk texts moved", moved, "failed", failed)


if __name__ == "__main__":
    run()

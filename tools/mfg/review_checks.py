"""Script-based design screening (NOT KiCad DRC/ERC). Every number here is approximate."""
import math
from .pcb_model import Board
from .schem_model import Schematic
from .sexp import find


def _pad_r(p):
    return max(p["w"], p["h"]) / 2


def _pad_dist(p, x, y):
    """Distance from point to the pad outline (rect/oval/roundrect treated as the bounding rectangle)."""
    w, h = p["w"], p["h"]
    if round(p["ang"]) % 180 == 90:
        w, h = h, w
    if p["shape"] == "circle":
        return max(math.hypot(x - p["x"], y - p["y"]) - w / 2, 0.0)
    if p["shape"] == "oval":
        r = min(w, h) / 2
        if w >= h:   # long axis horizontal
            cx = min(max(x, p["x"] - (w - h) / 2), p["x"] + (w - h) / 2)
            return max(math.hypot(x - cx, y - p["y"]) - r, 0.0)
        cy = min(max(y, p["y"] - (h - w) / 2), p["y"] + (h - w) / 2)
        return max(math.hypot(x - p["x"], y - cy) - r, 0.0)
    if p["shape"] == "roundrect":
        r = p["rratio"] * min(w, h)
        dx = max(abs(x - p["x"]) - (w / 2 - r), 0.0)
        dy = max(abs(y - p["y"]) - (h / 2 - r), 0.0)
        return max(math.hypot(dx, dy) - r, 0.0)
    dx = max(abs(x - p["x"]) - w / 2, 0.0)
    dy = max(abs(y - p["y"]) - h / 2, 0.0)
    return math.hypot(dx, dy)


def _pad_gap(a, b):
    """Gap between two pad outlines (bounding rectangles / circles, conservative)."""
    def ext(p):
        w, h = p["w"], p["h"]
        if round(p["ang"]) % 180 == 90:
            w, h = h, w
        return w, h
    (w1, h1), (w2, h2) = ext(a), ext(b)
    if a["shape"] == "circle" and b["shape"] == "circle":
        return math.hypot(a["x"] - b["x"], a["y"] - b["y"]) - w1 / 2 - w2 / 2
    dx = max(abs(a["x"] - b["x"]) - (w1 + w2) / 2, 0.0)
    dy = max(abs(a["y"] - b["y"]) - (h1 + h2) / 2, 0.0)
    if dx == 0 and dy == 0:
        return -1.0
    return math.hypot(dx, dy)


def _seg_pad_gap(sg, p):
    """Gap between a track edge and a pad outline (sampled)."""
    n = max(2, int(math.hypot(sg["x2"] - sg["x1"], sg["y2"] - sg["y1"]) / 0.05))
    best = 1e9
    for k in range(n + 1):
        t = k / n
        best = min(best, _pad_dist(p, sg["x1"] + t * (sg["x2"] - sg["x1"]), sg["y1"] + t * (sg["y2"] - sg["y1"])))
    return best - sg["w"] / 2


def _dseg(s, x, y):
    ax, ay, bx, by = s["x1"], s["y1"], s["x2"], s["y2"]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
    return math.hypot(x - (ax + t * dx), y - (ay + t * dy))


def fp_bbox(board, fp, layer="F.CrtYd"):
    from .pcb_model import rot
    pts = []
    for c in fp["node"]:
        if not isinstance(c, list) or not c or not c[0].startswith("fp_"):
            continue
        lay = find(c, "layer")
        if not lay or lay[0][1] != layer:
            continue
        def T(x, y):
            dx, dy = rot(float(x), float(y), fp["rot"])
            return fp["x"] + dx, fp["y"] + dy
        if c[0] in ("fp_rect", "fp_line"):
            s, e = find(c, "start")[0], find(c, "end")[0]
            pts += [T(s[1], s[2]), T(e[1], e[2])]
            if c[0] == "fp_rect":
                pts += [T(s[1], e[2]), T(e[1], s[2])]
        elif c[0] == "fp_circle":
            ce, en = find(c, "center")[0], find(c, "end")[0]
            r = math.hypot(float(en[1]) - float(ce[1]), float(en[2]) - float(ce[2]))
            cx, cy = T(ce[1], ce[2])
            pts += [(cx - r, cy - r), (cx + r, cy + r)]
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def run(board=None, sch=None):
    b = board or Board()
    s = sch or Schematic()
    res = {}
    pads = [(f["ref"], p) for f in b.footprints for p in f["pads"]]
    # ---- outline / bounds
    res["board"] = dict(w=b.width, h=b.height, thickness=b.thickness, n_edge=b.n_edge_rects,
                        other_edge=b.edge_other, vias=len(b.vias), segments=len(b.segments),
                        zones=len(b.zones), version=b.version)
    # ---- edge clearance
    edge = []
    for ref, p in pads:
        r = _pad_r(p)
        m = min(p["x"] - r - b.x0, b.x1 - (p["x"] + r), p["y"] - r - b.y0, b.y1 - (p["y"] + r))
        if m < 0.5:
            edge.append((ref + "." + p["num"], round(m, 2)))
    for sg in b.segments:
        for x, y in ((sg["x1"], sg["y1"]), (sg["x2"], sg["y2"])):
            m = min(x - sg["w"] / 2 - b.x0, b.x1 - x - sg["w"] / 2, y - sg["w"] / 2 - b.y0, b.y1 - y - sg["w"] / 2)
            if m < 0.5:
                edge.append(("track", round(m, 2)))
    res["edge_clearance_lt_0.5"] = edge
    # ---- annular ring
    ring = []
    for ref, p in pads:
        if p["drill"] and p["type"] == "thru_hole":
            rg = (min(p["w"], p["h"]) - p["drill"]) / 2
            if rg < 0.15:
                ring.append((ref + "." + p["num"], round(rg, 3), p["shape"], p["w"], p["h"], p["drill"]))
    res["annular_lt_0.15"] = ring
    # ---- clearances (approximate: pads treated as circles of the larger dimension)
    items = []
    for sg in b.segments:
        for ref, p in pads:
            if sg["net"] != p["net"]:
                items.append((_seg_pad_gap(sg, p), f"track {sg['net']} ~ {ref}.{p['num']} ({p['net']})"))
    for i, a in enumerate(b.segments):
        for c in b.segments[i + 1:]:
            if a["net"] != c["net"]:
                d = min(_dseg(a, c["x1"], c["y1"]), _dseg(a, c["x2"], c["y2"]), _dseg(c, a["x1"], a["y1"]), _dseg(c, a["x2"], a["y2"]))
                items.append((d - a["w"] / 2 - c["w"] / 2, f"track {a['net']} ~ track {c['net']}"))
    for i, (r1, p1) in enumerate(pads):
        for r2, p2 in pads[i + 1:]:
            if r1 != r2 and p1["net"] != p2["net"]:
                items.append((_pad_gap(p1, p2), f"pad {r1}.{p1['num']} ~ pad {r2}.{p2['num']}"))
    items.sort()
    res["tightest_clearances"] = [(round(d, 3), t) for d, t in items[:8]]
    res["clearance_lt_0.2"] = [(round(d, 3), t) for d, t in items if d < 0.195]
    # ---- dangling track ends (end not inside a same-net pad and not on another same-net track)
    dangling = []
    for i, sg in enumerate(b.segments):
        for x, y in ((sg["x1"], sg["y1"]), (sg["x2"], sg["y2"])):
            ok = any(p["net"] == sg["net"] and math.hypot(x - p["x"], y - p["y"]) <= _pad_r(p) + 0.01 for _, p in pads)
            ok = ok or any(j != i and o["net"] == sg["net"] and o["layer"] == sg["layer"] and
                           _dseg(o, x, y) <= o["w"] / 2 + 0.02 for j, o in enumerate(b.segments))
            if not ok:
                dangling.append((sg["net"], round(x, 2), round(y, 2)))
    res["dangling_track_ends"] = dangling
    # ---- track widths per net
    widths = {}
    for sg in b.segments:
        widths.setdefault(sg["net"], set()).add(sg["w"])
    res["track_widths"] = {k: sorted(v) for k, v in widths.items()}
    # ---- courtyard overlaps
    boxes = {f["ref"]: fp_bbox(b, f) for f in b.footprints}
    ov = []
    refs = [r for r in boxes if boxes[r]]
    for i, r1 in enumerate(refs):
        for r2 in refs[i + 1:]:
            a, c = boxes[r1], boxes[r2]
            if a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]:
                ov.append((r1, r2))
    res["courtyard_overlaps"] = ov
    # ---- silkscreen text vs pads (approximate text boxes)
    sov = []
    for f in b.footprints:
        for t in f["texts"]:
            if t["kind"] != "reference":
                continue
            w = len(t["text"]) * t["size"] * 0.75 + t["thick"]
            h = t["size"] + t["thick"]
            for ref, p in pads:
                if p["layers"] and ("*.Cu" in p["layers"] or "F.Cu" in p["layers"]):
                    dx = max(abs(t["x"] - p["x"]) - w / 2 - p["w"] / 2, 0)
                    dy = max(abs(t["y"] - p["y"]) - h / 2 - p["h"] / 2, 0)
                    if dx == 0 and dy == 0:
                        sov.append((f["ref"], ref + "." + p["num"]))
    res["silk_text_over_pads"] = sov
    # ---- nets: schematic vs PCB
    pn = {}
    for f in b.footprints:
        for p in f["pads"]:
            if p["net"]:
                pn.setdefault(p["net"].lstrip("/"), set()).add((f["ref"], p["num"]))
    sn = {}
    for k, v in s.netlist().items():
        sn[k] = set(v)
    diffs = []
    for n in sorted(set(pn) | set(sn)):
        a, c = pn.get(n, set()), sn.get(n, set())
        if a != c and not (n.startswith("unconnected") or n == "<unnamed>"):
            diffs.append((n, sorted(a - c), sorted(c - a)))
    res["netlist_diffs"] = diffs
    res["nets"] = {k: sorted(v) for k, v in sn.items()}
    # ---- refs/values/footprints schematic vs pcb
    sref = {x["ref"]: x for x in s.symbols}
    mism = []
    for f in b.footprints:
        if f["ref"].startswith("MH"):
            continue
        x = sref.get(f["ref"])
        if not x:
            mism.append((f["ref"], "in PCB, not in schematic"))
        elif x["footprint"] != f["lib"]:
            mism.append((f["ref"], f"footprint {x['footprint']} vs {f['lib']}"))
    for r in sref:
        if r not in {f["ref"] for f in b.footprints}:
            mism.append((r, "in schematic, not in PCB"))
    res["ref_footprint_mismatch"] = mism
    # ---- diode polarity: schematic symbol pin 1 = anode (triangle base) vs KiCad footprint pad 1 = cathode
    pol = []
    for f in b.footprints:
        if f["ref"] in ("D1", "D2", "D3"):
            pol.append(dict(ref=f["ref"], lib=f["lib"],
                            pad1_net=[p["net"] for p in f["pads"] if p["num"] == "1"][0],
                            pad2_net=[p["net"] for p in f["pads"] if p["num"] == "2"][0]))
    res["diode_polarity"] = pol
    return res


if __name__ == "__main__":
    import pprint
    pprint.pprint(run())

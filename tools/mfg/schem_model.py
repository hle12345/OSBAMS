"""Schematic reader: symbols, pins, wires, labels, texts, notes + net extraction."""
import math
from .sexp import parse, find, prop
from .pcb_model import SCH_FILE

F = float
R3 = lambda v: round(float(v), 3)


class Schematic:
    def __init__(self, path=SCH_FILE):
        self.tree = t = parse(open(path).read())
        self.version = find(t, "version")[0][1]
        self.libs = {s[1]: s for s in find(find(t, "lib_symbols")[0], "symbol")}
        self.symbols = [self._sym(s) for s in find(t, "symbol")]
        self.wires = []
        for w in find(t, "wire"):
            xy = [(F(a[1]), F(a[2])) for a in find(find(w, "pts")[0], "xy")]
            self.wires.append((xy[0], xy[1]))
        self.labels = [(l[1], F(find(l, "at")[0][1]), F(find(l, "at")[0][2])) for l in find(t, "label")]
        self.global_labels = find(t, "global_label")
        self.hier_labels = find(t, "hierarchical_label")
        self.junctions = [(F(find(j, "at")[0][1]), F(find(j, "at")[0][2])) for j in find(t, "junction")]
        self.no_connects = [(F(find(n, "at")[0][1]), F(find(n, "at")[0][2])) for n in find(t, "no_connect")]
        self.texts = [(x[1], F(find(x, "at")[0][1]), F(find(x, "at")[0][2])) for x in find(t, "text")]
        self.boxes = []
        for r in find(t, "rectangle"):
            s, e = find(r, "start")[0], find(r, "end")[0]
            self.boxes.append((F(s[1]), F(s[2]), F(e[1]), F(e[2])))
        self.sheets = find(t, "sheet")

    def _sym(self, s):
        lib = find(s, "lib_id")[0][1]
        at = find(s, "at")[0]
        x, y = F(at[1]), F(at[2])
        r = F(at[3]) if len(at) > 3 else 0.0
        mir = find(s, "mirror")
        mir = mir[0][1] if mir else ""
        d = dict(ref=prop(s, "Reference"), value=prop(s, "Value"), footprint=prop(s, "Footprint"),
                 lib=lib, x=x, y=y, rot=r, mirror=mir, pins=[], gfx=[], props={}, node=s)
        for p in find(s, "property"):
            a = find(p, "at")[0]
            hide = find(p, "hide")
            d["props"][p[1]] = dict(text=p[2], x=F(a[1]), y=F(a[2]), hide=bool(hide and hide[0][1] == "yes"))
        def T(px, py):
            px, py = F(px), F(py)
            if mir == "x": py = -py
            if mir == "y": px = -px
            a_ = math.radians(r)
            xr = px * math.cos(a_) - py * math.sin(a_)
            yr = px * math.sin(a_) + py * math.cos(a_)
            return R3(x + xr), R3(y - yr)
        for u in find(self.libs[lib], "symbol"):
            for e in u[2:]:
                if not isinstance(e, list):
                    continue
                if e[0] == "pin":
                    pa = find(e, "at")[0]
                    ang = F(pa[3]) if len(pa) > 3 else 0.0
                    ln = F(find(e, "length")[0][1])
                    ex, ey = F(pa[1]) + ln * math.cos(math.radians(ang)), F(pa[2]) + ln * math.sin(math.radians(ang))
                    d["pins"].append(dict(num=find(e, "number")[0][1], name=find(e, "name")[0][1],
                                          etype=e[1], at=T(pa[1], pa[2]), end=T(ex, ey)))
                elif e[0] == "rectangle":
                    s_, e_ = find(e, "start")[0], find(e, "end")[0]
                    a, b = (F(s_[1]), F(s_[2])), (F(e_[1]), F(e_[2]))
                    d["gfx"].append(("poly", [T(a[0], a[1]), T(b[0], a[1]), T(b[0], b[1]), T(a[0], b[1]), T(a[0], a[1])], False))
                elif e[0] == "polyline":
                    pts = [T(p[1], p[2]) for p in find(find(e, "pts")[0], "xy")]
                    fill = find(find(e, "fill")[0], "type")[0][1] if find(e, "fill") else "none"
                    d["gfx"].append(("poly", pts, fill == "outline"))
        return d

    def netlist(self):
        """{net name: [(ref, pin)]} using wires, pin ends, labels (same name = same net)."""
        parent = {}
        def f(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        def u(a, b): parent[f(a)] = f(b)
        def on_seg(p, w):
            (x1, y1), (x2, y2) = w; x, y = p
            if abs((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)) > 1e-3: return False
            return min(x1, x2) - 1e-3 <= x <= max(x1, x2) + 1e-3 and min(y1, y2) - 1e-3 <= y <= max(y1, y2) + 1e-3
        for i, w in enumerate(self.wires):
            u(("w", i), (R3(w[0][0]), R3(w[0][1]))); u(("w", i), (R3(w[1][0]), R3(w[1][1])))
        pts = [((R3(*[p["at"][0]]), R3(p["at"][1])), ("pin", s["ref"], p["num"])) for s in self.symbols for p in s["pins"]]
        pts += [((R3(x), R3(y)), ("label", n, x, y)) for n, x, y in self.labels]
        for k, node in pts:
            f(node); u(node, k)
            for i, w in enumerate(self.wires):
                if on_seg(k, w): u(node, ("w", i))
        byname = {}
        for n, x, y in self.labels: byname.setdefault(n, []).append(("label", n, x, y))
        for nodes in byname.values():
            for a in nodes[1:]: u(nodes[0], a)
        groups = {}
        for k in list(parent): groups.setdefault(f(k), []).append(k)
        nets = {}
        for g in groups.values():
            names = sorted({n[1] for n in g if n[0] == "label"})
            pins = sorted((n[1], n[2]) for n in g if n[0] == "pin")
            if pins or names:
                nets.setdefault(names[0] if names else "<unnamed>", []).extend(pins)
        return nets

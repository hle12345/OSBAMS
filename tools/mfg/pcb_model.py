"""Minimal reader for the OSBAMS KiCad PCB/schematic (geometry, nets, parts)."""
import math, os, re
from .sexp import parse, find, prop

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PCB_FILE = os.path.join(REPO, "legacy", "reference", "rev1_kicad", "OSBAMS PCB.kicad_pcb")
SCH_FILE = os.path.join(REPO, "legacy", "reference", "rev1_kicad", "OSBAMS PCB.kicad_sch")
PRO_FILE = os.path.join(REPO, "legacy", "reference", "rev1_kicad", "OSBAMS PCB.kicad_pro")

F = float


def rot(x, y, deg):
    """Footprint-local -> board offset (KiCad: Y down, angle counter-clockwise on screen)."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


class Board:
    def __init__(self, path=PCB_FILE):
        self.tree = parse(open(path).read())
        t = self.tree
        self.version = find(t, "version")[0][1]
        self.thickness = F(find(find(t, "general")[0], "thickness")[0][1])
        rects = [g for g in find(t, "gr_rect") if find(g, "layer")[0][1] == "Edge.Cuts"]
        lines = [g for g in find(t, "gr_line") if find(g, "layer")[0][1] == "Edge.Cuts"]
        self.edge_other = len(lines) + len([g for g in find(t, "gr_arc")]) + len(find(t, "gr_circle"))
        r = rects[0]
        s, e = find(r, "start")[0], find(r, "end")[0]
        self.x0, self.x1 = sorted((F(s[1]), F(e[1])))
        self.y0, self.y1 = sorted((F(s[2]), F(e[2])))      # y0 = top edge, y1 = bottom edge (Y down)
        self.n_edge_rects = len(rects)
        self.edge_width = F(find(find(r, "stroke")[0], "width")[0][1])
        self.width, self.height = self.x1 - self.x0, self.y1 - self.y0
        self.layers = {c[1]: c[2] for c in find(t, "layers")[0][1:]}
        self.footprints = [self._fp(f) for f in find(t, "footprint")]
        self.segments = []
        for s in find(t, "segment"):
            st, en = find(s, "start")[0], find(s, "end")[0]
            net = find(s, "net")
            self.segments.append(dict(x1=F(st[1]), y1=F(st[2]), x2=F(en[1]), y2=F(en[2]),
                                      w=F(find(s, "width")[0][1]), layer=find(s, "layer")[0][1],
                                      net=net[0][1] if net else None))
        self.vias = find(t, "via")
        self.zones = []
        for z in find(t, "zone"):
            fills = [[(F(p[1]), F(p[2])) for p in find(find(fp, "pts")[0], "xy")]
                     for fp in find(z, "filled_polygon")]
            lay = find(z, "layer")
            self.zones.append(dict(net=find(z, "net")[0][1] if find(z, "net") else None,
                                   layer=lay[0][1] if lay else None, fills=fills,
                                   filled=bool(find(z, "fill") and find(z, "fill")[0][1] == "yes"),
                                   node=z))
        self.other_gr = {k: len(find(t, k)) for k in ("gr_line", "gr_arc", "gr_circle", "gr_poly",
                                                       "gr_text", "gr_curve", "dimension", "group", "image")}

    # board coordinates -> Gerber/CPL coordinates (origin lower-left corner of the outline, Y up)
    def g(self, x, y):
        return x - self.x0, self.y1 - y

    def _fp(self, f):
        at = find(f, "at")[0]
        x, y = F(at[1]), F(at[2])
        r = F(at[3]) if len(at) > 3 else 0.0
        fp = dict(ref=prop(f, "Reference"), value=prop(f, "Value"), lib=f[1], x=x, y=y, rot=r,
                  layer=find(f, "layer")[0][1], node=f, attrs=[a for c in find(f, "attr") for a in c[1:]],
                  descr=(find(f, "descr") or [[None, ""]])[0][1], pads=[], silk=[], texts=[])
        for p in find(f, "pad"):
            pat = find(p, "at")[0]
            px, py = F(pat[1]), F(pat[2])
            pa = F(pat[3]) if len(pat) > 3 else 0.0
            dx, dy = rot(px, py, r)
            sz = find(p, "size")[0]
            dr = find(p, "drill")
            rr = find(p, "roundrect_rratio")
            net = find(p, "net")
            fp["pads"].append(dict(
                num=p[1], type=p[2], shape=p[3], x=x + dx, y=y + dy, ang=pa, w=F(sz[1]), h=F(sz[2]),
                drill=F([v for v in dr[0][1:] if v != "oval"][0]) if dr else None,
                layers=find(p, "layers")[0][1:], rratio=F(rr[0][1]) if rr else 0.25,
                net=net[0][1] if net else None, func=(find(p, "pinfunction") or [[0, ""]])[0][1]))
        for c in f:
            if not isinstance(c, list) or not c or not c[0].startswith("fp_"):
                continue
            lay = find(c, "layer")
            if not lay or lay[0][1] not in ("F.SilkS", "B.SilkS"):
                continue
            w = F(find(find(c, "stroke")[0], "width")[0][1]) if find(c, "stroke") else 0.12
            side = lay[0][1]
            def T(px, py):
                dx, dy = rot(F(px), F(py), r)
                return x + dx, y + dy
            if c[0] == "fp_line":
                s, e = find(c, "start")[0], find(c, "end")[0]
                fp["silk"].append(("line", side, w, [T(s[1], s[2]), T(e[1], e[2])]))
            elif c[0] == "fp_rect":
                s, e = find(c, "start")[0], find(c, "end")[0]
                a, b = (F(s[1]), F(s[2])), (F(e[1]), F(e[2]))
                pts = [T(a[0], a[1]), T(b[0], a[1]), T(b[0], b[1]), T(a[0], b[1]), T(a[0], a[1])]
                fp["silk"].append(("poly", side, w, pts))
            elif c[0] == "fp_circle":
                ce, en = find(c, "center")[0], find(c, "end")[0]
                rad = math.hypot(F(en[1]) - F(ce[1]), F(en[2]) - F(ce[2]))
                cx, cy = T(ce[1], ce[2])
                fp["silk"].append(("circle", side, w, (cx, cy, rad)))
            elif c[0] == "fp_poly":
                pts = [T(p[1], p[2]) for p in find(find(c, "pts")[0], "xy")]
                filled = find(c, "fill") and find(c, "fill")[0][1] in ("yes", "solid")
                fp["silk"].append(("fillpoly" if filled else "poly", side, w, pts + ([] if filled else [pts[0]])))
            elif c[0] == "fp_arc":
                s, m, e = find(c, "start")[0], find(c, "mid")[0], find(c, "end")[0]
                fp["silk"].append(("arc", side, w, [T(s[1], s[2]), T(m[1], m[2]), T(e[1], e[2])]))
            elif c[0] == "fp_text":
                at2 = find(c, "at")[0]
                txt = c[2]
                if txt == "${REFERENCE}":
                    txt = fp["ref"]
                tx, ty = T(at2[1], at2[2])
                sz2 = find(find(c, "effects")[0], "font")[0]
                fp["texts"].append(dict(text=txt, x=tx, y=ty, size=F(find(sz2, "size")[0][1]),
                                        thick=F(find(sz2, "thickness")[0][1]) if find(sz2, "thickness") else 0.15,
                                        side=side, kind="fp_text", angle=F(at2[3]) if len(at2) > 3 else 0.0))
        for pr in find(f, "property"):
            if pr[1] in ("Reference",):
                lay = find(pr, "layer")[0][1]
                hide = find(pr, "hide")
                if lay in ("F.SilkS", "B.SilkS") and not (hide and hide[0][1] == "yes"):
                    at2 = find(pr, "at")[0]
                    dx, dy = rot(F(at2[1]), F(at2[2]), r)
                    fnt = find(find(pr, "effects")[0], "font")[0]
                    fp["texts"].append(dict(text=pr[2], x=x + dx, y=y + dy, size=F(find(fnt, "size")[0][1]),
                                            thick=F(find(fnt, "thickness")[0][1]) if find(fnt, "thickness") else 0.15,
                                            side=lay, kind="reference", angle=0.0))
        return fp

    def smd_parts(self):
        return [f for f in self.footprints if "smd" in f["attrs"]]

    def board_parts(self):
        """Footprints that are real components (not mechanical)."""
        return [f for f in self.footprints if "exclude_from_bom" not in f["attrs"]
                and not f["ref"].startswith("MH")]

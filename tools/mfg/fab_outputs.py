"""Generate candidate Gerber/Excellon files for the OSBAMS PCB with gerbonara (writer only)."""
import math, os, zipfile
from gerbonara import GerberFile, ExcellonFile, LayerStack
from gerbonara.apertures import CircleAperture, RectangleAperture, ObroundAperture
from gerbonara.apertures import ExcellonTool
from gerbonara.graphic_objects import Line, Flash, Region
from gerbonara.cam import FileSettings
from gerbonara.layers import NamingScheme
from gerbonara.newstroke import Newstroke
from gerbonara.utils import MM

import functools
CircleAperture = functools.partial(CircleAperture, unit=MM)
RectangleAperture = functools.partial(RectangleAperture, unit=MM)
ObroundAperture = functools.partial(ObroundAperture, unit=MM)
_Line, _Flash, _Region = Line, Flash, Region
Line = functools.partial(_Line, unit=MM)
Flash = functools.partial(_Flash, unit=MM)
Region = functools.partial(_Region, unit=MM)

_font = None


def _pad_objects(board, pad, expansion=0.0):
    """Return gerbonara objects (Flash/Region) for one pad shape in Gerber coordinates."""
    gx, gy = board.g(pad["x"], pad["y"])
    w, h = pad["w"] + 2 * expansion, pad["h"] + 2 * expansion
    a = round(pad["ang"]) % 360
    if a not in (0, 90, 180, 270):
        raise ValueError(f"pad angle {pad['ang']} not a multiple of 90")
    if a in (90, 270):
        w, h = h, w
    sh = pad["shape"]
    if sh == "circle":
        return [Flash(gx, gy, CircleAperture(w))] if abs(w - h) < 1e-9 else \
               [Flash(gx, gy, ObroundAperture(w, h))]
    if sh == "rect":
        return [Flash(gx, gy, RectangleAperture(w, h))]
    if sh == "oval":
        return [Flash(gx, gy, ObroundAperture(w, h))]
    if sh == "roundrect":
        r = pad["rratio"] * min(w, h)
        pts = []
        for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                           (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
            for k in range(9):
                t = math.radians(a0 + 90 * k / 8)
                pts.append((gx + cx + r * math.cos(t), gy + cy + r * math.sin(t)))
        return [Region(pts)]
    raise ValueError(f"unsupported pad shape {sh}")


def _stroke_text(board, t, objs):
    global _font
    if _font is None:
        _font = Newstroke()
    strokes = list(_font.render(t["text"], size=t["size"]))
    if not strokes:
        return
    xs = [x for s in strokes for x, _ in s]
    ys = [y for s in strokes for _, y in s]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    gx, gy = board.g(t["x"], t["y"])
    ap = CircleAperture(t["thick"])
    for s in strokes:
        for (x1, y1), (x2, y2) in zip(s[:-1], s[1:]):
            objs.append(Line(gx + x1 - cx, gy - (y1 - cy), gx + x2 - cx, gy - (y2 - cy), ap))


def build(board):
    top_cu, bot_cu, top_mask, bot_mask, top_paste, bot_paste = ([] for _ in range(6))
    top_silk, bot_silk, outline = [], [], []
    pth, npth = [], []
    # ---- tracks and zones
    for s in board.segments:
        x1, y1 = board.g(s["x1"], s["y1"])
        x2, y2 = board.g(s["x2"], s["y2"])
        tgt = top_cu if s["layer"] == "F.Cu" else bot_cu
        tgt.append(Line(x1, y1, x2, y2, CircleAperture(s["w"])))
    for z in board.zones:
        tgt = top_cu if z["layer"] == "F.Cu" else bot_cu
        for poly in z["fills"]:
            tgt.append(Region([board.g(x, y) for x, y in poly]))
    # ---- pads
    for fp in board.footprints:
        for p in fp["pads"]:
            ls = p["layers"]
            on_f = any(l in ls for l in ("*.Cu", "F.Cu", "F&B.Cu"))
            on_b = any(l in ls for l in ("*.Cu", "B.Cu", "F&B.Cu"))
            mask_f = any(l in ls for l in ("*.Mask", "F.Mask"))
            mask_b = any(l in ls for l in ("*.Mask", "B.Mask"))
            paste_f = "F.Paste" in ls
            paste_b = "B.Paste" in ls
            if p["type"] != "np_thru_hole":
                if on_f: top_cu.extend(_pad_objects(board, p))
                if on_b: bot_cu.extend(_pad_objects(board, p))
            if mask_f: top_mask.extend(_pad_objects(board, p))
            if mask_b: bot_mask.extend(_pad_objects(board, p))
            if paste_f: top_paste.extend(_pad_objects(board, p))
            if paste_b: bot_paste.extend(_pad_objects(board, p))
            if p["drill"]:
                gx, gy = board.g(p["x"], p["y"])
                (pth if p["type"] == "thru_hole" else npth).append((gx, gy, p["drill"]))
    # ---- silkscreen (footprint graphics + reference text)
    for fp in board.footprints:
        for kind, side, w, data in fp["silk"]:
            tgt = top_silk if side == "F.SilkS" else bot_silk
            ap = CircleAperture(w)
            if kind in ("line", "poly"):
                pts = [board.g(x, y) for x, y in data]
                for a, b in zip(pts[:-1], pts[1:]):
                    tgt.append(Line(a[0], a[1], b[0], b[1], ap))
            elif kind == "fillpoly":
                tgt.append(Region([board.g(x, y) for x, y in data]))
            elif kind == "circle":
                cx, cy, r = data
                gx, gy = board.g(cx, cy)
                n = max(24, int(r * 24))
                pts = [(gx + r * math.cos(2 * math.pi * k / n), gy + r * math.sin(2 * math.pi * k / n))
                       for k in range(n + 1)]
                for a, b in zip(pts[:-1], pts[1:]):
                    tgt.append(Line(a[0], a[1], b[0], b[1], ap))
            elif kind == "arc":
                (sx, sy), (mx, my), (ex, ey) = data
                # circle through three points
                d = 2 * (sx * (my - ey) + mx * (ey - sy) + ex * (sy - my))
                ux = ((sx**2 + sy**2) * (my - ey) + (mx**2 + my**2) * (ey - sy) + (ex**2 + ey**2) * (sy - my)) / d
                uy = ((sx**2 + sy**2) * (ex - mx) + (mx**2 + my**2) * (sx - ex) + (ex**2 + ey**2) * (mx - sx)) / d
                r = math.hypot(sx - ux, sy - uy)
                a0, am, a1 = (math.atan2(py - uy, px - ux) for px, py in ((sx, sy), (mx, my), (ex, ey)))
                def norm(a): return a % (2 * math.pi)
                ccw = norm(am - a0) < norm(a1 - a0)
                span = norm(a1 - a0) if ccw else -norm(a0 - a1)
                pts = [board.g(ux + r * math.cos(a0 + span * k / 16), uy + r * math.sin(a0 + span * k / 16))
                       for k in range(17)]
                for a, b in zip(pts[:-1], pts[1:]):
                    tgt.append(Line(a[0], a[1], b[0], b[1], ap))
        for t in fp["texts"]:
            if t["kind"] == "fp_text" and t["text"] in ("",):
                continue
            _stroke_text(board, t, top_silk if t["side"] == "F.SilkS" else bot_silk)
    # ---- outline
    ap = CircleAperture(board.edge_width)
    pts = [(0, 0), (board.width, 0), (board.width, board.height), (0, board.height), (0, 0)]
    for a, b in zip(pts[:-1], pts[1:]):
        outline.append(Line(a[0], a[1], b[0], b[1], ap))
    # ---- excellon
    def drill_file(items, plated):
        tools = {}
        objs = []
        for x, y, d in items:
            t = tools.setdefault(round(d, 3), ExcellonTool(round(d, 3), plated=plated, unit=MM))
            objs.append(Flash(x, y, t))
        return ExcellonFile(objects=objs)
    G = lambda o: GerberFile(objects=o)
    stack = LayerStack(
        graphic_layers={('top', 'copper'): G(top_cu), ('bottom', 'copper'): G(bot_cu),
                        ('top', 'mask'): G(top_mask), ('bottom', 'mask'): G(bot_mask),
                        ('top', 'paste'): G(top_paste), ('bottom', 'paste'): G(bot_paste),
                        ('top', 'silk'): G(top_silk), ('bottom', 'silk'): G(bot_silk),
                        ('mechanical', 'outline'): G(outline)},
        drill_pth=drill_file(pth, True), drill_npth=drill_file(npth, False), board_name="OSBAMS_Rev2")
    return stack, dict(pth=pth, npth=npth, counts=dict(top_cu=len(top_cu), bot_cu=len(bot_cu),
                       top_mask=len(top_mask), bot_mask=len(bot_mask), top_paste=len(top_paste),
                       bot_paste=len(bot_paste), top_silk=len(top_silk), bot_silk=len(bot_silk)))


def save(stack, gerber_dir, drill_dir, zip_path, prefix="OSBAMS_Rev2"):
    """Write files; Excellon goes to Drill/, copper/mask/silk/paste/outline to Gerber/; zip holds all."""
    import shutil, tempfile
    tmp = tempfile.mkdtemp()
    stack.save_to_directory(tmp, naming_scheme=NamingScheme.kicad, board_name=prefix,
                            gerber_settings=FileSettings.defaults(), excellon_settings=None)
    os.makedirs(gerber_dir, exist_ok=True); os.makedirs(drill_dir, exist_ok=True)
    names = []
    for f in sorted(os.listdir(tmp)):
        dest = drill_dir if f.lower().endswith(".drl") else gerber_dir
        shutil.copy(os.path.join(tmp, f), os.path.join(dest, f))
        names.append((dest, f))
    shutil.rmtree(tmp)
    return names

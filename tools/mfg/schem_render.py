"""Render the KiCad schematic (script-based, not a KiCad plot) with matplotlib."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

WIRE, SYM, PIN, LAB, TXT = "#006400", "#8b0000", "#8b0000", "#0000aa", "#222222"


def draw(sch, ax, view=None):
    ax.set_aspect("equal")
    for w in sch.wires:
        ax.plot([w[0][0], w[1][0]], [w[0][1], w[1][1]], color=WIRE, lw=1.1, solid_capstyle="round")
    for x, y in sch.junctions:
        ax.plot(x, y, "o", color=WIRE, ms=3)
    for x, y in sch.no_connects:
        ax.plot([x - .8, x + .8], [y - .8, y + .8], color="#0000aa", lw=1); ax.plot([x - .8, x + .8], [y + .8, y - .8], color="#0000aa", lw=1)
    for s in sch.symbols:
        for kind, pts, filled in s["gfx"]:
            ax.add_patch(Polygon(pts, closed=False, fill=filled, fc="#e8c0c0" if filled else "none", ec=SYM, lw=1.2))
        for p in s["pins"]:
            ax.plot([p["at"][0], p["end"][0]], [p["at"][1], p["end"][1]], color=PIN, lw=1)
            dx = p["end"][0] - p["at"][0]; dy = p["end"][1] - p["at"][1]
            ax.text(p["end"][0] + (0.5 if dx >= 0 and dy == 0 else -0.5 if dx < 0 else 0), p["end"][1] + (0.6 if dy != 0 else 0),
                    p["name"], fontsize=3.6, color=SYM, va="center", ha="left" if dx >= 0 else "right")
            ax.text(p["at"][0] + (0.3 if dx >= 0 else -0.3), p["at"][1] + 0.8, p["num"], fontsize=3.2, color="#555", ha="left" if dx >= 0 else "right")
        for key in ("Reference", "Value"):
            pr = s["props"].get(key)
            if pr and not pr["hide"]:
                ax.text(pr["x"], pr["y"], pr["text"], fontsize=4.6 if key == "Reference" else 3.8, color="#0b3d91" if key == "Reference" else "#333",
                        ha="center", va="center", fontweight="bold" if key == "Reference" else "normal")
    for n, x, y in sch.labels:
        ax.plot(x, y, "s", color=LAB, ms=1.6)
        ax.text(x + 0.6, y + 0.7, n, fontsize=3.8, color=LAB, ha="left", va="bottom")
    for t, x, y in sch.texts:
        ax.text(x, y, t, fontsize=4.4, color=TXT, ha="left", va="center", style="italic")
    for x0, y0, x1, y1 in sch.boxes:
        ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color="#777777", lw=0.8, ls=(0, (5, 3)))
    if view:
        ax.set_xlim(view[0], view[2]); ax.set_ylim(view[3], view[1])
    else:
        ax.set_xlim(55, 205); ax.set_ylim(165, 28)
    ax.axis("off")


def page(sch, title, view=None, subtitle=""):
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.03, 0.07, 0.94, 0.82])
    draw(sch, ax, view)
    fig.text(0.03, 0.95, title, fontsize=13, fontweight="bold")
    fig.text(0.03, 0.92, subtitle, fontsize=7, color="#444")
    fig.text(0.03, 0.02, "OSBAMS Rev.2 controller PCB — rendered by tools/mfg/schem_render.py from 'OSBAMS PCB.kicad_sch' "
             "(NOT a KiCad plot; re-export with KiCad before release)", fontsize=6, color="#a00")
    return fig

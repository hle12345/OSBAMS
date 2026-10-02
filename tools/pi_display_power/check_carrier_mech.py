#!/usr/bin/env python3
"""Mechanical fit of the Pi Power Carrier (plan view against the official Raspberry Pi 5 mechanical drawing RP-008347-DS-1, digitised +-0.3 mm), key / support posts, stack heights,
and the mechanical placement drawing. usage: check_carrier_mech.py <project dir>"""
import sys, os, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_carrier import *
D = sys.argv[1]
I = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasheet_inputs.json")))
d = I["interposer_socket_dims"]["value"]; BODY, TAIL, PLASTIC, TIP = d["body_height_mm"], d["tail_length_mm"], d["pi_header_plastic_mm"], d["pi_pin_tip_height_mm"]
HDR_X, HDR_Y, PI_W = 32.5, 3.5, 65.0
PI = (0.0, 0.0, 85.0, 56.0)
COMP = {"A chip left of centre": (7.1, 7.0, 17.7, 20.2), "B chip below header": (25.8, 11.9, 40.5, 22.0), "C chip right": (52.3, 15.0, 64.5, 27.1), "D SoC heat spreader / Active Cooler": (24.5, 24.6, 41.7, 41.7),
        "E small part under header (right)": (55.1, 6.5, 56.8, 9.5), "F connector by right hole": (65.2, 1.0, 68.2, 7.0), "G connector by right hole (2)": (65.3, 8.3, 69.7, 15.7), "H feature by right hole": (60.0, 8.0, 63.0, 11.0),
        "USB/Ethernet stack": (70.8, 1.0, 85.0, 44.0)}
b2p = lambda x, y: (x - PI_OX, y - PI_OY)
def rect_dist(px, py, r): dx = max(r[0] - px, 0, px - r[2]); dy = max(r[1] - py, 0, py - r[3]); return (dx * dx + dy * dy) ** 0.5
rev = lambda x, y: (2 * HDR_X - x, 2 * HDR_Y - y)           # 180 deg about the header centre
outline = [b2p(*p) for p in [(0, 0), (BOARD_W, 0), (BOARD_W, MAIN_H), (TAB[2], MAIN_H), (TAB[2], BOARD_H), (TAB[0], BOARD_H), (TAB[0], MAIN_H), (0, MAIN_H)]]
POST_D = 6.0                                              # M3 standoff, hex 5.5 mm -> 6 mm used
out = ["Pi Power Carrier RevB - mechanical fit, plan view vs the official Raspberry Pi 5 drawing RP-008347-DS-1 (digitised, +-0.3 mm); Pi frame: origin = Pi top-left, header axis y = 3.5, header centre x = 32.5", ""]
ok = True
ox = [p[0] for p in outline]; oy = [p[1] for p in outline]
out.append(f"Carrier outline in Pi coordinates: x {min(ox):.1f}..{max(ox):.1f}, y {min(oy):.1f}..{max(oy):.1f} mm ({BOARD_W:.0f} x {BOARD_H:.1f} mm). Main body y <= -0.5 mm (outside the Pi outline); plug tab x 0..65, y -0.5..7.5 mm over the header (same footprint as the RC2 interposer).")
# 1. correct orientation: what lies under the carrier in plan
under = [(n, r) for n, r in COMP.items() if r[0] < 65.0 and r[2] > 0.0 and r[1] < 7.5 and r[3] > -0.5]
out.append("Components under the plug tab in plan (the carrier floats G = %.1f mm above the Pi PCB): %s" % (BODY + PLASTIC, ", ".join(n for n, _ in under) or "none"))
for n in ("D SoC heat spreader / Active Cooler", "USB/Ethernet stack", "F connector by right hole", "G connector by right hole (2)", "C chip right", "B chip below header"):
    r = COMP[n]; dx = max(r[0] - 65.0, 0 - r[2], 0); dy = max(r[1] - 7.5, -60 - r[3], 0); out.append(f"  plan gap tab -> {n}: {(dx*dx+dy*dy)**0.5:.1f} mm")
main_gap_usb = COMP["USB/Ethernet stack"][1] - (-0.5)
out.append(f"  main body vs USB/Ethernet stack (x {COMP['USB/Ethernet stack'][0]}..85, y >= {COMP['USB/Ethernet stack'][1]}): the body ends at Pi y = -0.5, i.e. {main_gap_usb:.1f} mm short of the stack in plan -> the body is beside/above the Pi's top edge, not over any connector.")
ok &= main_gap_usb > 1.0
# 2. posts: correct orientation free air, reversed -> bare PCB
out.append(""); out.append(f"Key / support posts (M3, {POST_D:.0f} mm assumed footprint). Correct orientation: all posts are outside the Pi outline (Pi y < -0.5) -> they stand on the enclosure floor in free air.")
keyed = []
for ref, (bx, by) in MECH_HOLES.items():
    px, py = b2p(bx, by); free = py + POST_D / 2 < -0.5
    xr, yr = rev(px, py); over = PI[0] < xr < PI[2] and PI[1] < yr < PI[3]
    dmin, nm = min((rect_dist(xr, yr, r) - POST_D / 2, n) for n, r in COMP.items())
    good = over and dmin >= 1.5
    out.append(f"  {ref} at Pi ({px:.1f}, {py:.1f}): {'free air (PASS)' if free else 'OVER THE PI (FAIL)'}; reversed 180 deg -> ({xr:.1f}, {yr:.1f}): " + (f"over the Pi PCB, {dmin:.1f} mm clear of the nearest component ({nm}) -> lands on bare PCB: KEY POST" if good else ("over the Pi but within 1.5 mm of a component - not used as a key" if over else "outside the Pi outline (support only, no keying)")))
    ok &= free
    if good: keyed.append(ref)
out.append(f"  Key posts (land on bare PCB when reversed): {', '.join(keyed)}"); ok &= len(keyed) >= 2
# 3. heights
G = BODY + PLASTIC; L = 20.0; margin = L - BODY - TIP
out += ["", f"Heights - Samtec SSW-120-01-L-D (body {BODY} mm, tail {TAIL} mm; Pi pins protrude {TIP - PLASTIC:.1f} mm above the {PLASTIC} mm header plastic, tip {TIP} mm):",
        f"  Seated gap G (carrier underside -> Pi PCB) = {BODY} + {PLASTIC} = {G:.2f} mm -> header-end spacers M1/M2: M2.5 x 11 mm.",
        f"  Carrier top surface = {G + 1.6:.1f} mm above the Pi PCB (parts on the carrier add their own height).",
        f"  Standoff length L (enclosure floor -> carrier underside) = Pi standoff height + 1.6 + {G:.2f}; with L = 20 mm the Pi standoffs are {L - 1.6 - G:.1f} mm.",
        f"  Reversed fit: posts rest on the Pi PCB -> socket face at L - {BODY} = {L - BODY:.1f} mm vs pin tips {TIP} mm -> margin {margin:+.1f} mm: " + ("pins cannot enter (PASS)" if margin >= 1.5 else "INSUFFICIENT"),
        f"  Minimum standoff length for >= 1.5 mm margin: {BODY + TIP + 1.5:.1f} mm  -> use M3 x 20 mm (Pi standoffs 7.4 mm). With shorter posts the key fails.",
        "  Carrier underside parts: RSDW40F-05 pins protrude 5.6 mm min below the board (spec side view) in free air beside the Pi; with L = 20 mm there is 14 mm to the floor. THT leads of C2/C4/J_IN/J_DISP are in free air. Only the SSW tails (2.64 mm) and the header-end spacers are over the Pi."]
ok &= margin >= 1.5
out += ["", "Clearances to the rest of the Pi and enclosure:",
        "  Active Cooler / SoC: the carrier body is outside the Pi outline; the plug tab is 17.1 mm (plan) from the SoC box D -> no collision (board floats 11 mm over header-side chips <= ~2 mm).",
        "  USB / Ethernet: plan gap tab -> stack 5.8 mm; body ends 1.5 mm before the stack's first edge in plan (the stack is 16 mm tall, the carrier body is outside the Pi PCB outline).",
        "  DSI / CSI flex connectors (left edge, Pi y >= 20 mm) and the PoE 2x2 header (bottom right): not under the carrier (> 12 mm). DSI ribbon routes away from the header edge below the carrier plane.",
        "  Power cables: J_IN and J_DISP mate toward +x (board right edge), away from the Pi; the display's DSI ribbon and USB-C power input are unaffected.",
        "  Small connector F by the right mounting hole is 0.2 mm from the tab edge in plan; the carrier floats 11 mm above it - check its height at fit.",
        f"  Enclosure envelope (plan): carrier {BOARD_W:.0f} x {BOARD_H:.1f} mm over the Pi's 85 x 56 mm; combined x {min(-7.5, 0):.1f}..85, y -60..56 mm; posts reach the floor {L:.0f} mm below the carrier. The official Pi 5 case does not take it: custom enclosure or open frame; wall clearance >= 2 mm around the outline.",
        "  Weight: the module (~25 g) and the carrier hang from the four M3 standoffs to the enclosure floor; the 2x20 socket carries no mechanical load (header-end spacers M1/M2 only locate/relieve the header)."]
out += ["", "RESULT (plan view + heights): " + ("PASS" if ok else "FAIL"), "Not covered: no STEP model of the Pi 5 / SSW socket / RSDW module was available: confirm with a physical fit (first-article D1) incl. the real standoffs."]
txt = "\n".join(out); print(txt); open(os.path.join(D, "reports", "Mechanical_fit_check.txt"), "w").write(txt + "\n")
# ---- drawing
fig, ax = plt.subplots(figsize=(13, 13.5)); ax.set_aspect("equal"); ax.invert_yaxis()
ax.add_patch(Rectangle((PI[0], PI[1]), PI[2], PI[3], fc="#e8f5e9", ec="#2e7d32", lw=1.8)); ax.text(2, 54, "Raspberry Pi 5 (85 x 56)", fontsize=8, color="#2e7d32")
for n, r in COMP.items(): ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], fc="#cfd8dc", ec="#546e7a", lw=0.8)); ax.text(r[0] + 0.5, r[1] + 2, n.split()[0], fontsize=7, color="#37474f")
ax.text(26, 33, "SoC / Active Cooler", fontsize=8, color="#37474f"); ax.text(72, 24, "USB / Ethernet", fontsize=8, color="#37474f")
ax.add_patch(Polygon(outline, closed=True, fc="#bbdefb", ec="#0d47a1", lw=2, alpha=0.55)); 
for ref, (bx, by) in MECH_HOLES.items():
    px, py = b2p(bx, by); ax.add_patch(Circle((px, py), POST_D / 2, fc="#ffcdd2" if ref in keyed else "#fff9c4", ec="#b71c1c" if ref in keyed else "#f57f17", lw=1.5)); ax.text(px + 3.4, py + 1, ref + (" key" if ref in keyed else " support"), fontsize=8)
    if ref in keyed:
        xr, yr = rev(px, py); ax.add_patch(Circle((xr, yr), POST_D / 2, fc="none", ec="#b71c1c", lw=1.2, ls="--")); ax.annotate("", xy=(xr, yr), xytext=(px, py), arrowprops=dict(arrowstyle="->", color="#b71c1c", ls=":", lw=0.8))
for ref, (bx, by) in PI_HOLES.items(): px, py = b2p(bx, by); ax.add_patch(Circle((px, py), 1.35, fc="white", ec="#0d47a1")); ax.text(px - 1, py - 2.5, ref, fontsize=7)
rev_out = [rev(*p) for p in outline]; ax.add_patch(Polygon(rev_out, closed=True, fc="none", ec="#b71c1c", lw=1, ls="--")); ax.text(2, 62, "reversed (180 deg) outline - blocked by the key posts", fontsize=7, color="#b71c1c")
ax.plot([-3, 68], [HDR_Y, HDR_Y], color="#6a1b9a", lw=0.8, ls="-."); ax.add_patch(Rectangle((HDR_X - 25.4, HDR_Y - 2.54), 50.8, 5.08, fc="#fff59d", ec="#6a1b9a", lw=1)); ax.text(HDR_X - 8, HDR_Y + 0.9, "2x20 header / SSW-120-01-L-D", fontsize=7)
mx, my = b2p(*U1_C); ax.add_patch(Rectangle((mx - 12.7, my - 25.4), 25.4, 50.8, fc="#fff3e0", ec="#e65100", lw=1.5)); ax.text(mx - 11, my, "RSDW40F-05\n(primary at top,\nsecondary toward the Pi)", fontsize=8)
for ref, lab in (("J_IN", "J_IN 12 V in  ->"), ("J_DISP", "J_DISP display 5 V  ->")): bx, by, _ = POS[ref]; px, py = b2p(bx, by); ax.add_patch(Rectangle((px - 4, py - 4), 12, 8, fc="#e3f2fd", ec="#0d47a1")); ax.text(px - 6, py - 5.5, lab, fontsize=8)
ax.annotate("", xy=(79.5, -57), xytext=(79.5, -2), arrowprops=dict(arrowstyle="<->", color="k")); ax.text(81, -30, f"{MAIN_H + 0.5:.0f} mm main body", fontsize=8, rotation=90, va="center")
ax.set_xlim(-14, 100); ax.set_ylim(70, -64); ax.set_title(f"OSBAMS Pi Power Carrier RevB - mechanical placement over the Raspberry Pi 5 (plan view, Pi frame, mm)", fontsize=11, fontweight="bold"); ax.grid(alpha=0.25)
fig.savefig(os.path.join(D, "docs", "Mechanical_placement_drawing.png"), dpi=130, bbox_inches="tight"); fig.savefig(os.path.join(D, "docs", "Mechanical_placement_drawing.pdf"), bbox_inches="tight")
sys.exit(0 if ok else 1)
